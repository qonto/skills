# Messaging modality

Loaded when the vendor sends invoices through WhatsApp or LinkedIn DM rather than email. Unipile proxies both if the user has connected the accounts.

## WhatsApp has no history backfill

When Unipile connects to a WhatsApp account through a QR scan, it starts observing messages from that moment onward. WhatsApp's protocol doesn't expose historical chats to API clients. In production, a freshly connected WhatsApp business number showed only post-connection messages in existing group chats and zero messages in DMs with foreign suppliers. Historical PIs from months earlier were unreachable.

When history matters the only workarounds are asking the user to run WhatsApp's built-in "Export chat" from the phone (which includes media), asking the supplier to resend the PI by email, or having the user screenshot and AirDrop individual messages.

LinkedIn is different — Unipile fully proxies LinkedIn's messaging API and past DMs are accessible without preconditions.

## API calls

`GET /api/v1/chats?account_id={acc}&limit=250` paginates on a cursor and lists the chats. Each chat carries `id`, `name` (contact or group name), and `provider_id` (WhatsApp uses `<phone>@s.whatsapp.net` for DMs and something ending in `@g.us` for group chats; LinkedIn uses an internal ID). `GET /api/v1/chats/{chat_id}/messages?limit=250` paginates the messages. A message with an attachment carries `attachments[]` with `id`, `type`, `file_name`, and `mime`.

Attachment download uses the same endpoint as email: `GET /api/v1/emails/{message_id}/attachments/{attachment_id}` with `X-API-KEY`. Yes, the path says `emails/` even for chat attachments — API quirk, not a mistake.

## Broker chats

Some brokers use one WhatsApp business number to serve several end-clients, which means their outgoing PIs may reference multiple factories or beneficiaries in the filename or accompanying text. Match by the internal reference field of the PI, not by the sender's identity.

## Broker export naming

Broker-exported chats often follow a canonical filename like `<PREFIX>-<CLIENT-CODE>-YYYYMMDD-<seq>-<description>-<amount><CCY>.pdf` — for example `PI-ACME-20260310-001-bot-design-500EUR.pdf`. The filename alone carries date, sequence, and amount, so the match can happen without opening the PDF:

```python
import re
m = re.match(r"[A-Z]+-[A-Z]+-(\d{8})-(\d+)-([\w-]+?)-(\d+)(EUR|USD|GBP|CNY|HKD)", filename)
if m:
    date, seq, desc, amt, ccy = m.groups()
```

Factory-direct PIs use vendor-specific reference schemes; those need PDF extraction rather than filename parsing.

## `.xls` proformas

Some suppliers send PIs as legacy Excel `.xls` (Composite Document File V2, Office 97-2003) instead of PDF. `pdftotext` fails; `xlrd` reads the sheet. A typical broker layout puts the ref number at row 6 column 6, the date at row 7 column 6 (Excel serial), and the amount at row 12 column 6. Decode Excel serials with `datetime(1899,12,30) + timedelta(days=int(v))`.

Brokers commonly reuse filenames when resending, so the internal `Ref. no.` and `Date of Issued` inside the sheet are the source of truth, not the filename. Convert to PDF with `fpdf` before uploading so the accountant gets a readable document.

## Fall back to local

When Unipile can't reach the chat (historical WhatsApp, disconnected account, blocked policy), the fallback is the local modality: ask the user to AirDrop the PDFs into a folder and switch flow.
