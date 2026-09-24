# Cross-cutting conventions

Observed against a live Qonto MCP session (July 2026). Field names and enum values are verbatim.

## Identifiers

- Every entity id is a **UUID string** (`"9f3b2c1a-7136-45be-b77f-000000000000"`). Most are UUIDv4; cash flow categories use **UUIDv7** (time-ordered, start with a timestamp prefix like `01928af2-…`).
- Transactions carry **two** identifiers: `id` (UUID — what `get_transaction` expects) and `transaction_id` (human-readable slug like `"acme-corp-1234-3-transaction-4"` — display only, never pass it to tools).
- Organizations and bank accounts also have a `slug` (`"acme-corp-1234"`), used to build Qonto webapp deep links.

## Money — three coexisting representations

| Representation | Where | Example |
|---|---|---|
| **Float euros** + separate ISO currency field | Transactions (`amount`, `local_amount`, `vat_amount`, `settled_balance`), bank accounts (`balance`, `authorized_balance`) | `"amount": 2.26, "currency": "EUR"` |
| **Integer cents** (alongside the float) | Bank accounts only (`balance_cents`, `authorized_balance_cents`) | `"balance_cents": 226` |
| **Decimal-string amount object** | Everything invoicing-related and pricing: `unit_price`, `total_amount`, subscription `monthly_price` | `{"value": "10.99", "currency": "EUR"}` or `{"amount": "11.00", "currency": "EUR"}` |

⚠️ Note the object key inconsistency: product/invoice item prices use `value`, subscription pricing uses `amount`.

### The rate-scale trap

`vat_rate` changes both type and scale per domain — never copy a rate across document types:

| Domain | Type | Scale | 20 % is written |
|---|---|---|---|
| Transactions | float | percent | `20` |
| Client invoices, products, supplier `taxes[].tax_rate` | string | **fraction** | `"0.2"` |
| **Quotes** | string | **percent** | `"20"` |
| Payment-link items | string | percent | `"20.0"` |
| IT `welfare_fund` / `withholding_tax` rates | string | fraction | `"0.2"` (everywhere, quotes included) |

- Currencies are ISO 4217 alpha-3 (`"EUR"` almost always; invoice `unit_price.currency` is EUR-only today).

## Dates & times

- Timestamps: ISO 8601 UTC with `Z`, millisecond precision (`"2024-01-03T06:27:51.638Z"`); card timestamps have microsecond precision.
- Date-only inputs (invoices, quotes, scheduled transfers): `YYYY-MM-DD`.
- Statement periods: `MM-YYYY` (`"06-2026"`).
- Transactions have three distinct clocks: `emitted_at` (initiated), `settled_at` (funds moved), `created_at` / `updated_at` (record lifecycle). Filter params exist for each (`emitted_at_from`, `settled_at_to`, …).

## Pagination — three meta variants

All list tools take `page` / `per_page` (⚠️ typed `string` on some tools — transactions, memberships, labels, attachments — and `integer` on others; both accept numeric values). The response `meta` block varies:

```jsonc
// Variant A — invoicing lists (clients, client_invoices, quotes, credit_notes, products)
{"current_page": 1, "next_page": null, "previous_page": null, "per_page": 2, "total_count": 0, "total_pages": 1}

// Variant B — banking/team lists (transactions, supplier_invoices, memberships, teams, statements, labels, payment_links)
{"current_page": 1, "next_page": 2, "prev_page": null, "per_page": 1, "total_count": 71, "total_pages": 71}

// Variant C — cards: no next/prev keys at all
{"current_page": 1, "per_page": 2, "total_count": 1, "total_pages": 1}
```

Robust pattern: **iterate while `current_page < total_pages`** rather than relying on `next_page`/`previous_page`/`prev_page` (payment_links was even observed returning `next_page: 0, prev_page: 1` on an empty result set).

Empty collections return `{"<entities>": [], "meta": {...}}` — never `null`.

Defaults differ per domain: `per_page` caps at 100 almost everywhere, but quotes accept up to **500**, and supplier invoices default to **25**. Upstream quote docs describe a `total` key where the MCP layer returned `total_count` — trust the live tool output.

## Deprecated fields (still returned, don't build on them)

| Entity | Deprecated | Replacement |
|---|---|---|
| Transaction | `category` (31 legacy values) | `cashflow_category` / `cashflow_subcategory` |
| Client | root-level `address`, `city`, `zip_code`, `country_code`, `province_code`, `type` | `billing_address.*`, `kind` |
| Client invoice / quote | `performance_date` | `performance_start_date` + `performance_end_date` |
| Supplier invoice | `matched_transactions_ids` | `matched_transactions[]` objects |

## Enum & naming inconsistencies (verbatim upstream)

- Casing: supplier `attachment_category` is UPPERCASE (`INVOICE`…); payment-link `resource_type` is PascalCase (`Invoice`/`Basket`); everything else snake_case.
- Discount `type`: `percentage | absolute` on invoices vs `percentage | amount` on quotes.
- `debitor_name` (payment links) is the actual spelling.
- Client flat `country_code` is lowercase (`"fr"`); `billing_address.country_code` is UPPERCASE (`"FR"`).
- Quote/invoice item field is `vat_exemption_reason`; product field is `vat_exemption_code`.

## Files & presigned URLs

Attachments and statements embed a `file`/`url` block:

```json
{
  "file_content_type": "application/pdf",
  "file_name": "2026-06-…-statement.pdf",
  "file_size": 29687,
  "file_url": "https://qonto.s3.eu-central-1.amazonaws.com/…X-Amz-Expires=1800…"
}
```

- URLs are **short-lived presigned S3 credentials (30 min)** — treat them like passwords: never persist or log them; re-call the tool to mint a fresh one.
- ⚠️ Type inconsistency: statement `file_size` is a **number**, attachment `file_size` is a **string** (`"27965"`).
- Attachments add `probative_attachment: {"status": "unavailable" | "available" | "pending" | "corrupted"}` (PAdES-sealed probative version) and `created_at`.
- Upload flow is two-step: `request_attachment_upload(file_name, content_type[, size_bytes])` → returns presigned PUT URL + `blob_ref` → PUT raw bytes → `upload_attachment(blob_ref, …)`. Accepts PDF/JPEG/PNG ≤ 15 MB.

## Errors & permissions

- Upstream errors surface as tool errors with the HTTP status and body, e.g. `list_requests: upstream returned status=403 body={"message":"Forbidden","trace_id":"…"}`.
- **403 usually means plan- or role-gating**, not broken auth: e.g. requests/approvals need a Business or Enterprise plan (a Solo Basic org gets 403); employees see less than admins/owners. Check `get_subscription` (plan) and `get_authenticated_membership` (role) before concluding anything.
- 422 for semantic violations (e.g. passing both `ibans` and `bank_account_ids` to `list_statements`).
- Invoice creation validates the **client** at invoice time: a client that was created fine can still make `create_client_invoice` fail (e.g. missing/invalid `tax_identification_number`) → fix via `update_client`, then retry the invoice.

## Security model (SCA)

- **No tool moves money.** `create_multi_transfer_request` only creates a *pending* batch; a member with review permission approves it in the Qonto app with their own Strong Customer Authentication (2FA). `approve_request` itself is SCA-protected and acts only on expense-management requests.
- Sensitive writes (card creation, etc.) may **block while the user confirms a push notification** on their paired Qonto device. Design flows to tolerate that latency and possible user rejection.
