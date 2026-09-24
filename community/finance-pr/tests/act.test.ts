import { describe, expect, it } from 'vitest';
import { act, approvalFromText } from '../src/engine/act.js';
import { prepare } from '../src/engine/prepare.js';
import { EventLog } from '../src/engine/events.js';
import { MemoryStore } from '../src/engine/store.js';
import { fixedClock, frozenClock } from '../src/engine/clock.js';
import { parseApproval } from '../src/engine/intent.js';
import { DisabledWriteAdapter, type WriteAdapter } from '../src/engine/writeAdapter.js';
import { hist, IBAN_A, IBAN_B, makeEvidence, makeInvoice, prepareRequest } from './helpers.js';
import type { Approval, StoredPr } from '../src/engine/types.js';

function preparedClean(prId = 'FPR-T') {
  const clock = fixedClock('2026-07-12T09:00:00.000Z', 1000);
  const events = new EventLog(clock);
  const store = new MemoryStore();
  const ev = makeEvidence({ supplier_history: [hist('1000', IBAN_A), hist('1100', IBAN_A), hist('900', IBAN_A), hist('1050', IBAN_A)] });
  const res = prepare({ request: prepareRequest, evidence: ev, clock, events, prId });
  store.putPr(res.stored);
  const fp = res.stored.integrity.fingerprint;
  const text = `Approve Finance PR ${prId}, fingerprint ${fp}`;
  const approval = approvalFromText(text, parseApproval(text)!, 'finance_reviewer@demo', res.reviewer_route, clock);
  store.putApproval(approval);
  return { clock, events, store, res, ev, fp, approval };
}

describe('Act revalidation & safety chain', () => {
  it('ready_for_finance_review by default (clean PR)', () => {
    expect(preparedClean().res.decision).toBe('ready_for_finance_review');
  });

  it('writes disabled by default → ready_for_qonto, no adapter call', async () => {
    const { store, events, res, approval, ev } = preparedClean();
    let calls = 0;
    const spy: WriteAdapter = { id: 'spy', async submit() { calls++; return { outcome: 'qonto_write_submitted', note: '' }; } };
    const r = await act({ store, prId: res.stored.body.pr_id, approval, freshInvoice: ev.invoice, clock: frozenClock('2026-07-12T09:05:00.000Z'), events, writeAdapter: spy });
    expect(r.outcome).toBe('ready_for_qonto');
    expect(calls).toBe(0);
  });

  it('wrong fingerprint blocks', async () => {
    const { store, events, res, ev } = preparedClean();
    const bad: Approval = { pr_id: res.stored.body.pr_id, fingerprint: 'DEAD-BEEF', approver: 'x', route: 'finance_reviewer', approved_at: '2026-07-12T09:05:00.000Z', raw_text: '' };
    const r = await act({ store, prId: res.stored.body.pr_id, approval: bad, freshInvoice: ev.invoice, clock: frozenClock('2026-07-12T09:05:00.000Z'), events });
    expect(r.outcome).toBe('blocked');
  });

  it('missing approval blocks', async () => {
    const { store, events, res, ev } = preparedClean();
    const r = await act({ store, prId: res.stored.body.pr_id, approval: null, freshInvoice: ev.invoice, clock: frozenClock('2026-07-12T09:05:00.000Z'), events });
    expect(r.outcome).toBe('blocked');
  });

  it('tampered stored body → integrity_failed', async () => {
    const { store, events, res, approval, ev } = preparedClean();
    const tampered: StoredPr = JSON.parse(JSON.stringify(store.getPr(res.stored.body.pr_id)));
    tampered.body.critical_state_display.amount.value = '9999.99';
    store.putPr(tampered);
    const r = await act({ store, prId: res.stored.body.pr_id, approval, freshInvoice: ev.invoice, clock: frozenClock('2026-07-12T09:05:00.000Z'), events });
    expect(r.outcome).toBe('integrity_failed');
  });

  it('expired PR → expired', async () => {
    const { store, events, res, approval, ev } = preparedClean();
    const r = await act({ store, prId: res.stored.body.pr_id, approval, freshInvoice: ev.invoice, clock: frozenClock('2026-07-12T11:00:00.000Z'), events });
    expect(r.outcome).toBe('expired');
  });

  it('changed amount after approval → stale', async () => {
    const { store, events, res, approval, ev } = preparedClean();
    const changed = makeInvoice({ ...ev.invoice, amount: { value: '2000.00', currency: 'EUR' } });
    const r = await act({ store, prId: res.stored.body.pr_id, approval, freshInvoice: changed, clock: frozenClock('2026-07-12T09:05:00.000Z'), events });
    expect(r.outcome).toBe('stale');
  });

  it('changed IBAN after approval → stale (blocked regardless of score)', async () => {
    const { store, events, res, approval, ev } = preparedClean();
    const changed = makeInvoice({ ...ev.invoice, iban: IBAN_B });
    const r = await act({ store, prId: res.stored.body.pr_id, approval, freshInvoice: changed, clock: frozenClock('2026-07-12T09:05:00.000Z'), events });
    expect(r.outcome).toBe('stale');
  });

  it('status flipped to paid after approval → stale', async () => {
    const { store, events, res, approval, ev } = preparedClean();
    const changed = makeInvoice({ ...ev.invoice, status: 'paid' });
    const r = await act({ store, prId: res.stored.body.pr_id, approval, freshInvoice: changed, clock: frozenClock('2026-07-12T09:05:00.000Z'), events });
    expect(r.outcome).toBe('stale');
  });

  it('act binds to the stored body: an unrelated fresh field (due_date) does not block', async () => {
    const { store, events, res, approval, ev } = preparedClean();
    const changed = makeInvoice({ ...ev.invoice, due_date: '2099-01-01' });
    const r = await act({ store, prId: res.stored.body.pr_id, approval, freshInvoice: changed, clock: frozenClock('2026-07-12T09:05:00.000Z'), events });
    expect(r.outcome).toBe('ready_for_qonto');
  });

  it('replay: second Act on the same PR is blocked', async () => {
    const { store, events, res, approval, ev } = preparedClean();
    const now = frozenClock('2026-07-12T09:05:00.000Z');
    const first = await act({ store, prId: res.stored.body.pr_id, approval, freshInvoice: ev.invoice, clock: now, events });
    const second = await act({ store, prId: res.stored.body.pr_id, approval, freshInvoice: ev.invoice, clock: now, events });
    expect(first.outcome).toBe('ready_for_qonto');
    expect(second.outcome).toBe('replay_blocked');
  });

  it('concurrent Act calls invoke the write adapter at most once', async () => {
    const { store, events, res, approval, ev } = preparedClean();
    let calls = 0;
    const counting: WriteAdapter = { id: 'count', async submit() { calls++; return { outcome: 'qonto_native_approval_pending', note: 'ok' }; } };
    const now = frozenClock('2026-07-12T09:05:00.000Z');
    const results = await Promise.all([
      act({ store, prId: res.stored.body.pr_id, approval, freshInvoice: ev.invoice, clock: now, events, writeAdapter: counting, writesEnabled: true }),
      act({ store, prId: res.stored.body.pr_id, approval, freshInvoice: ev.invoice, clock: now, events, writeAdapter: counting, writesEnabled: true }),
    ]);
    expect(calls).toBe(1);
    expect(results.filter((r) => r.outcome === 'replay_blocked')).toHaveLength(1);
    expect(results.filter((r) => r.outcome === 'qonto_native_approval_pending')).toHaveLength(1);
  });

  it('an ambiguous write result becomes execution_unknown and is not retried', async () => {
    const { store, events, res, approval, ev } = preparedClean();
    let calls = 0;
    const flaky: WriteAdapter = { id: 'flaky', async submit() { calls++; throw new Error('timeout'); } };
    const r = await act({ store, prId: res.stored.body.pr_id, approval, freshInvoice: ev.invoice, clock: frozenClock('2026-07-12T09:05:00.000Z'), events, writeAdapter: flaky, writesEnabled: true });
    expect(r.outcome).toBe('execution_unknown');
    expect(calls).toBe(1);
  });

  it('the default write adapter never mutates', async () => {
    const r = await DisabledWriteAdapter.submit({} as never);
    expect(r.outcome).toBe('ready_for_qonto');
  });
});
