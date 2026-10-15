# Qonto MCP tool inventory (sanitized)

Connection: `qonto-mcp-sandbox`, authenticated as an **owner** membership of a
synthetic sandbox org (FR SAS). Discovery was **read-only**. No write tool was
called. All live values below are masked.

## What we actually observed (read-only)

| Tool | Class | Observed shape (masked) |
|---|---|---|
| `get_authenticated_membership` | read | `{ id, role: "owner", kyc_status, locale, team_id, … }` |
| `get_organization` | read | `{ id, legal_name, legal_country: "FR", bank_accounts:[{ id, iban(FR76…768), bic, currency:"EUR", balance_cents, main:true, status:"active" }] }` |
| `list_supplier_invoices` | read | 2 invoices, both `supplier_name:"SUPPLIERONE"`, `supplier_id:0000…0000`, `iban:null`, `status:"to_review"`, `available_actions.pay:false` reason `["missing_iban"]`, amounts `1500.00` / `3200.00 EUR` |
| `get_supplier_invoice` | read | same fields + `declined_note`, `has_duplicates:false`, `matched`/`related_invoices:null`, `approval_workflow:null` |
| `list_transactions` | read | 3 `income`/`credit` txns (`completed`), counterparty IBAN + BIC, `settled_balance` |
| `get_transaction` | read | single txn, same shape |
| `list_transaction_attachments` / `get_attachment` | read | `[]` for the sampled txn; `get_attachment` yields a short-lived presigned `url` (treated as a password — never persisted) |
| `list_requests` | read | **403 Forbidden** on this org (plan-gated) |

Other **read** tools present but not required for the MVP: `get_subscription`,
`get_qonto_public_pricing`, `list_memberships`, `list_teams`, `list_cards`,
`list_clients`/`get_client`, `list_client_invoices`/`get_client_invoice`,
`list_credit_notes`/`get_credit_note`, `list_labels`/`get_label`,
`list_statements`/`get_statement`, `list_products`, `list_quotes`/`get_quote`,
`list_payment_links`/`get_payment_link`, `list_cash_flow_categories`.

## Write / sensitive tools (present, DISABLED, never called)

`create_card` · `create_card_request` · `create_client` · `create_client_invoice`
· `create_credit_note` · `create_membership` · `create_multi_transfer_request` ·
`create_payment_link` · `create_product` · `create_quote` · `create_team` ·
`create_cash_flow_category` · `update_card` · `update_client` ·
`update_client_invoice` · `update_quote` · `change_card_status` ·
`change_client_invoice_status` · `change_supplier_invoice_status` ·
`approve_request` · `decline_request` · `mark_client_invoice_as_paid` ·
`send_client_invoice` · `send_quote` · `delete_client` · `delete_client_invoice`
· `delete_quote` · `modify_transaction_cash_flow_category` ·
`remove_transaction_attachment` · `request_attachment_upload` ·
`upload_attachment`.

## Server's own boundary (verbatim from MCP instructions)

> This server cannot move money. No tool executes an outbound payment or transfer.
> The most `create_multi_transfer_request` can do is create a **pending** transfer
> request; a member with review permission must then approve it on Qonto with
> their own SCA (2FA). `approve_request` does **not** approve anything — it returns
> an approval deeplink.

This aligns exactly with Finance PR's thesis: the MCP already refuses to move
money, and Finance PR adds the *pre-Qonto* review the MCP cannot perform.

## Frozen MVP write decision

- **No tool** promotes a supplier invoice into a payment request / native approval
  workflow. The sampled invoices are additionally unpayable (`iban:null`,
  `pay:false` / `missing_iban`).
- `create_multi_transfer_request` is the only tool that reaches a Qonto approval
  workflow, and it only ever creates a **pending** request still gated by the
  user's own SCA. `list_requests` is 403 here, so even reading that workflow is
  unavailable on this plan.

**Decision: Act terminates at a verified `ready_for_qonto` handoff; all Qonto
writes are disabled by default.** The engine exposes a single allowlisted write
seam (`WriteAdapter`) whose default (`DisabledWriteAdapter`) performs no tool
call. Enabling a real write requires an explicit build flag **and** an explicit,
per-object user confirmation of the exact PR id, fingerprint, action, and target
(see `docs/KNOWN_LIMITATIONS.md`). We never invent an endpoint or fake a result.

## Redaction rules applied everywhere (UI, logs, fixtures, prompts)

IBAN → last 4 only; org/membership/object UUIDs → short masked form; emails,
names, phone → aliases; attachment/presigned URLs and tokens → never persisted.
Full IBAN is kept only transiently where a real execution would strictly require
it (not in the hashed PR body, which stores only a salted digest + last 4).
