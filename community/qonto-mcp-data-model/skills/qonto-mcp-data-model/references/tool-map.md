# Tool map

The ~60 Qonto MCP tools, grouped by domain. **Bold** = requires an id produced by another tool (dependency noted). Tool names appear with their short form; on the server they are prefixed (e.g. `mcp__claude_ai_Qonto__get_organization`).

## Identity & account context (start here)

| Tool | Kind | Notes |
|---|---|---|
| `get_organization` | read | Org identity + `bank_accounts[]` (ids, IBANs, balances). Source of `bank_account_id` for most banking tools. `include_external_accounts` opt-in. |
| `get_authenticated_membership` | read | "Me": role, kyc_status, team_id. |
| `get_subscription` | read | Org's own plan — check before plan-gated features. |
| `get_qonto_public_pricing` | read | Public price list of all plans. |

## Transactions & categorization

| Tool | Kind | Notes |
|---|---|---|
| **`list_transactions`** | read | Requires `bank_account_id` or `iban` ← `get_organization`. Completed only. Date filters ×4 clocks. |
| **`get_transaction`** | read | By transaction UUID (`id`, not `transaction_id` slug). |
| `list_cash_flow_categories` | read | Category tree (inflow/outflow), UUIDv7 ids. |
| `create_cash_flow_category` | write | Top-level: `name`+`type`; subcategory: `name`+`parent_category_id` (no `type`). |
| **`modify_transaction_cash_flow_category`** | write | transaction id ← list/get_transactions; category id ← list_cash_flow_categories. |
| `list_labels` / **`get_label`** | read | Custom tags referenced by `transaction.label_ids`. |

## Attachments (receipts / proof documents)

| Tool | Kind | Notes |
|---|---|---|
| `request_attachment_upload` | write (step 1) | Returns presigned PUT URL + `blob_ref`. PDF/JPEG/PNG ≤ 15 MB. |
| **`upload_attachment`** | write (step 2) | Pushes the uploaded blob (`blob_ref`) to Qonto. |
| **`get_attachment`** | read | By attachment UUID ← `transaction.attachment_ids`. 30-min presigned `url`. |
| **`list_transaction_attachments`** | read | All attachments of one transaction. |
| **`remove_transaction_attachment`** | write | Detach from a transaction. |

## Statements

| Tool | Kind | Notes |
|---|---|---|
| `list_statements` | read | Monthly PDFs; `period` MM-YYYY; `bank_account_ids` ⊕ `ibans` (422 if both). |
| **`get_statement`** | read | One statement by id. |

## Invoicing — clients & documents

| Tool | Kind | Notes |
|---|---|---|
| `list_clients` / **`get_client`** | read | Filter on email/name/TIN/VAT. Dedupe here before creating. |
| `create_client` | write | oneOf on `kind`; invoicing needs currency+locale+billing_address. |
| **`update_client`** / **`delete_client`** | write | Fix validation issues surfaced at invoice time via update. |
| **`create_client_invoice`** | write | Needs `client_id`. Required: currency, issue_date, due_date, items, payment_methods (Qonto IBAN). Set `status` explicitly. |
| `list_client_invoices` / **`get_client_invoice`** | read | Status: draft/unpaid/paid/canceled. |
| **`update_client_invoice`** / **`delete_client_invoice`** | write | Drafts mostly. |
| **`change_client_invoice_status`** | write | e.g. `finalize: true` (draft→unpaid), cancel. |
| **`mark_client_invoice_as_paid`** | write | Terminal happy-path status. |
| **`send_client_invoice`** | write | Emails the invoice to the client. |
| **`create_credit_note`** | write | Needs `invoice_id`; same currency; positive quantities (negated upstream). |
| `list_credit_notes` / **`get_credit_note`** | read | |
| **`create_quote`** | write | Needs `client_id` (create-only); required: currency, issue_date, expiry_date, items, terms_and_conditions. ⚠️ item vat_rate in **percent** (`"20"`). |
| `list_quotes` / **`get_quote`** / **`update_quote`** / **`delete_quote`** / **`send_quote`** | read/write | Status pending_approval/approved/canceled — never writable via API (client approves on `quote_url`). `update_quote` replaces `items` wholesale. |
| `list_products` | read | Catalog for `items[].product_id`. (`get_product`/`delete_product` not wired yet.) |
| `create_product` | write | title, type good/service, unit_price {value,currency}, vat_rate "0.2". |
| `create_payment_link` | write | Basket variant (items) ⊕ invoice variant (`invoice_id`). |
| `list_payment_links` / **`get_payment_link`** | read | get also returns payments received. |

## Supplier invoices (accounts payable)

| Tool | Kind | Notes |
|---|---|---|
| `list_supplier_invoices` | read | Full-text `query`; status filter client-side (not exposed yet). |
| **`get_supplier_invoice`** | read | |
| **`change_supplier_invoice_status`** | write | Lifecycle actions. |

## Team & members

| Tool | Kind | Notes |
|---|---|---|
| `list_memberships` | read | Everyone with access. |
| `list_teams` | read | Source of `team_id`. |
| `create_team` | write | Returns id+name. |
| **`create_membership`** | write | Invite by email; roles employee/reporting only; `team_id` de-facto required. |

## Cards

| Tool | Kind | Notes |
|---|---|---|
| `list_cards` | read | Filterable by holder/account/level/status; text `query`. |
| **`create_card`** | write, SCA | Variant by `card_level`; blocks on user 2FA confirmation. |
| **`update_card`** | write | Limits, options, nickname. |
| **`change_card_status`** | write | Pause / unlock / lost / stolen…  |
| **`get_card_iframe_url`** | read | Secure iframe to reveal PAN/PIN. |

## Requests (approval workflow — Business/Enterprise plans only, 403 otherwise)

| Tool | Kind | Notes |
|---|---|---|
| `list_requests` | read | Role-scoped visibility; filter by type/status. |
| `create_card_request` | write | Exactly one of `flash` ⊕ `virtual`. |
| `create_multi_transfer_request` | write | 1–400 SEPA transfers, pending until human SCA approval. **Never executes money by itself.** |
| **`approve_request`** | read-ish | ⚠️ Does NOT approve: returns an `approval_url` deeplink; the user approves in the Qonto app with SCA. Plural request_type (`transfers`…). |
| **`decline_request`** | write | Declines directly; `declined_note` required. |

## Suggested first calls for any new session

```
get_organization          → org id, bank_account ids, slug
get_authenticated_membership → my role (owner/admin/…)
get_subscription          → plan (gates requests & card category restrictions)
```
