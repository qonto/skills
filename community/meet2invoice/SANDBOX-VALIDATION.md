# Qonto Sandbox Validation Guide for Meet2Invoice

**Date:** 2026-07-11  
**Purpose:** Validate the exact write chain the skill uses, via the Qonto MCP.

## ✅ VALIDATION RESULTS — 2026-07-12 (via sandbox MCP, live)

Run against org `gmail-75182e66` (id `bbe3ffce-a155-461e-a0cc-81b80d0b9c2b`),
bank account `019f5587-2935-7d80-b77c-104f5b313580`,
IBAN `FR7616958000016654632896978`, role: owner.

| Step | Tool | Result |
|---|---|---|
| Auth | OAuth via MCP | ✅ works (redirect_uri issue from Jul 12 morning is gone) |
| List clients | `list_clients` | ✅ 2 seeded clients |
| Create quote | `create_quote` | ✅ `D-2026-001` (id `019f56b7-a71c-…de9499`), public `quote_url`, auto-numbering ON |
| Quote PDF | `get_quote` → `get_attachment` | ✅ `attachment_id` appears on re-fetch (NOT in create response); presigned S3 URL, 30-min expiry |
| Create invoice (draft) | `create_client_invoice` | ✅ `M2M-TEST-INV-001` (id `019f56ba-d715-…96f5ae`), proof string accepted in `terms_and_conditions` |
| Finalize | `change_client_invoice_status finalize:true` | ✅ draft → unpaid, custom number kept |
| **Proof on PDF** | `get_attachment` → download | ✅ **proof string renders in PDF footer** (verified visually; SHA-256 of PDF: `45afa16e…9e3aa3`) |
| Payment link (invoice) | `create_payment_link {invoice_id}` | ❌ 400 "connection with the provider does not exist" — sandbox org has no payment provider |
| Payment link (basket) | `create_payment_link {items}` | ❌ same error — **payment links are OUT for the demo** |
| Send invoice email | `send_client_invoice` | ✅ 204, sent to own address with copy_to_self |

### Dry run of the full demo flow — 2026-07-12 16:35 (all artifacts cleaned up)

Transcript (`demo/transcript.md`, Atelier Lumière) → extraction → client →
quote → PDF hash → draft invoice with real hash proof → deleted everything.

- `create_client` works, but **`create_quote` 422s if the client has no
  `tax_identification_number`** ("`tin_number` must have a value") →
  `update_client` with a SIREN, retry: OK. The skill/demo MUST extract or ask
  for a TIN when creating a new client.
- `update_client` PATCH semantics confirmed.
- Quote `D-2026-002` → `get_quote` re-fetch → `attachment_id` → PDF
  downloaded, SHA-256 `09bcdfb8…c4ca` computed locally.
- Draft invoice accepted a 224-char proof string with the real hash; drafts
  are auto-numbered `F-2026-00X-PROFORMA` until finalized.
- Cleanup verified: draft invoice deletion, quote deletion, and client
  deletion all return 204 (test-only calls, not part of the skill's flow).

Timing: full flow ran in ~2 minutes of tool calls — fits the 3-minute video.

**Consequences for the skill/demo:**
- Demo climax = finalized invoice PDF with visible cryptographic proof + email send. No payment link.
- Always re-fetch quote/invoice via `get_quote`/`get_client_invoice` to obtain `attachment_id`.
- Parameter shapes verified: `vat_rate: "0.2"` (decimal, not percent), `unit_price: {value, currency}`, `payment_methods: {iban}`, quote requires `terms_and_conditions` at create.
- Test artifacts left in sandbox: quote `D-2026-001`, invoice `M2M-TEST-INV-001` (unpaid).

## Dev note: reproducing this run

The run above went through the Qonto MCP connected to a Qonto Sandbox
organisation (set one up from the Toolkit in the Qonto Developer Portal).
No direct API calls, scripts or tokens are needed: authenticate the MCP via
OAuth and follow the tool sequence in `skills/meet2invoice/SKILL.md`.
Payment links need a payment provider on the organisation, which the sandbox
org did not have, so they are not part of the tested flow.
