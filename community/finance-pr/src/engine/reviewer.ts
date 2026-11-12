// Optional independent reviewer. Disabled by default. It has NO Qonto tools and
// NO execution authority. Its output can only PRESERVE or INCREASE review
// requirements — it may never downgrade a deterministic risk or gate, and it can
// never authorize Act.
//
// The default implementation is a deterministic, offline heuristic (no network).
// A networked model would implement the same interface and receive only the
// sanitized context below.

import type { IntentResult, ReviewOutput, RiskSummary, Signal } from './types.js';

export interface ReviewContext {
  intent_class: IntentResult['intent_class'];
  band: RiskSummary['band'];
  coverage: number;
  amount_value: string;
  currency: string;
  /** sanitized signal snapshot: id + status + risk only (no raw evidence). */
  signals: Array<Pick<Signal, 'id' | 'status' | 'risk'>>;
  instructions_detected: boolean;
}

export interface IndependentReviewer {
  readonly id: string;
  review(ctx: ReviewContext): ReviewOutput;
}

/** Escalate-only heuristic reviewer. Never returns a downgrade the caller could
 * misuse; the caller (policy) only ever uses non-`agree` verdicts to escalate. */
export class HeuristicReviewer implements IndependentReviewer {
  readonly id = 'heuristic-offline';

  review(ctx: ReviewContext): ReviewOutput {
    const ibanDrift = ctx.signals.find((s) => s.id === 'supplier_iban_drift');
    const reasons: string[] = [];

    if (ctx.instructions_detected) reasons.push('untrusted instruction text present');
    if (ctx.intent_class === 'AMBIGUOUS') reasons.push('ambiguous intent');
    if (ibanDrift && ibanDrift.status === 'observed' && ibanDrift.risk >= 0.7) reasons.push('supplier IBAN drift');
    if (ctx.band === 'high_observed_risk') reasons.push('high observed risk band');

    if (reasons.length > 0) {
      return {
        verdict: 'escalate',
        rationale: `Independent review recommends escalation: ${reasons.join(', ')}.`,
        reviewer_id: this.id,
        available: true,
      };
    }

    if (ctx.coverage < 0.8) {
      return {
        verdict: 'unclear',
        rationale: `Score coverage is ${(ctx.coverage * 100).toFixed(0)}% — insufficient to conclude.`,
        reviewer_id: this.id,
        available: true,
      };
    }

    return { verdict: 'agree', rationale: 'No independent concern beyond deterministic checks.', reviewer_id: this.id, available: true };
  }
}
