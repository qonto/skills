---
name: qonto-receipt-hunter
description: Receipt hunter for Qonto accounts. Finds transactions missing their receipt, ranks them by urgency (recoverable VAT at stake, amount, age), then hunts the original receipts down in connected sources — Gmail (merchant/amount/date search around the purchase date) and Google Drive — and attaches each found original to the right transaction, one user confirmation at a time. Use for "quelles transactions sans justificatif ?", "hunt my missing receipts", "combien de TVA je risque de perdre ?", "retrouve la facture Amazon dans mes mails", "attach this receipt to the right transaction".
permissions:
  mcp:
    qonto: [get_attachment, get_organization, list_transaction_attachments, list_transactions, remove_transaction_attachment, request_attachment_upload, upload_attachment]
  network: []
  env: []
  tools: [Read]
---

# Qonto Receipt Hunter

Zero missing receipts. The skill inventories the gaps, quantifies the recoverable VAT at stake, hunts originals in Gmail and Google Drive, and attaches them to the right transactions — one confirmation per attachment, originals only, never a fabricated document.

## Prerequisites
1. `get_organization` **first** → accounts and `bank_account_id`/`iban` (required by `list_transactions`). Default scope: the last 90 days across all accounts; offer to widen (quarter, fiscal year) or narrow.
2. **Country-aware**: works for every Qonto country. The VAT-at-stake estimate uses `vat_amount` when present; the 20/120 ceiling fallback applies to **France only** — for other countries (DE, ES, IT, AT, NL, BE, PT…), never guess a rate: report the untagged amounts as "VAT unknown".
3. **Multi-MCP optional, detected dynamically**: Gmail and Google Drive MCPs power the hunt. Without them, the core still delivers on Qonto alone: the prioritized inventory of missing receipts + the VAT at stake + where-to-look suggestions. Say plainly which sources are available and which are not.

## Workflow

### 1. Inventory the gaps
`list_transactions` per account, paginate `per_page: "50"`. A transaction is a **gap** when `attachment_ids` is empty AND `attachment_required` is true AND `attachment_lost` is false. Double-check ambiguous cases with `list_transaction_attachments`. Set aside `side: credit` (client payments match invoices, not receipts) and declined/reversed operations.

### 2. Rank by urgency
Score each gap: **recoverable VAT at stake** (`vat_amount` if present; else, FR only, amount × 20/120 announced as a ceiling estimate) + **amount** + **age** (older gaps are harder to recover and closer to the accountant's closing). Tag 🔴 urgent / 🟠 soon / 🟢 low. Headline: "X missing receipts, ~Y € of recoverable VAT at stake."

### 3. Hunt — Gmail (if the MCP is present)
For each gap, search the inbox: merchant name variants (from `clean_counterparty_name` / raw label), amount, and a **date window around `emitted_at`** — never `settled_at`, card payments settle 1–2 days late. Use **amount tolerance** (tips, foreign currency, partial captures); if the exact amount misses, retry merchant + date window alone. Target the original: the merchant's PDF invoice or the order-confirmation attachment.

### 4. Hunt — Google Drive (if the MCP is present)
Search files by merchant, date and amount in names and contents. Download the candidate and read it before proposing anything.

### 5. Verify & attach — one confirmation each, never in bulk
Coherence check before proposing: the document names the merchant, the amount matches within tolerance, the date sits in the `emitted_at` window. **Originals only** (merchant PDF, email attachment) — NEVER generate, regenerate or "reconstruct" a receipt: a fabricated document has zero probative value and is a tax-audit liability. Show the match (transaction ↔ document) and wait for **explicit confirmation**; then `request_attachment_upload` (opens the upload slot) → `upload_attachment` (pushes the file) → verify with `list_transaction_attachments` / `get_attachment`. If the host cannot pull the file binary (some connectors expose email attachments as metadata only), hand the user the exact email/file pointer for a one-drag manual attach — and say so, don't pretend.

### 6. Report
Table: **attached ✅** / **found, to attach manually 📎** (with the direct pointer) / **not found ❌** with one concrete lead each — merchant portal (invoices section), secondary or personal inbox, Qonto's native receipt auto-collection, ask the supplier for a duplicate. Close with the completeness score (transactions with receipt ÷ transactions requiring one) before/after the session.

## Guardrails
- **NEVER fabricate a receipt**: no generated PDFs, no reconstructed invoices, no screenshots-as-receipts. If no original exists, the transaction stays in the "not found" list with a lead.
- Never attach without explicit confirmation of the displayed match; if several transactions or documents are plausible candidates, ask — don't guess. No silent batch attaching, ever.
- Exclude `attachment_required: false`, credit side and `attachment_lost` from the score — don't pollute it.
- Match on `emitted_at` with amount tolerance; disclose the tolerance used in every proposed match.
- If Gmail/Drive MCPs are absent, say so and deliver the Qonto-only inventory — still useful on its own.
- Mask IBANs and card numbers (last digits only). Paginate everything (`per_page` ≤ 50).
