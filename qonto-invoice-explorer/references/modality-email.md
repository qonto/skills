# Email modality (Unipile)

Unipile aggregates Google OAuth, Outlook, and IMAP mailboxes behind a single API. This file covers how to search and download invoice PDFs across them.

## Setup

`.env` needs `UNIPILE_DSN=<host>:<port>` and `UNIPILE_API_KEY=<uuid>`. List accounts once at the start of the phase with `GET /api/v1/accounts`; the response gives each account's `id`, `type` (`GOOGLE_OAUTH` / `OUTLOOK` / `IMAP` / `LINKEDIN` / `WHATSAPP`), and `name` (the email or handle). Match accounts by name, never hardcode IDs — Unipile changes them when an account is deleted and re-added.

## Search filters

The `/api/v1/emails` endpoint accepts `account_id` (required), `from` (exact from address), `any_email` (substring match against sender or recipient — useful when a vendor uses several senders), `subject` (substring), `has_attachments=true`, `limit` (default around 50, max around 200), and `after`/`before` for date bounds. There's no `q=` free-text search — or rather it exists but returns unrelated recent messages and is useless in practice.

URL-encode `+` as `%2B` in addresses like `invoice+statements@lovable.dev`, or use `--data-urlencode` in curl. Untouched `+` gets parsed as a space and the search returns nothing.

The developer docs URL for this endpoint (`developer.unipile.com/reference/emailing`) 404s as of mid-2026, so the filter set above is empirical. Update it if Unipile publishes a schema.

## Download

`GET /api/v1/emails/{email_id}/attachments/{attachment_id}` with the `X-API-KEY` header returns raw bytes. Sanity-check that the first four bytes are `%PDF` before writing to disk; if not, the vendor sent an HTML receipt or the ID was wrong.

## Multi-tenant mailbox scope

Founders often connect Unipile mailboxes belonging to other legal entities on the same install — a side project, a previous role, a spouse's business. Before running any vendor search, ask the user to tag each mailbox `IN_SCOPE` or `OUT_OF_SCOPE` for the target org and exclude out-of-scope accounts from the loop. Every false vendor match in the production run traced back to a missing scope filter.

## 404 on Google Workspace individual GETs

Some Google Workspace accounts return search results correctly but 404 on `GET /api/v1/emails/{id}` for the individual message. The cause is a Workspace admin policy blocking Unipile's per-message read; it persists across a full delete-and-re-add. Don't retry. The workaround is to forward the emails to a personal Gmail or use the Gmail web UI directly.

## Invoice vs Receipt

Stripe-hosted flows send both an `Invoice-*.pdf` and a `Receipt-*.pdf` for the same charge. French compta requires the Invoice (SIREN, VAT number); when both are present, keep the Invoice. When only a Receipt exists, keep it — better than nothing.

## Rate limits

Unipile allows about one request per second per account. Bursts of five or more parallel calls will 429. `time.sleep(1)` between calls or a small concurrency limiter is enough.

## Sample call

```python
import urllib.request, json

def unipile_get(path, key, dsn):
    req = urllib.request.Request(
        f"https://{dsn}/api/v1{path}",
        headers={"X-API-KEY": key, "accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())

emails = unipile_get(
    f"/emails?account_id={acc_id}&limit=50&from=invoice%2Bstatements@mail.fiverr.com",
    UNIPILE_KEY, UNIPILE_DSN,
)
for e in emails.get("items", []):
    for a in e.get("attachments") or []:
        if (a.get("mime") or "").startswith("application/pdf"):
            # download via /emails/{e['id']}/attachments/{a['id']}
            pass
```
