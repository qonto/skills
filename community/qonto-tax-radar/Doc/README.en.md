# 🛰️ qonto-tax-radar — The tax pre-audit that works FOR you

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> **100 % read-only — zero writes, zero risk.** The only tax inspector that sits on your side of the desk.

---

## 🎯 Why this matters (usefulness)

The number-one fear of French company directors is the tax audit — and nobody knows where they're vulnerable until the letter arrives. `qonto-tax-radar` flips the roles: it screens Qonto transactions against the **8 verification axes real DGFIP auditors use** during a vérification de comptabilité, and hands you the report BEFORE the tax office writes it.

1. **The 8-axis screen** — lavish expenses, personal spending booked as business, director's current account, VAT deducted vs receipts actually on file, benefits in kind, duplicate charges, cash, recurring round amounts
2. **Every finding is sourced** — a precise transaction + the tax rule cited (article/principle) + a risk level + a corrective action. "Points of attention", never accusations
3. **Priced exposure** — reclaimable VAT, corporate-tax reintegrations, interest and penalties, as educational orders of magnitude
4. **A remediation plan** — the ranked list of fixes to make this month so the file is clean — then re-run the skill and watch the grade improve

Would someone run this on a Monday morning? It's the quarterly "sleep well" ritual — and the week before the accountant's annual review, it's priceless.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **8 axes and cited rules: France** (CGI, Code de commerce, CMF). Other Qonto countries (DE, ES, IT…): graceful degradation — universal axes only (receipts, duplicates, cash, round amounts), French articles never cited outside their scope | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| ≥ 12 months of history | Below that, the skill analyzes what exists and says so honestly (partial coverage announced) | ⭕ |
| Receipts attached in Qonto | Not required — if there are none at all, axis 4 becomes the headline finding, not an error | ⭕ |
| Sub-account, write access, consent | **None**: fully read-only, there is literally nothing to authorize | — |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Map the organization**: `get_organization` first — country, legal form, accounts. France → all 8 axes; other country → universal axes, stated plainly
2. **Collect the history**: 12 months of transactions paginated ≤ 50 in quarterly windows (24 on request), cross-checked with supplier invoices, labels and attached receipts. The transaction fields `attachment_ids`, `vat_amount`, `attachment_required` do most of the work; `list_transaction_attachments` only verifies the transactions about to be flagged. Card patterns read on `emitted_at` — `settled_at` lags 1–2 days, so a Sunday purchase can show up on Tuesday
3. **Screen the 8 axes** (reference table below) — the checklist real auditors follow
4. **Price the exposure**: reclaimable VAT + corporate-tax reintegration (25 %, or 15 % on the reduced-rate share) + late interest 0.20 %/month + 10 % baseline penalty — educational orders of magnitude, never presented as an official computation
5. **Risk report**: 🟢🟡🔴 per axis, global grade = worst axis (an audit follows the weakest point), every finding = transaction + rule cited + fix
6. **Remediation plan**: receipts to recover, expenses to reimburse or reclassify, documents to produce — validated with the accountant, then re-run and compare

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The security story is the whole story**: there are **only solid arrows** (reads). This skill never asks for write consent because it never writes. No write tool is ever called — it cannot modify a transaction, set a label, or move a cent. It's the auditor sitting on **your side of the desk**.

## 📊 The 8 verification axes (reference grid)

| # | Axis | What the skill detects | Rule cited |
|---|---|---|---|
| 1 | **Lavish expenses** | High-end restaurants (amount per sitting), travel, gifts above thresholds (VAT on gifts recoverable ≤ €73 incl. tax /yr/beneficiary; statement 2067 if gifts > €3,000/yr or receptions > €6,100/yr) | art. 39-4 CGI; art. 28-00 A ann. IV CGI |
| 2 | **Personal spending as business** | Weekend/Sunday purchases, merchants inconsistent with the business purpose (gaming, clothing, leisure), consumer subscriptions | art. 39-1 CGI; abnormal management act |
| 3 | **Director's current account** | Transfers to personal-looking beneficiaries, back-and-forth flows with the director, debit-balance patterns | art. L223-21 C. com.; art. 111-a CGI |
| 4 | **VAT deducted vs receipts** | `vat_amount` > 0 **and** no attachment on file → VAT deducted with no invoice to show | art. 271 II CGI — no invoice, no deduction |
| 5 | **Benefits in kind** | Vehicle, phone, housing, mixed-use subscriptions paid by the company with no sign of declaration | art. 82 CGI; BOSS |
| 6 | **Duplicate charges** | `has_duplicates` on supplier invoices; same counterparty + same amount within ±72 h | art. 54 CGI; art. 1729 (context only) |
| 7 | **Cash** | Recurring round withdrawals; professional cash payments > €1,000 | art. L112-6 + D112-3 CMF (€1,000 cap) |
| 8 | **Recurring round amounts** | Regular round transfers to one beneficiary with no matching invoice | art. 54 CGI — burden of proof |

## 🧪 Holds up on messy data

- No labels, no categories? → the skill screens raw counterparties and merchant names; a user's own "perso" label, when present, is surfaced gently
- No attachments anywhere? → axis 4 becomes the top finding with the full VAT amount at stake — that IS the Monday-morning value, not a failure mode
- Empty or young account? → partial coverage announced, no invented findings
- Non-French company? → universal axes only, and the skill says which axes it skipped and why
- `403 missing oauth scope` on `list_cash_flow_categories`? → expected on the claude.ai connector; labels are the fallback
- False positives are owned up front: a flagged restaurant can be 100 % legitimate — the report says so in as many words

## 📤 Output formats (where does the report land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Global risk banner + 8-axis table + findings detail + remediation plan, in markdown | **Always** — the baseline |
| **Interactive "pre-audit notice"** | **HTML** file/artifact: global grade, per-axis gauges, findings table, remediation checklist | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to markdown otherwise |
| **Comparative re-run** | Same report after the fixes — the grade improves, that's the retention loop | Every re-run |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the fear → launching the pre-audit → findings axis by axis → **the report dropping** ("2 red flags: €1,430 of VAT deducted with no receipt, and 3 expenses to reclassify — fix that this month and your file is clean") → guardrails and wrap-up. It runs live on a real production account.

## 💡 Roadmap ideas

- Assisted remediation mode: `request_attachment_upload` for each missing receipt + "to document" labels, behind explicit consent — the writes exist in the MCP; v1 is deliberately read-only, that's the positioning
- Country-specific audit grids (DE · ES · IT…) — Qonto is pan-European; v1 = France + universal axes
- Optional multi-MCP enrichment: cross-check axis 4 against invoices found in Gmail/Drive when those MCPs are present — detected dynamically, otherwise the skill says so and continues
- Grade tracking over time (re-run history) — the retention loop, quantified
- Revenue-coherence axis (paid invoices vs actual inflows)

## 🛡 Guardrails

- **Fully read-only**: no write tool is ever called — a commitment, not a setting
- **Never an accusation**: "point of attention", not "fraud"; a flagged expense may be perfectly legitimate — the skill may under- or over-estimate for lack of context, and says so
- **Not tax advice**, not the administration's position: educational simulation, accountant validation recalled in every report
- Non-French org → universal axes only, French articles never cited outside their scope
- IBANs masked (last 4 digits), sensitive names masked in any export · pagination ≤ 50 everywhere

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
