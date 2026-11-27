# Qonto MCP tools: mapping, parameters and quirks

## Calls used by this skill

| Purpose | Tool | Notes |
|---|---|---|
| Country, locale | `get_organization` | `legal_country` selects the counterparty dictionary and tax calendar |
| Accounts and balances | `list_bank_accounts` | Includes closed accounts (`status: closed`). Keep every IBAN for internal-transfer detection |
| Category tree | `list_cash_flow_categories` | Returns top-level categories with `type` (INFLOW / OUTFLOW) and leaf `subcategories`. Names are localised: match on IDs |
| Transactions | `list_transactions` | One account per call (`bank_account_id`). Paginate until `next_page` is null. `includes: ["labels"]` adds labels |
| One transaction | `get_transaction` | Use `includes: "vat_details"` when VAT split matters |
| Client invoices | `list_client_invoices` | Use `exclude_imported: false` for full coverage, sort by issue date. Paid ones (`filter_status: ["paid"]`) carry `issue_date`, `due_date`, `paid_at`, `invoice_type`: the basis for measured DSO |
| Supplier invoices | `list_supplier_invoices` | Use `filter_exclude_credit_notes: true` and `per_page: 100`. Query unpaid statuses (`to_review`, `to_approve`, `awaiting_payment`, `scheduled`, `pending`) one call each for outstanding payables. Paid ones (`filter_status: paid`) carry `issue_date`, `due_date`, `payment_date` and sometimes `matched_transactions`: the basis for measured DPO |
| Credit notes | `list_credit_notes` | Net them off client invoices |
| Clients | `list_clients`, `get_client` | Names for matching transaction counterparties to invoices |
| Labels | `list_labels` | Customer's own tags; can reveal project or cost-centre structure |
| Pending requests | `list_requests` | Pending transfer requests are near-term outflows |
| Cards | `list_cards` | Use `statuses: ["live"]`. `card_type: "flex"` signals a Flex (deferred debit) card. Card holder helps identify personal vs business spend |
| Plan | `get_subscription` | Plan name drives which products and features are available |
| Pay Later usage | Transactions labelled "Qonto Pay Later" | See `qonto-financing.md`. `list_supplier_invoices` with `filter_source: pay_later` can return nothing even when Pay Later is used |
| Financing terms | `get_qonto_public_pricing` | `include_addons: true` for financing products and current terms |
| Create category | `create_cash_flow_category` | Only after the owner says yes. Subcategory: pass `parent_category_id`, not `type` |
| Assign category | `modify_transaction_cash_flow_category` | `assign: {category_id, transaction_ids}`, up to 100 IDs, leaf ID required if the parent has subcategories. Only after the owner says yes |

## Transaction fields that matter

- `side`: credit (in) or debit (out). `amount` is always positive.
- `operation_type`: `income` (incoming transfer), `transfer` (outgoing transfer), `card`, `direct_debit`, `qonto_fee`, `swift_income`, `cheque`, `financing_installment` (Flex card settlement, with a `deferred_debit_card_repayment` block), and others. Pay Later uses ordinary `income` and `direct_debit` types; see `qonto-financing.md`. Treat unknown values as unclassified rather than guessing.
- `label`: counterparty as shown in the app. `clean_counterparty_name`: normalised counterparty when available; prefer it.
- `reference` and `note`: free text from the payer or the customer. Useful for transfers. **Unreliable for card payments** (card references are often unrelated to the merchant); use `label` for cards.
- `income.counterparty_account_number` / `transfer.counterparty_account_number`: counterparty IBAN. Match against the customer's own IBANs to detect internal transfers.
- `cashflow_category` / `cashflow_subcategory`: existing categorisation, may be null.
- `vat_amount`, `vat_rate`: present on some transactions; useful to split VAT out of revenue.
- `settled_at`: use for cash timing. `settled_balance`: balance after the transaction, sometimes null.
- `card_id`, `initiator_id`: who spent, useful for personal-spend questions.
- `attachment_ids`: an attached receipt or invoice can help confirm a category.

## Data-cleaning rules

- **Duplicates**: same account, amount, counterparty and settlement date within a few minutes, especially when `transaction_id` is empty or `local_amount` is 0 while `amount` is not. Keep one, report how many were removed.
- **Null balances**: rebuild running balance from the current `balance` backwards using signed amounts.
- **Closed accounts**: include their history; exclude them from current liquidity.
- **Multi-account**: a transfer between two of the customer's accounts appears twice (debit on one, credit on the other). Exclude both legs from inflows and outflows.

## Known issues

- **One unreadable transaction breaks every page that contains it.** `list_transactions` then returns 503 ("mandatory transaction subject could not be loaded") or 500 for any request covering that record, and retrying does not help. When a page fails twice:
  1. Switch to date windows with `settled_at_from` / `settled_at_to`, one month at a time.
  2. Split a failing window in halves until each failing window is a few days long, and every other window has loaded.
  3. Record the unreadable windows, and report the share of transactions loaded (compare with `meta.total_count` of the first page).
  4. Rebuild what is missing from recurring patterns (same counterparty, same day of month) and label it as rebuilt.
- Never filter on `operation_type`; it has triggered the same errors. Fetch without it and filter locally.
- Closed accounts can return 404 on `list_transactions`. Note it and continue; their balance is already 0.
- If `authorized_balance` is lower than `balance` and there are no pending transactions, start the forecast from `authorized_balance` and flag the unexplained difference.
- No endpoint exposes overdraft limits, Pay Later limits or eligibility. Use data signals plus the owner question (see `qonto-financing.md`).
- Monthly statements may be empty for some organisations; do not depend on them.
- In HTML artefacts, do date arithmetic with `T12:00:00Z` and `setUTCDate()`. Using `T00:00:00` with Paris time zones has caused infinite loops. The simulator template already does this.
