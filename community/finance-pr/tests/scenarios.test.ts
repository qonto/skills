import { beforeAll, describe, expect, it } from 'vitest';
import { beatsFor, buildScenarios, type ScenarioRun } from '../src/fixtures/scenarios.js';

let runs: ScenarioRun[];
const byId = (id: string) => runs.find((r) => r.id === id)!;

beforeAll(async () => {
  runs = await buildScenarios();
});

describe('synthetic scenarios (driven through the real engine)', () => {
  it('build deterministically (identical fingerprints on a second build)', async () => {
    const again = await buildScenarios();
    for (let i = 0; i < runs.length; i++) {
      expect(again[i].stored.integrity.fingerprint).toBe(runs[i].stored.integrity.fingerprint);
    }
  });

  it('A: clean invoice → ready_for_finance_review → crosses to native approval pending', () => {
    const a = byId('A');
    expect(a.prepare.decision).toBe('ready_for_finance_review');
    expect(a.act?.outcome).toBe('qonto_native_approval_pending');
  });

  it('B: changed IBAN + elevated amount → manual_review_required, does NOT cross', () => {
    const b = byId('B');
    expect(b.prepare.decision).toBe('manual_review_required');
    expect(b.prepare.reviewer_route).toBe('designated_approver');
    expect(b.act).toBeNull();
    expect(b.events.some((e) => e.type === 'qonto_write_submitted')).toBe(false);
  });

  it('C: question + document injection → blocked before Finance review', () => {
    const c = byId('C');
    expect(c.prepare.decision).toBe('blocked');
    expect(c.stored.body.sanitization.detected_instructions.length).toBeGreaterThan(0);
    expect(c.events.some((e) => e.type === 'finance_pr_blocked')).toBe(true);
  });

  it('D1/D2/D3: integrity, stale, replay are named blocks (not a generic red score)', () => {
    expect(byId('D1').act?.outcome).toBe('integrity_failed');
    expect(byId('D2').act?.outcome).toBe('stale');
    expect(byId('D3').act?.outcome).toBe('replay_blocked');
  });

  it('no scenario emits a Qonto write except the synthetic-adapter crossing in A', () => {
    for (const r of runs) {
      const crossed = r.events.some((e) => e.type === 'qonto_write_submitted');
      expect(crossed).toBe(r.id === 'A');
    }
  });

  it('event/visual parity: every beat points at a real event sequence', () => {
    for (const r of runs) {
      const maxSeq = Math.max(...r.events.map((e) => e.seq));
      for (const beat of beatsFor(r)) {
        expect(beat.atSeq).toBeGreaterThanOrEqual(0);
        expect(beat.atSeq).toBeLessThanOrEqual(maxSeq);
      }
    }
  });

  it('all committed scenario data is synthetic', () => {
    for (const r of runs) expect(r.stored.body.data_mode).toBe('synthetic');
  });
});
