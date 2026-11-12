# 🧾 qonto-monthly-close — The month-end CFO in 3 minutes

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> **100 % read-only** — one prompt reviews the whole month; the report proposes, you act.

---

## 🎯 Why this matters (usefulness)

Every month-end, small-business owners burn 2–4 hours compiling statements, receipts, VAT and unpaid invoices for their accountant. One prompt — "**close my month**" — triggers the full review of the past month:

1. **Missing receipts, prioritized by stakes** — a €3 coffee and a €1,200 laptop are not the same to-do line: ranked by amount and recoverable VAT at risk, with a month completeness score
2. **The month's VAT** — collected (computed **on receipts** when cash-basis VAT is detected) − deductible (announced as a floor when debits are untagged) = net to provision
3. **Anomalies** — unusual spend at a known counterparty, **duplicate direct debit**, never-seen-before beneficiary — flagged with evidence, never accused
4. **The rest of the review** — unlabeled transactions (category proposed), unpaid client invoices (days overdue + payer history), month-over-month comparison (top category rises and falls)

→ An actionable **closing report** with a fix-it to-do sorted by priority (P1 money at risk → P2 compliance → P3 hygiene).

Would someone use this on a Monday morning? It's literally the first Monday of the month, every month.

## 🧭 Where it sits in the family

`qonto-monthly-close` is the **monthly orchestrator**: it detects and prioritizes, read-only. Each finding then has its specialist:

| It detects… | The specialist that acts |
|---|---|
| Missing receipts | `qonto-receipt-hunter` (chase + upload) |
| Unpaid client invoices | `qonto-invoice-chaser` (dunning drafts) |
| VAT to provision | `qonto-tax-pilot` (tax schedule + SCA-gated provisioning) |

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | Receipts, anomalies, unpaid invoices, comparisons: **every Qonto country**. VAT module: French logic; other countries (DE, ES, IT…) → generic collected−deductible estimate, stated as such | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| ≥ 3 months of history | The anomaly detectors and the month-over-month comparison need a baseline; below that, the skill degrades honestly | ⭕ |
| Gmail MCP | Optional, detected dynamically: hunts the inbox for missing receipts; otherwise the skill says so and continues | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Scope the month**: `get_organization` first (accounts, country, legal form), month to close (default: last full calendar month), paginated reads ≤ 50 for the month **+ 3–6 months of history** for baselines. Card operations reasoned on `emitted_at` (1–2 day lag vs `settled_at`)
2. **Missing receipts**: `attachment_required` with empty `attachment_ids`, prioritized by amount and recoverable VAT, completeness score. Gmail connected → offers to hunt the inbox for the receipts
3. **The month's VAT**: collected from client invoices (**on cash receipts** when `vat_payment_condition: "on_receipts"`) − deductible (summed `vat_amount`, floor disclosed); the cost of missing receipts is quantified (no invoice = VAT not deductible)
4. **Anomalies**: three detectors against history — unusual spend, duplicate direct debit (same payee, same amount, same month), new beneficiary. Every flag ships with its evidence and a severity
5. **Unlabeled & unpaid**: category proposed from the `list_labels` taxonomy (cash-flow categories return 403 on the claude.ai connector — fallback built in); unpaid client invoices with days overdue and payer history
6. **Closing report**: scorecard + previous-month comparison + **prioritized to-do**, each line pointing to the dedicated skill or the one-tap action in the app

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The key design choice**: every arrow is solid — **fully read-only**. This skill calls no write tool: nothing is created, modified, sent or moved. It's the one skill in the family you can run on any account, any time, with zero side effects — including a judge's account.

## 🧪 Holds up on messy data

- Empty month? → scorecard says so, no invented findings
- Untagged VAT on debits? → deductible announced as a floor, count of unknowns disclosed
- No labels taxonomy? → categorization proposed from counterparty patterns, stated as suggestions
- Short history? → anomaly detectors state their baseline is thin instead of over-flagging
- Non-French org? → the universal modules run in full; the VAT module degrades to a generic estimate and says so
- `list_cash_flow_categories` 403 on the claude.ai connector → labels fallback, handled silently

## 📤 Output formats (where does the report land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: scorecard, receipts, VAT, anomalies, comparison, unpaid, to-do | **Always** — the baseline |
| **Closing dashboard** | **HTML** file/artifact: month scorecard, completeness gauge, VAT tile, anomaly cards, to-do checklist | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the month-end chore → one prompt → the live review → **the full report landing in one pass** ("96 transactions reviewed, 3 missing receipts, 1 duplicate caught, this month's VAT: €717 — here's your 10-minute to-do") → the dashboard. It runs live on a real production account.

## 💡 Roadmap ideas

- Accountant-ready export (structured PDF) — the content exists, only the firm-friendly layout is missing
- Closing memory: compare scorecards month after month — completeness going up means the books are getting healthy
- Zombie-subscription detector (recurring direct debit, never labeled, never justified) — reuses the anomaly baselines
- Multi-MCP: receipts from Google Drive in addition to Gmail — same dynamic-detection pattern

## 🛡 Guardrails

- **Fully read-only**: no write tool is ever called — the report proposes, the user disposes
- Anomalies are **flags with evidence, not accusations**: the baseline that triggered each flag is always shown
- VAT figures are estimates, not filings — accountant validation recommended in every report
- Honest degradation: empty month, no invoices, non-French org → the skill says what it could and couldn't compute
- IBANs masked (last 4 digits) · pagination ≤ 50 everywhere

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
