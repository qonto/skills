# Quotes (devis)

MCP tools: `list_quotes`, `get_quote`, `create_quote`, `update_quote`, `send_quote`, `delete_quote`. Commercial offers issued **before** invoicing; an approved quote converts into client invoices (tracked via `invoice_ids`, and `client_invoice.quote_id` on the invoice side).

## Status & lifecycle

```
pending_approval ──> approved ──> (converted: invoice_ids populated)
        └──────────> canceled
```

| Status | Meaning | Timestamp |
|---|---|---|
| `pending_approval` | initial status on creation, awaiting client approval | `created_at` |
| `approved` | client approved | `approved_at` |
| `canceled` | canceled | `canceled_at` |

- **`status` is never writable** — no `status` field in create/update payloads. Approval/cancellation happen in the Qonto product (e.g. via the public `quote_url` portal); the API only reflects them.
- No documented status preconditions for update/delete/send — expect a 422 at runtime if the operation is invalid for the current status.
- ⚠️ No `updated_at` field on quotes (only `created_at` / `approved_at` / `canceled_at`), and line items carry no `id`.

## Response object

```jsonc
{
  "id": "uuid", "organization_id": "uuid",
  "number": "Q-2024-001",                        // unique within the org, ≤40 chars
  "status": "pending_approval",
  "attachment_id": "uuid|null",                  // the PDF
  "quote_url": "https://portal.qonto.com/quotes/<uuid>",   // public page for the client
  "contact_email": "contact@org.example",
  "currency": "EUR",
  "total_amount": {"value": "240.00", "currency": "EUR"}, "total_amount_cents": 24000,
  "vat_amount":   {"value": "40.00",  "currency": "EUR"}, "vat_amount_cents": 4000,
  "discount": {"type": "percentage",             // percentage | amount  (⚠️ `amount`, not `absolute` as on invoices)
               "value": "10",
               "amount": {"value": "20.00", "currency": "EUR"}, "amount_cents": 2000},
  "issue_date": "2024-01-15", "expiry_date": "2024-02-15",   // YYYY-MM-DD
  "created_at": "2024-01-15T10:30:00Z",
  "approved_at": null, "canceled_at": null,
  "terms_and_conditions": "…", "header": "…", "footer": "…",
  "items": [{
    "title": "Consulting services",              // ≤255 chars on quotes (⚠️ ≤40 on invoices)
    "description": "Monthly consulting",         // ≤1800
    "quantity": "2.5",                           // decimal string
    "unit": "hour",                              // ≤50 chars on quotes (⚠️ ≤20 on invoices)
    "unit_price": {"value": "100.00", "currency": "EUR"}, "unit_price_cents": 10000,
    "vat_rate": "20",                            // ⚠️ PERCENTAGE ("20" = 20 %) — invoices use fractions ("0.2")
    "vat_exemption_reason": null,                // IT: N-codes (N1…)
    "discount": {"type": "percentage", "value": "5",
                 "amount": {"value": "10.00", "currency": "EUR"}, "amount_cents": 1000},
    // computed, response-only:
    "subtotal": {"value": "160.00", "currency": "EUR"}, "subtotal_cents": 16000,
    "total_vat": {"value": "40.00", "currency": "EUR"}, "total_vat_cents": 4000,
    "total_amount": {"value": "200.00", "currency": "EUR"}, "total_amount_cents": 20000
  }],
  "client": { /* embedded client snapshot — same shape as on invoices (see invoicing.md) */ },
  "organization": { /* org snapshot at issuance — same shape as on invoices */ },
  "invoice_ids": [],                             // client invoices generated from this quote
  // Italian-only (null elsewhere):
  "welfare_fund": {"type": "TC22", "rate": "0.1", "amount": "10.00"},        // rate is a FRACTION
  "withholding_tax": {"reason": "RT01", "rate": "0.1", "amount": "10.00", "payment_reason": "M1"},
  "stamp_duty_amount": "0.10"                    // plain string, not a money object
}
```

## `create_quote`

Required: `client_id`, `currency`, `issue_date`, `expiry_date`, `items[]` (min 1), `terms_and_conditions` (≤3000 chars).

| Field | Notes |
|---|---|
| `number` | required if auto-numbering disabled (the default); if provided while enabled, it overrides the generated one |
| `header` / `footer` | ≤1000 chars each |
| `settings` | per-document org overrides: `vat_number`, `district_court` (DE), `company_leadership`, `commercial_register_number`, `tax_number` |
| `discount` | `{type: percentage\|amount, value}` |
| `upload_id` | pre-uploaded file (via the client-invoice uploads endpoint) |
| IT-only | `welfare_fund {type, rate}`, `withholding_tax {reason, rate, payment_reason}`, `stamp_duty_amount`; `amount` fields computed server-side |

Item required fields: `title`, `currency` (**must equal the quote's currency**), `quantity`, `unit_price {value, currency}`, `vat_rate` (percentage string). If `vat_rate` is `"0"`, add `vat_exemption_reason` (IT: N-codes — note the field is `vat_exemption_reason`, not `…_code`).

## `update_quote`

Partial update — only provided fields change, **except** `items`, which is **replace-not-merge**: sending `items` replaces the whole array and every item must again carry the 5 required fields.
`client_id` is create-only: a quote cannot be re-assigned to another client.

## `send_quote`

Emails the quote. Returns 204, no body, no documented status change.

| Field | Required | Notes |
|---|---|---|
| `send_to[]` | yes | recipient emails |
| `email_title` | yes | subject |
| `email_body` | no | body text |
| `copy_to_self` | no | default `true` |

## List — filters & meta

Upstream filters: `filter[status]` (the 3 statuses), `filter[created_at_from/to]`; `sort_by` only on `created_at` (default `desc`); `per_page` default 100, **max 500** (higher than other domains).

⚠️ Meta discrepancy: upstream docs give `{total, current_page, total_pages, next_page, prev_page}` for quotes, but the **MCP layer returned** `{total_count, previous_page, …}` (invoicing variant A) on a live call — code against what the tool actually returns.

## Quirks

- **Rate-scale trap**: quote item `vat_rate` is a percentage string (`"20"`), client-invoice item `vat_rate` is a fraction (`"0.2"`), and IT `welfare_fund`/`withholding_tax` rates are fractions even on quotes. Never copy rates between document types blindly.
- Discount `type` enum is `percentage | amount` on quotes but `percentage | absolute` on invoices (per upstream docs) — verify empirically when reusing code.
- Item `title` limit differs (255 on quotes vs 40 on invoices), as does `unit` (50 vs 20).
- The quote schemas contain copy-paste artifacts from invoices ("Invoice for inventory stock" in send examples) — cosmetic only.
- Quotes have no dedicated OAuth scope upstream; they ride on `client_invoices.read` / `client_invoice.write`.
