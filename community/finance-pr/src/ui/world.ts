// Pure reducer: worldAt(events, cursorMs) -> World.
// Clean-room reimplementation of the FlowTwin idea (a pure function from a clock
// position + event track to the whole world). No FlowTwin code is used.
//
// The visual NEVER owns business state — it only projects engine domain events.

import type { DomainEvent, EventType } from '../engine/types.js';
import type { ScenarioRun, StationId } from '../fixtures/scenarios.js';
import { beatsFor } from '../fixtures/scenarios.js';

export type StationStatus = 'idle' | 'active' | 'done' | 'blocked' | 'review' | 'crossed';
export type WorldMode = 'flow' | 'blocked' | 'manual_review' | 'crossed';

export const STATION_ORDER: StationId[] = [
  'intake',
  'observe',
  'intent',
  'risk',
  'independent',
  'finance_pr',
  'approver',
  'act',
  'boundary',
  'qonto',
  'outcome',
];

const EVENT_STATION: Partial<Record<EventType, StationId>> = {
  invoice_observed: 'intake',
  evidence_collected: 'observe',
  intent_classified: 'intent',
  signal_evaluated: 'risk',
  hard_gate_evaluated: 'risk',
  second_review_requested: 'independent',
  second_review_returned: 'independent',
  finance_pr_prepared: 'finance_pr',
  finance_review_requested: 'approver',
  finance_pr_approved: 'approver',
  act_revalidation_started: 'act',
  finance_pr_blocked: 'risk',
  integrity_failed: 'boundary',
  state_stale: 'boundary',
  replay_blocked: 'boundary',
  expired: 'boundary',
  ready_for_qonto: 'boundary',
  qonto_write_submitted: 'boundary',
  qonto_native_approval_pending: 'qonto',
  execution_unknown: 'qonto',
};

const BLOCK_TYPES: EventType[] = ['integrity_failed', 'state_stale', 'replay_blocked', 'expired'];
const CROSS_TYPES: EventType[] = ['qonto_write_submitted', 'qonto_native_approval_pending', 'ready_for_qonto'];

export interface World {
  occurred: DomainEvent[];
  lastEvent: DomainEvent | null;
  tokenStation: StationId;
  status: Record<StationId, StationStatus>;
  visited: StationId[];
  dwellMs: number;
  mode: WorldMode;
  gate: 'locked' | 'open';
  terminalLabel: string | null;
}

function ms(e: DomainEvent, t0: number): number {
  return Date.parse(e.t) - t0;
}

export function totalMs(events: DomainEvent[]): number {
  if (events.length === 0) return 0;
  const t0 = Date.parse(events[0].t);
  return ms(events[events.length - 1], t0);
}

export function worldAt(events: DomainEvent[], cursorMs: number): World {
  const empty: Record<StationId, StationStatus> = Object.fromEntries(STATION_ORDER.map((s) => [s, 'idle'])) as Record<
    StationId,
    StationStatus
  >;
  if (events.length === 0) {
    return { occurred: [], lastEvent: null, tokenStation: 'intake', status: empty, visited: [], dwellMs: 0, mode: 'flow', gate: 'locked', terminalLabel: null };
  }

  const t0 = Date.parse(events[0].t);
  const occurred = events.filter((e) => ms(e, t0) <= cursorMs);
  const lastEvent = occurred.length ? occurred[occurred.length - 1] : null;

  // Token station + dwell (forward-only walk over occurred events).
  let curStation: StationId = 'intake';
  let entry = 0;
  const visited = new Set<StationId>(['intake']);
  for (const e of occurred) {
    const st = EVENT_STATION[e.type];
    if (!st) continue;
    visited.add(st);
    if (st !== curStation) {
      curStation = st;
      entry = ms(e, t0);
    }
  }
  const dwellMs = Math.max(0, cursorMs - entry);

  // Mode.
  const explicitBlocked =
    occurred.some((e) => BLOCK_TYPES.includes(e.type)) || occurred.some((e) => e.type === 'finance_pr_blocked');
  const crossed = occurred.some((e) => CROSS_TYPES.includes(e.type));
  const manualPark = !crossed && !explicitBlocked && lastEvent?.type === 'finance_review_requested' && curStation === 'approver';

  let mode: WorldMode = 'flow';
  if (explicitBlocked) mode = 'blocked';
  else if (crossed) mode = 'crossed';
  else if (manualPark) mode = 'manual_review';

  // Station statuses.
  const status = { ...empty };
  for (const s of STATION_ORDER) {
    if (visited.has(s)) status[s] = 'done';
  }
  if (mode === 'blocked') status[curStation] = 'blocked';
  else if (mode === 'manual_review') status[curStation] = 'review';
  else if (mode === 'crossed' && curStation === 'qonto') status[curStation] = 'crossed';
  else status[curStation] = 'active';

  const gate: 'locked' | 'open' = mode === 'crossed' ? 'open' : 'locked';

  const terminalLabel = terminalOf(occurred);

  return { occurred, lastEvent, tokenStation: curStation, status, visited: [...visited], dwellMs, mode, gate, terminalLabel };
}

function terminalOf(occurred: DomainEvent[]): string | null {
  const map: Partial<Record<EventType, string>> = {
    integrity_failed: 'INTEGRITY FAILED',
    state_stale: 'STALE STATE',
    replay_blocked: 'REPLAY BLOCKED',
    expired: 'EXPIRED',
    finance_pr_blocked: 'BLOCKED',
    qonto_native_approval_pending: 'QONTO NATIVE APPROVAL PENDING',
    ready_for_qonto: 'READY FOR QONTO',
    execution_unknown: 'EXECUTION UNKNOWN',
  };
  for (let i = occurred.length - 1; i >= 0; i--) {
    const label = map[occurred[i].type];
    if (label) return label;
  }
  return null;
}

// --- end-of-run summary (computed from events, not hard-coded counters) -----

export interface Summary {
  observed: number;
  prepared: number;
  ready_for_review: number;
  manual_review: number;
  blocked_before_qonto: number;
  approvals: number;
  submitted_across_boundary: number;
  native_pending: number;
  integrity_stale_replay_prevented: number;
  median_dwell_ms: number;
}

export function computeSummary(runs: ScenarioRun[]): Summary {
  let observed = 0,
    prepared = 0,
    ready = 0,
    manual = 0,
    blocked = 0,
    approvals = 0,
    submitted = 0,
    pending = 0,
    prevented = 0;
  const dwells: number[] = [];

  for (const run of runs) {
    const types = run.events.map((e) => e.type);
    if (types.includes('invoice_observed')) observed++;
    if (types.includes('finance_pr_prepared')) prepared++;
    if (run.prepare.decision === 'ready_for_finance_review') ready++;
    if (run.prepare.decision === 'manual_review_required') manual++;
    if (types.includes('finance_pr_approved')) approvals++;
    if (types.includes('qonto_write_submitted')) submitted++;
    if (types.includes('qonto_native_approval_pending')) pending++;
    const term = run.act?.outcome;
    if (run.prepare.decision === 'blocked') blocked++;
    if (term === 'integrity_failed' || term === 'stale' || term === 'replay_blocked' || term === 'expired') prevented++;

    // dwell per run = its total timeline span.
    dwells.push(totalMs(run.events));
  }

  dwells.sort((a, b) => a - b);
  const median = dwells.length ? dwells[Math.floor(dwells.length / 2)] : 0;

  return {
    observed,
    prepared,
    ready_for_review: ready,
    manual_review: manual,
    blocked_before_qonto: blocked,
    approvals,
    submitted_across_boundary: submitted,
    native_pending: pending,
    integrity_stale_replay_prevented: prevented,
    median_dwell_ms: median,
  };
}

export { beatsFor };
