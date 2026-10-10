---
name: qonto-mcp-data-model
description: Data model reference for the Qonto MCP server. Use when reading or writing Qonto data through MCP tools (transactions, invoices, clients, cards, memberships, statements, cash flow categories) — to know entity shapes, required fields, enums, pagination formats, money representations, and cross-tool dependencies before calling any qonto tool.
permissions:
  mcp:
    qonto: [approve_request, change_card_status, change_client_invoice_status, change_supplier_invoice_status, create_card, create_card_request, create_cash_flow_category, create_client, create_client_invoice, create_credit_note, create_membership, create_multi_transfer_request, create_payment_link, create_product, create_quote, create_team, decline_request, delete_client, delete_client_invoice, delete_quote, get_attachment, get_authenticated_membership, get_client, get_client_invoice, get_credit_note, get_organization, get_payment_link, get_qonto_public_pricing, get_quote, get_statement, get_subscription, get_supplier_invoice, get_transaction, list_cards, list_cash_flow_categories, list_client_invoices, list_clients, list_credit_notes, list_labels, list_memberships, list_payment_links, list_products, list_quotes, list_requests, list_statements, list_supplier_invoices, list_teams, list_transaction_attachments, list_transactions, mark_client_invoice_as_paid, modify_transaction_cash_flow_category, remove_transaction_attachment, request_attachment_upload, send_client_invoice, send_quote, update_card, update_client, update_client_invoice, update_quote, upload_attachment]
  network: []
  env: []
  tools: [Read]
---

# Qonto MCP Data Model

The Qonto MCP server exposes a Qonto business account (French/European B2B neobank) through ~60 tools mirroring the Qonto Business API v2 (`docs.qonto.com`). This skill documents the data structures those tools return and accept, so an agent can chain calls correctly on the first try.

## Entity map

```
Organization (1 per token)
├── bank_accounts[]  ──────────── Transactions ── Attachments (receipts/invoices)
│                                      │
│                                      ├── cashflow_category / subcategory (tags)
│                                      └── labels[] (custom tags)
├── Statements (monthly PDF, per bank account)
├── Memberships (people with access) ── Teams
├── Cards (holder = membership, attached to a bank_account)
├── Requests (flash_card / virtual_card / transfer / multi_transfer approvals)
├── Subscription (the org's own Qonto plan)
└── Invoicing
    ├── Clients (counterparties) ── Client Invoices ── Credit Notes
    ├── Quotes (pre-invoice offers)
    ├── Products (reusable line-item catalog)
    ├── Payment Links (hosted checkout pages)
    └── Supplier Invoices (incoming bills)
```

## The 5 rules that prevent most mistakes

1. **Everything is scoped to one organization** — the OAuth token binds to one org; there is no org id parameter anywhere. Start sessions with `get_organization` (gives `bank_accounts[].id`, needed by `list_transactions`) and `get_authenticated_membership` (who am I, role).
2. **IDs are UUIDs; entities are linked by id, never by name.** Cash flow category *names* are localized (the catalog may return English while a transaction embeds French) — always match on `id`.
3. **Money has three representations** depending on the domain (float euros, integer cents, decimal-string + currency object), and **`vat_rate` switches between fraction and percentage scale per document type** (invoice `"0.2"` vs quote `"20"` for 20 %). See [references/conventions.md](references/conventions.md) — never assume one format.
4. **Nothing here moves money.** The strongest write is `create_multi_transfer_request`, which creates a *pending* request a human must approve in the Qonto app with their own 2FA (SCA). Sensitive writes may block waiting for the user's SCA confirmation.
5. **Some tools are plan-gated**: `list_requests` & approvals return HTTP 403 on Solo plans (requests need Business/Enterprise). Treat 403 as "feature not in plan", not as a bug.

## Reference files

| File | Read it when working on |
|---|---|
| [references/entities.md](references/entities.md) | **Start here for coverage questions**: the full entity × operations matrix (what can be listed/created/updated/deleted), action-tool semantics, what the MCP cannot do |
| [references/conventions.md](references/conventions.md) | Pagination (3 meta variants!), money formats, the vat_rate scale trap, dates, presigned URLs, deprecated fields, error semantics, SCA |
| [references/banking.md](references/banking.md) | Organization, bank accounts, transactions (full enums + per-type sub-objects), attachments, statements, cash flow categories, labels |
| [references/invoicing.md](references/invoicing.md) | Clients, client invoices (full lifecycle, e-invoicing statuses), credit notes |
| [references/quotes.md](references/quotes.md) | Quotes/devis: statuses, quote→invoice conversion, send-by-email, the percentage-vs-fraction vat_rate trap |
| [references/products-payment-links.md](references/products-payment-links.md) | Product catalog, payment links (statuses, Basket vs Invoice variants) |
| [references/supplier-invoices.md](references/supplier-invoices.md) | Incoming bills: 10-state lifecycle, OCR fields, `available_actions`, matched transactions |
| [references/team-cards-requests.md](references/team-cards-requests.md) | Memberships, teams, cards (7 variants, 13 statuses), requests (per-type shapes, SCA approval), subscription/pricing |
| [references/tool-map.md](references/tool-map.md) | Full inventory of the ~60 tools, grouped by domain, with call-order dependencies |

## Typical call chains

- **"How much did we spend on X?"** → `get_organization` → `list_transactions(bank_account_id, …)` → filter on `side: "debit"`, group by `cashflow_category.id`.
- **Invoice a customer** → `list_clients(filter)` (dedupe — no uniqueness upstream!) → `create_client` if missing (needs `currency`, `locale`, `billing_address` for invoicing) → `create_client_invoice` (required: `client_id`, `currency`, `due_date`, `issue_date`, `items`, `payment_methods`) → `send_client_invoice`.
- **Quote first, invoice later** → `create_quote` (status `pending_approval`) → `send_quote(send_to, email_title)` → client approves via the public `quote_url` (status is never writable through the API) → `create_client_invoice(quote_id: …)`; the quote's `invoice_ids` tracks the conversion. ⚠️ quote `vat_rate` is a percentage (`"20"`), invoice `vat_rate` a fraction (`"0.2"`).
- **Attach a receipt** → `request_attachment_upload` (returns presigned PUT URL + `blob_ref`) → user uploads bytes → `upload_attachment(blob_ref)`.
- **Categorize spend** → `list_cash_flow_categories` (tree of inflow/outflow categories) → `modify_transaction_cash_flow_category(transaction_id, category_id)`.
