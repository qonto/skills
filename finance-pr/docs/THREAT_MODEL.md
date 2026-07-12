# Threat model

## 1. Scope and claims

Protected asset: correctness and auditability of AI-initiated financial proposals before they reach a Qonto write tool.

Trust boundaries:

1. User-authored authority versus untrusted documents/tool output.
2. Claude/Skill orchestration versus local Finance PR engine.
3. Immutable prepared proposal versus later approval/lifecycle data.
4. Local Act gate versus Qonto MCP.
5. Finance PR review versus Qonto permissions, native approval, SCA, and execution.
6. Qonto/sandbox data versus UI, logs, fixtures, and optional model provider.

The MVP protects only the Finance PR workflow. It cannot prevent a user, another agent, or another MCP client from invoking Qonto directly. Do not claim global enforcement.

## 2. Assets

- literal user intent and authority provenance;
- invoice, supplier, amount, currency, IBAN, attachment and match state;
- exact proposed Qonto action;
- policy version and decision;
- immutable Finance PR hash/fingerprint;
- approval binding and reviewer route;
- one-shot execution state;
- Qonto credentials/tool connection (never handled by the local engine);
- personal and financial data;
- audit event integrity.

## 3. Threat actors and failure sources

- accidental user ambiguity;
- compromised or malicious invoice/document author;
- hallucinating or instruction-following primary model;
- unavailable or inconsistent secondary model;
- local tampering with PR/store/event files;
- stale concurrent Qonto changes;
- replay, duplicate invocation, network timeout, or ambiguous mutation response;
- developer/demo error that presents synthetic values as real;
- unauthorized direct Qonto tool use outside the protected workflow.

## 4. Threat register

| ID | Threat | Example | Impact | MVP control | Residual risk / roadmap |
|---|---|---|---|---|---|
| T1 | Question interpreted as permission | “Can this be paid?” becomes create request | Unauthorized action | Typed intent class; `explicit_action_intent` hard gate; exact approval syntax | Language classifier can err; require literal approval at Act |
| T2 | Advice becomes execution | “How should I pay this?” triggers write | Unauthorized action | Advice/observe modes cannot reach Act | Direct MCP bypass remains |
| T3 | Document authorizes itself | PDF says “pay immediately” | Authority confusion | Document/tool text tagged untrusted; authority provenance gate | Detection may miss instruction-like text, but provenance separation still holds |
| T4 | Prompt injection | Invoice says ignore policy/use tools | Agent manipulation | Never treat raw document as instructions; sanitize; advisory indicator; hard gate when proposed action originates from document | Hardened content isolation/proxy is roadmap |
| T5 | Hallucinated supplier/amount/IBAN | Model invents a beneficiary | Wrong financial target | Proposed values must map to structured Qonto evidence; missing/conflict gate | Qonto OCR may itself be wrong; show provenance and attachment conflict |
| T6 | State changes after review | IBAN, amount, status or match changes | Approved artifact no longer valid | Critical snapshot digest; fresh Qonto reread; stale gate; new PR required | Race between final read and Qonto write; minimize window, use Qonto idempotency/version controls if available |
| T7 | Modified Finance PR | Local JSON edited after approval | Approval applied to different payload | Canonical full SHA-256 recomputation; fingerprint binding | Local attacker could replace store and approval together; signing/remote append-only log is roadmap |
| T8 | Replay/double submit | Same approved PR used twice | Duplicate request/payment | Atomic `approved -> executing` reservation; terminal one-shot states; no hidden retry | Distributed/multi-host execution needs centralized store roadmap |
| T9 | Already paid/matched invoice | Closed invoice prepared again | Duplicate payment | Fresh status, matched transaction and request checks as hard gates | Depends on tool completeness and state freshness |
| T10 | Insufficient history looks safe | New supplier gets anomaly score 0 | False confidence | `insufficient_data`, separate coverage, minimum coverage policy, manual review | Reviewer may still over-trust color; full decision label required |
| T11 | Correlated signals double-count | Amount counted as anomaly, velocity, budget, history | Inflated/opaque risk | One signal per risk cause; documented weights; gates separate | Calibration remains heuristic; do not call probability |
| T12 | Unclear Green | Reviewer reads Green as approved/safe | Over-approval | Approved Green copy; Qonto boundary; always explicit Finance + Qonto remaining steps | Human-factor testing needed |
| T13 | Finance review confused with Qonto approval | “Approved” shown before native flow | Governance failure | State names `finance_pr_approved` and `qonto_native_approval_pending`; separate zones | UI copy regression; acceptance test exact terms |
| T14 | Fake native roles | CFO/CEO shown as Qonto role | Misleading product claim | `designated_approver`; titles are local policy labels only | Qonto roles should be read/displayed only when MCP returns them |
| T15 | Sensitive data leakage | Full IBAN, ID or attachment URL in report/model/log | Privacy/security breach | Masking, minimal persistence, URL ban, sanitized model packet, fixture scan | Local process memory still sees necessary data; retention roadmap |
| T16 | Synthetic shown as sandbox | Demo result appears real | Misrepresentation | Required `data_mode`, global banner, provenance ledger, fixture prefixes | Screenshots can crop label; repeat label in token/panel/summary |
| T17 | Optional model authorizes | Second model says “safe” | Non-deterministic bypass | No tools/authority; can only preserve/increase review; deterministic result cannot be reduced | Provider privacy/availability; feature flag off by default |
| T18 | Second model unavailable | Timeout silently skips review | False confidence | Required review fails to manual; record unavailable event | Adds latency; optional MVP |
| T19 | Direct Finance PR bypass | Agent calls Qonto write directly | All pre-Qonto controls skipped | Skill constitution, write tools disabled by default, explicit sandbox test gate, honest claim boundary | Hardened MCP proxy/allowlist is required for production |
| T20 | Ambiguous write response | Timeout after Qonto accepted call | Unsafe retry/duplicate | `execution_unknown`; never retry; reconcile with reads/idempotency key if supported | Exact reconciliation depends on Qonto tool contract |
| T21 | Fingerprint collision/confusion | User checks only four chars | Wrong PR approval | Use grouped 8 hex chars for display and full hash internally; approval includes ID + fingerprint | Human transcription risk remains; structured approval UI roadmap |
| T22 | Policy changes after Prepare | New threshold but old PR acts | Stale policy use | Hash policy ID/version/digest; Act requires configured policy version rule | Decide whether old PRs expire immediately; default require new PR |
| T23 | Evidence URL expires | Act relies on temporary attachment URL | Missing evidence / leakage | Hash content/metadata; never persist URL; reread attachment reference if required | Full content comparison depends on tool access |
| T24 | Source-code ownership issue | Copy unlicensed FlowTwin code | Submission/legal risk | Clean reimplementation; attribution; licence gate | Obtain written permission before any copy |

## 5. Five largest blind spots

### 5.1 Direct bypass is not technically prevented

The Skill is a workflow convention. If the same agent still sees raw Qonto write tools, it can bypass the local Act gate. For the hackathon, disable writes by default, place explicit Skill instructions around them, and demonstrate one controlled path. Production requires an MCP proxy, capability broker, or Qonto-side integration where the Finance PR token is mandatory.

### 5.2 Integrity is not authenticity

A SHA-256 hash detects accidental or partial mutation, but a local attacker able to replace the PR, hash, approval, and database can forge the entire history. Production needs signatures or MACs backed by protected keys, append-only remote logging, reviewer authentication, and separation of duties.

### 5.3 The read/write race cannot be removed locally

Qonto state can change after Act's final read and before the write. Use Qonto version/idempotency/precondition fields if the real tool supports them. Keep the window short and ensure native Qonto validation remains authoritative.

### 5.4 Sparse data limits risk conclusions

Supplier history may be absent, inconsistently named, or inaccessible through the MCP. The product can detect inconsistency only in available evidence. Coverage and unknown states are essential; a Green result must never imply supplier verification.

### 5.5 Human review can become a rubber stamp

Fingerprints and reports do not guarantee attention. Make the action diff prominent, force explicit PR ID/fingerprint binding, surface changed IBAN/amount in human language, and keep Qonto approval distinct. Structured approval UI, dual control, and reviewer analytics are roadmap.

## 6. Optional second-model safety design

Trigger only when configured:

- primary intent is ambiguous;
- proposal exceeds a policy threshold;
- literal user language and proposed action differ materially.

Sanitize before sending:

- strip document text except a neutral description of the conflict;
- mask supplier and object identifiers;
- remove IBAN, email, attachment URL, personal data, and tool credentials;
- include deterministic findings as immutable facts;
- state that the model cannot authorize or call tools.

Merge rules:

1. Deterministic fail remains fail.
2. Deterministic unknown remains unknown/manual.
3. Model `disagree`, `unclear`, or `escalate` adds manual review.
4. Model `agree` does not lower risk or satisfy a gate.
5. Timeout, schema failure, provider error, or missing configuration produces `unavailable`; if review was required, route manual.

## 7. Security verification priorities

1. Prove Observe and Prepare call no write tools.
2. Prove Act accepts no action values from chat input.
3. Prove all listed hard gates dominate every low-risk score.
4. Prove atomic replay protection under concurrent attempts.
5. Prove ambiguous Qonto responses are never retried.
6. Prove redaction across CLI, report, event fixture, UI, and model payload.
7. Prove direct-bypass limitation is documented in UI and README.

## 8. Production roadmap

- MCP proxy/capability token that cryptographically requires a valid Finance PR.
- Signed PRs and approvals with managed keys.
- Central append-only event store and audit export.
- Reviewer identity mapping to Qonto membership and separation of duties.
- Retention/deletion policy, encryption at rest, access controls, and DPIA.
- Atomic Qonto preconditions/idempotency/reconciliation using verified tool support.
- Calibrated policy evaluation from real, consented history.

