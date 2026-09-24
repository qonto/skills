---
name: qonto-rebill
description: Recovers billable expenses from a Qonto account. Finds client-attributable transactions (client-named Qonto labels, teams, or history-assisted interactive attribution), groups them by client and period, inventories the receipts already attached to each transaction, explains the French "disbursement vs rebilled expense" VAT choice without ever deciding alone, and drafts the rebill invoice line by line (create_client_invoice as DRAFT, sent only after explicit confirmation), with an optional 5-10% handling fee. Use for "refacture mes frais à mes clients", "which expenses did I advance for client X this quarter?", "rebill my project expenses", "did I forget billable expenses?", "invoice my travel and hosting costs back".
permissions:
  mcp:
    qonto: [create_client_invoice, create_quote, delete_client_invoice, get_attachment, get_organization, list_cash_flow_categories, list_clients, list_labels, list_transaction_attachments, list_transactions, send_client_invoice]
  network: []
  env: []
  tools: [Read]
---

# Qonto Rebill

Freelancers and agencies advance money for their clients — plugins, stock photos, hosting, train tickets, mission meals — and forget to rebill half of it. This skill finds those expenses, groups them per client, checks the receipts, and turns them into a line-by-line rebill invoice. Read-heavy, one safe write: the invoice is created as a **draft**; nothing leaves without the user's explicit confirmation.

## Prerequisites
1. `get_organization` **always first** → accounts, balances, legal identity (`list_transactions` requires a `bank_account_id`/`iban`).
2. `list_labels` + `list_clients` → the attribution referential. Best setup: Qonto labels named after clients (or teams per client/mission). **No client labels? The skill still works**: it switches to interactive attribution (step 2) — slower, but nothing is lost.
3. **Country-aware**: the find → group → draft mechanics are universal. The **disbursement regime (débours)** described below is **French law** (art. 267 II-2° CGI). For other Qonto countries (DE, ES, IT, AT, NL, BE, PT…), the skill drafts the invoice all the same but says plainly that local VAT treatment of recharged costs must come from a local accountant — it never states foreign VAT rules.

## Workflow

### 1. Scope the hunt
Agree the period with the user (default: the last full quarter) and which client(s) to cover (default: all). Load referentials: `list_labels`, `list_clients`. Normalize label names (case, accents) and match them against invoicing clients — "acme studio" the label and "ACME Studio" the client are the same entity.

### 2. Detect client-attributable expenses
`list_transactions` per account, `side: debit` scope, paginate `per_page: "50"`, over the agreed period. **Group by `emitted_at`, not `settled_at`** — card expenses settle 1-2 days later and would leak across period boundaries. Attribution sources, in order:
- **Client-named labels** on the transaction → direct attribution.
- **Teams / mission labels** mapped to a client (confirm the mapping once).
- **History-assisted interactive attribution** for everything else: shortlist candidates (counterparties already attributed to a client in the past; mission-typed spend: SaaS/plugins, stock photos, hosting, transport, hotels, meals near mission dates) and ask **transaction by transaction** — "Was this €X at [counterparty] on [date] for a client?" Nothing is EVER attributed silently. Offer to label accepted transactions going forward so next quarter is automatic.

### 3. Group and inventory receipts
Per client and period: table of expenses (date · counterparty · amount · VAT on the purchase · label) with totals. For each expense, `list_transaction_attachments` → receipt **already attached** inventoried (`get_attachment` gives a time-limited download URL); missing receipts flagged per line. If gaps: recommend running **qonto-receipt-hunter** first — rebilling with receipts attached is what gets paid without questions.

### 4. Explain the VAT choice — then ask, never decide
| Criterion | Disbursement — *débours* (art. 267 II-2° CGI) | Rebilled expense (standard) |
|---|---|---|
| Principle | Paid **in the client's name and on their behalf** (mandate) | Paid in your own name, recharged as part of your price |
| Margin | Forbidden — exact amount, euro for euro | Allowed (handling fee 5-10%…) |
| VAT | **Outside VAT scope**: no VAT on the line, input VAT on the purchase not deductible | **VAT at the rate of the main service** (often 20%), even if the underlying cost was 10% or VAT-free |
| Receipt | Original invoice **in the client's name**, handed over to them | Original invoice in your name, kept in your books |
| Books | Third-party account (not revenue) | Revenue |
| Country | French regime | Universal mechanics; outside France, ask a local accountant |

The skill presents this table, asks which regime applies (per line when mixed), and asks whether to add a handling fee (5-10%, user's choice; **never on disbursements**). It never picks a regime alone, and every report recommends accountant validation.

### 5. Draft the invoice — one line per expense
Only after the regime is chosen: `create_client_invoice` as **DRAFT** for the matched `client_id` — one item per expense ("YYYY-MM-DD — Counterparty — short description", quantity 1, unit price from the transaction, VAT rate per the chosen regime), plus a separate "Handling fee X%" line if chosen. Use a neutral number format (INV-YYYY-NNN) if a number is required. Show the draft line by line in the conversation, with the receipt inventory (✅ attached / ⚠️ missing) alongside.

### 6. Confirm, send — or delete
- **Send only after explicit confirmation in the current conversation** (`send_client_invoice`). Until then it is a draft in Qonto's invoicing section — say so, never present it as sent.
- Rehearsals and demos: fictitious client + draft + `delete_client_invoice` — **invoices created via MCP are real** and finalized numbers enter the legal sequence.
- Final recap: money recovered per client, receipts coverage, next ritual date. To chase payment afterwards, hand over to **qonto-invoice-chaser**.

## Output formats
**Always** in the conversation: markdown tables (expenses per client with receipt status · draft invoice line by line · recovered total). **When the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): an HTML recap — per-client cards, receipts gauge, quarter-over-quarter recovered amounts. Otherwise the tables are the deliverable — say nothing about it. The receipt pack is a list of `get_attachment` download links (time-limited) the user can forward with the invoice.

## Guardrails
- Invoices created via MCP are **real**. DRAFT until explicit confirmation; NEVER present a draft as sent; rehearse on a fictitious client and `delete_client_invoice` afterwards.
- Never attribute an expense to a client without the user's agreement; never invent an attribution, an amount, or a receipt.
- The disbursement/rebill choice is the **user's decision** (with their accountant) — the skill explains and asks, full stop.
- Empty account, no labels, no invoicing clients → the skill says what it can and cannot do, and proposes the one-time setup (labels named after clients).
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50).
