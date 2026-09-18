# ⏳ qonto-prescription-guard — Every unpaid invoice has a legal death date

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> **100% read-only — zero writes.** The skill analyzes and alerts; it touches nothing.
> ⚖️ **Not legal advice**: prudent estimates, to be validated with a lawyer before acting — or giving up.

---

## 🎯 Why this matters (usefulness)

An unpaid invoice doesn't die when you forget it — it dies when the **limitation period** runs out: **5 years between businesses** (art. L110-4 French Commercial Code), **2 years against a consumer** (art. L218-2 French Consumer Code). After that, no court will help you. And the reverse trap is just as real: a **partial payment counts as an acknowledgment of the debt and resets the clock** — receivables you wrote off may still be alive. `qonto-prescription-guard` puts an expiry date on every receivable:

1. **Full scan** — every unpaid client invoice, across the entire history (old, messy invoices are exactly the point)
2. **B2B/B2C qualification** — SIREN or VAT number on the client record → likely a business (5 years); otherwise the skill **asks** — it never guesses, because the qualification changes everything
3. **Clock-resetting events** — a partial payment spotted in the transactions → "limitation period probably reset on [date] — confirm with a lawyer"; acknowledgments of debt or legal actions → declared by the user
4. **The "act before…" schedule** — a death date per receivable, time left, sorted by urgency × amount: 🔴 < 6 months · 🟠 < 12 months · 🟡 < 2 years · 🟢 beyond · ⚫ probably time-barred

Would someone run this on a Monday morning? Once a quarter, before writing anything off — and the first run on a real account with years of history is usually a revelation.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Limitation rules: France only.** Other Qonto countries (DE, ES, IT…): graceful degradation — an age-of-receivables report, no legal qualification, never an invented rule | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Client invoicing in Qonto | The skill reads `list_client_invoices` — invoices issued outside Qonto aren't visible | ✅ |
| Client records filled in | SIREN / VAT number on the record → automatic B2B qualification; otherwise the skill asks | ⭕ recommended |
| Nothing else | Zero writes, zero sub-accounts, zero consent to give: there is nothing to approve | — |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Receivables inventory**: `list_client_invoices` with unpaid status, paginated ≤ 50, over the entire history — outstanding amount, issue date, due date, client
2. **B2B/B2C qualification** per client record (heuristic, stated as such: SIREN/VAT → likely a business; ambiguous → the skill asks and computes **both dates** meanwhile, highlighting the shorter one)
3. **Rules embedded statically** (no external dependency): 5 years L110-4 / 2 years L218-2, prudent starting point = the issue date (art. 2224 Civil Code), interruption = acknowledgment of debt, partial payment, legal action (art. 2240–2244) — and crucially: **a dunning letter, even registered, interrupts NOTHING** (misconception #1)
4. **Interruptive acts**: partial payments detected in `list_transactions` (counterparty/reference/amount matching, announced as a heuristic) + user-declared acts (written acknowledgment, payment order)
5. **Death-date computation**: start + period, reset at the latest interruptive act — time left, 🔴🟠🟡🟢⚫ buckets
6. **Report & next move**: table sorted by urgency × amount, totals at risk within 6/12 months, handoff to `qonto-invoice-chaser` (friendly dunning) or to a bailiff when the deadline closes in

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The key point**: everything is a solid arrow — reads only. This skill creates nothing, modifies nothing, asks for no write consent — there is literally nothing to approve. The risk isn't in the tool, it's in the calendar: time is what acts here, not the skill.

## ⚖️ Embedded limitation rules (France)

| Situation | Period | Legal basis |
|---|---|---|
| Debt between businesses (or arising from the debtor's commercial activity) | **5 years** | art. L110-4 Commercial Code |
| Professional against a **consumer** (private individual, non-professional purpose) | **2 years** | art. L218-2 Consumer Code |
| Starting point | Day the creditor knew the facts — for an invoice, prudently the **issue date** (conservative: never overstate time left) | art. 2224 Civil Code |
| Interruption → **the clock fully restarts** | Acknowledgment of the debt (a **partial payment** counts as a tacit one), legal action, enforcement act | art. 2240–2244 Civil Code |
| ⚠️ NOT interruptive | Reminders, emails, even a registered dunning letter | settled case law |

Worth knowing: after an interruption, a **new period of the same duration** runs (art. 2231); limitation must be raised by the debtor — a judge won't apply it automatically (art. 2247) — but in practice, treat the date as the death of the claim.

## 🧪 Holds up on messy data

- No unpaid invoices? → the skill says so and stops cleanly — no invented urgency
- Client records without SIREN/VAT? → the skill asks B2B or B2C, computes both dates meanwhile, highlights the shorter
- Partial payment made outside Qonto, in cash, or on another bank? → invisible to the heuristic — the skill asks instead of assuming
- Invoice actually paid but still marked unpaid? → flagged with a suggestion to update it in the app, never silently dropped
- Non-French organization? → age-of-receivables report, clearly labeled, zero legal dates
- Counterparty spelling chaos (caps, accents, abbreviations) → normalized before matching payments to debtors

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: "act before…" schedule, totals at risk, detected resets | **Always** — the baseline |
| **Interactive timeline** | **HTML** file/artifact: one bar per receivable (start → death date), today marker, color by urgency, width by amount | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |
| **"Probably time-barred" list** | Separate report section, never mixed with living receivables | Every scan |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem (receivables dying silently) → the scan and the schedule → the highlight: **a detected partial payment resurrecting an invoice the user had written off** → the final report and the pipeline with `qonto-invoice-chaser`. It runs live on a real production account (all figures shown are the account's own).

## 🔗 Pipeline with other skills

`qonto-invoice-chaser` chases invoices amicably; `qonto-prescription-guard` tells you **until when** amicable chasing still makes sense — and when to go legal. Together: **chase → sue → never let a receivable die**. Structural reminder: chaser reminders do **not** interrupt the limitation period — one more reason to watch both.

## 💡 Roadmap ideas

- Calendar reminders on "act before…" dates (calendar MCP detected dynamically — optional multi-MCP, the core stays pure Qonto)
- Country modules (DE: 3 years §195 BGB, ES, IT…) — same engine, per-country period tables
- Suspension tracking (mediation, art. 2238 Civil Code) — declarative, refines the dates
- Draft handoff letter for the bailiff — text output, still zero MCP writes

## 🛡 Guardrails

- **Not legal advice** — every report says so: prudent dates, validate with a lawyer or bailiff before acting or writing off
- **Never certain on B2C**: the 2-year qualification is always an assumption to confirm (a sole trader buying for business → back to 5 years)
- Interruption detection is **announced as a heuristic**: "partial payment detected on [date] → period probably reset — confirm with a lawyer"
- A "probably time-barred" receivable is never declared definitively dead — nor definitively alive
- France only for legal dates; elsewhere → plain aging report, clearly labeled
- 100% read-only · masked IBANs (last 4 digits) · pagination ≤ 50 everywhere
- All examples in this documentation are **invented** (INV-YYYY-NNN numbers, fictional amounts)

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML, FR/EN).*
