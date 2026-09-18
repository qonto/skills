---
name: qonto-meeting-invoice
description: Turns a sales-call transcript into a Qonto quote or invoice. Extracts the negotiated terms (deliverables, quantities, prices, payment terms), matches them against the Qonto product catalog and client records, creates the document as a DRAFT, and sends it only after explicit line-by-line confirmation. Use for "turn this call into a quote", "fais le devis du call de ce matin", "draft an invoice from this meeting transcript", "voici le transcript, prépare le devis", "the client said yes — send the quote".
permissions:
  mcp:
    qonto: [create_client, create_client_invoice, create_payment_link, create_quote, delete_client_invoice, delete_quote, get_client, get_organization, list_clients, list_products, list_quotes, send_client_invoice, send_quote]
  network: []
  env: []
  tools: [Read]
---

# Qonto Meeting Invoice

From call to quote, before the coffee gets cold. The skill reads a sales-call transcript, extracts **only what was actually said**, checks it against real Qonto data, and prepares a draft the user validates line by line. One principle everywhere: ask, never invent.

## Prerequisites
1. `get_organization` first → organization, legal identity, country. Quotes and invoices are built on the organization's **existing Qonto invoicing settings** (numbering, legal mentions, payment details) — the skill never reinvents them. If invoicing isn't set up in Qonto yet, say so and stop before creating anything.
2. **Transcript source**: pasted text always works. If a Notion or Google Drive MCP is connected, fetch the note/file from there; if not, say so and ask for a paste. The skill depends on **no** third-party MCP.
3. **Country-aware**: document creation works for any Qonto country. VAT rates are **never assumed** (no default 20 %): they come from the product catalog or from explicit user confirmation. Legal mentions come from the Qonto settings of the organization's country.

## Workflow

### 1. Ingest the transcript
Accept a pasted transcript, an attached file, or — when the MCP is available — a Notion / Google Drive note the user points to. If the source MCP is absent, state it plainly and continue with a paste. Messy input is normal: filler words, interruptions, multiple speakers, mixed languages.

### 2. Extract the negotiated terms — extract, don't imagine
From the transcript, list: deliverables/services, quantities, unit prices, discounts, payment terms, delivery or start dates, quote validity or invoice due date, and who the client is (company, contact, email if spoken).
**Hard rule**: only what was explicitly said lands in the extraction. Anything missing or fuzzy (a price "as usual", an unstated VAT treatment, no payment term) goes to the ambiguity list of step 4 — never into the document. Quote the transcript line that supports each extracted term so the user can verify.

### 3. Match against real Qonto data
- `list_products` (paginate `per_page: "50"`) → match each deliverable to the catalog: canonical title, unit price, VAT rate, unit. Flag divergences ("the call says €850/day, your catalog says €900").
- `list_clients` + `get_client` → find the client by company name / contact / email heard on the call. Match found → use it, show which one. No match → propose `create_client` with the details read back (name, email, address if known, missing fields asked); create **only after explicit confirmation**.
- `list_quotes` → check for an existing recent quote for the same client to avoid duplicates; if one exists, show it and ask before creating another.

### 4. Surface ambiguities BEFORE generating
One single list, before any write: unmatched products, price divergences, missing VAT rate, unstated payment term or validity date, unclear quantities. The user settles each point. No document exists until this list is empty or explicitly arbitrated.

### 5. Create as DRAFT
Default document is a **quote** (`create_quote`); switch to `create_client_invoice` only if the user explicitly asked to invoice directly. Always draft, never sent at this stage. Then show the full line-by-line recap in the conversation: client, each item (title · quantity · unit price · VAT rate · line total), subtotal, VAT, total, dates, payment terms — with the transcript justification per line. Numbering and legal mentions are handled by Qonto's invoicing settings.

### 6. Send — only after explicit confirmation
On an explicit "yes, send it" in the current conversation: `send_quote` / `send_client_invoice` to the client's email (confirm the address first). Report exactly what happened: sent to whom, or still a draft in Qonto's Quotes/Invoices section if the user chose to keep it. Never present a document as sent when it is a draft.

## Output formats
1. **Always**: the line-by-line recap as markdown tables in the conversation (extraction with transcript quotes → ambiguity list → final document recap).
2. **In Qonto**: the draft quote/invoice, visible in the app (Invoicing section), on the organization's own template.
3. **To the prospect**: the Qonto email with the document, only after confirmation.

## Guardrails
- Documents created via MCP are **REAL** business documents. Draft first, always. NEVER send without explicit confirmation in the current conversation; never present a draft as sent.
- Never invent a price, a VAT rate, a quantity, or a due date — anything not in the transcript is asked. Never assume French VAT for non-French organizations.
- `create_client` only with confirmed details; check `list_clients` first to avoid duplicates.
- Rehearsals and demos: use a fictitious client, then clean up with `delete_quote` / `delete_client_invoice` (drafts only — a finalized invoice cannot be deleted; that's precisely why the skill is draft-first).
- Paginate everything (`per_page` ≤ 50). Mask personal data when echoing client records.
- The skill drafts business documents; it gives no legal or tax advice — the organization's invoicing settings and accountant remain the reference.
