// Hard gates. Gates answer "can this proceed at all?" and are strictly separate
// from weighted risk. A risk score can NEVER turn a failed gate into a pass, and
// integrity/replay/state gates are never score inputs.

import type {
  Approval,
  Evidence,
  FinancePrBody,
  Gate,
  IntentResult,
  Integrity,
  SupplierInvoiceEvidence,
  TrustedPolicy,
} from './types.js';
import { criticalFieldDiffs, criticalStateDigest } from './critical.js';
import { canonicalize } from './canonical.js';
import { sha256 } from 'js-sha256';
import { fxRate, hasSupplierBlockList, supplierBlock } from './trustedPolicy.js';
import { maskId } from './redact.js';

// --- Prepare-phase gates ----------------------------------------------------

export function prepareGates(ev: Evidence, intent: IntentResult, trustedPolicy?: TrustedPolicy | null): Gate[] {
  const inv = ev.invoice;
  const gates: Gate[] = [];

  const isAction = intent.intent_class === 'PREPARE' || intent.intent_class === 'ACT';
  gates.push({
    id: 'explicit_action_intent',
    phase: 'both',
    status: isAction ? 'pass' : 'fail',
    reason: isAction
      ? `Request is ${intent.intent_class} — an explicit instruction to act.`
      : `Request is ${intent.intent_class}. A question, observation, or ambiguous phrase is not an instruction to act.`,
    remediation: isAction ? undefined : 'Ask explicitly, e.g. "Prepare invoice <id> for payment review."',
  });

  gates.push({
    id: 'intent_source_is_authoritative',
    phase: 'both',
    status: intent.source_is_authoritative ? 'pass' : 'fail',
    reason: intent.source_is_authoritative
      ? 'Action intent came from the authoritative user chat.'
      : 'The only action-like text originates from untrusted document/tool content — not authority.',
    remediation: intent.source_is_authoritative ? undefined : 'A human must issue the instruction directly.',
  });

  gates.push({
    id: 'target_and_action_unambiguous',
    phase: 'both',
    status: intent.target_and_action_unambiguous ? 'pass' : 'fail',
    reason: intent.target_and_action_unambiguous
      ? 'A single target invoice and action were identified.'
      : 'Target/action is ambiguous.',
    remediation: intent.target_and_action_unambiguous ? undefined : 'Name the exact invoice and action.',
  });

  const coreEvidence = Boolean(inv.amount.value && inv.amount.currency && inv.supplier_name);
  gates.push({
    id: 'required_evidence_present',
    phase: 'both',
    status: coreEvidence ? 'pass' : 'fail',
    reason: coreEvidence
      ? 'Required structured evidence (amount, currency, supplier) is present.'
      : 'Required structured evidence is missing.',
    remediation: coreEvidence ? undefined : 'Re-observe the invoice; required fields must be available.',
  });

  const paidOrMatched = inv.status === 'paid' || inv.matched_transaction_ids.length > 0;
  gates.push({
    id: 'not_already_paid_or_matched',
    phase: 'both',
    status: paidOrMatched ? 'fail' : 'pass',
    reason: paidOrMatched
      ? `Invoice is already ${inv.status === 'paid' ? 'paid' : 'matched to a transaction'}.`
      : 'Invoice is not already paid or matched.',
    remediation: paidOrMatched ? 'No further payment action is appropriate.' : undefined,
  });

  const completedDuplicate = ev.supplier_history.some(
    (h) => h.invoice_number === inv.invoice_number && h.status === 'paid',
  );
  gates.push({
    id: 'exact_duplicate_not_completed',
    phase: 'both',
    status: completedDuplicate ? 'fail' : 'pass',
    reason: completedDuplicate
      ? `An invoice with number "${inv.invoice_number}" is already paid — exact completed duplicate.`
      : 'No completed exact duplicate found.',
    remediation: completedDuplicate ? 'Do not pay again; investigate the prior payment.' : undefined,
  });

  if (trustedPolicy) {
    // Supplier block list — added only when the policy declares one. Matched on the
    // STRUCTURED Qonto supplier fields (id exact, name normalized), never on
    // document text. A block fails the gate → the decision logic turns it `blocked`.
    if (hasSupplierBlockList(trustedPolicy)) {
      const block = supplierBlock(trustedPolicy, inv.supplier_name, inv.supplier_id);
      gates.push({
        id: 'supplier_not_blocked',
        phase: 'prepare',
        status: block.blocked ? 'fail' : 'pass',
        reason: block.blocked
          ? `blocked by policy: supplier ${
              block.by === 'id' ? `id ${maskId(inv.supplier_id)}` : `"${inv.supplier_name}"`
            } is on the trusted supplier block list.`
          : 'Supplier is not on the trusted supplier block list.',
        remediation: block.blocked
          ? 'This supplier is blocked by trusted operator policy; resolve outside this tool.'
          : undefined,
      });
    }

    // Trusted-policy hard threshold. A (possibly converted) amount strictly above
    // the hard block fails the gate. Cross-currency is evaluated ONLY via an
    // operator-frozen rate; without one it is not evaluated (never converted).
    const sameCurrency = inv.amount.currency === trustedPolicy.currency;
    const rawAmount = Number.parseFloat(inv.amount.value);
    const hard = Number.parseFloat(trustedPolicy.hard_block_amount);
    const rate = sameCurrency ? null : fxRate(trustedPolicy, inv.amount.currency, trustedPolicy.currency);
    const evaluable = sameCurrency || rate !== null;
    const amount = rate !== null ? rawAmount * Number.parseFloat(rate) : rawAmount;
    const conv = rate !== null
      ? ` (converted from ${inv.amount.value} ${inv.amount.currency} at operator rate ${rate}, not a market rate)`
      : '';
    const breach = evaluable && Number.isFinite(amount) && amount > hard;
    gates.push({
      id: 'within_trusted_policy_hard_limit',
      phase: 'prepare',
      status: breach ? 'fail' : 'pass',
      reason: breach
        ? `blocked by policy: amount ${amount.toFixed(2)} ${trustedPolicy.currency}${conv} exceeds the trusted hard-block threshold ${hard} ${trustedPolicy.currency}.`
        : evaluable
          ? `Amount ${amount.toFixed(2)} ${trustedPolicy.currency}${conv} is within the trusted policy hard-block threshold (${hard} ${trustedPolicy.currency}).`
          : `Trusted policy hard limit not evaluated (invoice ${inv.amount.currency} ≠ policy ${trustedPolicy.currency}; no operator FX rate defined, no conversion).`,
      remediation: breach
        ? 'This amount cannot proceed under the trusted policy; escalate outside this tool.'
        : undefined,
    });
  }

  return gates;
}

// --- Act-phase gates --------------------------------------------------------

export interface ActGateInput {
  body: FinancePrBody;
  integrity: Integrity;
  approval: Approval | null;
  freshInvoice: SupplierInvoiceEvidence;
  nowIso: string;
  reservationAvailable: boolean;
  writesEnabled: boolean;
}

export function actGates(input: ActGateInput): Gate[] {
  const { body, integrity, approval, freshInvoice, nowIso, reservationAvailable, writesEnabled } = input;
  const gates: Gate[] = [];

  // Recompute the hash of the stored body — detects any tamper with stored JSON.
  const recomputedHash = sha256(canonicalize(body));
  const hashOk = recomputedHash === integrity.hash;
  gates.push({
    id: 'full_hash_matches',
    phase: 'act',
    status: hashOk ? 'pass' : 'fail',
    reason: hashOk ? 'Stored PR body hashes to the recorded value.' : 'Stored PR body no longer matches its recorded hash — tampered.',
    remediation: hashOk ? undefined : 'Reject and re-prepare a fresh Finance PR.',
  });

  const idFpMatch = Boolean(
    approval && approval.pr_id === body.pr_id && approval.fingerprint === integrity.fingerprint,
  );
  gates.push({
    id: 'finance_pr_id_and_fingerprint_match',
    phase: 'act',
    status: idFpMatch ? 'pass' : 'fail',
    reason: idFpMatch
      ? 'Approval references this PR id and the correct fingerprint.'
      : 'Approval PR id / fingerprint does not match this PR.',
    remediation: idFpMatch ? undefined : 'Approve the exact PR id and fingerprint shown.',
  });

  gates.push({
    id: 'explicit_approval_present',
    phase: 'act',
    status: approval ? 'pass' : 'fail',
    reason: approval ? 'An explicit approval record is present.' : 'No explicit approval was supplied.',
    remediation: approval ? undefined : 'Provide an explicit fingerprint-bound approval.',
  });

  const routeOk = Boolean(approval && approval.route === body.policy.reviewer_route && body.policy.reviewer_route !== 'none');
  gates.push({
    id: 'approval_route_satisfied',
    phase: 'act',
    status: routeOk ? 'pass' : 'fail',
    reason: routeOk
      ? `Approval came via the required route (${body.policy.reviewer_route}).`
      : `Approval route does not satisfy the required route (${body.policy.reviewer_route}).`,
    remediation: routeOk ? undefined : 'Route the approval through the required reviewer.',
  });

  const notExpired = Date.parse(nowIso) < Date.parse(body.expires_at);
  gates.push({
    id: 'not_expired',
    phase: 'act',
    status: notExpired ? 'pass' : 'fail',
    reason: notExpired ? 'PR is within its validity window.' : 'PR has expired.',
    remediation: notExpired ? undefined : 'Re-prepare a fresh Finance PR.',
  });

  const freshDigest = criticalStateDigest(freshInvoice);
  const stateUnchanged = freshDigest === body.critical_state_digest;
  gates.push({
    id: 'critical_qonto_state_unchanged',
    phase: 'act',
    status: stateUnchanged ? 'pass' : 'fail',
    reason: stateUnchanged
      ? 'Critical Qonto state digest is unchanged since Prepare.'
      : 'Critical Qonto state changed since Prepare.',
    remediation: stateUnchanged ? undefined : 'Re-observe and re-prepare; do not act on stale state.',
  });

  const diffs = criticalFieldDiffs(body, freshInvoice);
  gates.push({
    id: 'amount_currency_iban_supplier_unchanged',
    phase: 'act',
    status: diffs.length === 0 ? 'pass' : 'fail',
    reason: diffs.length === 0
      ? 'Amount, currency, IBAN, supplier, and status are unchanged.'
      : `Critical field(s) changed: ${diffs.join('; ')}.`,
    remediation: diffs.length === 0 ? undefined : 'Block regardless of score; re-prepare.',
  });

  const actionOk =
    body.proposed_action.type === 'prepare_payment_review' &&
    body.proposed_action.target_object.id === body.target.invoice_id &&
    freshInvoice.id === body.target.invoice_id;
  gates.push({
    id: 'prepared_action_exact_match',
    phase: 'act',
    status: actionOk ? 'pass' : 'fail',
    reason: actionOk
      ? 'The action to run is exactly the stored, allowlisted prepared action.'
      : 'The action/target does not match the stored prepared action.',
    remediation: actionOk ? undefined : 'Act never accepts replacement parameters; re-prepare.',
  });

  gates.push({
    id: 'not_used_or_in_progress',
    phase: 'act',
    status: reservationAvailable ? 'pass' : 'fail',
    reason: reservationAvailable ? 'One-shot reservation is available.' : 'PR was already used or is in progress — replay blocked.',
    remediation: reservationAvailable ? undefined : 'Each PR is single-use; re-prepare for a new action.',
  });

  gates.push({
    id: 'writes_explicitly_enabled_for_test',
    phase: 'act',
    status: writesEnabled ? 'pass' : 'fail',
    reason: writesEnabled
      ? 'Controlled write flag is explicitly enabled for this test.'
      : 'Qonto writes are disabled by default — Act stops at a verified ready_for_qonto handoff.',
  });

  return gates;
}

export function allPass(gates: Gate[]): boolean {
  return gates.every((g) => g.status === 'pass');
}
