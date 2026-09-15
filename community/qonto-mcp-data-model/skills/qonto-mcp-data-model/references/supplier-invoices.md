# Supplier invoices (accounts payable)

Incoming bills. MCP tools: `list_supplier_invoices`, `get_supplier_invoice`, `change_supplier_invoice_status`. (The upstream API also has a multipart bulk-create endpoint, not exposed through MCP.)

## Status lifecycle

```
to_review ──→ to_approve ──→ rejected
    │             │
    ▼             ▼
  to_pay / pending ──→ awaiting_payment / scheduled ──→ paid
    │
    └──→ archived (with declined_note) / discarded
```

Full enum: `to_review`, `to_pay`, `to_approve`, `awaiting_payment`, `pending`, `scheduled`, `paid`, `archived`, `rejected`, `discarded`.

## Response object

Most business fields are populated by Qonto's OCR/analysis of the uploaded document — check `analyzed_at` before trusting them.

| Field | Type | Notes |
|---|---|---|
| `id`, `organization_id` | uuid | |
| `status` | enum | see lifecycle |
| `supplier_id` | uuid? | |
| `supplier_name`, `issuer_name` | string | issuer_name = extracted from document |
| `invoice_number` | string | OCR-extracted |
| `description`, `file_name` | string | |
| `iban` | string | payee IBAN (extracted/entered) |
| `vat_number`, `tin_number` | string? | issuer identifiers |
| `total_amount` | money `{value,currency}` | gross, decimal string |
| `total_amount_excluding_taxes`, `total_tax_amount` | money? | |
| `taxes` | array? | per-rate breakdown `{tax_amount, tax_rate}` — ⚠️ `tax_rate` is a **fraction** (`"0.20"` = 20 %) |
| `payable_amount` | money? | remaining after credit notes |
| `total_amount_credit_notes` | money? | |
| `issue_date`, `due_date`, `payment_date`, `scheduled_date` | `YYYY-MM-DD` | |
| `created_at`, `updated_at`, `analyzed_at` | ISO 8601 | `analyzed_at` = OCR completion |
| `is_credit_note` | bool | supplier credit notes share this entity |
| `has_suggested_credit_notes`, `has_discrepancies`, `has_duplicates` | bool | data-quality flags |
| `attachment_id`, `display_attachment_id` | uuid | stored document vs the one to render |
| `attachment_category` | enum ⚠️ UPPERCASE | `INVOICE`, `EXPENSE_RECEIPT`, `CARD_RECEIPT`, `CREDIT_CARD_RECEIPT`, `CREDIT_NOTE`, `OTHER_FINANCIAL_DOCUMENT`, `OTHER_NON_FINANCIAL_DOCUMENT`, `UNKNOWN` |
| `source_type` | enum | `email`, `e_invoicing`, `direct_upload` |
| `source` | enum | `email_forward`, `e_invoicing`, `supplier_invoices`, `pay_by_invoice`, `integration`, `regate`, `generic_upload`, `pay_later` |
| `initiator_id` | uuid | membership that created it |
| `declined_note` | string | archive reason (defaults `""`) |
| `matched_transactions` | array? | `{subject_id, subject_type: "transfer", transaction_id}` (⚠️ `matched_transactions_ids` is **deprecated**) |
| `transfer_ids` | array[uuid]? | |
| `suggested_transactions` | array? | matcher suggestions `{id, score}` |
| `related_invoices` | array? | `{id, invoice_number?, total_amount, attachment_id, file_name}` |
| `supplier_snapshot` | object? | `{id, name, iban, tin, vat_number, email, currency, status}` — frozen at match time |
| `approval_workflow` | object? | `{approver_ids[], supplier_invoice_request_id?, verified_by?, last_approved_by?}` |
| `available_actions` | object | `{delete, archive, unarchive, pay: bool, reasons: {...}}` — reasons explain *why not*: pay → `is_credit_note`, `missing_iban`, `missing_data`, `invalid_status`, `incorrect_approval_workflow`; delete → `invalid_status`, `linked_self_invoice`, `is_recorded` |
| `is_einvoice`, `e_invoice_type` | bool, enum? | German orgs: `zugferd`, `xrechnung` |
| `einvoicing_lifecycle_events` | array? | French e-invoicing lifecycle: `{status_code: 200–214 ("Déposée"…"Visée"), reason, reason_message, timestamp}` |
| `meta` | object? | accounting integration: `{integration_type, connector, accounting_recorded_at, accounting_recorded_source}` |
| `self_invoice_id`, `request_transfer` | uuid?, object | related entities |

**Practical tip**: `available_actions` is the source of truth for what you may do next — check it instead of re-deriving rules from `status`.

## List filters (upstream; MCP exposes a subset — check the tool schema)

- `filter[status]` (full enum), `filter[due_date]`: `past_and_today` / `future` / `missing_date`; `filter[payment_date]` / `filter[issue_date]`: relative buckets only (`today`, `yesterday`, `this_week`, `past_week`, `this_month`, `past_month`).
- `filter[payable_amount]`: `lte:100.00:EUR` / `gte:100.00:EUR`.
- `filter[document_type]`: `duplicates`, `non_financial_documents`. `filter[exclude_credit_notes]`, `filter[missing_data]`, `filter[matched_transactions]` (booleans).
- Full-text: `query` + `query_fields` ⊆ `supplier_name`, `amount`, `file_name`, `invoice_number`.
- Pagination default is **25/page** (most other domains default to 100).
- ⚠️ Through MCP, status/approver filters are not wired yet — filter client-side on `status`.

## Lifecycle actions — `change_supplier_invoice_status(id, <exactly one>)`

| Action | Effect |
|---|---|
| `reject: "<note>"` | rejects with the given note — **irreversible** |
| `mark_as_paid: "YYYY-MM-DD"` | records an out-of-band settlement (date ≤ today). ⚠️ This is bookkeeping only — **not** proof that a Qonto payment ran |
| `unmark_as_paid: true` | only from `paid`; reverts to `to_review` |

## Creating supplier invoices via MCP

The upstream multipart bulk endpoint is not exposed. Instead: `request_attachment_upload` → PUT the file → `upload_attachment(blob_ref, target: "supplier_invoice")` — Qonto creates the supplier invoice from the document (OCR fills the fields, watch `analyzed_at`).
