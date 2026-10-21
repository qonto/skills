# Clients, client invoices & credit notes

Issued (receivable) documents. Money in this domain is **decimal-string amount objects** (`{"value": "12.52", "currency": "EUR"}`) with an integer `*_cents` twin on computed totals. Rates are **fraction strings** (`"0.1"` = 10 %).

Related files: [quotes.md](quotes.md) (devis), [products-payment-links.md](products-payment-links.md), [supplier-invoices.md](supplier-invoices.md).

## Client — `list_clients`, `get_client`, `create_client`, `update_client`, `delete_client`

A counterparty you bill. Discriminated on `kind` (legacy alias `type`; `kind` wins if both sent):

| `kind` | Required identity fields | Notes |
|---|---|---|
| `individual` | `first_name`, `last_name` | physical person |
| `company` | `name` | legal entity |
| `freelancer` | `first_name`, `last_name` | **Italian orgs only** |

Fields accepted by `create_client` (also read back, plus `id` and timestamps):

```jsonc
{
  "kind": "company",
  "name": "ACME GmbH",
  "email": "billing@acme.example",
  "extra_emails": ["cc@acme.example"],   // send recipients, not printed on docs
  "currency": "EUR",                     // REQUIRED for invoicing — becomes the invoice currency
  "locale": "FR",                        // document language: fr/en/it/de/es — REQUIRED for invoicing
  "tax_identification_number": "…",      // FR: SIREN(9)/SIRET(14); IT: Codice Fiscale; ES: NIF/CIF; DE: Steuernummer
  "vat_number": "FR12345678901",         // FR format: FR + 2-char key + 9-digit SIREN
  "billing_address": {                   // REQUIRED for invoicing
    "street_address": "123 Main Street", // ≤250
    "city": "Paris",                     // ≤50
    "zip_code": "75009",                 // ≤20
    "country_code": "FR",                // ISO 3166, UPPERCASE here
    "province_code": null                // Italian orgs only (2 chars)
  },
  "delivery_address": { /* same shape */ },
  "phone": {"country_code": "+33", "number": "123456789"},
  "e_invoicing_address": "987654321",    // FR orgs: SIREN[_SIRET[_routingCode]] — must exist in the Annuaire
  "recipient_code": null                 // IT orgs: SDI codice destinatario
}
```

- ⚠️ Root-level `address`/`city`/`zip_code`/`country_code`/`province_code` are **deprecated** duplicates of `billing_address.*`.
- ⚠️ In responses, the flat `country_code` is **lowercase** (`"fr"`) while `billing_address.country_code` is **UPPERCASE** (`"FR"`).
- ⚠️ **No uniqueness upstream** — `list_clients(filter: {email | name | tax_identification_number | vat_number})` and dedupe before creating. `name` is partial + accent-insensitive (min 2 chars); the others exact, case-insensitive.
- Client validation is **deferred to invoice time**: `create_client_invoice` can fail on a bad TIN → `update_client`, retry.

## Client invoice — full response object

Wrapped as `{"client_invoice": {...}}` (get) or `{"client_invoices": [...], "meta": {...}}` (list).

```jsonc
{
  "id": "uuid", "organization_id": "uuid",
  "number": "INV-001",
  "status": "unpaid",                          // draft | unpaid | paid | canceled
  "invoice_type": "standard",                  // standard | deposit | balance (progress invoicing)
  "quote_id": null,                            // source quote when converted from one
  "attachment_id": "uuid|null",                // the PDF — generated ASYNC (~10 s after create); fetch via get_attachment
  "invoice_url": "https://pay.qonto.com/invoices/<uuid>",  // public page, no auth, valid 180 days, dead once canceled
  "contact_email": "owner@org.example",
  "currency": "EUR",
  "total_amount": {"value": "12.52", "currency": "EUR"}, "total_amount_cents": 1252,
  "vat_amount":   {"value": "0.51",  "currency": "EUR"}, "vat_amount_cents": 51,
  "amount_paid":  {"value": "12.52", "currency": "EUR"}, // ⚠️ "0.00" if marked paid manually (no linked transaction)
  "discount": {"type": "percentage",           // percentage | absolute
               "value": "0.1",                 // fraction string (percentage: 0.0001–1)
               "amount": {"value": "10.00", "currency": "EUR"}},  // computed
  "issue_date": "2026-03-01", "due_date": "2026-03-31",   // due_date ≥ issue_date (422 otherwise)
  "performance_start_date": null, "performance_end_date": null,  // (`performance_date` deprecated)
  "created_at": "…", "finalized_at": "…",      // finalized_at set on draft → unpaid
  "paid_at": null,
  "purchase_order": null, "header": null, "footer": null, "terms_and_conditions": null,
  "discount_conditions": null,                 // FR only ┐
  "late_payment_penalties": null,              // FR only │ legal mentions
  "legal_fixed_compensation": null,            // FR only ┘
  "items": [ /* DocumentItem, below */ ],
  "client": { /* embedded client snapshot */ },
  "organization": { /* org snapshot at issuance: legal_name, legal_number, addresses,
                       vat_number, tax_number, commercial_register_number (RCS/HRB),
                       district_court + company_leadership (DE), legal_capital_share,
                       transaction_type, vat_payment_condition (FR) */ },
  "payment_methods": [                         // ⚠️ ARRAY in responses (object in create!)
    {"type": "transfer", "iban": "FR76…", "bic": "…", "beneficiary_name": "…"}
  ],
  "credit_notes_ids": ["uuid"],                // linked credit notes
  "einvoicing_status": "pending",              // pending | submitted | declined | approved | not_delivered | submission_failed
  "einvoicing_lifecycle_events": [             // French e-invoicing/e-reporting trail
    {"status_code": 200, "reason": null, "reason_message": null, "timestamp": "…"}
    // codes 200–214: 200 Déposée/Submitted, 205 Approuvée, 207 En litige, 210 Refusée, 211 Paiement transmis, 213 Rejetée, 214 Visée…
  ],
  // Italian / Spanish specifics (null elsewhere):
  "welfare_fund": {"type": "TC01", "rate": "0.04"},                       // TC01–TC22
  "withholding_tax": {"reason": "RF01", "rate": "0.20", "payment_reason": "A1", "amount": "1.00"},  // reason RF01–RF06; amount computed
  "payment_reporting": {"conditions": "TP01", "method": "MP01"},          // TP01–TP03; MP01–MP22
  "stamp_duty_amount": null
}
```

### DocumentItem (shared with credit notes & quotes)

| Field | Type | Notes |
|---|---|---|
| `title` | string | ≤40 chars — **required** |
| `description` | string? | ≤1800 chars |
| `quantity` | decimal string | `"1.5"`, period separator — **required** |
| `unit` | string? | ≤20 chars (10 for IT XML); FR EN16931 codes: `unit`(C62), `hour`(HUR), `day`(DAY), `month`(MON), `gram`, `kilogram`, `liter`, `meter`, `square_meter`, `cubic_meter`, `kilowatt_hour`… |
| `unit_price` | `{value, currency}` | **required**; ⚠️ `currency` is **EUR-only today** |
| `vat_rate` | decimal string | fraction: `"0.1"` = 10 % — **required** |
| `vat_exemption_reason` | enum? | required (IT) when vat_rate = "0"; N-codes N1–N7 (+ N2.1, N3.1–N3.6, N6.1–N6.9…) |
| `discount` | object? | `{type: percentage\|absolute, value}`; absolute max = quantity × unit_price |
| computed in responses | | `subtotal`(+`_cents`), `total_vat`(+`_cents`), `total_amount`(+`_cents`), `unit_price_cents`, `discount.amount` |

### `create_client_invoice` — key facts

Required: `client_id`, `currency` (must match the client's; ~28 currencies documented but item `unit_price` is EUR-only), `issue_date`, `due_date`, `items[]` (min 1), `payment_methods` **as an object** `{"iban": "FR76…"}` — the IBAN must belong to a Qonto account of this org.

- `status`: `draft` (editable) or `unpaid` (finalizes immediately: sets `finalized_at`, allocates number, generates PDF). Upstream default is `unpaid` — **set it explicitly**.
- `number`: required if auto-numbering disabled; 409 `invoice_number_already_exists` on duplicates.
- `quote_id` links the invoice to an existing quote. `upload_id` attaches a pre-uploaded file.
- `settings` overrides org display fields for this one document (vat_number, legal_capital_share, transaction_type FR, district_court DE…).
- Italian orgs must have e-invoicing activated to use this endpoint at all.

### Lifecycle & actions

```
draft ──(finalize / status=unpaid)──> unpaid ──(mark_client_invoice_as_paid | matched payment)──> paid
                                        └──(credit notes total == invoice total)──> canceled  [terminal]
```

- `mark_client_invoice_as_paid(paid_at?)`: `paid_at` ≤ today, defaults to today; calling on an already-`paid` invoice just updates `paid_at`.
- `send_client_invoice`: `send_to[]` (required), `email_title` (required), `email_body?`, `copy_to_self?` (default true). Returns 204, no body.
- `change_client_invoice_status(id, <action>: true)` — exactly one of: `finalize` (draft → unpaid; locks against update/delete), `cancel` (unpaid → canceled, **irreversible** — for drafts use `delete_client_invoice` instead), `unmark_as_paid` (paid → unpaid; undoes mark-as-paid).
- `update_client_invoice` / `delete_client_invoice` work on **drafts only** — finalized/paid/canceled invoices reject both.
- `delete_client` is **permanent**: recurring invoices attached to the client are auto-canceled; already-issued invoices keep displaying the client's data.
- List filters: `filter_status` (comma-separable), created_at/updated_at ranges, `filter_due_date[_from|_to]`, `exclude_imported` (default **true** — imported invoices hidden unless set to false).

## Credit note — `list_credit_notes`, `get_credit_note`, `create_credit_note`

Refund counter-document linked to an invoice. **No status of its own** — final on creation (`finalized_at`).

Response deltas vs invoice: has `invoice_id` + `invoice_issue_date`; has **no** `status`, `due_date`, `payment_methods`, `organization`, `quote_id`, `invoice_type`, `amount_paid`/`paid_at`, performance dates. Shares: `number`, `attachment_id` (async PDF), `invoice_url` (180 days), `total_amount`/`vat_amount` (+cents), `items[]`, `client`, `einvoicing_status` + events, IT/ES tax blocks.

`create_credit_note` required: `invoice_id`, `currency` (= invoice's), `issue_date`, `items[]`, `reason` (≤500 chars).

Business rules:
- Item quantities sent **positive**; the server negates them.
- Cumulative credit-note total ≤ invoice total; **reaching equality auto-cancels the invoice**.
- Not allowed on partial (deposit/balance) invoices.
- With auto-numbering enabled, a supplied `number` still overrides the generated one.

## Quirks recap

- `payment_methods`: **object** in create, **array** in responses.
- Amount `value` strings are not normalized to 2 decimals (`"10.0"`, `"120"` both appear).
- `amount_paid` is `"0.00"` for manually-marked invoices (and transactions linked before 2026-01-01).
- The PDF (`attachment_id`) appears ~10 s after creation — poll `get_client_invoice`, then `get_attachment`.
- FR-only fields: `discount_conditions`, `late_payment_penalties`, `legal_fixed_compensation`, `legal_capital_share`, `transaction_type`, `vat_payment_condition`. DE: `district_court`, `company_leadership`, `commercial_register_number`. IT: `welfare_fund`, `payment_reporting`, `stamp_duty_amount`, `report_einvoicing`, `recipient_code`, `province_code`, `vat_exemption_reason`. IT + ES freelancers: `withholding_tax`.
