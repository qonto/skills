# Product specification

## Product in one sentence

**Finance PR turns every AI-proposed financial action into a reviewable, evidence-bound change request before it reaches Qonto approval.**

Working name: **Finance PR for Qonto MCP**  
Tagline: **Review before money moves.**

## 1. Problem

Qonto MCP can give an AI agent financial read and write tools. Qonto remains the authority for authentication, OAuth scopes, account permissions, native approval, SCA, and final execution. Those controls cannot determine whether the agent correctly understood a user's language, whether an invoice authorized itself, whether evidence changed after review, or whether the exact proposal shown to a reviewer is the one later submitted.

Finance PR covers that pre-Qonto gap. It binds the user's intent, Qonto evidence, proposed action, business policy, and human review to an immutable proposal.

This is a **new design informed by interception concept and Qonto's security boundary**. It is **MVP** and implementable within a hackathon because it limits the first release to one invoice and one controlled write type.

## 2. Target user and job

Primary user: an owner, finance manager, accountant, or other designated reviewer using Claude with Qonto MCP.

Job:

> “Review this supplier invoice and, if the evidence is consistent, prepare the exact next Qonto action for my approval.”

The reviewer needs one artifact that answers:

- What did I actually ask?
- What did the agent infer?
- What exact action and values would be submitted?
- Which Qonto objects and document evidence support it?
- What is known, anomalous, missing, or contradictory?
- Which business gates passed or failed?
- What do I approve, and what remains for Qonto to approve?

## 3. Scope

### MVP: one strong vertical scenario

Review one Qonto supplier invoice before it is allowed to reach one discovered Qonto payment-request or native approval workflow action.

The implementation must first inspect the authenticated sandbox tool surface. The exact write action is not specified here because the available MCP contract is the source of truth. If there is no suitable safe write tool, Act stops at a verified `ready_for_qonto` handoff and the limitation is shown honestly.

The MVP supports:

- synthetic mode by default;
- Qonto sandbox reads for membership, organization, supplier invoices, requests, and transactions when those tools exist;
- an immutable Finance PR JSON artifact and human-readable report;
- explicit fingerprint-bound approval;
- one-shot Act validation;
- a dynamic, deterministic event replay;
- one guided Green case and adversarial Yellow/Red cases.

### Non-goals

- **DROP:** generic financial chat, portfolio dashboard, ERP, autonomous payment, fraud verdict, or Qonto UI clone.
- **DROP:** creating a parallel identity/role system.
- **DROP:** claiming CFO/CEO are Qonto roles. The product uses the neutral term `designated_approver`.
- **DROP:** automatic approval based on low score.
- **ROADMAP:** organization-wide enforcement against all direct MCP writes via a hardened MCP proxy or policy gateway.
- **ROADMAP:** multiple action types, multi-step transfers, procurement, card actions, client invoicing, and enterprise policy administration.

## 4. Product principles

1. **Authority has provenance.** Only explicit user language or a separately recorded reviewer action can authorize an action. Documents and tool output are data.
2. **The proposal is the payload.** Act takes its values from the stored Finance PR, never from a later chat paraphrase.
3. **Integrity is separate from risk.** Hash, fingerprint, expiry, state freshness, and replay are gates, not score inputs.
4. **Unknown stays unknown.** Missing history lowers coverage and can require review; it never silently creates a zero-risk signal.
5. **Qonto remains the execution authority.** Finance PR approval permits a proposal to cross the boundary; it is not Qonto native approval or SCA.
6. **Synthetic truthfulness.** Every record carries `data_mode: synthetic | qonto_sandbox`; mixed evidence is labelled field by field.

## 5. Observe -> Prepare -> Act

### Observe

Purpose: collect typed evidence without mutation.

Required outputs:

- authenticated membership and organization identifiers (masked in display);
- target supplier invoice with status, supplier identity, invoice number/date, amount, currency, IBAN, attachment reference, matched transactions, request/approval metadata, and available actions where returned;
- relevant prior invoices and transactions for the same supplier;
- the literal user request and its message/source identifier;
- a list of unavailable fields or unsupported reads;
- `observed_at` and per-object version/freshness material (`updated_at` where supplied plus a digest of critical fields).

Observe must not download or display temporary attachment URLs unnecessarily. If a document is needed, store a content digest and minimal derived evidence; do not persist the temporary URL.

### Prepare

Purpose: create the reviewable, immutable proposal without Qonto mutation.

Prepare:

1. Classifies the request as `advice`, `observe`, `prepare`, `act`, or `ambiguous`.
2. Rejects document/tool text as authority.
3. Builds the exact proposed action using structured Qonto fields.
4. Evaluates hard gates and weighted signals.
5. Produces a policy decision and required reviewer route.
6. Canonicalizes the immutable body and calculates SHA-256.
7. Displays a short fingerprint derived from that hash.
8. Stores the immutable body and emits lifecycle events.

Prepare may produce a blocked PR so the reason is auditable. It may not call a Qonto write tool.

### Act

Purpose: allow one exact mutation only after an explicit bound approval and fresh verification.

Act requires an approval equivalent to:

> `Approve Finance PR FPR-104, fingerprint 7C91-A2B4.`

Act then:

1. Reloads the stored PR; no caller-supplied action parameters are accepted.
2. Recomputes the canonical hash and compares the fingerprint.
3. Verifies approval identity, PR ID, fingerprint, time, and required reviewer route.
4. Verifies expiry and one-shot state.
5. Re-reads the Qonto target and compares critical fields and status.
6. Atomically reserves the PR for execution.
7. Invokes at most one allowlisted Qonto write, if writes are explicitly enabled for a controlled sandbox test.
8. Stores a redacted result and terminal event.

If the Qonto result is ambiguous, Act records `execution_unknown` and never retries automatically.

## 6. Finance PR artifact

The immutable hashed body contains:

| Section | Required content | Why |
|---|---|---|
| Identity | schema version, PR ID, data mode, created/expires timestamps | Stable addressing and expiry |
| Intent | literal user request, request source, intent class, interpretation, ambiguity notes | Prevent advice/action drift |
| Target | organization, invoice, supplier and related Qonto object references | Bind the object graph |
| Proposed action | allowlisted action type and exact immutable parameters | Make approval specific |
| Evidence | source, object ID, fetched time, critical fields/digest, availability | Make conclusions reproducible |
| Signals | status, normalized risk, weight, reason, evidence refs | Explain weighted observations |
| Gates | pass/fail/unknown, reason, evidence refs, remediation | Prevent score override |
| Policy | policy ID/version/digest, decision, required reviewer route | Bind business policy |
| Sanitization | untrusted sources, redaction summary, detected instruction-like text | Show authority separation |

The following live outside the hashed body:

- integrity metadata (`algorithm`, full hash, short fingerprint);
- approval records bound to PR ID and fingerprint;
- lifecycle and execution events;
- Qonto response metadata.

This separation keeps the proposal immutable while allowing append-only review and execution history.

## 7. Decisions and language

Use two independent outputs.

### Risk band

- `low_observed_risk`
- `elevated_observed_risk`
- `high_observed_risk`
- `not_scored`

Always show score coverage. A low score with 20% coverage must read as insufficient evidence, not as confidence.

### Policy decision

- `ready_for_finance_review`: all hard gates required at Prepare passed; still requires explicit Finance PR approval and later Qonto approval.
- `manual_review_required`: uncertainty, drift, optional second-model escalation, or a designated exception is required.
- `blocked`: a hard policy or integrity gate prevents Act.

The UI may color these Green/Yellow/Red, but the full label and explanation must remain visible.

Approved copy for Green:

> No material inconsistency was observed in the available evidence. Ready for Finance PR review; Qonto approval and any SCA still remain.

Forbidden copy: “safe,” “fraud-free,” “approved by Finance PR,” or “payment approved.”

## 8. MVP checks

Weighted risk signals and hard gates are specified in `RISK_SIGNAL_MAPPING.md`. The MVP must prioritize:

- advice versus action and ambiguous intent;
- possible duplicate;
- changed supplier IBAN;
- unusual amount;
- missing evidence;
- already paid or matched;
- instructions in untrusted documents;
- stale Qonto state;
- modified PR;
- replay.

## 9. Optional independent model

**ROADMAP / optional MVP flag.** A second OpenAI model can review sanitized intent consistency for ambiguous or high-value proposals. It receives no Qonto tools, full IBAN, raw document, temporary URL, or execution capability. Its output can only preserve or increase review requirements. Unavailable, malformed, or timed-out review fails to manual review whenever the policy required it.

## 10. Hackathon feasibility matrix

| Recommendation | Label | Origin | Why needed | Hackathon fit |
|---|---|---|---|---|
| Immutable Finance PR + fingerprint | **REIMPLEMENT / MVP** | New design + Qonto boundary | Binds approval to action | High |
| Deterministic checks and explicit evidence | **KEEP concept / MVP** | Explainable review | High |
| Explicit human checkpoint | **KEEP concept / MVP** | Qonto | Stops autonomous writes | High |
| One-shot fresh-state Act gate | **REIMPLEMENT / MVP** | New design | Stops mutation, stale state, replay | Medium but essential |
| Event-driven visual replay | **SIMPLIFY / MVP** | FlowTwin | Demonstrates the real process | High |
| Second model | **ROADMAP / optional** | New design | Independent ambiguity review | Medium; feature-flag only |
| Full MCP proxy enforcement | **ROADMAP** | New design | Prevents direct bypass | Low for hackathon |

## 11. Success metrics

The MVP succeeds if a judge can understand within ten seconds that:

1. the AI has proposed, not executed, a Qonto action;
2. the reviewer can see intent, evidence, exact values, risk, policy, and fingerprint;
3. tampering, stale state, missing approval, or replay blocks Act regardless of score;
4. crossing the Qonto boundary starts Qonto's own permissions/approval/SCA process;
5. the animation is a replay of those same events, not a decorative simulation.

