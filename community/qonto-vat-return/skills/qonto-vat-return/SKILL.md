---
name: qonto-vat-return
description: >-
  French VAT return (CA3, form 3310-CA3) preparer for Qonto accounts. Builds the declaration box by box from real account data — collected VAT per rate (20/10/5.5/2.1%), deductible VAT (goods & services, fixed assets), net VAT payable or credit to carry forward — as a "form box → amount → justification" table ready to copy into impots.gouv.fr, with consistency checks against past months and past DGFIP payments. Read-only, zero writes. Use for "prépare ma CA3", "prepare my VAT return for June", "combien de TVA je dois déclarer ce mois-ci ?", "fill in my 3310-CA3", "TVA collectée vs déductible", "check my VAT before I file".
permissions:
  mcp:
    qonto: [get_organization, get_statement, list_cash_flow_categories, list_client_invoices, list_statements, list_supplier_invoices, list_transaction_attachments, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto VAT Return

Turn a month of Qonto data into a CA3 you can copy box by box into impots.gouv.fr. **This is a preparation aid, not a filing**: the skill reads, computes and cross-checks; it never files anything, and every output recommends accountant validation. Zero write tools.

## Prerequisites
1. `get_organization` **always first** → accounts (`list_transactions` requires `bank_account_id`/`iban`), legal identity, country.
2. **Country-aware**: the CA3 is a **French** form. For other Qonto countries (DE, ES, IT, AT, NL, BE, PT…), say so plainly and degrade to a generic collected-vs-deductible VAT summary — never map foreign VAT to French form boxes.
3. Works with any history; below 6 months, or with untagged VAT data, the skill degrades honestly (floors, warnings) instead of pretending.

## Workflow

### 1. Scope: regime, chargeability, filing period — detect, don't ask
- **Filing frequency** from DGFIP history: `list_transactions` (paginate `per_page: "50"`), and **narrow to outgoing direct debits first** — French taxes are collected by SEPA direct debit (`operation_type: direct_debit` filter if exposed, else filter on the transaction's `operation_type` field). Match the tax office under all its spellings (`DGFIP`, `DIRECTION GENERALE DES FINANCES PUBLIQUES`, `Direction Générale des Finances Publiques` — normalize case/accents, merge as one counterparty) + VAT-labelled counterparties. Monthly debits → monthly CA3 (réel normal); quarterly debits → quarterly CA3 (allowed when annual VAT < €4,000).
- **Réel simplifié (CA12 + July/December instalments) is OUT OF SCOPE of the CA3**: if detected, say it, prepare nothing box-mapped, and warn that **the simplified regime is abolished on 2027-01-01** (art. 38, 2025 Finance Act) — the user will move to monthly or quarterly CA3 and this skill will then apply.
- **Chargeability (fait générateur) — the make-or-break setting**: read `vat_payment_condition` on client invoices (`list_client_invoices`). `on_receipts` → collected VAT follows **payments received** during the period (services default). Otherwise → VAT on debits, collected VAT follows **invoices issued**. Mixed portfolios: handle per invoice.

### 2. Collected VAT, per rate
- **On debits**: invoices issued in the period → group VAT by rate (20 / 10 / 5.5 / 2.1 %), base and tax per rate. Deduct credit notes issued in the period.
- **On receipts**: match the period's **incoming transactions** to client invoices (amount + counterparty + reference; `paid_at` status helps) and take the matched invoices' VAT breakdown. Incoming credits with no matching invoice → listed separately as "unassigned receipts", never silently taxed or ignored.
- → Boxes **01** (base of taxed operations), **08 / 09 / 9B / 11** (base + tax per rate), line **16** (total gross VAT).

### 3. Deductible VAT — announced as a floor
- Sum `vat_amount` on the period's **debits** (`list_transactions`), plus `total_tax_amount` on the period's supplier invoices (`list_supplier_invoices`) — **dedupe** invoices already matched to a transaction.
- Report the **count of debits with no VAT info**: the deductible total is a **floor**, said explicitly. Never estimate a VAT rate on an untagged expense.
- **Fixed assets** (box 19): only when detectable (label/category, supplier-invoice description, unusually large equipment purchase) — otherwise everything goes to box **20** (other goods & services) and the skill says why.
- **Prior credit** (box 22): taken from the previous declaration if the user provides it, or inferred 🟡 from history when a past CA3 shows a credit; flagged as "confirm from your last filed CA3".
- **Reverse charge (autoliquidation)** — EU acquisitions, imports, foreign suppliers detected in counterparties: the skill **flags** the candidate transactions and the boxes involved (03, 17, A4/I-lines, 24) as **"to verify with your accountant"** — it never computes reverse-charge VAT silently.

### 4. Net position
- Line **23** = total deductible (19 + 20 + 21 + 22).
- If 16 > 23 → line **28** net VAT due (and **32** total payable). If 23 > 16 → line **25** VAT credit → **27** credit to carry forward (or **26** refund request — mentioned, user's choice with their accountant).
- Compute in cents, then show the **whole-euro rounding the form expects**, both visible.

### 5. Consistency checks — before the user copies anything
| Check | Against | Output |
|---|---|---|
| Net VAT vs history | Median of past DGFIP VAT payments | ⚠️ if deviation > 30 % (explained: seasonality? big invoice? missing data?) |
| Collected vs previous periods | Same-period bases and rates, prior months | ⚠️ on rate mix changes or base jumps |
| Transactions vs statement | `list_statements` / `get_statement` period totals | ⚠️ if the analysed transactions don't cover the full statement period |
| Receipts matching (on_receipts) | Unassigned incoming credits | Listed with amounts — user decides with accountant |
| Untagged debits | Count + total amount | Deductible floor disclaimer |

### 6. Report — output formats
**Always** reply in the conversation with:
1. **The CA3 table**: form box → official label → amount (cents + rounded euro) → justification (which invoices/transactions, which rule). Ready to copy into impots.gouv.fr.
2. **Consistency checks table** with ✅/⚠️ per check.
3. Narrative caveats: chargeability used, floors, reverse-charge flags, filing deadline reminder (between the 15th and 24th of the following month, per the company's DGFIP schedule).

**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): an **HTML dashboard** — the CA3 as a form-like view, collected/deductible split per rate, history sparkline vs past DGFIP payments. If the host cannot render files, say nothing about it: the markdown tables are the deliverable.

## Guardrails
- **This prepares, it does not declare.** The skill never files, never transmits anything to the DGFIP, and has **no write tool at all**. The user (or their accountant) copies the values into impots.gouv.fr themselves.
- Every report states: **estimates from bank data ≠ accounting records — have your accountant validate before filing**, especially reverse-charge, fixed assets and prior credit.
- Never invent: no French boxes for non-French organizations, no VAT rate guessed on untagged expenses, no reverse-charge amounts computed silently.
- Degrade honestly on messy data: floors announced with counts, unassigned receipts listed, short history flagged.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50).
