# Qonto Sandbox Validation Guide for Meet2Invoice

**Date:** 2026-07-11  
**Purpose:** Validate the exact write chain before building the MCP skill.

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
- Cleanup verified: `delete_client_invoice` (draft), `delete_quote`,
  `delete_client` all return 204.

Timing: full flow ran in ~2 minutes of tool calls — fits the 3-minute video.

**Consequences for the skill/demo:**
- Demo climax = finalized invoice PDF with visible cryptographic proof + email send. No payment link.
- Always re-fetch quote/invoice via `get_quote`/`get_client_invoice` to obtain `attachment_id`.
- Parameter shapes verified: `vat_rate: "0.2"` (decimal, not percent), `unit_price: {value, currency}`, `payment_methods: {iban}`, quote requires `terms_and_conditions` at create.
- Test artifacts left in sandbox: quote `D-2026-001`, invoice `M2M-TEST-INV-001` (unpaid).

> For the hackathon you can (and should) use the **Qonto Sandbox**. No real Geschäftskonto or Steuernummer required.

## Quick Setup (from Developer Portal)

1. Go to https://developers.qonto.com/ and register (prefer "Sign in with Qonto" to avoid ~48h review).
2. Create an App.
3. Select scopes (minimum):
   - `client.read` + `client.write`
   - `client_invoices.read` + `client_invoice.write`
   - `payment_link.read` + `payment_link.write`
   - `organization.read`
4. Open **Toolkit → Sandbox web app**.
5. (Optional but recommended) Create a test organization with virtual balance.
6. Copy:
   - Access Token (for `Authorization: Bearer ...`)
   - **X-Qonto-Staging-Token**

**Critical:** Every request to the sandbox must send **both** headers:

```
Authorization: Bearer YOUR_ACCESS_TOKEN
X-Qonto-Staging-Token: YOUR_STAGING_TOKEN
```

Missing the Staging token → you get HTML/OneLogin redirect instead of JSON.

**Sandbox base URL:**
`https://thirdparty-sandbox.staging.qonto.co`

**Helpful pre-made org:** The portal often provides an "Abacate Organization" that is already set up for payment link testing.

## Exact Validation Chain (copy-paste ready)

Replace the placeholders and run in order.

```bash
#!/usr/bin/env bash
set -euo pipefail

BASE="https://thirdparty-sandbox.staging.qonto.co"
AUTH="Authorization: Bearer $QONTO_ACCESS_TOKEN"
STAGING="X-Qonto-Staging-Token: $QONTO_STAGING_TOKEN"

echo "=== 1. List clients ==="
curl -s "$BASE/v2/clients?per_page=5" \
  -H "$AUTH" -H "$STAGING" | jq .

echo "=== 2. Create test client (Hackathon Test ACME) ==="
CLIENT_RESP=$(curl -s -X POST "$BASE/v2/clients" \
  -H "$AUTH" -H "$STAGING" -H "Content-Type: application/json" \
  -d '{
    "kind": "company",
    "name": "Hackathon Test ACME",
    "email": "test-acme-20260711@example.com",
    "currency": "EUR",
    "locale": "en",
    "billing_address": {
      "street_address": "42 Hackathon Lane",
      "city": "Berlin",
      "zip_code": "10115",
      "country_code": "DE"
    }
  }')
echo "$CLIENT_RESP" | jq .
CLIENT_ID=$(echo "$CLIENT_RESP" | jq -r '.client.id')

echo "=== 3. Create DRAFT invoice ==="
# Get a valid IBAN first if you don't have one:
# curl -s "$BASE/v2/bank_accounts" -H "$AUTH" -H "$STAGING" | jq .

INVOICE_RESP=$(curl -s -X POST "$BASE/v2/client_invoices" \
  -H "$AUTH" -H "$STAGING" -H "Content-Type: application/json" \
  -d "{
    \"client_id\": \"$CLIENT_ID\",
    \"issue_date\": \"2026-07-11\",
    \"due_date\": \"2026-08-10\",
    \"currency\": \"EUR\",
    \"payment_methods\": { \"iban\": \"YOUR_SANDBOX_IBAN_HERE\" },
    \"items\": [{
      \"title\": \"Website redesign project - Phase 1\",
      \"quantity\": \"1\",
      \"unit_price\": { \"value\": \"4800.00\", \"currency\": \"EUR\" },
      \"vat_rate\": \"0.20\"
    }]
  }")
echo "$INVOICE_RESP" | jq .
INVOICE_ID=$(echo "$INVOICE_RESP" | jq -r '.client_invoice.id')
echo "Draft invoice ID: $INVOICE_ID (status should be draft)"

echo "=== 4. Finalize the invoice ==="
# MCP equivalent: change_client_invoice_status with action "finalize"
curl -s -X POST "$BASE/v2/client_invoices/$INVOICE_ID/finalize" \
  -H "$AUTH" -H "$STAGING" | jq .

echo "=== 5. Create payment link linked to the finalized invoice ==="
PL_RESP=$(curl -s -X POST "$BASE/v2/payment_links" \
  -H "$AUTH" -H "$STAGING" -H "Content-Type: application/json" \
  -d "{
    \"invoice_id\": \"$INVOICE_ID\",
    \"name\": \"Hackathon Test ACME - Phase 1 Payment\"
  }")
echo "$PL_RESP" | jq .
PAYMENT_LINK_ID=$(echo "$PL_RESP" | jq -r '.payment_link.id // .id')
echo "Payment link ID: $PAYMENT_LINK_ID"

echo "=== 6. Send invoice + retrieve proof ==="
curl -s -X POST "$BASE/v2/client_invoices/$INVOICE_ID/send" \
  -H "$AUTH" -H "$STAGING" -H "Content-Type: application/json" \
  -d '{"recipients": ["test-acme-20260711@example.com"]}' | jq .

echo "=== Proof - Invoice ==="
curl -s "$BASE/v2/client_invoices/$INVOICE_ID" \
  -H "$AUTH" -H "$STAGING" | jq '{id, status, number, invoice_url, total_amount}'

echo "=== Proof - Payment Link ==="
curl -s "$BASE/v2/payment_links/$PAYMENT_LINK_ID" \
  -H "$AUTH" -H "$STAGING" | jq .
```

## What to Report Back

- Did client creation + invoice creation succeed?
- Did `finalize` (change status) work?
- Did `create_payment_link` accept an `invoice_id` on a finalized invoice, or did you have to use basket mode?
- Was there a `create_quote` / quote flow available?
- Any validation errors (especially around IBAN, currency, address, VAT)?
- Full end-to-end success? (Y/N + key IDs + payment link URL)

## Relation to the MCP Skill

The final submission skill (`SKILL.md`) talks to the **Qonto MCP** using friendly tool names:
- `list_clients` / `create_client`
- `create_client_invoice`
- `change_client_invoice_status`
- `create_payment_link`
- `send_client_invoice`
- `get_client_invoice` + `get_payment_link`

The sandbox exercise above proves that the underlying Business API supports the desired flow. The MCP is a curated, conversational wrapper on top of the same operations.

## Tips

- Use the official Postman collections from Qonto and just add the two sandbox headers.
- For payment link testing, the pre-configured "Abacate Organization" in the portal is often the fastest.
- The MCP itself may still require a production-connected experience for the final 3-minute video. Sandbox is for development + proof that the chain is possible.

Once this chain runs cleanly on sandbox, we have strong evidence that the MCP version will also work. Then we can confidently polish the SKILL.md and record the demo.