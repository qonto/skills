// One-off driver: run EVERY supplier invoice in a reads bundle through the real
// Finance PR engine (Prepare) with an optional trusted policy. Read-only; stores
// immutable PRs so each can later be Act-ed individually. No Qonto mutation.
import { readFileSync } from 'node:fs';
import {
  EventLog,
  prepare,
  parseTrustedPolicyText,
  systemClock,
  POLICY,
  type Evidence,
  type UserRequest,
  type TrustedPolicy,
} from '../engine/index.js';
import { FileStore } from './fileStore.js';
import { evidenceFromQonto } from './qontoAdapter.js';

const readsPath = process.argv[2];
const policyPath = process.argv[3];
const bundle = JSON.parse(readFileSync(readsPath, 'utf8'));
const invoices: any[] = bundle.supplier_invoices.supplier_invoices;

let policy: TrustedPolicy | null = null;
if (policyPath) policy = parseTrustedPolicyText(readFileSync(policyPath, 'utf8'));

const store = new FileStore('.finance-pr');
const rows: string[] = [];
console.log(`\nRunning ${invoices.length} invoices through the engine (policy=${policyPath ? 'ON' : 'off'})\n`);

invoices.forEach((inv, i) => {
  const prId = `FPR-${String(i + 1).padStart(2, '0')}`;
  const evidence: Evidence = evidenceFromQonto({
    organization: bundle.organization,
    membership: bundle.membership,
    supplier_invoice: inv,
    supplier_invoices: bundle.supplier_invoices,
    observed_at: bundle.observed_at,
  } as any);
  const request: UserRequest = {
    text: `Prepare invoice ${evidence.invoice.invoice_number} for payment review.`,
    source: 'user_chat',
    message_id: `checkall-${i}`,
  };
  const log = new EventLog(systemClock);
  const r = prepare({ request, evidence, clock: systemClock, events: log, prId, trustedPolicy: policy });
  store.putPr(r.stored);
  store.putLifecycle(r.stored.body.pr_id, r.decision === 'blocked' ? 'blocked' : 'prepared');

  const failedGates = r.gates.filter((g) => g.status !== 'pass');
  const matSignals = r.signals.filter((s) => s.status === 'observed' && s.risk >= POLICY.material_signal_risk);
  const amt = `${evidence.invoice.amount.value} ${evidence.invoice.amount.currency}`;
  rows.push(
    `${prId} ${r.stored.integrity.fingerprint}  ${r.decision.toUpperCase().padEnd(24)} ${evidence.invoice.supplier_name.slice(0, 26).padEnd(27)} ${amt.padStart(16)}  cov=${Math.round((r.risk.coverage ?? 0) * 100)}% band=${(r.risk as any).band}`,
  );
  if (failedGates.length || matSignals.length) {
    for (const g of failedGates) rows.push(`        GATE  [${g.status}] ${g.id} — ${g.reason}`);
    for (const s of matSignals) rows.push(`        SIGNAL [${s.status} risk=${s.risk}] ${s.id}`);
  }
});

console.log(rows.join('\n'));
console.log(`\nStored ${invoices.length} PRs in .finance-pr/ (fingerprints inside each). No Qonto mutation.\n`);
