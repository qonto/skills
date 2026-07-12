#!/usr/bin/env -S npx tsx
// Finance PR CLI — the local engine the Claude Skill invokes.
// Observe -> Prepare -> Act. Synthetic by default. Qonto WRITES ARE DISABLED.

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import {
  EventLog,
  act,
  approvalFromText,
  parseApproval,
  parseTrustedPolicyJson,
  parseTrustedPolicyText,
  prepare,
  renderReport,
  shortSummary,
  systemClock,
  type Evidence,
  type SupplierInvoiceEvidence,
  type TrustedPolicy,
  type UserRequest,
} from '../engine/index.js';
import { FileStore } from './fileStore.js';
import { evidenceFromQonto, invoiceFromQonto } from './qontoAdapter.js';
import { buildScenarios } from '../fixtures/scenarios.js';

function arg(name: string, fallback?: string): string | undefined {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && i + 1 < process.argv.length ? process.argv[i + 1] : fallback;
}
function readJson(path: string): unknown {
  return JSON.parse(readFileSync(path, 'utf8'));
}
function storeDir(): string {
  return arg('store', '.finance-pr')!;
}
function persistEvents(store: FileStore, log: EventLog): void {
  for (const e of log.all()) store.appendEvent(e);
}

const HELP = `
Finance PR — review before money moves.  (synthetic by default; Qonto writes disabled)

  finance-pr synth [A|B|C|D1|D2|D3|all]      Run a synthetic scenario through the engine
  finance-pr map    --bundle b.json [--out e.json]
                                             Map raw Qonto MCP JSON -> typed evidence
  finance-pr prepare --evidence e.json [--request "..."] [--source user_chat|document]
                     [--pr FPR-1] [--store DIR] [--policy trusted-policy.txt|.json]
                                             Build the immutable Finance PR (no mutation).
                                             --policy loads an explicitly trusted operator
                                             policy (role limits + hard block). Never from invoice text.
  finance-pr act    --pr FPR-1 --approval "Approve Finance PR FPR-1, fingerprint 7C91-A2B4"
                     [--fresh rawInvoice.json] [--store DIR]
                                             Revalidate + one-shot. Terminates at ready_for_qonto.
  finance-pr show   --pr FPR-1 [--store DIR]

Qonto MCP tools are read-only here. No tool moves money; Qonto native approval and
SCA always remain the user's own, in the Qonto app.
`;

async function cmdSynth(): Promise<void> {
  const which = (process.argv[3] ?? 'all').toUpperCase();
  const runs = await buildScenarios();
  if (which === 'ALL') {
    console.log('\nSYNTHETIC scenarios (driven through the real engine):\n');
    for (const r of runs) {
      const outcome = r.act ? r.act.outcome : '(prepare only)';
      console.log(`  ${r.id.padEnd(3)} ${shortSummary(r.stored).padEnd(46)} act:${outcome}`);
    }
    console.log('\nRun `finance-pr synth A` for the full report of one scenario.\n');
    return;
  }
  const run = runs.find((r) => r.id === which);
  if (!run) {
    console.error(`Unknown scenario "${which}". Use A, B, C, D1, D2, D3, or all.`);
    process.exit(1);
  }
  console.log(renderReport(run.prepare));
  if (run.act) console.log(`\nACT OUTCOME: ${run.act.outcome}\n  ${run.act.reasons.join('\n  ')}`);
}

function cmdMap(): void {
  const bundlePath = arg('bundle');
  if (!bundlePath) throw new Error('map requires --bundle <path>');
  const ev = evidenceFromQonto(readJson(bundlePath) as never);
  const out = arg('out');
  const json = JSON.stringify(ev, null, 2);
  if (out) {
    writeFileSync(out, json);
    console.log(`Wrote evidence -> ${out}  (data_mode=${ev.data_mode})`);
  } else {
    console.log(json);
  }
}

function cmdPrepare(): void {
  const evPath = arg('evidence');
  if (!evPath) throw new Error('prepare requires --evidence <path>');
  const evidence = readJson(evPath) as Evidence;
  const request: UserRequest = {
    text: arg('request', `Prepare invoice ${evidence.invoice.invoice_number} for payment review.`)!,
    source: (arg('source', 'user_chat') as UserRequest['source']),
    message_id: `cli-${Date.now()}`,
  };
  // Optional trusted policy — loaded ONLY from an explicit operator file, never
  // from the invoice/evidence. .json parses as JSON; anything else as key=value text.
  const policyPath = arg('policy');
  let trustedPolicy: TrustedPolicy | null = null;
  if (policyPath) {
    const text = readFileSync(policyPath, 'utf8');
    trustedPolicy = policyPath.endsWith('.json') ? parseTrustedPolicyJson(JSON.parse(text)) : parseTrustedPolicyText(text);
  }

  const dir = storeDir();
  const store = new FileStore(dir);
  const log = new EventLog(systemClock);
  const result = prepare({ request, evidence, clock: systemClock, events: log, prId: arg('pr'), trustedPolicy });
  store.putPr(result.stored);
  store.putLifecycle(result.stored.body.pr_id, result.decision === 'blocked' ? 'blocked' : 'prepared');
  persistEvents(store, log);

  // Sidecar: keep the observed invoice for a local `act` dry-run re-read.
  mkdirSync(join(dir, 'observed'), { recursive: true });
  writeFileSync(join(dir, 'observed', `${result.stored.body.pr_id}.json`), JSON.stringify(evidence.invoice, null, 2));

  console.log(renderReport(result));
  console.log(`\nStored in ${dir}. PR ${result.stored.body.pr_id} fingerprint ${result.stored.integrity.fingerprint}.`);
}

async function cmdAct(): Promise<void> {
  const prId = arg('pr');
  const approvalText = arg('approval');
  if (!prId || !approvalText) throw new Error('act requires --pr <id> and --approval "..."');
  const dir = storeDir();
  const store = new FileStore(dir);
  const stored = store.getPr(prId);
  if (!stored) throw new Error(`Unknown PR ${prId} in ${dir}`);

  const parsed = parseApproval(approvalText);
  const approval = parsed
    ? approvalFromText(approvalText, parsed, 'cli-reviewer', stored.body.policy.reviewer_route, systemClock)
    : null;

  // Fresh re-read: use --fresh if given, else the sidecar observed invoice.
  let fresh: SupplierInvoiceEvidence;
  const freshPath = arg('fresh');
  if (freshPath) {
    fresh = invoiceFromQonto(readJson(freshPath) as never);
  } else {
    const sidecar = join(dir, 'observed', `${prId}.json`);
    if (!existsSync(sidecar)) throw new Error('No --fresh invoice and no observed sidecar; provide --fresh <rawInvoice.json>.');
    fresh = JSON.parse(readFileSync(sidecar, 'utf8')) as SupplierInvoiceEvidence;
  }

  const log = new EventLog(systemClock);
  const result = await act({ store, prId, approval, freshInvoice: fresh, clock: systemClock, events: log });
  persistEvents(store, log);

  console.log(`\nACT ${prId} (${stored.integrity.fingerprint})`);
  console.log(`OUTCOME: ${result.outcome.toUpperCase()}`);
  for (const r of result.reasons) console.log(`  ${r}`);
  const failed = result.gates.filter((g) => g.status !== 'pass');
  if (failed.length) {
    console.log('  Gate detail:');
    for (const g of failed) console.log(`    [${g.status}] ${g.id} — ${g.reason}`);
  }
  console.log('\nQonto writes are disabled. Qonto native approval and SCA still apply, in the Qonto app.');
}

function cmdShow(): void {
  const prId = arg('pr');
  if (!prId) throw new Error('show requires --pr <id>');
  const store = new FileStore(storeDir());
  const stored = store.getPr(prId);
  if (!stored) throw new Error(`Unknown PR ${prId}`);
  console.log(JSON.stringify(stored, null, 2));
}

async function main(): Promise<void> {
  const cmd = process.argv[2];
  try {
    switch (cmd) {
      case 'synth':
        await cmdSynth();
        break;
      case 'map':
        cmdMap();
        break;
      case 'prepare':
        cmdPrepare();
        break;
      case 'act':
        await cmdAct();
        break;
      case 'show':
        cmdShow();
        break;
      default:
        console.log(HELP);
    }
  } catch (err) {
    console.error(`Error: ${(err as Error).message}`);
    process.exit(1);
  }
}

void main();
