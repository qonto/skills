# Entity catalog — everything the Qonto MCP can manage

The complete map of entity types reachable through the MCP server, with the operations available on each. ✓ = MCP tool exists; ⬆ = exists in the upstream API but **not exposed through MCP**; — = does not exist at all.

## Operations matrix

| Entity | List | Get | Create | Update | Delete | Lifecycle / actions | Reference file |
|---|---|---|---|---|---|---|---|
| **Organization** | — | ✓ `get_organization` | — | — | — | — | [banking.md](banking.md) |
| **Bank account** | ✓ (embedded in organization) | — | — | — | — | — | [banking.md](banking.md) |
| **Transaction** | ✓ (needs `bank_account_id`) | ✓ | — (bank-generated) | — | — | ✓ re-categorize (`modify_transaction_cash_flow_category`) | [banking.md](banking.md) |
| **Cash flow category** | ✓ (tree, no pagination) | — | ✓ (top-level or subcategory) | ⬆ | ⬆ | — | [banking.md](banking.md) |
| **Label** | ✓ | ✓ | ⬆ | ⬆ | ⬆ | read-only via MCP | [banking.md](banking.md) |
| **Attachment** | ✓ per transaction | ✓ | ✓ 2-step upload (presigned PUT → `upload_attachment`) | — | ✓ detach only (`remove_transaction_attachment` — the file itself is kept) | upload targets: `standalone` / `transaction` / `supplier_invoice` / `client_invoice` | [banking.md](banking.md) |
| **Statement** | ✓ | ✓ | — (monthly, bank-generated) | — | — | — | [banking.md](banking.md) |
| **Client** | ✓ (filterable) | ✓ | ✓ | ✓ PATCH semantics | ✓ **permanent** | — | [invoicing.md](invoicing.md) |
| **Client invoice** | ✓ | ✓ | ✓ | ✓ *drafts only* | ✓ *drafts only* | ✓ `finalize` / `cancel` / `unmark_as_paid`, `mark_client_invoice_as_paid`, `send_client_invoice` | [invoicing.md](invoicing.md) |
| **Credit note** | ✓ | ✓ | ✓ (linked to an invoice) | — (final on creation) | — | — | [invoicing.md](invoicing.md) |
| **Quote (devis)** | ✓ | ✓ | ✓ | ✓ (items = replace-all) | ✓ | ✓ `send_quote`; status itself is never writable (client approves via `quote_url`) | [quotes.md](quotes.md) |
| **Product** | ✓ | ⬆ | ✓ | ⬆ | ⬆ | — | [products-payment-links.md](products-payment-links.md) |
| **Payment link** | ✓ | ✓ | ✓ (Basket ⊕ Invoice variant) | — | — | ⬆ deactivate, ⬆ provider connect | [products-payment-links.md](products-payment-links.md) |
| **Supplier invoice** | ✓ | ✓ | ⬆ (multipart bulk upload) — via MCP use `upload_attachment(target: supplier_invoice)` | — | — | ✓ `reject` / `mark_as_paid` / `unmark_as_paid` (`change_supplier_invoice_status`) | [supplier-invoices.md](supplier-invoices.md) |
| **Membership** | ✓ | ✓ "me" only (`get_authenticated_membership`) | ✓ invite (`employee` / `reporting` roles only) | ⬆ (role changes happen in-app) | — | — | [team-cards-requests.md](team-cards-requests.md) |
| **Team** | ✓ | — | ✓ | ⬆ | ⬆ | — | [team-cards-requests.md](team-cards-requests.md) |
| **Card** | ✓ | — (filter the list by `ids`) | ✓ (SCA — blocks on user confirmation) | ✓ `nickname` XOR `options` | — | ✓ `lock` / `unlock` / `lost` / `stolen` / `discard`; `get_card_iframe_url` (PAN/CVV reveal) | [team-cards-requests.md](team-cards-requests.md) |
| **Request** (approval workflow) | ✓ (plan-gated: 403 on Solo) | — | ✓ `create_card_request` (flash ⊕ virtual), ✓ `create_multi_transfer_request`; ⬆ single-transfer request | — | — | ✓ `decline_request`; `approve_request` ⚠️ returns an `approval_url` deeplink — the user approves in the Qonto app with SCA | [team-cards-requests.md](team-cards-requests.md) |
| **Subscription (own plan)** | — | ✓ `get_subscription` | — | — | — | — | [team-cards-requests.md](team-cards-requests.md) |
| **Public pricing** | — | ✓ `get_qonto_public_pricing` | — | — | — | returns `{fetched_at, markdown, source}` — a **markdown snapshot** of qonto.com/pricing, not structured data; filter with `plan` / `include_addons` | [team-cards-requests.md](team-cards-requests.md) |

## Action-tool semantics (exactly-one-flag pattern)

The three `change_*_status` tools take the entity `id` plus **exactly one** action field:

| Tool | Actions | Notes |
|---|---|---|
| `change_card_status` | `lock` (reversible) / `unlock` (owners & admins only) / `lost` / `stolen` / `discard` | the last three are **permanent** |
| `change_client_invoice_status` | `finalize` (draft → unpaid, locks against update/delete) / `cancel` (unpaid → canceled, **irreversible** — for drafts use `delete_client_invoice`) / `unmark_as_paid` (paid → unpaid) | |
| `change_supplier_invoice_status` | `reject: "<note>"` (irreversible) / `mark_as_paid: "YYYY-MM-DD"` (≤ today; records out-of-band settlement — **not** proof a Qonto payment ran) / `unmark_as_paid: true` (paid → `to_review`) | |

Same pattern on `update_card`: exactly one of `nickname` or `options` (and `options` requires all four flags together, physical cards only).

## Shared value objects (no tools of their own)

| Object | Shape | Appears on |
|---|---|---|
| Money | `{value: "10.99", currency: "EUR"}` (+ `*_cents` int twins on documents) | all invoicing entities, subscription (⚠️ key `amount` there) |
| Address | `{street_address, city, zip_code, province_code?, country_code}` | client billing/delivery; org (different field names) |
| DocumentItem | title, quantity, unit, unit_price, vat_rate, discount + computed totals | invoices, credit notes, quotes |
| Discount | `{type: percentage\|absolute (invoices) / amount (quotes), value, amount…}` | documents & items |
| EmbeddedClient / EmbeddedOrganization | snapshots frozen at issuance | invoices, credit notes, quotes |
| IT/ES tax blocks | `welfare_fund`, `withholding_tax`, `payment_reporting`, `stamp_duty_amount` | invoices, credit notes, quotes |
| Pagination meta | 3 variants — see [conventions.md](conventions.md) | every list |
| File block | `{file_name, file_content_type, file_size, url}` presigned 30 min | attachments, statements |

## Not reachable through this MCP at all

No tools exist for: **beneficiaries/trusted IBANs**, **single immediate transfers** (only multi-transfer *requests*), **direct debits / SEPA mandates**, **checks**, external-account connections (read-only flag on bank accounts), insurance contracts, financing offers, or user/role administration beyond inviting employee/reporting members. And remember the global rule: **nothing here moves money** — the strongest write creates a pending request that a human approves in the Qonto app with SCA.
