# Qonto sandbox read recipe (read-only)

Only these READ tools are needed. **Never** call a write tool during Observe or
Prepare.

| Step | MCP tool | Why | Bundle key |
|---|---|---|---|
| 1 | `get_organization` | org id, legal country, accounts | `organization` |
| 2 | `get_authenticated_membership` | who is acting (role) | `membership` |
| 3 | `get_supplier_invoice` (target id) | the invoice under review | `supplier_invoice` |
| 4 | `list_supplier_invoices` | supplier history for duplicate/amount/IBAN checks | `supplier_invoices` |

`list_requests` may return **403** on some plans — that is expected; record it as
an unavailable field rather than failing.

## Building the bundle

Assemble the raw JSON results into one file, keeping each tool's own wrapper key
(`{"organization": {…}}`, `{"supplier_invoice": {…}}`, …). The mapper unwraps
them. Add an `observed_at` timestamp.

```json
{
  "organization":     { "organization": { "...": "get_organization result" } },
  "membership":       { "membership": { "...": "get_authenticated_membership result" } },
  "supplier_invoice": { "supplier_invoice": { "...": "get_supplier_invoice result" } },
  "supplier_invoices":{ "supplier_invoices": [ "...list_supplier_invoices elements..." ] },
  "observed_at": "2026-07-12T09:00:00.000Z"
}
```

Then: `npm run pr -- map --bundle bundle.json --out evidence.json`

## Redaction

The mapper and engine mask IBANs to the last 4, mask object ids, and never store
attachment or presigned URLs. Do not paste full IBANs, emails, or temporary URLs
into chat.

## Fresh re-read for Act

Before Act, call `get_supplier_invoice` again and save the raw result to
`fresh_supplier_invoice.json`. Act compares its critical fields (amount,
currency, IBAN, supplier, status) against the sealed PR and blocks on any drift.
