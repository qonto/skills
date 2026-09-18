---
name: meet2invoice
description: "Turn a sales meeting artifact (transcript, notes, calendar event) into money movement in Qonto: extract the deal, preview it, create the quote, hash the authoritative PDF locally (SHA-256), and on acceptance create + finalize the invoice with an offline-verifiable proof injected into its terms — then send it from Qonto. The document never leaves your machine; only the hash travels."
when-to-use: "Use after a sales call or when meeting notes contain an agreed deal: 'turn this transcript into a quote', 'they accepted — invoice them', 'meet2invoice these notes', 'close the loop with proof in Qonto'. Also for escalating an existing Qonto quote to a proven, sent invoice."
argument-hint: "[meeting transcript/notes + client hints, or an existing Qonto quote ID + 'accepted']"
permissions:
  mcp:
    qonto: [change_client_invoice_status, create_client, create_client_invoice, create_credit_note, create_payment_link, create_quote, delete_client, delete_client_invoice, delete_quote, get_attachment, get_client_invoice, get_organization, get_payment_link, get_quote, list_clients, send_client_invoice, update_client, update_quote]
  network: []
  env: []
  tools: [Read, Bash]
---

# Meet2Invoice

From meeting artifact → reviewed quote → (acceptance) → finalized invoice with
cryptographic proof in its footer → sent from Qonto. One guarded flow, two
confirmation gates, zero documents uploaded anywhere. Turn the agreed deal
into a payable, provable Qonto invoice.

**Core promise:** the agreed deal leaves the meeting and becomes a payable,
provable Qonto invoice. The quote/invoice PDF is downloaded and hashed
**locally**; only the SHA-256 (plus optional signature metadata) is written
back into Qonto, visible on the final invoice PDF.

## How the Proof Works

1. Qonto generates the authoritative quote PDF. The skill downloads it via a
   presigned URL and computes `shasum -a 256` **on your machine**.
2. That hash — 64 hex characters, nothing else — is injected into the
   invoice's `terms_and_conditions`, so Qonto renders it in the footer of the
   official, finalized invoice PDF.
3. Anyone holding the original quote PDF can verify the link offline:

   ```bash
   scripts/verify-proof.sh quote.pdf invoice.pdf
   # ✔ PROOF VERIFIED — the invoice footer contains the SHA-256 of the local quote
   ```

   The verifier needs only `shasum` (falls back from `pdftotext` to a
   zero-dependency python3 extractor). No MCP, no network, no upload — the
   document never leaves the machine; only the hash travels.

4. **The client can verify too, with no Qonto account.** The public
   `quote_url` serves the same authoritative PDF, so the company that hired
   the freelancer downloads it, runs the same script against the invoice they
   received, and gets an independent, offline tamper-check that the invoice
   matches the quote they accepted. Proof works for both sides of the deal.

## Non-Negotiable Rules

1. **A meeting artifact is the entry point.** Transcript, notes file, or
   calendar event text. A bare typed amount is accepted but the skill should
   ask whether meeting context exists.
2. **Preview before every write.** Show extracted fields (client, scope,
   amount, VAT, terms, quote-vs-invoice recommendation) and wait for explicit
   confirmation. Two gates: one before the quote, one before the invoice.
3. **Quote first by default.** Only go straight to invoice when the artifact
   clearly says the deal is closed ("they accepted", "signed off", "go ahead").
   Even then, still create the quote as the **proof anchor** — it is hashed
   locally but never sent to the client; the flow proceeds to the invoice
   immediately. Skip the anchor only if the user explicitly declines it
   (then say honestly that the invoice carries no document proof).
4. **Never invent legal data.** Missing street address, tax ID (SIREN /
   Steuernummer / P.IVA), or VAT number → ask the user. Placeholder values are
   acceptable **only in sandbox testing and only with explicit approval**;
   every assumption made must be listed in the preview at Gate 1.
5. **The document never leaves the machine.** PDFs are fetched via
   `get_attachment` presigned URLs, stored locally, hashed locally with
   `shasum -a 256` (or `sha256sum` on Linux). No PDF is sent to any third
   party by this skill.
6. **Proof lives in `terms_and_conditions`** of the invoice (≤525 chars):
   `Signed proof: <verify-url or ref> | SHA-256: <hex> | Signers: <n/m> | Cert: <ref>`.
   It renders in the footer of the official Qonto invoice PDF (verified).
7. **No payments, no transfers.** This skill never moves money. Payment links
   are an optional post-step and only in accounts with a connected payment
   provider (sandbox orgs have none — expect 400 "connection with the
   provider does not exist"; skip gracefully).
8. **Respect invoicing law for the client's country.** Before any write,
   consult `references/invoicing-law.md`. Decide the VAT treatment from the
   parties' countries — domestic VAT / **intra-EU B2B reverse charge** /
   export — apply the correct rate, and inject any legally required mention
   into `terms_and_conditions` (it shares that ≤525-char field with the proof
   string). Never invent a VAT rate or a tax ID — ask if it's missing. This is
   guidance, not tax advice; Qonto handles numbering, VAT breakdown, and the
   e-invoice format (DE ZUGFeRD/XRechnung, FR Factur-X, IT SdI/FatturaPA).

## The Flow

**Two real entry points:**

- **A. From a meeting artifact** (default) — extract → quote → invoice, below.
- **B. From an existing Qonto quote** ("they accepted D-2026-004, invoice it"):
  call `get_quote(id)` for the client, items, and `attachment_id`; download that
  existing PDF and hash it locally (skip Step 1–2, that quote *is* the anchor);
  confirm at **Gate 2** and continue from Step 4. Do not create a second quote.

### Step 1 — Extract the deal from the artifact

From the transcript/notes, extract:

- client name + billing email (match against `list_clients` with
  `filter: {"name": "..."}` or `{"email": "..."}`; dedupe before creating)
- client country + tax ID (SIREN/USt-IdNr./Partita IVA) and status (business
  vs individual) — drives VAT treatment and the mandatory tax-ID field
- scope → line-item title(s) — real deals often have several items (phases,
  day rates × quantity, options); extract each as its own item, don't lump
- net amount and currency; VAT rate as **decimal string** (`"0.19"` = 19% DE,
  `"0.2"` = 20% FR, `"0.22"` = 22% IT) — pick per `references/invoicing-law.md`
- payment terms → due date
- deal state → quote (default) vs invoice (only if clearly closed)

**VAT treatment** (see `references/invoicing-law.md`), by client type:
- **Business in another EU country** with a valid VAT ID → **reverse charge**:
  `vat_rate: "0"`, require both VAT IDs, plan the mandatory mention
  (FR *Autoliquidation* / DE *Steuerschuldnerschaft des Leistungsempfängers* /
  IT *Inversione contabile*).
- **Individual / consumer (B2C), anywhere** → **always domestic VAT** at the
  org's local rate; reverse charge never applies to non-business clients.
- **Business outside the EU** → typically export, VAT `"0"` with an export
  mention — confirm with the user, rules vary by service type.
- **Otherwise** (same country, or B2C) → the org's local rate.
- **Seller under a small-business scheme** (FR *franchise en base* art. 293 B,
  DE *Kleinunternehmer* §19 UStG, IT *regime forfettario* — common for
  freelancers) → **no VAT at all**, inject the scheme mention instead. IT
  forfettario still requires SdI e-invoicing. If the org's VAT status is
  unknown, ask once and remember the answer for the session.
- **Spanish freelancer orgs**: apply IRPF **withholding tax** on B2B invoices —
  pass the user's IRPF rate in `withholding_tax: { rate }` (ask for it; typical
  15%, reduced 7% for new freelancers). Never guess the rate.

Set the client's `kind` (`company` vs `individual`) and `locale` correctly at
creation — they drive both the VAT logic and the document language.

Show the preview table (include country + VAT treatment). **Gate 1: confirm.**

### Step 2 — Create the quote

```
create_quote(
  client_id, currency,
  issue_date: today, expiry_date: today+30d,
  terms_and_conditions: <payment terms text>,   # REQUIRED on quotes
  items: [{ title, quantity: "1",
            unit_price: { value: "4800.00", currency: "EUR" },
            vat_rate: "0.2" }]
)
```

Notes proven against the live API:
- Auto-numbering may be ON — omit `number` unless the org requires it.
- The create response has **no `attachment_id`**. Re-fetch with `get_quote(id)`
  a moment later to get it, then `get_attachment(attachment_id)` for a
  presigned PDF URL (expires in 30 min — download immediately).
- Share the returned public `quote_url` with the user.

Download the PDF locally, compute `shasum -a 256`. This hash is the anchor
for everything that follows.

### Step 3 — (Optional) Collect signatures via a second MCP

If a signature MCP is available: send **only the hash + signer list**, let
signers approve on their devices, receive back a proof bundle
(signatures + cert reference). If none is available, the proof is the
locally computed hash alone — say so honestly in the output.

This repo ships a reference implementation: `sign-ring/server.py`, a
zero-dependency MCP server (register with
`claude mcp add sign-ring -- python3 <path>/sign-ring/server.py`).
Tools: `start_signature_ring(document_name, sha256, signers)` → one
signing URL per signer served on the LAN (signers tap on their phones),
`check_ring_status()`, `get_signature_proof()` → ready-to-inject
proof string (≤525 chars, live-tested at 223).

### Step 4 — On acceptance: invoice with injected proof

**Gate 2: confirm** the exact invoice + the proof string to be injected.

```
create_client_invoice(
  client_id, currency,
  issue_date, due_date,                # from payment terms
  status: "draft",
  payment_methods: { iban: <org's own Qonto IBAN from get_organization> },
  terms_and_conditions: <proof string ≤525 chars>,
  items: <same line items as the quote>
)
change_client_invoice_status(id, finalize: true)   # draft → unpaid, locks it
```

Then re-fetch `get_client_invoice(id)` → `attachment_id` →
`get_attachment` → download the final PDF and **show the proof rendered in
its footer**. Verify it end-to-end with the bundled script:

```bash
scripts/verify-proof.sh <local quote.pdf> <local invoice.pdf>
```

Green `✔ PROOF VERIFIED` means the finalized invoice provably references the
exact quote PDF on disk.

### Step 5 — Send it from Qonto

```
send_client_invoice(id, email_title, send_to: [client email], copy_to_self: true)
```

Write the email subject and body in the **client's language** (their `locale`
drives the document language too — set it at client creation).

Returns 204; the invoice status does not change. Surface in the final output:
quote ID + URL, invoice ID + URL, local PDF paths, the SHA-256, and what
still needs a human (payment tracking, real countersignature).

### After sending — real lifecycle (optional)

The invoice stays `unpaid` until money arrives. When the client pays, mark it
with `mark_client_invoice_as_paid(id)` (reversible via `unmark_as_paid`). If a
deal is cancelled, `change_client_invoice_status(id, cancel: true)`; a finalized
invoice can't be deleted, only cancelled or corrected with a `create_credit_note`.
Never mark paid on the client's word alone — confirm against a real transaction.

## Production Notes (what changes outside the sandbox)

Every call above is a GA Qonto Business API endpoint via the official MCP —
the flow runs unchanged on a production account. Differences to expect:

- **SCA prompts.** Sensitive writes go through the user's own Strong Customer
  Authentication. That is Qonto's third gate on top of this skill's two — a
  feature, not a failure; tell the user to expect it.
- **IBAN choice.** Production orgs often have several accounts: use the one
  with `main: true` from `get_organization`, and ask if the transcript implies
  a different account.
- **Currency.** Invoice currency must equal the client's `currency`; for a
  non-EUR deal set it correctly at client creation, don't default to EUR.
- **Anchor immutability.** Never `update_quote` after hashing — any change
  invalidates the proof. If the quote must change, re-hash and re-inject.
- **Manual numbering orgs.** If auto-numbering is disabled, `create_quote` /
  `create_client_invoice` fail without `number` — ask the user for the next
  number in their sequence; never guess one.
- **E-invoicing mandates.** IT already routes via SdI; FR phases in from
  Sept 2026 (Factur-X — set the client's `e_invoicing_address`); DE from 2027.
  Qonto emits the compliant format; surface the status, don't generate XML.
- **Payment links** work once a provider is connected — offer them after
  finalize in production; skip silently in sandbox (400, no provider).

## Verified Tool Chain (live-tested 2026-07-12, Qonto sandbox MCP)

| Tool | Status |
|---|---|
| `get_organization` (org IBAN, bank accounts) | ✅ |
| `list_clients` with name/email filter | ✅ |
| `create_quote` → public `quote_url` | ✅ |
| `get_quote` → `attachment_id` (re-fetch pattern) | ✅ |
| `get_attachment` → presigned PDF URL (30 min) | ✅ |
| `create_client_invoice` with proof in `terms_and_conditions` | ✅ |
| `change_client_invoice_status` finalize | ✅ |
| Proof string renders on final invoice PDF | ✅ |
| `send_client_invoice` | ✅ |
| `create_payment_link` | ❌ in sandbox (no provider connection) — optional in production |

## Error Handling

- **Client not found** → preview a `create_client` with extracted billing
  details; never create without confirmation. Include
  `tax_identification_number` (FR: SIREN) — **quote creation fails with 422
  "`tin_number` must have a value" without it** (live-verified). If unknown,
  ask the user or fix via `update_client` and retry once.
- **Draft invoices get a PROFORMA number** (e.g. `F-2026-003-PROFORMA`) when
  auto-numbering is on; the real number is assigned at finalize.
- **Validation error from Qonto** → show the exact upstream message and the
  field it concerns; fix and retry once.
- **`attachment_id` missing right after create** → wait 2–3s and re-fetch;
  it is populated asynchronously.
- **Presigned URL expired** → call `get_attachment` again.
- **Payment link 400 "connection with the provider does not exist"** → the
  org has no payment provider connected; continue without it, say so.
- **Insufficient permissions** → the account needs client-invoice write
  scopes (Client Invoice Management or equivalent); tell the user exactly
  which call was refused.
- **Duplicate risk** → before creating, list recent quotes/invoices for the
  client and surface near-identical ones; ask to proceed or cancel.

## Example Prompts

- "Here's the transcript from my Bouygues call — meet2invoice it."
- "They accepted quote D-2026-001. Invoice them, inject the proof, send it."
- "Turn these notes into a quote: ACME, €4,800 + VAT, net 30, Phase 1."
- "Draft only — don't finalize or send anything yet."
- 🇩🇪 "Mach aus diesem Telefonprotokoll ein Angebot und dann die Rechnung."
- 🇫🇷 "Cet appel est clôturé — facture en autoliquidation, TVA 0, mentions OK."
- 🇮🇹 "Deal chiuso: crea la fattura, IVA 22%, serve il codice destinatario SdI."
- 🇪🇸 "Crea un borrador de factura con IVA 21%, pero no la emitas ni la envíes."

## Example Artifacts (`demo/`)

Sample transcripts covering the main language / deal-state / VAT combinations,
usable as test fixtures or as a starting point for your own inputs:

| File | Lang | State | Legal case |
|---|---|---|---|
| `transcript.md` | EN | closed | FR domestic, standard VAT |
| `transcript-de-geschlossen.md` | DE | **closed** | DE domestic B2B, 19% |
| `transcript-de-angebot.md` | DE | **quote only** | stops at Gate 1, no invoice |
| `transcript-fr-reverse-charge.md` | FR | closed | intra-EU B2B **reverse charge** |
| `transcript-it-chiuso.md` | IT | closed | IT domestic, 22%, SdI code |
| `transcript-es-borrador.md` | ES | **draft only** | ES domestic, 21%, don't finalize/send |
