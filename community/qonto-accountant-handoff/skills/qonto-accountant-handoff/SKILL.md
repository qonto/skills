---
name: qonto-accountant-handoff
description: Monthly (or quarterly) accountant handoff pack built from a Qonto account. Gathers the period's bank statements, a receipt completeness report with the precise list of what's missing, factually annotated transactions (labels, VAT, anomaly notes), client and supplier invoices, and a drafted handoff letter — then files everything into a YYYY/MM Google Drive tree and drafts a recap email to the accounting firm when those MCPs are present (structured local pack otherwise). Use for "prépare le pack comptable de juin", "mon comptable me demande les pièces de mars", "prepare the handoff pack for my accountant", "what's missing before I send the month to my accountant?".
permissions:
  mcp:
    qonto: [get_organization, get_statement, list_cash_flow_categories, list_client_invoices, list_statements, list_supplier_invoices, list_transaction_attachments, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto Accountant Handoff

The monthly handoff to the accountant, without the chore. Zero writes on Qonto: the skill prepares the material — statements, receipts status, annotated transactions, invoices, a drafted letter — and files it. It does NOT do the accounting: annotation stays strictly factual; the accountant remains the professional.

## Prerequisites
1. `get_organization` FIRST → accounts (`list_transactions` requires `bank_account_id`/`iban`), legal name, country. Works for **any Qonto country**: statements, invoices and receipts are universal. Country-specific remarks (e.g. French VAT wording) only when detected — never invent local rules.
2. **Period**: previous complete month by default ("the June pack" = June 1 → 30); quarter on request. A statement only exists once its month is closed — for an in-progress month, deliver a partial pack and say so plainly.
3. **Optional MCPs, detected dynamically**: Google Drive (filing) and Gmail (recap draft). Neither is required — without them the pack is produced as a structured local output (markdown + CSV, described file by file) and the user forwards it however they like.

## Workflow

### 1. Scope the period
`get_organization`, confirm period and accounts with the user, then state which enrichments are active: "Drive detected → filed to `Accounting/YYYY/MM/`" or "no Drive MCP → local pack". Never block on a missing enrichment.

### 2. Statements
`list_statements` filtered on the period (paginate `per_page: "50"`), then `get_statement` per account for the official PDF. An account with no statement (opened mid-month, month not closed) is flagged in the pack, never papered over.

### 3. Receipts status
`list_transactions` per account over the period (settled status; watch `emitted_at` vs `settled_at` — card payments settle 1–2 days later, keep both visible at month boundaries). For each transaction, `list_transaction_attachments` → ✅ attached · ⚠️ missing · ➖ not needed (internal transfers between own accounts). Output the **precise missing list**: date · counterparty · amount · attachment expected. Suggest running **qonto-receipt-hunter** on that list *before* sending the pack.

### 4. Annotate — facts only
Per transaction: existing labels, `vat_amount` (disclose the count of nulls — the VAT view is a floor), and plain-language notes where they help the accountant: a credit matched to the debit it reverses ("this refund corresponds to the May 12 payment to X"), internal transfers named as such, suspected duplicates flagged. **NEVER an account number, journal entry or allocation** — anything that smells like bookkeeping becomes a question in the letter instead.

### 5. Invoices & the handoff letter
`list_client_invoices` and `list_supplier_invoices` filtered on the period, with statuses (paid / pending / draft). Then draft the **handoff letter**: the month in ten lines (totals in/out, transaction count, receipt coverage X/Y), the 2–3 points that deserve the accountant's attention, and the open questions (unmatched refunds, unusual amounts, receipts nobody could find).

### 6. Deliver
- **Google Drive MCP present**: file the pack into `Accounting/YYYY/MM/` — `00-handoff-letter`, `01-statements`, `02-client-invoices`, `03-supplier-invoices`, `04-receipts-status` (status table + missing list). Reuse the tree month after month.
- **Gmail MCP present**: create a **draft** recap to the firm — subject `Pack comptable YYYY-MM — <company>`, the letter as body, link to the Drive folder. NEVER send it; the user reviews and hits send themselves.
- **Neither present**: produce the same pack as local markdown/CSV files, list them, and tell the user what to forward.
- **Always** reply in the conversation with markdown tables: pack contents, receipts status (coverage + missing list), the letter itself.

## Guardrails
- The skill does NOT do the accounting: no journal entries, no chart-of-accounts allocation, no tax advice. Factual annotation only — the accountant validates everything.
- Nothing leaves without the user: the Gmail recap is a **draft**; the Drive filing is announced before it happens; no data flows to an MCP that wasn't detected and named.
- Never present a pack as complete while pieces are missing — the missing list is the headline of the letter, not a footnote.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50). `list_cash_flow_categories` can return `403 missing oauth scope` on the claude.ai connector → use transaction labels instead.
- Companion skills: **qonto-receipt-hunter** to chase missing receipts before the handoff · **qonto-monthly-close** for the quality check on the closed month.
