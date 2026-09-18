// Finance PR — domain types.
// One canonical vocabulary shared by engine, CLI, tests, and the visual reducer.

export type DataMode = 'synthetic' | 'qonto_sandbox';

export const SCHEMA_VERSION = 'finance-pr/1';

// ---------------------------------------------------------------------------
// Intent
// ---------------------------------------------------------------------------

/** How the user's request maps to authority. Only ACT (a fingerprint-bound
 * approval) may authorize a Qonto-crossing write. */
export type IntentClass = 'ADVICE_ONLY' | 'OBSERVE' | 'PREPARE' | 'ACT' | 'AMBIGUOUS';

/** Provenance of a piece of text. Only `user_chat` can carry authority. */
export type TextSource = 'user_chat' | 'document' | 'tool_output';

export interface UserRequest {
  text: string;
  source: TextSource;
  message_id: string;
}

export interface IntentResult {
  intent_class: IntentClass;
  /** true only when the request came from an authoritative user_chat source. */
  source_is_authoritative: boolean;
  /** true when a single unambiguous target + action can be identified. */
  target_and_action_unambiguous: boolean;
  interpretation: string;
  ambiguity_notes: string[];
  /** Instruction-like text detected inside untrusted data (document/tool). */
  detected_instructions: string[];
}

// ---------------------------------------------------------------------------
// Evidence (typed, read-only observation of Qonto or synthetic data)
// ---------------------------------------------------------------------------

export interface Money {
  /** decimal string, e.g. "3200.00" */
  value: string;
  /** ISO 4217, e.g. "EUR" */
  currency: string;
}

export interface SupplierHistoryItem {
  invoice_number: string;
  amount: Money;
  /** normalized IBAN (no spaces, upper) or null if unknown. */
  iban: string | null;
  issue_date: string | null;
  status: string;
}

export interface SupplierInvoiceEvidence {
  object_type: 'supplier_invoice';
  id: string;
  invoice_number: string;
  supplier_name: string;
  supplier_id: string;
  /** normalized IBAN or null. */
  iban: string | null;
  amount: Money;
  status: string; // to_review | paid | scheduled | ...
  due_date: string | null;
  issue_date: string | null;
  has_duplicates: boolean;
  matched_transaction_ids: string[];
  available_actions: { pay: boolean; reasons?: Record<string, string[]> };
  /** Untrusted extracted document text (never authority). */
  attachment_text: string | null;
  updated_at: string | null;
}

export interface Evidence {
  data_mode: DataMode;
  organization: { id: string; name: string; legal_country: string };
  membership: { id: string; role: string };
  invoice: SupplierInvoiceEvidence;
  supplier_history: SupplierHistoryItem[];
  /** Normalized IBANs previously seen for this supplier. */
  known_supplier_ibans: string[];
  observed_at: string;
  /** Fields we could not read (e.g. list_requests 403). */
  unavailable_fields: string[];
}

// ---------------------------------------------------------------------------
// Trusted policy (explicitly trusted, operator-authored — never invoice text)
// ---------------------------------------------------------------------------

/** A small, deterministic finance policy loaded ONLY from a trusted operator
 * file. Denominated in a single currency; amounts are compared, never converted.
 * It never comes from invoice/document text. */
export interface TrustedPolicy {
  /** provenance marker — only a trusted operator file may set this. */
  source: 'trusted_file';
  /** ISO 4217 currency the limits are denominated in. */
  currency: string;
  /** decimal string; an amount strictly above this (same currency) hard-blocks. */
  hard_block_amount: string;
  /** initiator role -> approval limit (decimal string), e.g. { owner: "10000" }. */
  role_limits: Record<string, string>;
  /** Normalized supplier names to hard-block outright (matched against the
   * STRUCTURED Qonto supplier_name field, never document text). Omitted when empty
   * so the policy digest of a bare policy is unchanged. */
  blocked_supplier_names?: string[];
  /** Supplier ids (UUIDs) to hard-block outright (exact match on supplier_id). */
  blocked_supplier_ids?: string[];
  /** Operator-FROZEN FX rates: fx_rates[FROM][TO] = decimal rate (1 FROM = rate TO).
   * A static operator constant, bound into the PR hash — NEVER a live/fetched rate.
   * Used only to convert invoice.currency -> policy.currency for the limit checks. */
  fx_rates?: Record<string, Record<string, string>>;
}

/** Redacted provenance summary that lives inside the hashed PR body. */
export interface EvidenceRef {
  source: DataMode;
  object_type: string;
  object_id_masked: string;
  fetched_at: string;
  available: boolean;
  /** digest of the critical fields at observation time. */
  critical_digest: string;
}

// ---------------------------------------------------------------------------
// Proposed action (allowlisted)
// ---------------------------------------------------------------------------

/** MVP action set. `prepare_payment_review` is the only one; it terminates at a
 * verified ready_for_qonto handoff (no Qonto mutation). */
export type ActionType = 'prepare_payment_review';

export interface ProposedAction {
  type: ActionType;
  target_object: { object_type: 'supplier_invoice'; id: string };
  parameters: {
    amount: Money;
    supplier_name: string;
    supplier_id: string;
    iban_masked: string | null;
  };
}

// ---------------------------------------------------------------------------
// Signals (weighted, advisory) and Gates (hard, terminal)
// ---------------------------------------------------------------------------

export type SignalStatus = 'observed' | 'insufficient_data' | 'not_applicable' | 'not_run';

export interface Signal {
  id: SignalId;
  status: SignalStatus;
  /** 0..1 observed risk; only meaningful when status === 'observed'. */
  risk: number;
  weight: number;
  reason: string;
  evidence_refs: string[];
}

/** The five scored signals whose weights feed the hashed policy digest. */
export type CoreSignalId =
  | 'possible_duplicate'
  | 'supplier_iban_drift'
  | 'unusual_amount'
  | 'evidence_gap_risk'
  | 'untrusted_instruction_indicator';

/** All signal ids. `policy_amount_over_limit` is added only when a trusted
 * policy file is supplied; it is NOT part of POLICY.signal_weights (so existing
 * PR fingerprints are unchanged when no policy is used). */
export type SignalId = CoreSignalId | 'policy_amount_over_limit';

export type GateStatus = 'pass' | 'fail' | 'unknown';

export type GateId =
  // Prepare + Act
  | 'explicit_action_intent'
  | 'intent_source_is_authoritative'
  | 'target_and_action_unambiguous'
  | 'required_evidence_present'
  | 'not_already_paid_or_matched'
  | 'exact_duplicate_not_completed'
  | 'within_trusted_policy_hard_limit'
  | 'supplier_not_blocked'
  // Act only
  | 'finance_pr_id_and_fingerprint_match'
  | 'full_hash_matches'
  | 'explicit_approval_present'
  | 'approval_route_satisfied'
  | 'not_expired'
  | 'critical_qonto_state_unchanged'
  | 'amount_currency_iban_supplier_unchanged'
  | 'prepared_action_exact_match'
  | 'not_used_or_in_progress'
  | 'writes_explicitly_enabled_for_test';

export interface Gate {
  id: GateId;
  phase: 'prepare' | 'act' | 'both';
  status: GateStatus;
  reason: string;
  remediation?: string;
}

export type RiskBand = 'low_observed_risk' | 'elevated_observed_risk' | 'high_observed_risk' | 'not_scored';

export interface RiskSummary {
  /** observed-only weighted risk in 0..1, or null when coverage is 0. */
  observed_risk: number | null;
  /** fraction of applicable weight that was actually observed. */
  coverage: number;
  band: RiskBand;
}

export type PolicyDecision = 'ready_for_finance_review' | 'manual_review_required' | 'blocked';

// ---------------------------------------------------------------------------
// Finance PR — the immutable, hashed body
// ---------------------------------------------------------------------------

export interface FinancePrBody {
  schema_version: string;
  pr_id: string;
  data_mode: DataMode;
  created_at: string;
  expires_at: string;

  intent: {
    literal_request: string;
    request_source: TextSource;
    message_id: string;
    intent_class: IntentClass;
    interpretation: string;
    ambiguity_notes: string[];
  };

  target: {
    organization_id_masked: string;
    invoice_id: string;
    invoice_number: string;
    supplier_name: string;
    supplier_id: string;
  };

  proposed_action: ProposedAction;

  /** salted digest of {amount,currency,iban_norm,supplier_name,supplier_id,status}. */
  critical_state_digest: string;
  critical_state_display: {
    amount: Money;
    iban_masked: string | null;
    supplier_name: string;
    status: string;
  };

  evidence: EvidenceRef[];
  signals: Signal[];
  risk: RiskSummary;
  gates: Gate[]; // prepare-phase snapshot

  policy: {
    policy_id: string;
    policy_version: string;
    policy_digest: string;
    decision: PolicyDecision;
    reviewer_route: ReviewerRoute;
  };

  /** Present only when an operator trusted-policy file constrained this PR. */
  trusted_policy?: {
    source: 'trusted_file';
    currency: string;
    hard_block_amount: string;
    /** digest binding the exact policy used (limits + block list + fx rates). */
    policy_digest: string;
    applied_role: string;
    applied_limit: string | null;
    /** Display-only list of active supplier blocks (names + masked ids). Present
     * only when the policy declared a block list. */
    blocked_suppliers?: string[];
    /** The operator-frozen conversion actually applied to this invoice, if any.
     * Present only when invoice.currency !== policy.currency AND a rate existed. */
    fx_applied?: {
      from: string;
      to: string;
      rate: string;
      converted_amount: string;
      note: string;
    };
  };

  sanitization: {
    untrusted_sources: string[];
    detected_instructions: string[];
    redaction_summary: string;
  };
}

export type ReviewerRoute = 'finance_reviewer' | 'designated_approver' | 'returned' | 'none';

// ---------------------------------------------------------------------------
// Integrity, approval, lifecycle, events — all live OUTSIDE the hashed body
// ---------------------------------------------------------------------------

export interface Integrity {
  algorithm: 'sha256';
  hash: string;
  /** grouped short code derived from the hash, e.g. "7C91-A2B4". */
  fingerprint: string;
}

export type LifecycleStatus =
  | 'prepared'
  | 'blocked'
  | 'approved'
  | 'reserved'
  | 'ready_for_qonto'
  | 'qonto_native_approval_pending'
  | 'stale'
  | 'integrity_failed'
  | 'replay_blocked'
  | 'expired'
  | 'execution_unknown';

export interface Approval {
  pr_id: string;
  fingerprint: string;
  approver: string; // masked membership id or 'designated_approver'
  route: ReviewerRoute;
  approved_at: string;
  raw_text: string;
}

export interface StoredPr {
  body: FinancePrBody;
  integrity: Integrity;
}

export type EventType =
  | 'invoice_observed'
  | 'evidence_collected'
  | 'intent_classified'
  | 'signal_evaluated'
  | 'hard_gate_evaluated'
  | 'second_review_requested'
  | 'second_review_returned'
  | 'finance_pr_prepared'
  | 'finance_pr_blocked'
  | 'finance_review_requested'
  | 'finance_pr_approved'
  | 'act_revalidation_started'
  | 'state_stale'
  | 'integrity_failed'
  | 'replay_blocked'
  | 'expired'
  | 'ready_for_qonto'
  | 'qonto_write_submitted'
  | 'qonto_native_approval_pending'
  | 'execution_unknown'
  | 'terminal';

export interface DomainEvent {
  seq: number;
  t: string; // ISO time
  type: EventType;
  pr_id: string;
  /** Redacted, display-safe payload only. */
  payload: Record<string, unknown>;
  note?: string;
}

// ---------------------------------------------------------------------------
// Act
// ---------------------------------------------------------------------------

export type ActOutcome =
  | 'ready_for_qonto'
  | 'blocked'
  | 'stale'
  | 'integrity_failed'
  | 'replay_blocked'
  | 'expired'
  | 'qonto_write_submitted'
  | 'qonto_native_approval_pending'
  | 'execution_unknown';

export interface ActResult {
  pr_id: string;
  fingerprint: string;
  outcome: ActOutcome;
  gates: Gate[];
  reasons: string[];
}

// ---------------------------------------------------------------------------
// Independent reviewer (optional, escalate-only, no Qonto tools)
// ---------------------------------------------------------------------------

export type ReviewVerdict = 'agree' | 'unclear' | 'disagree' | 'escalate';

export interface ReviewOutput {
  verdict: ReviewVerdict;
  rationale: string;
  reviewer_id: string;
  available: boolean;
}
