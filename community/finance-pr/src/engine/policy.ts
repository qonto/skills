// Transparent demo policy. Weights are policy defaults, NOT learned fraud
// probabilities. Everything here is versioned and digested into the PR body so a
// reviewer can see exactly which policy produced a decision.

import type { CoreSignalId } from './types.js';
import { digest } from './canonical.js';

export interface Policy {
  policy_id: string;
  policy_version: string;
  /** minutes a prepared PR remains valid for Act. */
  pr_ttl_minutes: number;
  signal_weights: Record<CoreSignalId, number>;
  /** minimum score coverage for a Green (ready_for_finance_review) decision. */
  min_coverage: number;
  /** signal risk >= this routes to manual review even if all gates pass. */
  material_signal_risk: number;
  bands: { low_below: number; high_at_or_above: number };
  /** amount that always routes to the designated approver, regardless of score. */
  high_value_amount: number;
}

export const POLICY: Policy = {
  policy_id: 'finance-pr.demo',
  policy_version: '2026-07-12',
  pr_ttl_minutes: 60,
  signal_weights: {
    possible_duplicate: 0.3,
    supplier_iban_drift: 0.3,
    unusual_amount: 0.2,
    evidence_gap_risk: 0.1,
    untrusted_instruction_indicator: 0.1,
  },
  min_coverage: 0.8,
  material_signal_risk: 0.5,
  bands: { low_below: 0.25, high_at_or_above: 0.7 },
  high_value_amount: 10_000,
};

export function policyDigest(p: Policy = POLICY): string {
  return digest(
    p.policy_id,
    p.policy_version,
    JSON.stringify(p.signal_weights),
    String(p.min_coverage),
    String(p.material_signal_risk),
    String(p.high_value_amount),
  );
}
