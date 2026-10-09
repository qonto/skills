// PREPARE — build the immutable, hashed Finance PR. Zero Qonto mutation.

import type { Clock } from './clock.js';
import { addMinutes } from './clock.js';
import type { EventLog } from './events.js';
import { classifyIntent } from './intent.js';
import { evaluateSignals } from './signals.js';
import { prepareGates, allPass } from './gates.js';
import { criticalStateDigest, criticalStateDisplay } from './critical.js';
import { canonicalize, digest, fingerprintFromHash } from './canonical.js';
import { sha256 } from 'js-sha256';
import { POLICY, policyDigest } from './policy.js';
import { fxRate, hasSupplierBlockList, trustedPolicyDigest } from './trustedPolicy.js';
import { maskId, maskIban, stripSensitive } from './redact.js';
import type { HeuristicReviewer, IndependentReviewer } from './reviewer.js';
import {
  SCHEMA_VERSION,
  type Evidence,
  type EvidenceRef,
  type FinancePrBody,
  type Gate,
  type IntentResult,
  type PolicyDecision,
  type ReviewerRoute,
  type ReviewOutput,
  type RiskSummary,
  type Signal,
  type StoredPr,
  type TrustedPolicy,
  type UserRequest,
} from './types.js';

export interface PrepareInput {
  request: UserRequest;
  evidence: Evidence;
  clock: Clock;
  events: EventLog;
  /** explicit id for deterministic scenarios; otherwise derived. */
  prId?: string;
  /** optional escalate-only reviewer. */
  reviewer?: IndependentReviewer | HeuristicReviewer | null;
  /** optional trusted operator policy (from a trusted file, never invoice text). */
  trustedPolicy?: TrustedPolicy | null;
}

export interface PrepareResult {
  stored: StoredPr;
  intent: IntentResult;
  signals: Signal[];
  risk: RiskSummary;
  gates: Gate[];
  decision: PolicyDecision;
  reviewer_route: ReviewerRoute;
  review: ReviewOutput | null;
}

function buildEvidenceRefs(ev: Evidence): EvidenceRef[] {
  const refs: EvidenceRef[] = [
    {
      source: ev.data_mode,
      object_type: 'organization',
      object_id_masked: maskId(ev.organization.id),
      fetched_at: ev.observed_at,
      available: true,
      critical_digest: 'n/a',
    },
    {
      source: ev.data_mode,
      object_type: 'supplier_invoice',
      object_id_masked: maskId(ev.invoice.id),
      fetched_at: ev.observed_at,
      available: true,
      critical_digest: criticalStateDigest(ev.invoice),
    },
    {
      source: ev.data_mode,
      object_type: 'supplier_history',
      object_id_masked: `${ev.supplier_history.length} record(s)`,
      fetched_at: ev.observed_at,
      available: true,
      critical_digest: digest('history', JSON.stringify(ev.supplier_history)),
    },
  ];
  for (const f of ev.unavailable_fields) {
    refs.push({
      source: ev.data_mode,
      object_type: f,
      object_id_masked: 'unavailable',
      fetched_at: ev.observed_at,
      available: false,
      critical_digest: 'n/a',
    });
  }
  return refs;
}

function decide(
  ev: Evidence,
  prepGates: Gate[],
  signals: Signal[],
  risk: RiskSummary,
  review: ReviewOutput | null,
): { decision: PolicyDecision; route: ReviewerRoute } {
  if (!allPass(prepGates)) {
    return { decision: 'blocked', route: 'returned' };
  }

  const amount = Number.parseFloat(ev.invoice.amount.value);
  const highValue = Number.isFinite(amount) && amount >= POLICY.high_value_amount;
  const ibanDrift = signals.find((s) => s.id === 'supplier_iban_drift');
  const ibanDriftHigh = ibanDrift?.status === 'observed' && ibanDrift.risk >= POLICY.material_signal_risk;
  const materialSignal = signals.some((s) => s.status === 'observed' && s.risk >= POLICY.material_signal_risk);
  const lowCoverage = risk.coverage < POLICY.min_coverage;
  const reviewEscalates = Boolean(review && review.verdict !== 'agree');

  if (highValue || ibanDriftHigh) {
    return { decision: 'manual_review_required', route: 'designated_approver' };
  }
  if (materialSignal || lowCoverage || reviewEscalates) {
    return { decision: 'manual_review_required', route: 'finance_reviewer' };
  }
  return { decision: 'ready_for_finance_review', route: 'finance_reviewer' };
}

export function prepare(input: PrepareInput): PrepareResult {
  const { request, evidence: ev, clock, events } = input;

  // created_at fixed first so it is deterministic and distinct from event times.
  const created_at = clock.now();
  const expires_at = addMinutes(created_at, POLICY.pr_ttl_minutes);
  const pr_id = input.prId ?? `FPR-${digest(ev.invoice.id, created_at, request.text).slice(0, 6).toUpperCase()}`;

  const trustedPolicy = input.trustedPolicy ?? null;
  const intent = classifyIntent(request, ev.invoice.attachment_text);
  const { signals, risk } = evaluateSignals(ev, intent, trustedPolicy);
  const gates = prepareGates(ev, intent, trustedPolicy);

  // Optional escalate-only independent review (ambiguous / high-value only).
  let review: ReviewOutput | null = null;
  const amount = Number.parseFloat(ev.invoice.amount.value);
  const highValue = Number.isFinite(amount) && amount >= POLICY.high_value_amount;
  if (input.reviewer && (intent.intent_class === 'AMBIGUOUS' || highValue || risk.band === 'high_observed_risk')) {
    events.emit('second_review_requested', pr_id, { reviewer: input.reviewer.id });
    review = input.reviewer.review({
      intent_class: intent.intent_class,
      band: risk.band,
      coverage: risk.coverage,
      amount_value: ev.invoice.amount.value,
      currency: ev.invoice.amount.currency,
      signals: signals.map((s) => ({ id: s.id, status: s.status, risk: s.risk })),
      instructions_detected: intent.detected_instructions.length > 0,
    });
    events.emit('second_review_returned', pr_id, { verdict: review.verdict });
  }

  const { decision, route } = decide(ev, gates, signals, risk, review);

  const body: FinancePrBody = {
    schema_version: SCHEMA_VERSION,
    pr_id,
    data_mode: ev.data_mode,
    created_at,
    expires_at,
    intent: {
      literal_request: stripSensitive(request.text),
      request_source: request.source,
      message_id: request.message_id,
      intent_class: intent.intent_class,
      interpretation: intent.interpretation,
      ambiguity_notes: intent.ambiguity_notes,
    },
    target: {
      organization_id_masked: maskId(ev.organization.id),
      invoice_id: ev.invoice.id,
      invoice_number: ev.invoice.invoice_number,
      supplier_name: ev.invoice.supplier_name,
      supplier_id: ev.invoice.supplier_id,
    },
    proposed_action: {
      type: 'prepare_payment_review',
      target_object: { object_type: 'supplier_invoice', id: ev.invoice.id },
      parameters: {
        amount: ev.invoice.amount,
        supplier_name: ev.invoice.supplier_name,
        supplier_id: ev.invoice.supplier_id,
        iban_masked: maskIban(ev.invoice.iban),
      },
    },
    critical_state_digest: criticalStateDigest(ev.invoice),
    critical_state_display: criticalStateDisplay(ev.invoice),
    evidence: buildEvidenceRefs(ev),
    signals,
    risk,
    gates,
    policy: {
      policy_id: POLICY.policy_id,
      policy_version: POLICY.policy_version,
      policy_digest: policyDigest(),
      decision,
      reviewer_route: route,
    },
    ...(trustedPolicy
      ? {
          trusted_policy: {
            source: 'trusted_file' as const,
            currency: trustedPolicy.currency,
            hard_block_amount: trustedPolicy.hard_block_amount,
            policy_digest: trustedPolicyDigest(trustedPolicy),
            applied_role: ev.membership.role,
            applied_limit: trustedPolicy.role_limits[ev.membership.role] ?? null,
            ...(hasSupplierBlockList(trustedPolicy)
              ? {
                  blocked_suppliers: [
                    ...(trustedPolicy.blocked_supplier_names ?? []),
                    ...(trustedPolicy.blocked_supplier_ids ?? []).map((i) => `id:${maskId(i)}`),
                  ],
                }
              : {}),
            ...(() => {
              const invCur = ev.invoice.amount.currency;
              if (invCur === trustedPolicy.currency) return {};
              const rate = fxRate(trustedPolicy, invCur, trustedPolicy.currency);
              if (rate === null) return {};
              const converted = (Number.parseFloat(ev.invoice.amount.value) * Number.parseFloat(rate)).toFixed(2);
              return {
                fx_applied: {
                  from: invCur,
                  to: trustedPolicy.currency,
                  rate,
                  converted_amount: converted,
                  note: 'operator-frozen rate, bound into this PR hash — not a market rate',
                },
              };
            })(),
          },
        }
      : {}),
    sanitization: {
      untrusted_sources: ['supplier_invoice.attachment_text'],
      detected_instructions: intent.detected_instructions,
      redaction_summary: 'IBANs masked to last 4; object ids masked; URLs/tokens stripped.',
    },
  };

  const hash = sha256(canonicalize(body));
  const fingerprint = fingerprintFromHash(hash);
  const stored: StoredPr = { body, integrity: { algorithm: 'sha256', hash, fingerprint } };

  // Events (Observe is represented by the first two; Prepare by the rest).
  events.emit('invoice_observed', pr_id, {
    data_mode: ev.data_mode,
    supplier: ev.invoice.supplier_name,
    invoice_number: ev.invoice.invoice_number,
  });
  events.emit('evidence_collected', pr_id, {
    evidence_count: body.evidence.length,
    unavailable: ev.unavailable_fields,
  });
  events.emit('intent_classified', pr_id, {
    intent_class: intent.intent_class,
    source_is_authoritative: intent.source_is_authoritative,
  });
  for (const s of signals) {
    events.emit('signal_evaluated', pr_id, { id: s.id, status: s.status, risk: s.risk, weight: s.weight });
  }
  for (const g of gates) {
    events.emit('hard_gate_evaluated', pr_id, { id: g.id, status: g.status });
  }

  if (decision === 'blocked') {
    events.emit('finance_pr_blocked', pr_id, { fingerprint, reason: 'A required Prepare gate failed.' });
  } else {
    events.emit('finance_pr_prepared', pr_id, {
      fingerprint,
      decision,
      route,
      band: risk.band,
      coverage: risk.coverage,
    });
    events.emit('finance_review_requested', pr_id, { route });
  }

  return { stored, intent, signals, risk, gates, decision, reviewer_route: route, review };
}
