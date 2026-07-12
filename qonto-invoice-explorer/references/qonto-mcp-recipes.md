# Qonto MCP recipes

Verified call patterns from a production run on a live SAS. Load when the workflow needs the exact shape of a call.

## Discover the org

`get_organization` returns `bank_accounts[]`. Take the account flagged `main`, or ask the user when several non-closed accounts exist. The bank account ID is required for every downstream call and shouldn't be re-fetched — save it in the session.

## List transactions

`list_transactions` requires `bank_account_id` (or `iban`); omitting it fails with "bank_account_id or iban is missing". Supported filters are `settled_at_from`, `settled_at_to`, `emitted_at_from`, `emitted_at_to`, `per_page` (up to 100), and `page`. The request param is `page`; the response's `meta` uses `current_page` and `next_page` — don't echo those back into the request. There's no server-side search, so vendor and label filtering happens client-side after paginating.

Response size overflows the ~30K token cap as soon as one page hits a hundred rows. The tool then writes to `.claude/projects/<project>/<session>/tool-results/mcp-qonto-list_transactions-<ts>.txt` and returns the path. `scripts/list_missing.py` handles both inline and spillover shapes.

## Get one transaction

`get_transaction` by id. The keys used downstream are `id`, `amount`, `currency`, `local_amount`, `local_currency`, `emitted_at`, `settled_at`, `label`, `clean_counterparty_name`, `side`, `operation_type`, `attachment_ids`, `attachment_required`, `attachment_lost`, and `card_last_digits`.

## Attachment upload — the three-step dance

Step one: `request_attachment_upload` with `file_name` (any string) and `content_type: "application/pdf"`. Response includes `blob_ref`, `upload_url` (S3 PUT, `X-Amz-Expires=900` = 15 minutes), and `max_size_bytes` around 15 MB. Treat 12 minutes as the safe deadline.

Step two: PUT the file bytes to `upload_url` with `Content-Type: application/pdf` exactly. Success is a `200` with an empty body; failure surfaces as an S3 XML error, most commonly `ExpiredToken` (re-request the URL) or `AccessDenied` (wrong Content-Type).

Step three: `upload_attachment` with `blob_ref`, `target: "transaction"` (singular, not "transactions"), and `transaction_id`. The response confirms upload but attachment processing is asynchronous — `list_transaction_attachments` returns empty for two to eight seconds afterward.

Batching pattern: request N URLs, PUT them in parallel via `scripts/upload_batch_put.sh`, then call `upload_attachment` N times. Keep N under six per round to stay comfortably inside the 15-minute window.

## Ghost-record countermeasure

When only a UUID prefix is at hand (from a grouped summary), never type the tail from memory. Fabricated UUIDs like `019e3cd9-ffff-7000-0000-000000000000` look plausible and reliably 404. Look up the full UUID from the local transaction JSON with `startswith(prefix)` before every `upload_attachment` call.

## Verify

`list_transaction_attachments` with `transaction_id`. Wait five seconds and retry once if the first call returns empty.

## Statements

`list_statements` paginates like `list_transactions`. Statement PDF signed URLs expire in 30 minutes rather than 15 — more forgiving. `get_statement` takes only `id`; passing `bank_account_id` returns "unexpected additional properties".

## Sensitive tools not to call

`create_multi_transfer_request`, `approve_request`, `decline_request`, `remove_transaction_attachment`, `change_supplier_invoice_status`, `mark_client_invoice_as_paid` are outside this skill's scope. They belong to other flows and moving money in particular requires the user's own SCA in the Qonto UI regardless.

## Native integrations

Amazon Business, Google Drive drop-folder, and forwarding to `receipts@<org>.qonto.com` are activated in the Qonto web UI, not via MCP. When a vendor is covered, instruct the user to enable the integration once and skip the vendor in the current run.

## Errors seen in production

`bank_account_id or iban is missing` — pass the ID from `get_organization`. `unexpected additional properties ["search" | "current_page" | "bank_account_id"]` — the filter isn't supported, or you passed `current_page` instead of `page`, or you passed `bank_account_id` to a statement call. `404 transaction not found` on `upload_attachment` — hallucinated UUID; look up the full ID. `ExpiredToken` from S3 — the 15-minute window closed; re-request. `AccessDenied` from S3 — Content-Type header is missing or wrong.
