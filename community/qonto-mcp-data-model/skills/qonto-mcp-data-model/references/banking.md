# Banking entities

Shapes captured live (July 2026), values anonymized.

## Organization — `get_organization`

The root entity; one per OAuth token. Also the only source of `bank_accounts[].id`.

```jsonc
{
  "organization": {
    "id": "11111111-…-uuid",
    "name": "ACME INTERACTIVE",
    "legal_name": "ACME INTERACTIVE",
    "slug": "acme-corp-1234",          // for webapp deeplinks
    "locale": "fr",
    "legal_country": "FR",
    "legal_form": "SARL",
    "legal_number": "123456789…",             // SIREN/SIRET
    "legal_sector": "6201Z",                  // NAF/APE code
    "legal_share_capital": 238000,
    "legal_registration_date": "2007-11-01",
    "legal_address": "17 RUE EXEMPLE 75010 PARIS FRANCE",
    "address": {                              // structured variant
      "first_line": "17 RUE EXEMPLE", "second_line": null, "third_line": null,
      "city": "PARIS 10", "zipcode": "75010", "country": "FR", "state": null
    },
    "contract_signed_at": "2018-01-18T09:31:34.677Z",
    "bank_accounts": [ /* see below */ ]
  }
}
```

`include_external_accounts: true` also returns accounts connected from other banks (`is_external_account: true`).

### Bank account (embedded in organization)

```jsonc
{
  "id": "aaaa1111-…-uuid",                    // ← pass this to list_transactions / list_cards / list_statements
  "name": "Compte principal",
  "slug": "acme-corp-1234-bank-account-3",
  "iban": "FR7616958000010000000000000",
  "bic": "QNTOFRP1XXX",
  "currency": "EUR",
  "balance": 1234.56,                          // float euros
  "balance_cents": 123456,                     // integer cents (same value)
  "authorized_balance": 1234.56,               // balance minus holds
  "authorized_balance_cents": 123456,
  "account_number": "",
  "main": true,                                // exactly one main account
  "status": "active",                          // active | closed
  "is_external_account": false,
  "updated_at": "2026-04-01T14:23:41.375Z"
}
```

## Transaction — `list_transactions`, `get_transaction`

`list_transactions` **requires** `bank_account_id` or `iban` (call `get_organization` first) and only returns `status: "completed"` rows. Sortable/filterable by `created_at` / `updated_at` / `settled_at` / `emitted_at`.

```jsonc
{
  "id": "bbbb2222-…-uuid",                     // UUID — use for get_transaction & attachment tools
  "transaction_id": "acme-…-3-transaction-4",  // human slug — display only
  "bank_account_id": "aaaa1111-…-uuid",
  "amount": 2.26,                              // float, always positive; direction is in `side`
  "currency": "EUR",
  "local_amount": 2.26,                        // amount in local_currency (FX transactions differ)
  "local_currency": "EUR",
  "side": "debit",                             // debit | credit
  "operation_type": "qonto_fee",               // see enum below
  "status": "completed",                       // pending | declined | completed (list returns completed only)
  "subject_type": "BillingTransfer",           // polymorphic source entity, see below
  "label": "Qonto",                            // counterparty display name
  "clean_counterparty_name": null,
  "reference": "invoice-2024-001",             // payment reference / remittance info
  "note": null,                                // free-text user note
  "emitted_at":  "2024-01-03T06:27:49.169Z",
  "settled_at":  "2024-01-03T06:27:50.662Z",
  "created_at":  "2024-01-03T06:27:51.638Z",
  "settled_balance": 0,                        // account balance after settlement (float)
  "vat_amount": 0.38,                          // float; may be null/0
  "vat_rate": 20,                              // float percent
  "attachment_ids": ["cccc3333-…-uuid"],       // → get_attachment / list_transaction_attachments
  "attachment_lost": false,
  "attachment_required": true,
  "card_id": null,                             // set when operation_type = "card"
  "card_last_digits": null,
  "initiator_id": null,                        // membership UUID who initiated
  "label_ids": [],                             // custom labels → list_labels
  "cashflow_category":    {"id": "01928af2-…", "name": "Frais bancaires"},   // ⚠️ name is LOCALIZED
  "cashflow_subcategory": null,                // same {id, name} shape, nullable
  "is_external_transaction": false,
  "logo": {"small": "https://…/small.png", "medium": "https://…/medium.png"}
}
```

### Authoritative enums (upstream API docs)

- `operation_type` (20 values): `income`, `transfer`, `card`, `card_acquirer_payout`, `direct_debit`, `direct_debit_collection`, `direct_debit_hold`, `qonto_fee`, `cheque`, `recall`, `swift_income`, `pay_later`, `financing_installment`, `account_remuneration`, `f24`, `pagopa_payment`, `nrc_payment`, `riba_payment`, `investment`, `other`.
- `subject_type` (17 values): `Card`, `Transfer`, `Income`, `DirectDebit`, `DirectDebitCollection`, `DirectDebitHold`, `WalletToWallet`, `Check`, `SwiftIncome`, `PagopaPayment`, `F24Payment`, `BillingTransfer`, `FinancingIncome`, `FinancingInstallment`, `AccountRemuneration`, `Investment`, `Other`.
- `status`: `pending` | `completed` | `declined` | `reversed` — ⚠️ `reversed` exists as a field value but is not a documented filter value; the MCP list returns `completed` only.
- `side`: `debit` | `credit`. `amount` is always positive; direction lives in `side`.
- `vat_rate`: `-1` means "uncategorized or multiple VAT rates" (not an error).
- Upstream also returns `*_cents` integer twins (`amount_cents`, `local_amount_cents`, `vat_amount_cents`, `settled_balance_cents`) and a **deprecated** `category` field (31 legacy values like `restaurant_and_bar`, `office_rental`, `fallback`…) — use `cashflow_category`/`cashflow_subcategory` instead.
- ⚠️ `cashflow_category.name` came back in **French** on transactions while `list_cash_flow_categories` returned **English** names for the same ids — match by `id` only.
- `modify_transaction_cash_flow_category(transaction_id, category_id)` re-tags a transaction (pass a category **or** subcategory id).

### Nested sub-objects (presence keyed on `subject_type`; null otherwise)

The upstream API embeds a per-type detail object on each transaction:

| `subject_type` | Sub-object fields |
|---|---|
| `Transfer` / `Income` | `counterparty_account_number` (+`_format`: `IBAN`), `counterparty_bank_identifier` (+`_format`: `SWIFT_BIC`) |
| `SwiftIncome` | same 4 fields; formats `unstructured` / `sort_code` |
| `DirectDebit` / `DirectDebitCollection` | same counterparty fields + `unique_mandate_reference` |
| `DirectDebitHold` | `guarding_rate` |
| `Check` | `check_number`, `check_key` |
| `FinancingInstallment` | `total_installments_number`, `current_installment_number` |
| `PagopaPayment` | `notice_number`, `creditor_fiscal_code`, `iuv` |
| deferred-debit repayment | `period_start`, `period_end`, `capital_amount`, `accumulated_fees_amount`, `total_transactions_count` |

Upstream also supports `includes[]` = `vat_details`, `labels`, `attachments` (embeds those objects per transaction) and `side` / `operation_type[]` / `status[]` / `with_attachments` filters — **not yet exposed through the MCP tool**, whose schema only has account, date-range, sort and pagination params.

## Attachment — `get_attachment`, `list_transaction_attachments`

```jsonc
{
  "attachment": {
    "id": "cccc3333-…-uuid",
    "file_name": "12-23-invoice-14195839.pdf",
    "file_content_type": "application/pdf",
    "file_size": "27965",                      // ⚠️ STRING here (number on statements)
    "created_at": "2024-01-01T10:23:25.927Z",
    "probative_attachment": {"status": "unavailable"},  // PAdES version when "available"
    "url": "https://qonto.s3…X-Amz-Expires=1800…"       // presigned, 30 min TTL
  }
}
```

- Upload flow: `request_attachment_upload(file_name, content_type)` → PUT the bytes to the presigned URL → `upload_attachment(blob_ref, target)` with `target` = `standalone` (reusable attachment → `attachment_id`) | `transaction` (+`transaction_id`) | `supplier_invoice` (creates a supplier invoice from the file) | `client_invoice` (returns an `upload_id` for `create_client_invoice`). Optional `idempotency_key` dedupes retries.
- `remove_transaction_attachment(transaction_id, attachment_id)` removes **the link only** — the file is kept, other transactions referencing it keep their link, and `get_attachment` still resolves it. No bulk detach: call once per attachment.

## Statement — `list_statements`, `get_statement`

Monthly PDF account statements.

```jsonc
{
  "id": "019faaaa-…-uuid",
  "bank_account_id": "aaaa1111-…-uuid",
  "period": "06-2026",                         // MM-YYYY
  "file": {
    "file_name": "2026-06-…-statement.pdf",
    "file_content_type": "application/pdf",
    "file_size": 29687,                        // number here
    "file_url": "https://qonto.s3…"            // presigned, 30 min TTL
  }
}
```

⚠️ Filters `bank_account_ids` and `ibans` are mutually exclusive → 422 if both are sent.

## Cash flow categories — `list_cash_flow_categories`, `create_cash_flow_category`

Two-level tree, not paginated. Ids are UUIDv7. These are the values behind `transaction.cashflow_category` / `cashflow_subcategory`.

```jsonc
{
  "cash_flow_categories": [
    {
      "id": "01928af2-…", "name": "Sales revenue",
      "type": "CATEGORY_TYPE_INFLOW",          // CATEGORY_TYPE_INFLOW | CATEGORY_TYPE_OUTFLOW
      "subcategories": []
    },
    {
      "id": "01928af2-…", "name": "Operational expenses",
      "type": "CATEGORY_TYPE_OUTFLOW",
      "subcategories": [
        {"id": "01928af2-…", "name": "Rent"}   // no `type` — inherits parent direction
      ]
    }
  ]
}
```

`create_cash_flow_category`: top-level → pass `name` + `type`, no parent; subcategory → pass `name` + `parent_category_id`, **omit** `type`. Optional `vat_rate` as decimal string (`"20"`, `"5.5"`).

## Labels — `list_labels`, `get_label`

Custom transaction tags, one-level nesting: `{"id": uuid, "name": string, "parent_id": uuid|null}`. Referenced from `transaction.label_ids`. Read-only through MCP (no create/update tool).
