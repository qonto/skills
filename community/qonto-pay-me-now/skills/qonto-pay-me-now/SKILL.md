---
name: qonto-pay-me-now
description: Quote-to-cash accelerator for Qonto accounts. Detects accepted quotes that were never invoiced, generates the invoice from the quote (draft first, explicit confirmation before sending), creates a Qonto payment link so the client can pay instantly by card or bank transfer, optionally shortens it into a trackable link (plus a QR code for printed invoices), then follows up — link clicked but unpaid after 48 h triggers a proposed gentle nudge. Use for "my quote was accepted, invoice it and get me paid", "create a payment link for this invoice", "who clicked my payment links but didn't pay?", "fais-moi payer ce devis".
permissions:
  mcp:
    qonto: [create_client_invoice, create_payment_link, delete_client_invoice, get_organization, get_payment_link, list_client_invoices, list_payment_links, list_quotes, list_transactions, mark_client_invoice_as_paid, send_client_invoice]
  network: []
  env: []
  tools: [Read]
---

# Qonto Pay Me Now

From quote to cash, without the black hole. The freelance trap: the quote gets accepted… then the invoice waits, and the payment waits even longer. This skill closes the gap in one conversation: accepted quote → invoice → payment link → tracked follow-up. Three writes, all harmless by design: an invoice draft (sent only after explicit confirmation), a payment link (a way to RECEIVE money — it can never move money out), and a paid-marking on an invoice — always proposed with the matching transaction as evidence, never automatic.

## Prerequisites
1. `get_organization` first → accounts, `bank_account_id`/IBAN (required by `list_transactions`), country, legal identity. Nothing hardcoded — the skill adapts to any organization.
2. **Payment links** must be activated once in the Qonto app. If `create_payment_link` is refused, say so, explain the one-time activation, and continue with the invoice alone.
3. **Country-aware**: the quote → invoice → payment link cycle is identical for every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT). Legal wording of reminders is fully covered for **France**; elsewhere, adapt the tone and never invent local legal mentions.
4. **Optional MCPs, detected dynamically**: Short.io (`create-short-link`, `link-statistics`) for a trackable short link; Gmail for sending. Absent → the raw Qonto payment link and copy-ready text work fine; say so and continue.

## Workflow

### 1. Spot the money left on the table
`list_quotes` paginated (`per_page` ≤ 50), filter accepted quotes. Cross-check against `list_client_invoices` (client + amount + quote number in title/description): surface **only the accepted quotes that were never invoiced**, with client, amount, acceptance date. No accepted quotes? Say so and offer to start from any existing unpaid invoice instead — the rest of the cycle is identical.

### 2. Invoice from the quote — draft first
`create_client_invoice` as a **DRAFT**, carrying over the quote's client, line items, amounts and VAT. ⚠️ Invoices created via MCP are **REAL legal documents**: always show the draft (lines, totals, due date) and **never send without explicit confirmation** in the current conversation. Then `send_client_invoice`. Respect the organization's numbering — never invent invoice numbers. Note: `vat_payment_condition: "on_receipts"` means VAT follows the client's *payment*, not the invoice — worth telling the user their payment link literally accelerates their VAT cycle too.

### 3. Create the payment link
`create_payment_link` for the invoice amount, reusing the invoice number in the description so reconciliation is trivial. The client pays by card or bank transfer in one click. ⚠️ **The official MCP docs list payment links as unsupported — they work** (verified against the live API on July 3rd). Call the tool; don't trust the doc. If it errors, the payment-link feature isn't activated on the account → point to the Qonto app, continue invoice-only.

### 4. Short link + QR (optional enrichment)
If the Short.io MCP is present: `create-short-link` with a readable slug (e.g. `pay-INV-2026-042`) → a short, trackable URL. Offer a **QR code** encoding the link for printed invoices (generate it as a file/artifact when the host renders files). Without Short.io: the raw Qonto link is perfectly fine — say so, skip tracking, continue.

### 5. Deliver — only with explicit consent
With the user's explicit go: `send_client_invoice`, and/or a Gmail draft (if the Gmail MCP is present) containing the invoice and the payment link — the user reviews and hits send themselves. Otherwise: copy-ready message text. Never present anything as sent while it is pending.

### 6. Follow up — clicks vs cash
On request or ~48 h later: `list_payment_links` / `get_payment_link` (status), Short.io `link-statistics` (clicks), and `list_transactions` (real money in — requires `bank_account_id` from step 0). Decision matrix:
- **Not clicked, not paid** → check delivery, offer to resend through another channel.
- **Clicked, unpaid > 48 h** → propose a **gentle nudge** ("the link is still active") — drafted, never auto-sent.
- **Paid via the link** → confirm, close the loop.
- **Paid by plain transfer outside the link** → match the transaction (amount ± 0.01, counterparty, reference) and propose `mark_client_invoice_as_paid` with the transaction as evidence.

## Output formats
**Always** reply in the conversation with markdown tables: the quote→invoice→link pipeline (one row per accepted quote), and the follow-up matrix (clicked · paid · proposed action). The **payment link + short link** are the deliverable the user shares. **When the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): also generate the QR code. If it can't, say nothing about it — the links are enough.

## Guardrails
- Invoices via MCP are REAL: draft first, explicit confirmation before `send_client_invoice`, rehearsals on a fictional client + `delete_client_invoice` afterwards.
- **This skill never moves money out.** A payment link only lets the client pay *in*; it is unrelated to outbound transfers, which the MCP cannot execute anyway — any transfer request requires the user's own SCA in the Qonto app.
- Nothing is sent (invoice, email, nudge) without explicit confirmation in the current conversation; never presented as sent/paid while pending.
- Amounts always come from the quote or invoice — never invented. Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50).
- Degrade honestly: no quotes, no payment-link feature, no Short.io, non-French account → say what works and what doesn't, and keep going with what does.
