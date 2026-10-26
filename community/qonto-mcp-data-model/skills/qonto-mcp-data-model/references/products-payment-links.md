# Products & payment links

## Product — `list_products`, `create_product`

Reusable catalog entry referenced from invoice/quote/credit-note items via `product_id`.

| Field | Type | Notes |
|---|---|---|
| `id`, `organization_id` | uuid | |
| `title` | string | ≤120 chars — **required** |
| `description` | string? | ≤600 chars |
| `internal_note` | string? | ≤50 000 chars, never client-visible |
| `type` | enum | `good` \| `service` — **required** |
| `unit_price` | `{value, currency}` | decimal string — **required** |
| `vat_rate` | decimal string | **fraction**: `"0.2"` = 20 % — **required** |
| `unit` | string? | free text (`"hour"`, `"kilogram"`) |
| `vat_exemption_code` | enum? | IT codes `N1`–`N7` (+ dotted variants), plus S-codes (`S4`, `S13B`, `S20`…); **required for IT orgs when vat_rate is 0** |
| `links` | array? | `{title, url}` — both required per item |
| `created_at`, `updated_at` | datetime | |

Upstream list supports `sort_by` (`title:asc` default, `created_at:…`) and `filter[type]`.
⚠️ `get_product` / `delete_product` exist upstream but are **not wired into MCP** — filter `list_products` client-side.

## Payment link — `list_payment_links`, `get_payment_link`, `create_payment_link`

Hosted checkout page (`https://pay.qonto.com/{uuid}?resource_id={uuid}`).

### Status & lifecycle

`open` → `processing` → `paid`; terminal alternatives: `expired`, `canceled`.
(Upstream also has *deactivate* — sets `canceled` — and *connect* — provider onboarding; **neither is exposed through MCP**. Payment links only work once the org has completed the provider connection: status `not_connected` → `pending` → `enabled`.)

### Response object

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | |
| `status` | enum | `open`, `processing`, `paid`, `expired`, `canceled` |
| `url` | string | shareable checkout URL |
| `expiration_date` | datetime | |
| `amount` | `{value, currency}` | **gross, VAT included** |
| `potential_payment_methods` | array | `credit_card`, `apple_pay`, `paypal`, `ideal` |
| `resource_type` | enum ⚠️ PascalCase | `Invoice` \| `Basket` |
| `reusable` | bool | can accept multiple payments |
| `items` | array \| null | Basket links only; null for Invoice links |
| `invoice_id`, `invoice_number`, `debitor_name` | ?  | Invoice links only (spelling is `debitor_`, sic) |
| `created_at` | datetime | |

Item shape: `{title, type: good|service, description, quantity (number ⚠️ double, not string), measure_unit, unit_price: {value, currency}, vat_rate}` — ⚠️ `vat_rate` here is a **percentage string** (`"21.0"` = 21 %), unlike everywhere else in invoicing (fractions).

⚠️ `get_payment_link` does **not** return the individual payments — only `status` reflects payment state.

### `create_payment_link` — two variants (oneOf)

```jsonc
// Basket
{"payment_link": {
  "items": [{"title": "Widget", "quantity": 2,
             "unit_price": {"value": "10.99", "currency": "EUR"},   // max 2 decimals
             "vat_rate": "21.0", "type": "good"}],                  // percentage scale!
  "reusable": false,
  "potential_payment_methods": ["credit_card"]}}                    // min 1

// Invoice (always non-reusable)
{"payment_link": {
  "invoice_id": "uuid", "invoice_number": "INV-2026-001",
  "debitor_name": "Acme SARL",
  "amount": {"value": "250.00", "currency": "EUR"},
  "potential_payment_methods": ["credit_card", "paypal"]}}
```

List filter quirk: upstream uses bare `status[]` (not `filter[status]`); sortable by `amount` / `expiration_date`.
