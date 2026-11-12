// The five MVP weighted signals + observed-only aggregate and separate coverage.
//

import type { CoreSignalId, Evidence, IntentResult, RiskSummary, Signal, SignalId, TrustedPolicy } from './types.js';
import { POLICY } from './policy.js';
import { normalizeIban } from './redact.js';
import { fxRate } from './trustedPolicy.js';

const MIN_HISTORY_FOR_AMOUNT = 4;
const NEAR_DAYS = 7;

/** Weight of the trusted-policy signal. Kept OUT of POLICY.signal_weights so the
 * hashed policy digest (and therefore existing PR fingerprints) never changes. */
const TRUSTED_POLICY_SIGNAL_WEIGHT = 0.3;

function amountNumber(value: string): number {
  return Number.parseFloat(value);
}

function median(nums: number[]): number {
  const s = [...nums].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
}

function daysBetween(a: string | null, b: string | null): number {
  if (!a || !b) return Number.POSITIVE_INFINITY;
  return Math.abs(Date.parse(a) - Date.parse(b)) / 86_400_000;
}

function w(id: CoreSignalId): number {
  return POLICY.signal_weights[id];
}

// --- individual signals -----------------------------------------------------

function evalUnusualAmount(ev: Evidence): Signal {
  const id: CoreSignalId = 'unusual_amount';
  const amounts = ev.supplier_history
    .filter((h) => h.amount.currency === ev.invoice.amount.currency)
    .map((h) => amountNumber(h.amount.value))
    .filter((n) => Number.isFinite(n) && n > 0);

  if (amounts.length < MIN_HISTORY_FOR_AMOUNT) {
    return {
      id,
      status: 'insufficient_data',
      risk: 0,
      weight: w(id),
      reason: `Only ${amounts.length} prior amount(s) for this supplier (need ${MIN_HISTORY_FOR_AMOUNT}); baseline unknown.`,
      evidence_refs: ['supplier_history'],
    };
  }

  const amount = amountNumber(ev.invoice.amount.value);
  const med = median(amounts);
  const ratio = med > 0 ? amount / med : Number.POSITIVE_INFINITY;
  let risk = 0;
  let reason = `Amount ${amount} is near the supplier median (${med}).`;
  if (ratio >= 3 || ratio <= 1 / 3) {
    risk = 1;
    reason = `Amount ${amount} is ${ratio.toFixed(1)}× the supplier median (${med}) — extreme deviation.`;
  } else if (ratio >= 1.75) {
    risk = 0.5;
    reason = `Amount ${amount} is ${ratio.toFixed(1)}× the supplier median (${med}) — elevated.`;
  }
  return { id, status: 'observed', risk, weight: w(id), reason, evidence_refs: ['supplier_history'] };
}

function evalPossibleDuplicate(ev: Evidence): Signal {
  const id: CoreSignalId = 'possible_duplicate';
  const inv = ev.invoice;

  if (inv.has_duplicates) {
    return {
      id,
      status: 'observed',
      risk: 1,
      weight: w(id),
      reason: 'Qonto flagged this invoice as having duplicates.',
      evidence_refs: ['invoice.has_duplicates'],
    };
  }

  const amount = inv.amount.value;
  const cur = inv.amount.currency;
  let risk = 0;
  let reason = 'No duplicate candidate found in supplier history.';

  for (const h of ev.supplier_history) {
    if (h.invoice_number && h.invoice_number === inv.invoice_number && h.status !== 'paid') {
      risk = Math.max(risk, 1);
      reason = `Same supplier + invoice number "${inv.invoice_number}" already on file (not confirmed paid).`;
      continue;
    }
    if (h.amount.value === amount && h.amount.currency === cur && daysBetween(h.issue_date, inv.issue_date) <= NEAR_DAYS) {
      risk = Math.max(risk, 0.7);
      if (risk === 0.7) reason = `Same amount ${amount} ${cur} within ${NEAR_DAYS} days of a prior invoice.`;
    } else if (h.amount.value === amount && h.amount.currency === cur) {
      risk = Math.max(risk, 0.4);
      if (risk === 0.4) reason = `Same amount ${amount} ${cur} as a prior invoice (different date) — weak candidate.`;
    }
  }

  return { id, status: 'observed', risk, weight: w(id), reason, evidence_refs: ['supplier_history', 'invoice.has_duplicates'] };
}

function evalIbanDrift(ev: Evidence, amountElevated: boolean, hasInstructions: boolean): Signal {
  const id: CoreSignalId = 'supplier_iban_drift';
  const invIban = normalizeIban(ev.invoice.iban);
  const known = ev.known_supplier_ibans.map((i) => normalizeIban(i)).filter(Boolean) as string[];

  if (!invIban) {
    return {
      id,
      status: 'not_applicable',
      risk: 0,
      weight: w(id),
      reason: 'Invoice carries no IBAN (nothing to compare); payability blocked upstream.',
      evidence_refs: ['invoice.iban'],
    };
  }

  if (known.length === 0) {
    return {
      id,
      status: 'observed',
      risk: 0.4,
      weight: w(id),
      reason: 'No known IBAN on file for this supplier — a new payee cannot be verified against history.',
      evidence_refs: ['known_supplier_ibans'],
    };
  }

  if (known.includes(invIban)) {
    return {
      id,
      status: 'observed',
      risk: 0,
      weight: w(id),
      reason: 'Invoice IBAN matches a previously used IBAN for this supplier.',
      evidence_refs: ['known_supplier_ibans'],
    };
  }

  // Known supplier, changed IBAN.
  const corroborated = amountElevated || hasInstructions;
  return {
    id,
    status: 'observed',
    risk: corroborated ? 1 : 0.7,
    weight: w(id),
    reason: corroborated
      ? 'Supplier IBAN differs from history AND a corroborating anomaly (elevated amount / document instruction) is present.'
      : 'Supplier IBAN differs from every IBAN previously used for this supplier.',
    evidence_refs: ['known_supplier_ibans', 'invoice.iban'],
  };
}

function evalEvidenceGap(ev: Evidence): Signal {
  const id: CoreSignalId = 'evidence_gap_risk';
  const gaps: string[] = [];
  if (!ev.invoice.attachment_text) gaps.push('no extracted document text');
  if (!ev.invoice.issue_date) gaps.push('missing issue date');
  if (!ev.invoice.due_date) gaps.push('missing due date');
  if (ev.invoice.matched_transaction_ids.length === 0) gaps.push('no matched transaction');
  const risk = Math.min(1, gaps.length * 0.34);
  return {
    id,
    status: 'observed',
    risk,
    weight: w(id),
    reason: gaps.length ? `Optional evidence gaps: ${gaps.join(', ')}.` : 'No optional evidence gaps.',
    evidence_refs: ['invoice'],
  };
}

function evalUntrustedInstruction(intent: IntentResult): Signal {
  const id: CoreSignalId = 'untrusted_instruction_indicator';
  const hits = intent.detected_instructions;
  const strong = hits.some((h) => /approve|pay|authori|ignore|bypass|transfer|release|execute/i.test(h));
  const risk = hits.length === 0 ? 0 : strong ? 1 : 0.5;
  return {
    id,
    status: 'observed',
    risk,
    weight: w(id),
    reason: hits.length
      ? `Instruction-like text found in untrusted document content: ${hits.map((h) => `“${h}”`).join('; ')}.`
      : 'No instruction-like text detected in document content.',
    evidence_refs: ['invoice.attachment_text'],
  };
}

/** Trusted-policy limit signal. Only evaluated when an explicitly trusted policy
 * file is supplied. Compares the invoice amount to the initiator role's approval
 * limit in the policy currency. A cross-currency invoice is converted ONLY when
 * the operator declared a frozen rate for that pair; otherwise it stays
 * `not_applicable` (never converted). */
function evalPolicyLimit(ev: Evidence, tp: TrustedPolicy): Signal {
  const id: SignalId = 'policy_amount_over_limit';
  const weight = TRUSTED_POLICY_SIGNAL_WEIGHT;
  const role = ev.membership.role;
  const invCur = ev.invoice.amount.currency;

  // Resolve the comparable amount in the policy currency (same-currency, or an
  // operator-frozen conversion). `conv` labels the conversion for the reason.
  let amount = amountNumber(ev.invoice.amount.value);
  let conv = '';
  if (invCur !== tp.currency) {
    const rate = fxRate(tp, invCur, tp.currency);
    if (rate === null) {
      return {
        id,
        status: 'not_applicable',
        risk: 0,
        weight,
        reason: `Trusted policy is denominated in ${tp.currency}; invoice is ${invCur} and no operator FX rate ${invCur}->${tp.currency} is defined — no conversion attempted, limit not evaluated.`,
        evidence_refs: ['invoice.amount', 'trusted_policy'],
      };
    }
    amount = amount * amountNumber(rate);
    conv = ` (converted from ${ev.invoice.amount.value} ${invCur} at operator rate ${rate}, not a market rate)`;
  }

  const limitStr = tp.role_limits[role];
  if (limitStr === undefined) {
    return {
      id,
      status: 'not_applicable',
      risk: 0,
      weight,
      reason: `No approval limit defined for initiator role "${role}" in the trusted policy.`,
      evidence_refs: ['membership.role', 'trusted_policy'],
    };
  }

  const limit = amountNumber(limitStr);
  if (!(amount > limit)) {
    return {
      id,
      status: 'observed',
      risk: 0,
      weight,
      reason: `Amount ${amount.toFixed(2)} ${tp.currency}${conv} is within the initiator (${role}) approval limit ${limit}.`,
      evidence_refs: ['membership.role', 'trusted_policy'],
    };
  }
  return {
    id,
    status: 'observed',
    risk: 1,
    weight,
    reason: `policy breach: amount exceeds initiator limit — ${amount.toFixed(2)} ${tp.currency}${conv} > ${role} limit ${limit}.`,
    evidence_refs: ['membership.role', 'trusted_policy'],
  };
}

// --- aggregate --------------------------------------------------------------

export function aggregate(signals: Signal[]): RiskSummary {
  const applicable = signals.filter((s) => s.status !== 'not_applicable' && s.status !== 'not_run');
  const observed = signals.filter((s) => s.status === 'observed');

  const configuredWeight = applicable.reduce((sum, s) => sum + s.weight, 0);
  const observedWeight = observed.reduce((sum, s) => sum + s.weight, 0);

  const coverage = configuredWeight > 0 ? observedWeight / configuredWeight : 0;

  if (observedWeight === 0) {
    return { observed_risk: null, coverage, band: 'not_scored' };
  }

  const observed_risk = observed.reduce((sum, s) => sum + s.risk * s.weight, 0) / observedWeight;

  let band: RiskSummary['band'];
  if (observed_risk < POLICY.bands.low_below) band = 'low_observed_risk';
  else if (observed_risk >= POLICY.bands.high_at_or_above) band = 'high_observed_risk';
  else band = 'elevated_observed_risk';

  return { observed_risk, coverage, band };
}

export function evaluateSignals(
  ev: Evidence,
  intent: IntentResult,
  trustedPolicy?: TrustedPolicy | null,
): { signals: Signal[]; risk: RiskSummary } {
  const unusual = evalUnusualAmount(ev);
  const amountElevated = unusual.status === 'observed' && unusual.risk >= 0.5;
  const hasInstructions = intent.detected_instructions.length > 0;

  const signals: Signal[] = [
    evalPossibleDuplicate(ev),
    evalIbanDrift(ev, amountElevated, hasInstructions),
    unusual,
    evalEvidenceGap(ev),
    evalUntrustedInstruction(intent),
  ];

  // Appended only when a trusted policy file is supplied — keeps the default
  // signal set (and every existing PR fingerprint) untouched.
  if (trustedPolicy) signals.push(evalPolicyLimit(ev, trustedPolicy));

  return { signals, risk: aggregate(signals) };
}
