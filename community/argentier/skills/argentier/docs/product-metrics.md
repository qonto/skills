# Argentier — Product Metrics & North Star Framework

> **One question this document answers:** how do we know Argentier works — for the user *and* the
> business — with a number that cannot be hallucinated by the LLM and whose core component can be
> checked against the customer's own bank statement? And, just as important: **where that number is
> a projection, where the guardrails are convention rather than architecture, and what we still have
> to build.** A metric framework that hides its own gaps is a vanity framework.

Argentier is a **read-only** AI CFO agent on the Qonto MCP. It is **free**; it charges a **5% success
fee on savings proven at J+30** ("no savings, no cost"). That business model is why the North Star is
easy to choose: the metric that captures user value and the metric that captures revenue are **the
same euro**.

---

## 0. What is real today (read this first)

The framework below is designed against the product's **actual** mechanics, not an idealized one.
The load-bearing facts:

- `data/decisions.json` is a **single flat file** with `decisions: []` (empty today) and two scalars,
  both `0`: `economies_prouvees_eur_an`, `economies_en_attente_eur_an`. **There is no account/customer
  identifier anywhere in the data model** — the prototype is single-tenant.
- The real decision-status machine, from the commands, is **`approuve | refuse` → `prouve`**.
  `audit.md` step f writes `statut: approuve|refuse`; `verify.md` promotes `approuve → prouve`. There
  is **no per-decision `en_attente` status** — "pending" exists only as the aggregate scalar
  `economies_en_attente_eur_an` (sum of approved-not-yet-proven euros).
- `engine.py analyze()` annualizes recurring levers **×12** (`montant_mensuel × 12`, L354/L381) and FX
  **×365/90** (L259). `/verify` observes ~30 real days. **So the annual figure is a projection of a
  proven monthly drop, not an observed annual fact.** The framework treats it as such throughout.
- `engine.py classify()` uses only the hardcoded `PRO_KEYWORDS`/`PERSO_KEYWORDS` — it **never loads
  `profile.json`**. CLAUDE.md's "extensibles via profile.json" is a design intent, **not wired in code**.
- `settings.json` hard-denies Qonto write tools, but grants `mcp__linkup__*` and `mcp__brightdata__*`
  with **unrestricted args**, and does **not** deny the send-capable non-Qonto MCPs present in the
  environment (Gmail `create_draft`, Instantly, Apollo sequences).

Every metric that needs data we don't keep yet is marked **(to instrument)** and collected in §6.

---

## 1. The North Star Metric

### `economies_prouvees_eur_an` — Annualized Proven Savings (APS)

**Definition.** The sum of **engine-computed** `montant_optimisable_eur` over decisions that a human
**approved and sent**, and for which a **J+30 read-only re-read of the real Qonto account confirmed
the recurring debit dropped or vanished** for the elapsed cycle(s) — the recurring SEPA/card debit
disappeared, the renegotiated amount fell, or the aggregated `fx_card` fees dropped. Money the
business keeps because Argentier read the blind spots in its account. Not money "identified", not
money "recommended": money whose **monthly drop is visible on the statement**.

**The two halves — stated plainly.**

- **Proven half:** the **monthly** reduction that `/verify` sees leave the real statement at J+30.
- **Projected half:** the **×12** (or ×365/90 for FX) that `engine.py` applies. This is a
  deterministic annualization of the proven monthly delta — **it is not itself on any statement.** A
  tool cancelled in month 1 that silently resumes in month 2 would, until net-of-reversal is built
  (§6, backlog), keep a full projected year in APS. We name this openly rather than claim "you can't
  fake a number on the customer's statement" — the customer's statement shows one cycle; the year is
  Argentier's extrapolation of it.

**Formula.**

```
APS  =  Σ  montant_optimisable_eur          over decisions where statut = "prouve"
Revenue = 0.05 × APS         ⇒   user value  ==  business value   (identity, not correlation)
```

Expanded through the funnel the team actually moves:

```
APS ≈  Audits run
     × Qualified sourced+dated levers per audit        (engine yield)
     × Human approval rate            (recommend → approuve)
     × J+30 proof rate                (approuve → prouve)
     × Durability (non-reversal, once built)   × Avg proven € per lever
```

**Per-lever annualization is the engine's, verbatim** (rule #2 — the LLM never computes a euro).
Crucially, **only levers with an observable statement drop are APS-eligible.** From `engine.py`:

| Lever | `montant_optimisable_eur` | APS-eligible? | Rationale |
|---|---|---|---|
| Recurring sub (`abonnement`) | `montant_mensuel × 12` (L354/381) | ✅ annualized into APS | recurring debit drop is observable at J+30 |
| FX fees (`fx`) | 90-day `qonto_fee`+`fx_card` × 365/90 (L259) | ✅ annualized into APS | `fx_card` fees visibly fall in fresh flows |
| Renegotiated hike (`hausse`) | `(après−avant) × factor × 12` → `impact_annuel_eur` (L220) | ⚠️ **only if the debit visibly drops** | a renegotiation *down* is observable; a merely **avoided future hike** produces no drop → routed to the off-NSM **avoided-cost register** (§7.2), never into APS |
| Duplicate (`doublon`) | `unit × (cnt − 1)` (L313) | ⚠️ **one-shot, NOT ×12** | a same-day double charge has nothing recurring to "disappear"; proven via *refund landed / not repeated*, counted in a **separate one-shot proven-recovery total**, never in the annualized APS |
| Recoverable VAT (`tva_perdue`) | `base_ttc × 20/120` (L241) | ❌ **excluded from APS** | a tax-filing outcome, **invisible in Qonto flows**; `/verify` has no mechanism to observe it. Tracked off-ledger, accountant-confirmed (§7.3). Also: the flat 20/120 over-states real recoverable VAT (10 %/5.5 % rates, foreign suppliers, restaurant/fuel limits) — an estimate, not a banked euro. |

> **Why the eligibility filter matters.** An earlier draft summed *all five* levers into a "proven
> annual" number. That was wrong twice over: two levers (`tva_perdue`, avoided-cost `hausse`) can
> **never** be observed in Qonto flows, and `doublon` is a one-shot, not an annuity. APS now contains
> only what `/verify` can actually see drop.

**Source of truth.** `data/decisions.json`, field `economies_prouvees_eur_an`. It is moved into by
`/verify` (`verify.md` step 4), which (a) re-pulls 90 d of flows read-only into a fresh
`data/flows-<date>.json`, (b) re-runs `engine.py` to confirm the debit vanished/shrank, then (c)
shifts the amount from `economies_en_attente_eur_an` into `economies_prouvees_eur_an`.

> **Known integrity gap (backlog).** Today `verify.md` step 4 says *"déplace le montant"* — the
> **running total is maintained by the LLM**, no script recomputes `Σ montant_optimisable_eur` from
> `decisions[]`. That is in tension with rule #2 ("the engine computes every euro"). **Backlog item:
> a `sum_ledger.py` that recomputes both scalars deterministically from `decisions[]`, so the North
> Star aggregate is engine-computed, not model-summed.** Until then, per-lever euros are engine-true;
> the *sum* is not yet.

**Leading vs lagging.** APS is **lagging by construction**: a genuine proof needs ~30 real days of
post-action observation (`verify.md` — *honnêteté obligatoire*). Its **leading indicator** is the
scalar `economies_en_attente_eur_an` (approved-but-not-yet-proven). The team steers APS in-flight
through the input tree (§2), not by waiting on the lagging number.

**Why this metric, not the tempting alternatives.**

| Candidate | Why it fails the value-capture test |
|---|---|
| `# audits run` | Activity, not outcome. Grows while the customer saves €0 (and Argentier earns €0). |
| `Savings identified` (engine candidates) | A generous theoretical ceiling. Proves nothing left the account. |
| `economies_en_attente_eur_an` (approved) | Validated intent, but the money hasn't moved — the *leading* signal, not the star. |
| Loops / trust-loops count | Breaks `Revenue = APS × 5%` and invites magnitude-gaming (20 tiny proven duplicates outscore one €5,000/yr win). Good *engagement* signal → secondary. |
| **`economies_prouvees_eur_an`** | **Wins.** Its core (the monthly drop) survives contact with the real read-only account **and** it equals the revenue base — user value and business value collapse into one auditable euro. |

---

## 2. Input tree — the drivers the team moves

Each factor names where it is computed and, where relevant, what must be built. APS cannot exceed
what an earlier stage produced, so this is also the debugging order when APS stalls.

| # | Factor | Definition & source | Honest status |
|---|---|---|---|
| 1 | **Audits run (coverage)** | Completed `/audit` runs: OBSERVE (`list_transactions` 90 d → `data/flows-*.json`) through ANALYSE (`engine.py`). | **Single-tenant today** — no account_id in the data model, so "% of connected accounts" / "per-account" cuts are **(to instrument)**. Countable today as distinct dated `flows-*.json` snapshots. |
| 2 | **Qualified sourced levers per audit (engine yield)** | Per audit, count of `abonnement + doublon + fx` candidates with `montant_optimisable_eur > 0` **and** a passing source+date benchmark (rule #4). Source: `engine.py analyze()` lists. | Real today. **Anti-gaming:** yield must rise via *new detectors / better `clean_counterparty_name`*, **not** by loosening `cadence_of` windows, `min_occ`, or `similar()` tolerance — those thresholds are pinned by the 24 unit tests; changing them to inflate candidate counts should fail a test or a review. |
| 3 | **Human approval rate** (recommend → approuve) | Approved-and-sent ÷ recommended. Source: `decisions.json` entries with `statut = "approuve"`; refusals append to `profile.json → refus_passes`. | Real once `decisions[]` is populated. Gated by recommendation quality: a sourced+dated card with a *préavis*-calculated draft converts; a "non vérifié" claim does not. |
| 4 | **J+30 proof rate** (approuve → prouve) | Approved decisions `/verify` confirms at J+30 ÷ decisions past `preuve_attendue_le`. Source: `verify.md` steps 3–4. | **The only step that mints APS.** The truth filter: a renegotiation the supplier never honored, or a résiliation the user forgot to send, never converts. |
| 5 | **Durability × avg proven € per lever** | (a) Share of proven savings still absent on later `/verify` passes. (b) `economies_prouvees_eur_an ÷ # proven levers`. | (a) is **backlog** — `/verify` does not yet re-read `prouve` decisions (§6). Until built, the ×12 projection is unguarded against reversal. (b) is computable today; the engine sorts candidates by `montant_optimisable_eur` desc, so effort concentrates where a proven euro is largest. |

---

## 3. Secondary metrics

Adapted from the classic product-health set to Argentier's real artifacts. Each names a source.
Fields marked **(to instrument)** are honestly *not* readable today (`decisions[]` is empty); the two
aggregate scalars and all `engine.py` fields are.

| Metric | Definition | Design target | Source |
|---|---|---|---|
| **Pending pipeline** | `economies_en_attente_eur_an` — aggregate of approved-but-not-proven euros. Best leading indicator of next month's APS. | ≥ 1.5× current proven APS *(target to validate — no data yet)* | `decisions.json → economies_en_attente_eur_an` (real scalar) |
| **Activation rate** | Share of audits that reach the activation bar (§4). | ≥ 60% *(to validate)* | first `drafts/` file + first `decisions.json` entry with `statut = "approuve"` |
| **Actions approved & sent** | Count of `statut = "approuve"` decisions. GATE throughput. | trend up | `decisions.json statut` **(to instrument)** |
| **Acceptance rate** (trust proxy) | Approved ÷ recommended. Low = agent surfaces noise/untrusted numbers. | ≥ 60% *(to validate)* | `decisions.json` approuve vs proposed; refusals in `profile.json → refus_passes` |
| **Error / drop rate** (counter) | Share of shown items dropped to "non vérifié" (rule #4 retry-then-drop) + refusal rate. | "non vérifié" shown as a *price* = 0; refusals trending down | `audit.md` step d; `profile.json → refus_passes` |
| **Time-to-proof** | Median days from decision date to `statut = "prouve"`. Floor ~30 d is structural. | ≤ 45 days *(to validate)* | `decisions.json`: date → `/verify` pass **(to instrument)** |
| **Re-use frequency** | Audits per account per quarter — habit vs one-shot. | ≥ 1 audit / quarter *(to validate)* | distinct dated `data/flows-*.json`; **per-account cut is (to instrument)** — no account_id today |
| **Declared trust** | One-tap 1–5 at the GATE. No euros → does not touch rule #2. | median ≥ 4/5 *(to validate)* | `trust_declared` field **(to instrument — no such UI in the repo yet)** |
| **Sourced+dated rate** | Share of displayed prices carrying URL + date vs dropped to "non vérifié". | 100% of prices *shown* are sourced+dated | `audit.md` step d; Linkup results with `fromDate` |
| **PRO/PERSO resolution** (EI) | Share of 90 d debit € `engine.classify()` resolves to PRO/PERSO rather than A-CLARIFIER (doubt → A-CLARIFIER). Computable on the **first** audit, before any euro is proven — so the framework is not blind during the 30-day lag. | ≥ 85% auto-classified *(to validate)*; falling A-CLARIFIER **once** keyword extension is wired | `engine.py analyze() → categorie_ei`; **source note:** hardcoded `PRO_KEYWORDS`/`PERSO_KEYWORDS` **only** — `classify()` does **not** read `profile.json → regles_classification` today (backlog to wire it). |

### Future receivables module (roadmap — NOT computed today)

Argentier today is **cost-recovery**, not receivables collection. These belong to a **future
receivables module** and must **not** be claimed until the agent reads invoice/payment data:

| Metric | Would measure | Prerequisite (not connected today) |
|---|---|---|
| DSO / *délai moyen de paiement* | Days sales outstanding | reading `mcp__qonto__list_client_invoices` + payment dates |
| *Montant des impayés* | Overdue receivables balance | `list_client_invoices` status + credit notes |
| Acceptance / *taux d'acceptation* | Payment-link / invoice acceptance | `list_payment_links` outcomes |

They are deliberately **quarantined** from APS: adopting them now would claim value the product
cannot prove from its own data. They get their own instrumented sub-tree the day that data is read.

---

## 4. Activation & Aha

**Activation** — an audit is activated the first time a single `/audit` run satisfies **all**:
(a) it reads ≥ 90 days of the user's **real** Qonto transactions read-only; (b) `engine.py` surfaces
≥ 1 **APS-eligible** lever carrying a **sourced+dated** Linkup benchmark (rule #4 passed); and (c) the
human **approves ≥ 1 recommendation** through the GATE into `drafts/`, logged as the first
`decisions.json` entry with **`statut = "approuve"`** (matching `audit.md` step f — there is no
per-decision `en_attente` state) — with **0 Qonto write tools called and 0 PII sent to the web**.
Deliberately, *merely running `/audit`* — or generating recommendations nobody accepts — is **not**
activation; that is the agentic vanity trap. Activation requires the **first act of trust**: a
human-approved recommendation.

**Aha** — two moments, one hooks, one proves.

- **Hook (first `/audit`):** *"the statement lies"* dissolves — Argentier splits blended spend by
  nature, reveals the **true controllable run-rate**, and surfaces one lever the user didn't know
  about (a duplicate, a silent +X% hike, a phantom sub) with a dated alternative price and a draft
  letter already written — while being **provably unable to spend it** (read-only).
- **The aha (J+30 `/verify`):** the first euro moves into `economies_prouvees_eur_an` — the agent
  re-read **their own account** and proved the **monthly drop** landed, **without ever touching the
  money**. The aha unique to regulated finance: *"it saved me money, and it was never allowed to move
  my money."*

---

## 5. Guardrail / counter-metrics — graded by real enforcement

**Honesty first.** An earlier draft called every bound "architecture, not a dashboard alert." That
over-claimed. **Exactly one** guardrail is architecturally hard at two layers; the rest are
conventions or backlog. Grading them truthfully is what makes the North Star credible — and gives
engineering a concrete hardening list.

Grades: **HARD** = technically enforced (deny-list and/or the MCP server itself) · **SOFT** =
prompt/convention, LLM could deviate · **BACKLOG** = claimed but not yet implemented.

| Principle | Counter-metric | Bound | Enforced by | Grade |
|---|---|---|---|---|
| **Authorization before execution** | Qonto payment/transfer/card actions by Argentier | **= 0** | `settings.json` `deny` > `allow` hard-denies every write/transfer/card tool **and** the Qonto MCP server cannot move money (its own docs) | **HARD (two layers)** |
| **Least privilege** | Qonto write tools invoked | **= 0** | Explicit 8-read-tool allowlist; everything else denied | **HARD** |
| **Reversibility** | Irreversible banking side-effects | **= 0** | Output is a file in `drafts/`; read-only ⇒ no banking side-effect | **HARD** (follows from read-only) |
| **Explainability** | Displayed euro ≠ `engine.py` euro | **= 0** | Rule #2 + 24 `unittest` tests pin engine math | **SOFT + tests** — *backlog: assert card/letter € == engine output; recompute the APS sum with a script (today it is LLM-summed).* |
| **Traceability** | Approved decision without a ledger entry | **= 0** | `audit.md` step f writes each decision; `verify.md` acts only on those | **SOFT** (`decisions[]` empty today) |
| **Confidentiality (zero PII to web)** | PII fields sent to Linkup/Bright Data | **= 0** | `audit.md` step c tells the LLM to send merchant+category only | **SOFT** — *`settings.json` grants `linkup`/`brightdata` unrestricted args; backlog: a technical field filter, not just a prompt.* |
| **Recommendation vs decision** | Deliverables sent automatically by the agent | **= 0** | `drafts/` "PRÊT — À ENVOYER PAR TOI" label; Qonto banking sends sit behind the user's own SCA | **SOFT for non-Qonto** — *Gmail `create_draft`, Instantly, Apollo sequences are connected and **not** denied; backlog: add all send-capable MCP tools to `deny`.* |
| **Respect critical suppliers** | Résiliation recommended vs an `intouchable` supplier | **= 0** | `audit.md` step d crosses `profile.json → fournisseurs_intouchables` | **SOFT** — *`profile.json` is empty and `engine.py` never reads it; backlog: enforce in the engine, not the prompt.* |
| **Proof integrity (net-of-reversal)** | Proven euros later reversed and not removed | **= 0** | *claimed* self-correction on the next `/verify` | **BACKLOG** — *`verify.md` re-reads only `approuve` decisions; a `prouve` decision is never re-checked, so reversals do **not** net out today. This must be built for the "×12 is safe" claim to hold.* |
| **Wrong amount / unsourced price** | Price shown as fact without a dated source | **= 0** | Rule #4: 1 retry → "non vérifié", dropped | **SOFT** (prompt-enforced verification pass) |

**Hardening backlog (the three that most matter).**
1. **Deny send-capable non-Qonto MCPs** (`Gmail create_draft`, Instantly, Apollo) in `settings.json`
   so "autonomous sends = 0" is HARD, not convention.
2. **Filter PII at the tool boundary** for `linkup`/`brightdata` (whitelist merchant + category args)
   so "zero PII to web" is HARD.
3. **Implement net-of-reversal + a deterministic ledger-sum script** so the North Star aggregate is
   engine-computed and self-correcting, closing the two rule-#2 gaps.

---

## 6. Instrumentation status (honest accounting)

**Real today**

- `decisions.json → economies_prouvees_eur_an` and `economies_en_attente_eur_an` (aggregate scalars).
- All `engine.py analyze()` euro fields: `montant_optimisable_eur`, `montant_mensuel`,
  `niveau_confiance` (on `abonnements`/`doublons`/`fx` **only** — *not* `tva_perdue` or `hausse`,
  L220/241), `impact_annuel_eur`, `tva_recuperable_eur`, `categorie_ei`.
- PRO/PERSO/A-CLARIFIER classification — computable on the **first** audit (hardcoded keywords).
- The HARD guardrail counts (read-only Qonto, least-privilege) = 0 by construction.

**To instrument (v1 ledger schema — `decisions[]` is currently empty)**

- Per-decision `statut` (`approuve | refuse` → `prouve` — **no `en_attente`**; that is a scalar only).
- Per-decision `baseline` (pre-action run-rate) — required so `/verify` can diff at J+30 and net
  reversals. **Without it, both "proof-by-drop" and "net-of-reversal" are aspirational.**
- Per-decision `date` and `preuve_attendue_le` — for time-to-proof.
- `trust_declared` (1–5) — no such UI exists in the repo yet.
- **Account identifier** — the whole data model is single-tenant; any per-account / % -of-accounts
  metric needs it.

**Backlog code (not just schema)**

- `sum_ledger.py` — recompute both scalars deterministically from `decisions[]` (removes LLM summing).
- `/verify` re-read of `prouve` decisions — implement net-of-reversal.
- Wire `profile.json → regles_classification` and `fournisseurs_intouchables` into `engine.py`.
- Tool-boundary PII filter + deny-list for send-capable MCPs.

---

## 7. Risks this North Star under-weights (and the pairing that covers them)

1. **Value felt before J+30.** *"Statement-lies"* clarity and the PRO/PERSO split mint **zero APS**
   for 30+ days. → Paired with **PRO/PERSO resolution** (genuinely computable on the first audit) and
   **declared trust** (*to instrument*). Honest caveat: with declared-trust uninstrumented, PRO/PERSO
   is the **only** genuinely-readable pre-proof value signal today.
2. **Counterfactual / avoided-cost wins.** An avoided future hike (`detect_hausse` with no
   renegotiated drop) produces **no observable drop**, so it is **excluded from APS** and logged in a
   separate **avoided-cost register** — real value, but not a banked euro, and never smuggled into the
   revenue base.
3. **Off-ledger VAT.** `tva_perdue` depends on an accountant and is invisible in Qonto flows →
   **excluded from APS** (§1); tracked as an accountant-confirmed lead. Its flat 20/120 is also a
   deliberate over-estimate to flag, not a bankable figure.
4. **Easy-to-prove bias.** The 30-day lag + provability filter can bias the team toward clean
   résiliations over noisier renegotiations. → Watch **avg proven € per lever** and **share of
   engine-surfaced optimisable actually proven**, not just count.
5. **Lag & churn blindness.** APS reacts on a 30+ day cycle. → Paired with **re-use frequency** and
   **activation rate**.
6. **Adverse incentive + un-built reversal lock.** A pure savings maximand can push aggressive
   cancellations. The intended mitigation (net-of-reversal) is **backlog, not live** — so today the
   real mitigations are the human gate and (once wired) `fournisseurs_intouchables`. Named here so the
   metric's shadow side stays visible **and** un-implemented.
7. **Receivables blind spot.** DSO / *impayés* / acceptance are a **different product** → future
   receivables module (§3), never in this APS.

---

## 8. Why this framework reads as Senior AI PM work

- **Ambitious agentic vision, compressed into one shippable number.** "An autonomous-*grade* CFO"
  becomes a single euro a customer can verify — while the product stays honestly **read-only and
  never-sending**. (We keep the word "autonomous" for the *ambition*; the guardrail chapter shows the
  product is deliberately *not* autonomous with the user's money.)
- **Reliability graded, not asserted.** §5 grades every guardrail HARD / SOFT / BACKLOG and ships a
  three-item hardening list. Claiming "everything is architecture" would have been the junior move.
- **User value == business value, by construction.** `Revenue = 5% × APS` is an identity — no wedge
  between what we optimize and what the customer gets.
- **Honest instrumentation.** The framework names which fields exist, which are empty, which metrics
  are *to instrument*, and which guardrail claims are *not yet true* (§6) — and refuses to import AR
  metrics the product cannot compute (§3).
- **Fast + team-legible.** A five-factor input tree maps to engineering owners (coverage, engine
  yield, approval UX, verify loop, durability), and the backlog in §5–6 is a concrete next sprint.