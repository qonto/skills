import { describe, expect, it } from 'vitest';
import { HeuristicReviewer } from '../src/engine/reviewer.js';

const r = new HeuristicReviewer();
const base = {
  intent_class: 'PREPARE' as const,
  band: 'low_observed_risk' as const,
  coverage: 1,
  amount_value: '1000.00',
  currency: 'EUR',
  signals: [{ id: 'supplier_iban_drift' as const, status: 'observed' as const, risk: 0 }],
  instructions_detected: false,
};

describe('independent reviewer (escalate-only)', () => {
  it('escalates on untrusted instructions', () => {
    expect(r.review({ ...base, instructions_detected: true }).verdict).toBe('escalate');
  });
  it('escalates on IBAN drift', () => {
    expect(r.review({ ...base, signals: [{ id: 'supplier_iban_drift', status: 'observed', risk: 1 }] }).verdict).toBe('escalate');
  });
  it('marks unclear on low coverage', () => {
    expect(r.review({ ...base, coverage: 0.5 }).verdict).toBe('unclear');
  });
  it('agrees when nothing is concerning (never authorizes)', () => {
    const out = r.review(base);
    expect(out.verdict).toBe('agree');
    expect(['agree', 'unclear', 'disagree', 'escalate']).toContain(out.verdict);
  });
});
