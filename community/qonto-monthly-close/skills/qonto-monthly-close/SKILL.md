---
name: qonto-monthly-close
description: Month-end closing review for Qonto accounts, read-only. One prompt triggers a full review of the past month — missing receipts prioritized by stakes, the month's VAT (collected/deductible, cash-basis aware), anomalies (unusual spend, duplicate direct debit, new beneficiary), unlabeled transactions, unpaid client invoices, month-over-month comparison — and produces an actionable closing report with a prioritized fix-it list. Use for "close my month", "clôture mon mois", "month-end review", "get my books ready for my accountant", "anything unusual on my account last month?", "how did June compare to May?".
permissions:
  mcp:
    qonto: [get_organization, list_cash_flow_categories, list_client_invoices, list_labels, list_supplier_invoices, list_transaction_attachments, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto Monthly Close

The month-end CFO in 3 minutes. One prompt reviews the whole month and hands back a closing report with a prioritized to-do. **100 % read-only**: this skill never writes anything to Qonto — it detects and prioritizes; the user acts, or chains the dedicated skills for each follow-through.

## Prerequisites
1. `get_organization` **always first** → bank accounts (`bank_account_id` is required by `list_transactions`), balances, legal form, country.
2. **Country-aware**: receipts, anomalies, categorization, unpaid invoices and comparisons work for **every Qonto country**. The VAT module uses French logic (CA3 vocabulary, cash-basis detection); for DE, ES, IT, AT, NL, BE, PT it degrades to a generic collected−deductible estimate and says so — never invents local rules.
3. Month to close: default = **last full calendar month**; the user can name any month. Account scope: default = main account, offer to include the others.

## Workflow

### 1. Scope the month
- Compute the month window (`settled_at_from` = 1st 00:00 UTC, `settled_at_to` = last day 23:59 UTC).
- `list_transactions` per account with `bank_account_id`, the window, `per_page: "50"`, paginate until exhausted.
- Also pull the **previous 3–6 months** (same pagination) — baselines for the anomaly detectors and the month-over-month comparison need history, not just the month.
- Keep per transaction: counterparty label, `amount`, `side`, `operation_type`, `settled_at`, `emitted_at`, `attachment_ids`, `attachment_required`, `attachment_lost`, `label_ids`, `vat_amount`. Card operations: reason on `emitted_at` (settlement lags 1–2 days).

### 2. Missing receipts — prioritized by stakes
- Flag transactions where `attachment_ids` is empty AND `attachment_required` is true AND `attachment_lost` is false. When in doubt, confirm with `list_transaction_attachments`.
- **Priority = what the gap costs**: rank by amount and by recoverable VAT at risk (`vat_amount` known → exact; unknown → estimated at the standard rate, flagged as estimate). A €3 coffee and a €1,200 laptop are not the same to-do line.
- Compute the **completeness score**: transactions with a receipt ÷ transactions requiring one.
- **Optional Gmail enrichment**: if a Gmail MCP is connected, offer to search the inbox for the missing receipts (counterparty name + date window). If not, say so in one line and continue — the dedicated skill `qonto-receipt-hunter` handles deep receipt chasing and uploads.

### 3. The month's VAT
- **Collected**: from `list_client_invoices`. Check `vat_payment_condition` on the invoices: if `"on_receipts"`, VAT follows **client payments received in the month**, not issued invoices — sum `vat_amount` of invoices paid in the month; otherwise use invoices issued in the month.
- **Deductible**: sum `vat_amount` on the month's debit transactions; disclose how many debits had no VAT data → the figure is a **floor**. Cross-check with `list_supplier_invoices` totals when available. Receipts missing from step 2 = VAT not deductible until the invoice is found — quantify that link.
- **Net VAT** = collected − deductible, floor 0. Label it an estimate, not a filing. For the full tax schedule and provisioning, hand over to `qonto-tax-pilot`.

### 4. Anomalies — flagged, never accused
Three detectors, all compared against the 3–6 month baseline:
- **Unusual spend**: a known counterparty whose month total deviates strongly from its baseline (e.g. > 2× its median), or a single debit far above the account's usual range.
- **Duplicate direct debit**: same counterparty, same (±1 %) amount, twice or more in the month, `operation_type` direct debit — classic double-billing signature.
- **New beneficiary**: a counterparty never seen in the prior months receiving a meaningful outbound amount — worth a human glance (fraud, typo, or simply a new supplier).
Each anomaly carries the evidence (dates, amounts, baseline) and a severity. These are review flags for the user, not verdicts.

### 5. Unlabeled transactions & unpaid client invoices
- `list_labels` for the user's taxonomy (⚠️ `list_cash_flow_categories` returns **403 missing OAuth scope** on the claude.ai connector — labels are the reliable fallback). List transactions with empty `label_ids` and **propose** a label per counterparty pattern. Propose only — this skill writes nothing; applying labels is one tap in the Qonto app.
- `list_client_invoices` with unpaid status: days overdue vs `due_date`, per-client payment history (paid count, usual delay) → each unpaid line gets a suggested next step. Drafting and sending the dunning emails is `qonto-invoice-chaser`'s job — reference it by name.

### 6. The closing report
**Always** reply in the conversation with markdown tables:
1. **Scorecard**: transactions reviewed · receipt completeness % · net VAT estimate · anomaly count · unpaid total.
2. **Missing receipts** (counterparty · date · amount · VAT at risk · priority).
3. **VAT breakdown** (collected − deductible = net, with the floor caveat).
4. **Anomalies** (type · evidence · severity).
5. **Month-over-month**: top category rises and falls vs the previous month (computed from labels; unlabeled bucket shown honestly).
6. **Unpaid invoices** (client · amount · days overdue · history).
7. **The fix-it to-do**, sorted by priority (P1 money at risk → P2 compliance → P3 hygiene), each line pointing to the dedicated skill or the one-tap app action that resolves it.

**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): generate an **HTML dashboard** — month scorecard, receipt-completeness gauge, VAT tile, anomaly cards, to-do checklist. If the host cannot render files, say nothing about it: the markdown tables are the deliverable.

## Guardrails
- **This skill is read-only.** It never calls a write tool; nothing is created, modified, sent or moved. The report proposes; the user disposes. This also means it is safe to run on any account, any time — including a judge's.
- Anomalies are **flags with evidence, not accusations**. Always show the baseline that triggered the flag.
- VAT figures are estimates, not filings — recommend accountant validation in every report. Degrade honestly: empty month, no invoices, non-French org → say what could and couldn't be computed, never invent.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50).
- If asked to fix things directly (upload receipts, send reminders, provision taxes), point to the dedicated skills — `qonto-receipt-hunter`, `qonto-invoice-chaser`, `qonto-tax-pilot` — or the Qonto app.
