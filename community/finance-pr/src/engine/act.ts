// ACT — reload the stored PR, revalidate integrity + fresh state, reserve the
// one-shot atomically, and permit at most one allowlisted write. Act NEVER
// accepts action parameters from the caller; every value comes from the stored,
// hashed body.

import type { Clock } from './clock.js';
import type { EventLog } from './events.js';
import type { PrStore } from './store.js';
import { actGates } from './gates.js';
import { DisabledWriteAdapter, type WriteAdapter } from './writeAdapter.js';
import type {
  ActOutcome,
  ActResult,
  Approval,
  DomainEvent,
  EventType,
  Gate,
  GateId,
  SupplierInvoiceEvidence,
} from './types.js';

export interface ActInput {
  store: PrStore;
  prId: string;
  /** Reloaded approval; the caller must NOT pass action parameters here. */
  approval: Approval | null;
  /** Fresh re-read of the target invoice at Act time. */
  freshInvoice: SupplierInvoiceEvidence;
  clock: Clock;
  events: EventLog;
  writeAdapter?: WriteAdapter;
  /** Real Qonto writes stay disabled unless explicitly enabled for a test. */
  writesEnabled?: boolean;
}

/** First failing gate (in this priority) decides the terminal outcome. */
const FAIL_PRIORITY: Array<{ id: GateId; outcome: ActOutcome; event: EventType }> = [
  { id: 'full_hash_matches', outcome: 'integrity_failed', event: 'integrity_failed' },
  { id: 'explicit_approval_present', outcome: 'blocked', event: 'finance_pr_blocked' },
  { id: 'finance_pr_id_and_fingerprint_match', outcome: 'blocked', event: 'finance_pr_blocked' },
  { id: 'approval_route_satisfied', outcome: 'blocked', event: 'finance_pr_blocked' },
  { id: 'not_expired', outcome: 'expired', event: 'expired' },
  { id: 'critical_qonto_state_unchanged', outcome: 'stale', event: 'state_stale' },
  { id: 'amount_currency_iban_supplier_unchanged', outcome: 'stale', event: 'state_stale' },
  { id: 'prepared_action_exact_match', outcome: 'blocked', event: 'finance_pr_blocked' },
  { id: 'not_already_paid_or_matched', outcome: 'blocked', event: 'finance_pr_blocked' },
  { id: 'not_used_or_in_progress', outcome: 'replay_blocked', event: 'replay_blocked' },
];

function terminal(
  store: PrStore,
  events: EventLog,
  prId: string,
  fingerprint: string,
  outcome: ActOutcome,
  gates: Gate[],
  reasons: string[],
  event: EventType,
  payload: Record<string, unknown> = {},
): ActResult {
  const result: ActResult = { pr_id: prId, fingerprint, outcome, gates, reasons };
  events.emit(event, prId, { outcome, ...payload }, reasons[0]);
  store.putActResult(result);
  store.putLifecycle(prId, outcome as never);
  return result;
}

export async function act(input: ActInput): Promise<ActResult> {
  const { store, prId, approval, freshInvoice, clock, events } = input;
  const writeAdapter = input.writeAdapter ?? DisabledWriteAdapter;
  const writesEnabled = input.writesEnabled ?? false;

  const stored = store.getPr(prId);
  if (!stored) {
    const r: ActResult = { pr_id: prId, fingerprint: 'n/a', outcome: 'blocked', gates: [], reasons: ['Unknown PR id.'] };
    events.emit('finance_pr_blocked', prId, { outcome: 'blocked' }, 'Unknown PR id.');
    return r;
  }
  const fingerprint = stored.integrity.fingerprint;

  events.emit('act_revalidation_started', prId, { fingerprint });

  // Never proceed on a PR that Prepare itself blocked.
  if (stored.body.policy.decision === 'blocked') {
    return terminal(
      store,
      events,
      prId,
      fingerprint,
      'blocked',
      [],
      ['PR was blocked at Prepare and cannot be acted upon.'],
      'finance_pr_blocked',
    );
  }

  const gates = actGates({
    body: stored.body,
    integrity: stored.integrity,
    approval,
    freshInvoice,
    nowIso: clock.now(),
    reservationAvailable: !store.isReserved(prId),
    writesEnabled,
  });

  // Safety gates = everything except the write-enable switch.
  const failing = FAIL_PRIORITY.find((p) => gates.find((g) => g.id === p.id)?.status === 'fail');
  if (failing) {
    const gate = gates.find((g) => g.id === failing.id)!;
    return terminal(store, events, prId, fingerprint, failing.outcome, gates, [gate.reason], failing.event);
  }

  // All safety gates passed. Reserve the one-shot ATOMICALLY — this is the
  // decisive at-most-once step; a racing caller gets false here.
  const reserved = store.reserveOnce(prId);
  if (!reserved) {
    return terminal(
      store,
      events,
      prId,
      fingerprint,
      'replay_blocked',
      gates,
      ['PR reservation already taken — replay blocked.'],
      'replay_blocked',
    );
  }

  // Writes disabled by default → verified ready_for_qonto handoff, no Qonto call.
  if (!writesEnabled) {
    return terminal(
      store,
      events,
      prId,
      fingerprint,
      'ready_for_qonto',
      gates,
      ['All safety gates passed. Writes disabled by default — verified ready_for_qonto handoff.'],
      'ready_for_qonto',
      { note: 'Qonto permissions, native approval, and SCA still apply.' },
    );
  }

  // Controlled write path. Exactly one attempt. No automatic retry.
  events.emit('qonto_write_submitted', prId, { adapter: writeAdapter.id });
  let outcome: ActOutcome;
  let note: string;
  try {
    const res = await writeAdapter.submit(stored.body);
    outcome = res.outcome;
    note = res.note;
  } catch (err) {
    // Ambiguous result → execution_unknown, NEVER retried.
    outcome = 'execution_unknown';
    note = `Write outcome ambiguous (${(err as Error).message}); reconciliation required. No retry.`;
  }

  const event: EventType =
    outcome === 'qonto_native_approval_pending'
      ? 'qonto_native_approval_pending'
      : outcome === 'execution_unknown'
        ? 'execution_unknown'
        : 'ready_for_qonto';

  const result: ActResult = { pr_id: prId, fingerprint, outcome, gates, reasons: [note] };
  events.emit(event, prId, { outcome, adapter: writeAdapter.id }, note);
  store.putActResult(result);
  store.putLifecycle(prId, outcome as never);
  return result;
}

/** Build an Approval record from an approval message + route. The action values
 * are intentionally NOT taken from here. */
export function approvalFromText(
  raw_text: string,
  parsed: { pr_id: string; fingerprint: string },
  approver: string,
  route: Approval['route'],
  clock: Clock,
): Approval {
  return {
    pr_id: parsed.pr_id,
    fingerprint: parsed.fingerprint,
    approver,
    route,
    approved_at: clock.now(),
    raw_text,
  };
}

export type { DomainEvent };
