# Risk signal mapping

## 1. Finding: “13 signals” is a mock dashboard schema
s exact 13 signal names and weights are declared in:

- `/home/victor/_aprojects/qontofrontend/dashboard/src/types/dashboard.ts:14-42`
- weights at `types/dashboard.ts:147-162`
- synthetic value generation at `frontend/dashboard/src/lib/mockData.ts:78-102`

The UI describes `Final Score = sum(signal_value * weight) * 100`, and weights sum to 1.00. The incident generator does not calculate the displayed risk score that way. It chooses a risk band and random score first, then creates signal values from that band (`mockData.ts:169-223`). Therefore the 13-signal table is presentation data, not an implemented causal risk engine.

The exact synthetic generator selects `baseIntensity` by preselected label—low `0.15`, medium `0.40`, high `0.65`, blocked `0.85`—then adds `jitter = clamp(random(-0.25, 0.25))`. Because jitter is clamped before addition, it is in `[0, 0.25]`, never negative. Each table formula below is finally clamped to `[0, 1]`.

The real backend separately registers eight checks and computes a weighted average. Both inventories are documented below.

## 2. Exact 13 dashboard signals

All current values are synthetic/random. “Qonto support” below means conceptually calculable after Claude verifies the real MCP fields; it does not claim that the current local MCP returns every field.

| # | Exact signal | Weight | Current mock formula | Semantic type | Qonto/MVP assessment | Decision |
|---:|---|---:|---|---|---|---|
| 1 | `policy_alignment` | 0.20 | `clamp(baseIntensity + nonnegativeJitter)` | Positive safety metric by name, but treated as risk | Business policy is local; Qonto supplies evidence | **REIMPLEMENT** as deterministic `policy_violation_risk`; hard policy conflicts are gates |
| 2 | `override_memory` | 0.02 | `clamp(baseIntensity * 0.3 + jitter)` | Undefined risk concept | No reliable Qonto source | **DROP**; use explicit exception/approval records instead |
| 3 | `amount_anomaly` | 0.15 | `clamp(baseIntensity * 1.1 + jitter)` | Risk | Qonto history may support | **SIMPLIFY / MVP** as `unusual_amount` with insufficient-data state |
| 4 | `duplicate` | 0.10 | 15% chance of random 0.5–1, else 0 | Risk | Supplier invoice/transaction history can support | **REIMPLEMENT / MVP** as `possible_duplicate`; paid/matched exact duplicate is a gate |
| 5 | `history_similarity` | 0.10 | `clamp(1 - baseIntensity + jitter)` | Positive safety metric | Historical Qonto data may support | **DROP as separate score**; its evidence belongs to duplicate/amount/IBAN checks |
| 6 | `budget_delta` | 0.06 | `clamp(baseIntensity * 0.8 + jitter)` | Risk | No confirmed Qonto budget source | **DROP MVP / ROADMAP** with explicit external budget policy |
| 7 | `external_verification` | 0.08 | `clamp(0.5 + jitter)` | Positive safety metric | Requires external registry/vendor data | **DROP MVP / ROADMAP**; never fabricate |
| 8 | `snapshot_mismatch` | 0.04 | 10% chance of random 0.3–0.8, else 0 | Integrity risk | Qonto reread supports critical-field comparison | **REIMPLEMENT as hard stale-state gate**, not weighted risk |
| 9 | `actor_anomaly` | 0.08 | `clamp(baseIntensity * 0.9 + jitter)` | Risk | Membership plus history might partially support | **DROP MVP / ROADMAP**; insufficient volume and bias risk |
| 10 | `workflow_consistency` | 0.02 | `clamp(1 - baseIntensity * 0.5 + jitter)` | Positive safety metric | User request + proposed action + Qonto evidence support | **REIMPLEMENT as intent/action gates**; optional ambiguity signal |
| 11 | `timing_velocity` | 0.05 | `clamp(baseIntensity * 0.6 + jitter)` | Compound risk | Timestamps/transaction history may support | **DROP MVP**; amount frequency is correlated and time-of-day is weak |
| 12 | `geo_mismatch` | 0.04 | 8% chance of random 0.4–1, else 0 | Risk | No appropriate Qonto MCP evidence confirmed | **DROP MVP / ROADMAP** only with consented security telemetry |
| 13 | `model_confidence` | 0.06 | `clamp(0.6 + jitter)` | Positive epistemic metric | Model metadata, not financial risk | **DROP from risk**; if used, display only as model triage metadata |

`jitter()` is itself biased: negative samples are clamped to zero before addition (`mockData.ts:86`), so it only increases a base value. More importantly, the UI uses low `external_verification` and low `workflow_consistency` as category warnings (`mockData.ts:134-138`) while the contribution view adds their high values as risk. The direction is internally contradictory.

### Correct normalization

Every numeric risk metric must mean:

- `0.0`: no observed risk in available evidence;
- `1.0`: maximum observed risk under the documented rule.

If a source is a positive safety metric, either:

1. invert it with a justified calibration (`risk = 1 - safety`), rename it as risk, and preserve availability; or
2. keep it outside the risk score as confidence/coverage.

Do not invert missing data. `unknown` is not a number.

## 3. Eight backend checks

The active list is `backend/app/services/checks/__init__.py:43-54`. The backend aggregate is:

`risk_percent = sum(result.score * check.weight * 100) / sum(check.weight)`

An empty result returns 50; check errors are injected as 0.5 (`agentic_service.py:179-190,276-301`). Finance PR must not use those defaults.

Exact implementation files:

- `backend/app/services/checks/policy_compliance.py`
- `backend/app/services/checks/workflow_consistency.py`
- `backend/app/services/checks/vendor_reputation.py`
- `backend/app/services/checks/amount_velocity.py`
- `backend/app/services/checks/budget_check.py`
- `backend/app/services/checks/timing_anomaly.py`
- `backend/app/services/checks/amount_anomaly.py`
- `backend/app/services/checks/duplicate_invoice.py`

Their weights total 6.3; the aggregate divides by that total for a complete run.

| Check | Weight | Inputs | Current formula/dependency | Deterministic? | Qonto support | Finance PR decision |
|---|---:|---|---|---|---|---|
| `policy_compliance` | 1.0 | policy text; supplier email; amount/currency; category; PO; item/match/GR; requester/approver roles; approval count; prepayment | LLM score; fallback adds 0.5 prohibited category, 0.2 personal email, 0.2 missing PO, 0.4/0.5 role, 0.3 dual approval, 0.3 prepayment, 0.1 GR | Mixed | Partial invoice evidence; policy is local; several fields may not exist | **REIMPLEMENT** typed gates; no LLM authorization |
| `workflow_consistency` | 0.9 | conversation + supplier, amount, currency, description, category | LLM; fallback +0.3 amount absent, +0.2 supplier absent; no history gives 0.3 | Mixed | Yes for structured fields plus user request | **REIMPLEMENT / MVP** intent and exact-action gates |
| `vendor_reputation` | 0.8 | supplier email/domain, fabricated domain age/rating, optional LLM | +0.3 each regex, +0.4 age<90, +0.2 age<180, +0.3 personal domain; LLM may increase | External/LLM with mock | Not from Qonto alone | **DROP MVP** |
| `amount_velocity` | 0.7 | amount, recent count/total, vendor count/total | +0.3 >10k, +0.3 >50k, +0.3 >3x all-history average, +0.2 >2x vendor average | Deterministic but inputs mocked | Potentially with history | **SIMPLIFY / MVP** into unusual amount |
| `budget_check` | 0.6 | amount, category, hard-coded budget/spend | +0.5 over remaining, +0.3 over whole limit, +0.2 >80% remaining, +0.1 utilization >90% | Deterministic with fake data | Not confirmed | **DROP MVP** |
| `timing_anomaly` | 0.5 | current UTC, record created time, amount | +0.2 outside 08–18 UTC, +0.3 weekend, +0.1 month-end, +0.2 high-value month-end, +0.1 year-end, +0.2 age>30; >90 branch unreachable | Deterministic | Partial timestamps | **DROP MVP** |
| `amount_anomaly` | 0.8 | amount, category, historical amounts | category n<5 -> pass; z<=2 ->0; 2<z<=3 ->0.5; z>3 ->1; zero-variance mismatch ->1 | Deterministic | Potentially, subject to history mapping | **SIMPLIFY / MVP** and make n<minimum unknown |
| `duplicate_invoice` | 1.0 | supplier name, invoice ID, amount, record `created_at`, history | supplier+invoice ID ->1; supplier+amount+same day ->1; amount+same day/different supplier ->0.5 | Deterministic | Yes if history/status/matches returned | **REIMPLEMENT / MVP** with better dates/identity |

## 4. Duplicated and correlated signals

Do not add all prototype outputs. Group them by risk cause:

| Correlated family | Prototype members | Problem | MVP treatment |
|---|---|---|---|
| Amount/history | amount anomaly, amount velocity, history similarity, budget delta, high-value policy | The same large amount can be counted five times | One `unusual_amount` signal; high-value review is a separate policy route, not added again |
| Intent/consistency | policy alignment, workflow consistency, model confidence, override memory | LLM uncertainty and user/action mismatch blur together | Deterministic intent gates; optional second-model escalation metadata |
| Supplier identity | vendor reputation, external verification, personal-email policy, actor anomaly | Weak proxies can double-count and create bias | MVP only compares Qonto supplier/invoice/IBAN evidence; external reputation is roadmap |
| Duplicate | duplicate, history similarity, snapshot mismatch, already matched/paid | Exact and fuzzy evidence should have different consequences | Possible duplicate is weighted; paid/matched and state change are hard gates |
| Timing | timing velocity, actor anomaly, amount velocity | Activity frequency and time-of-day can reflect the same event | Drop from MVP |

## 5. Finance PR MVP weighted signals

Weights are policy defaults, not learned probabilities. They sum to 1.00 among configured signals.

| Signal | Default weight | Statuses | Risk calculation | Why | Origin |
|---|---:|---|---|---|---|
| `possible_duplicate` | 0.30 | observed / insufficient_data / not_applicable | 1.0 same supplier+invoice number not confirmed paid; 0.7 same supplier+amount+currency+near date; 0.4 fuzzy candidate; 0 no candidate | Duplicate payment is the clearest invoice risk | simplified |
| `supplier_iban_drift` | 0.30 | observed / insufficient_data / not_applicable | 1.0 known supplier with new IBAN and corroborating conflict; 0.7 known supplier with changed IBAN; 0.4 new supplier/no known IBAN; 0 same normalized IBAN | Common high-impact review point | New Qonto design |
| `unusual_amount` | 0.20 | observed / insufficient_data | Documented robust rule: compare supplier history median/range; 1.0 extreme, 0.5 elevated, 0 normal. Exact thresholds live in policy | Explains amount deviation without fake certainty | simplified |
| `evidence_gap_risk` | 0.10 | observed / not_applicable | Only optional evidence gaps: 0–1 by typed severity. Required evidence failures are gates | Shows review friction without overriding requirements | New design policy idea |
| `untrusted_instruction_indicator` | 0.10 | observed / not_run | 1.0 explicit tool/approval instruction in document; 0.5 instruction-like text; 0 none observed. Detection is advisory | Highlights document manipulation without claiming perfect detection | New threat design |

### Aggregate

For observed signals only:

`observed_risk = sum(risk_i * weight_i) / sum(weight_i observed)`

`coverage = sum(weight_i observed) / sum(weight_i configured_and_applicable)`

Rules:

- insufficient data is excluded from the numerator and denominator of observed risk but lowers coverage;
- no risk band is shown when coverage is zero;
- Green/`ready_for_finance_review` requires all Prepare gates pass and policy-defined minimum coverage (default 0.80);
- manual review is required below coverage threshold;
- a score never authorizes Act.

Suggested display bands only:

- `<0.25`: low observed risk;
- `0.25–<0.70`: elevated observed risk;
- `>=0.70`: high observed risk.

These are transparent demo policy defaults, not calibrated fraud probabilities.

## 6. Hard execution gates

Every gate is `pass | fail | unknown`. Only pass can proceed.

| Gate | Prepare or Act | Failure behavior |
|---|---|---|
| `explicit_action_intent` | Both | Advice/question/ambiguous request cannot act |
| `intent_source_is_authoritative` | Both | Document/tool text cannot authorize |
| `target_and_action_unambiguous` | Both | Require clarification/new PR |
| `required_evidence_present` | Both | Block or manual per typed policy; unknown never pass |
| `not_already_paid_or_matched` | Both, fresh at Act | Block |
| `exact_duplicate_not_completed` | Both | Block completed duplicate; possible duplicate routes review |
| `finance_pr_id_and_fingerprint_match` | Act | Block |
| `full_hash_matches` | Act | Block and integrity event |
| `explicit_approval_present` | Act | Block |
| `approval_route_satisfied` | Act | Block |
| `not_expired` | Act | Expire and require new PR |
| `critical_qonto_state_unchanged` | Act | Mark stale and require new PR |
| `amount_currency_iban_supplier_unchanged` | Act | Block regardless of score |
| `prepared_action_exact_match` | Act | Block; Act never accepts replacement params |
| `not_used_or_in_progress` | Act | Replay block |
| `writes_explicitly_enabled_for_test` | Act | No Qonto mutation |

## 7. Example logic review

`EXAMPLE.md` correctly asks for modular risk values and duplicate self-exclusion. Two recommendations must change:

1. “Category has fewer than five records -> 0.0” must become `insufficient_data`, with manual review when amount history is required.
2. A plain average of all signals treats correlated and unavailable signals as independent evidence. Finance PR uses documented weights, one signal per risk cause, and separate coverage.

The example's “same amount and same day from a different supplier = 0.5 duplicate” is too broad. In the MVP it is at most a weak candidate unless invoice number, supplier identity, currency, attachment digest, or transaction match corroborates it.
