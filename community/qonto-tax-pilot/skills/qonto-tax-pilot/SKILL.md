---
name: qonto-tax-pilot
description: French tax radar and cash pilot for Qonto accounts. Builds a dated, amount-estimated tax schedule (VAT, corporate tax instalments, CFE, dividend flat tax), projects the next 90 days of cash, computes the month's tax provision, and — with explicit user consent — creates a transfer request to a dedicated tax sub-account that the user approves with 2FA in the Qonto app. Use for "où en sera ma tréso fin septembre ?", "quand tombe ma TVA et combien ?", "provisionne mes impôts", "can I afford this purchase?", "what if my client pays late?".
permissions:
  mcp:
    qonto: [create_multi_transfer_request, decline_request, get_organization, list_client_invoices, list_supplier_invoices, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto Tax Pilot

Predict the taxman, then get his money out of harm's way. Read-heavy, one safe write: the skill computes and prepares; only the user's SCA approval in the Qonto app moves money.

## Prerequisites
1. `get_organization` → accounts, balances, fiscal identity (legal_form, country). Identify the **tax sub-account** (name contains "taxe"/"tax"/"impôt"/"TVA"). If none: show computations only and explain how to create one in the app (manual, one-time).
2. **Country-aware**: full tax calendar for **France**. For other Qonto countries (DE, ES, IT, AT, NL, BE, PT…), say so plainly and degrade to what stays valid everywhere: cash projection, recurring-flow detection, generic VAT provisioning from history — never invent foreign tax deadlines.
3. Assumes a company at IS (French corporate tax) for the calendar; adapt wording otherwise.

## Workflow

### 1. Learn the past (24–36 months)
`list_transactions` per account, paginate `per_page: "50"` in 3-month windows. Cover **at least the two previous fiscal years** when history allows: tax cadences (quarterly IS instalments, December CFE, VAT rhythm) only become visible across full years, and year-over-year comparison feeds the projection.
- **Recurring flows**: normalized counterparty, stable amount (±10 %), monthly/quarterly/yearly cadence, ≥3 hits (2 for yearly).
- **Tax history — search outgoing direct debits first**: French taxes (VAT, IS instalments, CFE) are collected by **SEPA direct debit**, so narrow the scan to outgoing direct debits before name-matching (`operation_type: direct_debit` filter if the connector exposes it, otherwise filter on each transaction's `operation_type` field) — far less noise than scanning every debit. Then match the counterparty under **all its spellings**: the same tax office shows up as `DGFIP`, `DIRECTION GENERALE DES FINANCES PUBLIQUES` (caps) and `Direction Générale des Finances Publiques` (mixed case) — normalize case/accents and merge them as ONE counterparty. Add tax-labelled transactions → amounts and cadence per tax, per year.
- **VAT regime AND filing frequency — detect, don't ask**: monthly DGFIP debits → monthly CA3 (réel normal); quarterly debits → quarterly CA3 (allowed when annual VAT < €4,000); July + December instalments → réel simplifié (CA12). ⚠️ **The simplified regime (CA12 + instalments) is abolished on 2027-01-01** (art. 38, 2025 Finance Act): from 2027, quarterly CA3 (turnover ≤ €1M) or monthly CA3 — warn users still on CA12 about the switch. Also read `vat_payment_condition` on client invoices: `on_receipts` means **VAT follows client payments, not issued invoices** — use cash receipts for collected VAT.

### 2. Tax reference calendar (company at IS, adapt to fiscal-year end)
| Deadline | Tax | Amount estimation |
|---|---|---|
| Monthly or quarterly ~15th–24th (réel normal; quarterly if annual VAT < €4,000) | VAT CA3 | Median of recent VAT payments; refine with collected−deductible |
| July 55 % + December 40 %; CA12 early May (réel simplifié — **abolished 2027-01-01**, plan the switch to CA3) | VAT instalments | Last CA12 / historical July+December payments |
| 15/03 · 15/06 · 15/09 · 15/12 | IS instalments (2571) | Past instalments, else IS N-1 ÷ 4; **no instalments if IS N-1 < 3 000 €** |
| 15/05 for 31/12 close | IS balance (2572) | Estimated IS N-1 − instalments |
| 15/06 (if ≥ 3 000 €) + 15/12 | CFE | Last year's payment |
| 15th of month after distribution | Dividends — **ASK who the shareholder is first** | Individual shareholder → PFU 30 % (form 2777), provision it. **Holding company under the parent-subsidiary regime** (art. 145/216 CGI, ≥ 5 % held) → **no PFU at all**, 95 % exempt — only a 5 % add-back taxed at the HOLDING's level, ~nothing to provision here. Never assume: ask (hint: past dividend transfers to a corporate counterparty suggest a holding). Only if a distribution is planned |

Every line carries a confidence tag: 🟢 seen in history / 🟡 estimated / 🔵 conditional.

### 3. Project 90 days
Day-by-day per account: balance + recurring flows on typical dates + dated items (`list_client_invoices` unpaid at due_date adjusted by client's historical delay; `list_supplier_invoices` scheduled) + tax schedule + irregular baseline. Output low point (date + amount), threshold crossings (default 0 / 2 000 €), end balance. What-if on request (client delay +N days, one-off purchase, new recurring cost).

### 4. Compute the month's provision
- **Collected VAT**: on cash **receipts** of the month if `on_receipts` (match incoming payments to invoices; use their `vat_amount`), else on invoices issued.
- **Deductible VAT**: sum `vat_amount` on the month's debits (say how many were null → estimate is a floor) or supplier invoice `total_tax_amount`.
- **Net VAT** = collected − deductible, floor 0. Plus **IS/12** and **CFE/12** from history.
- Show breakdown table with confidence tags.

### 5. Act — only with explicit consent
Compare vault balance vs cumulated target. If shortfall and **the user explicitly confirms**, `create_multi_transfer_request`: `debit_iban` = main account; transfer needs `credit_iban`, `credit_account_name`, **`credit_account_currency`** (422 if omitted), `amount`, `currency`, `reference` ("PROVISION IMPOTS YYYY-MM"). Put the full calculation in the request `note` — the approver sees it at approval time (transaction notes can't be set via MCP).
Then tell the user: **a push notification and the Requests section of the Qonto app now hold the pending request; nothing moves until they approve with their own 2FA.** That's the security model, not a limitation. Internal transfers to the tax sub-account are auto-categorized "Impôts et taxes" with no receipt required.

### 6. Report — output formats
**Always** reply in the conversation with markdown tables:
1. **Tax schedule table** (date · tax · amount · basis · confidence), each deadline marked ✅ covered / ⚠️ short by X € given the vault balance.
2. **90-day projection** (week × account), low point highlighted.
3. **Vault status** + this month's provision breakdown.
4. Narrative alerts by severity.

**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): generate an interactive **HTML dashboard** — one line per account, uncertainty band, tax deadlines as markers, vault gauge — and hand it to the user. If the host cannot render files, say nothing about it: the markdown tables are the deliverable. The third output is the **request note** (full calculation), which the approver sees in the Qonto app at SCA time.

## Guardrails
- NEVER create a transfer request without explicit user confirmation in the current conversation; never present it as executed — it is pending the user's SCA approval.
- Projections and tax amounts are estimates, not filings; recommend accountant validation. Degrade honestly if history < 6 months.
- In rehearsals, `decline_request` afterwards (`request_type: "multi_transfers"`, plural).
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50).
