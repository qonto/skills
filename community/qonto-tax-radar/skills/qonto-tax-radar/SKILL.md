---
name: qonto-tax-radar
description: French tax pre-audit ("pré-contrôle fiscal") for Qonto accounts, 100% read-only. Screens transactions against the 8 verification axes real DGFIP auditors use — lavish expenses, personal spending booked as business, director's current account, VAT deducted vs receipts on file, benefits in kind, duplicate charges, cash, recurring round amounts — and returns a risk report (🟢🟡🔴 per axis, amounts at stake, cited tax rules, fixes to make first). Use for "lance mon pré-contrôle fiscal", "am I ready for a tax audit?", "quels risques fiscaux dans mes comptes ?", "audit my expenses like a tax inspector would", "what would the tax office flag?".
permissions:
  mcp:
    qonto: [get_organization, list_cash_flow_categories, list_labels, list_supplier_invoices, list_transaction_attachments, list_transactions, request_attachment_upload]
  network: []
  env: []
  tools: [Read]
---

# Qonto Tax Radar

The only tax inspector that works FOR you. Replays a French tax audit (vérification de comptabilité) on real Qonto data, **entirely read-only** — zero writes, zero risk — and tells the user what to fix while there is still time.

> Positioning to state in every report: this is an **educational simulation** based on public audit practices. It is neither tax advice nor a position of the French administration. A "restaurant" line can be 100 % legitimate — the skill flags **points of attention**, never accusations, and may under- or over-estimate for lack of context. Accountant validation required before acting.

## Prerequisites
1. `get_organization` first → country, `legal_form`, accounts (`list_transactions` requires `bank_account_id`/`iban`).
2. **Country-aware**: the 8 axes and cited rules are **French** (CGI, Code de commerce, CMF). For other Qonto countries (DE, ES, IT, AT, NL, BE, PT…), say so plainly and degrade to the universal axes only — receipts present, duplicates, cash, round amounts — never citing French articles as if they applied.
3. Works on any account, even messy: no labels → analyze raw counterparties; no attachments anywhere → axis 4 becomes the headline finding, not an error.

## Workflow

### 1. Collect (read-only, paginated)
- `list_transactions` per account, `per_page: "50"`, quarterly `settled_at_from/to` windows, **12 months** (extend to 24 on request). Use `emitted_at` for card spending patterns (weekends, merchants) — `settled_at` lags 1–2 days.
- The transaction objects already carry `attachment_ids`, `attachment_required`, `vat_amount`, `label`, `category`: screen from these fields; call `list_transaction_attachments` only to verify the specific transactions you are about to flag.
- `list_supplier_invoices` (duplicate detection, `total_tax_amount` cross-check) · `list_labels` (user's own classification — a "perso" label is a self-confession worth surfacing gently). If `list_cash_flow_categories` returns `403 missing oauth scope` on the claude.ai connector, that is expected: labels are the fallback.

### 2. Screen the 8 audit axes (the real DGFIP checklist)
| # | Axis | Detection in Qonto data | Rule cited in each finding |
|---|---|---|---|
| 1 | **Lavish expenses** | High-end restaurants (high amount per sitting), travel, gifts above thresholds (VAT on gifts recoverable only ≤ €73 incl. tax /year/beneficiary; general-expenses statement 2067 if gifts > €3,000/yr or receptions > €6,100/yr) | art. 39-4 CGI; art. 28-00 A ann. IV CGI |
| 2 | **Personal spending booked as business** | Weekend/Sunday purchases, merchants inconsistent with the business purpose (gaming, clothing, leisure), consumer subscriptions | art. 39-1 CGI (expense in the company's interest); acte anormal de gestion |
| 3 | **Director's current account** | Transfers to personal-looking beneficiaries, back-and-forth flows with the director, debit-balance patterns | art. L223-21 C. com. (debit CCA forbidden for individual directors); art. 111-a CGI (deemed distributed income) |
| 4 | **VAT deducted vs receipts on file** | `vat_amount` > 0 **and** no attachment (`attachment_ids` empty, `attachment_required` true) → VAT deducted with no invoice to show | art. 271 II CGI — no invoice, no deduction |
| 5 | **Benefits in kind** | Vehicle, phone, housing, mixed-use subscriptions paid by the company with no sign of declaration | art. 82 CGI; BOSS avantages en nature |
| 6 | **Duplicate charges** | `has_duplicates` on supplier invoices; same counterparty + same amount within ±72 h | art. 54 CGI (probative accounting); art. 1729 (40 % if deliberate — context only) |
| 7 | **Cash** | Recurring round cash withdrawals; professional cash payments > €1,000 | art. L112-6 + D112-3 CMF (€1,000 cap) |
| 8 | **Recurring round amounts** | Regular round transfers to one beneficiary with no matching invoice | art. 54 CGI — burden of proof on charges |

Every finding = **precise transaction (date, counterparty, amount) + rule cited + risk level + corrective action**. Vocabulary: "point d'attention", "à documenter", "à requalifier" — never "fraude", never an assertion of guilt.

### 3. Price the exposure (educational orders of magnitude, current rules)
- VAT recallable = Σ `vat_amount` of receiptless deductions (axis 4) + VAT on non-deductible items.
- IS reintegration = 25 % (15 % on the reduced-rate share) of charges to reintegrate (axes 1, 2, 6).
- Late-payment interest 0.20 %/month + 10 % baseline penalty (mention 40 % bad-faith only as context).
- State the confidence honestly: amounts are ceilings/floors, not an assessment.

### 4. Score
Per axis: 🟢 clean · 🟡 to document · 🔴 exposed — driven by count AND amounts. **Global grade = worst axis** (a real audit follows the weakest point).

### 5. Report — output formats
**Always** reply in the conversation with markdown:
1. **Risk banner** (global grade + one-line summary: "2 red flags: €X of VAT deducted without receipts, N expenses to reclassify").
2. **8-axis table** (axis · findings count · amount at stake · level 🟢🟡🔴).
3. **Top findings detail** (date · counterparty · amount · rule cited · fix), IBANs masked.
4. **Remediation plan**, ranked: receipts to recover (per transaction), expenses to reimburse/reclassify, documents to produce (mileage log, AG minutes) — each item is an action the user takes in the Qonto app or with their accountant; the skill itself changes nothing.
5. Disclaimer footer (educational simulation · accountant validation · possible under/over-estimation).

**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): an **HTML "pre-audit notice"** — grade banner, 8 axis gauges, findings table, remediation checklist. If the host cannot render files, say nothing about it: the markdown report is the deliverable.

### 6. The retention loop
Close with: "fix these, re-run me, watch the grade improve." The re-run on cleaned data is the payoff.

## Guardrails
- **Strictly read-only**: no write tool is ever called. The skill cannot modify, tag, upload, or move anything — say it up front, it is the point.
- Never state that fraud or an offence exists; a flagged expense may be perfectly legitimate — the skill lacks context by design.
- Not tax advice, not the administration's position; recommend accountant validation in every report.
- Non-French org → universal axes only, French articles never cited as applicable.
- Mask IBANs (last 4 digits) and personal names in any exported report. Paginate everything (`per_page` ≤ 50).
