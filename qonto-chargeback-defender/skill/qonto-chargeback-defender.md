---
name: qonto-chargeback-defender
description: End-to-end payment dispute handling for Qonto accounts. Detects open chargebacks (via a Stripe/PayPal MCP when connected, otherwise by spotting clawback debits in Qonto transactions), finds the matching debit, assembles a sourced defense file (Shopify order, proof of delivery, Gmail customer threads), states the real response deadline, and — with explicit consent — attaches a dated evidence memo to the Qonto transaction for accounting traceability. Use for "j'ai reçu un chargeback", "why did Stripe take money back?", "defend this dispute", "assemble my dispute evidence", "when is my chargeback response due?".
---

# Qonto Chargeback Defender

A chargeback is money pulled back out of the account, plus a fee, plus a short response window (typically 7–21 days) — and most merchants never respond at all. This skill detects the dispute, rebuilds the money trail, assembles a sourced defense file, and pins the whole story to the Qonto transaction. Read-heavy, one safe write: **the skill prepares, the user submits** on the Stripe/PayPal portal.

## Prerequisites
1. `get_organization` first → bank accounts (`list_transactions` requires `bank_account_id`/`iban`), currency, country.
2. **Country-agnostic**: chargebacks follow card-network and PSP rules, not national tax law — the skill works identically for every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT).
3. **Optional MCPs, detected dynamically**: Stripe / PayPal (authoritative dispute list + deadlines), Shopify (orders + fulfillment/tracking), Gmail (customer threads). None connected? The Qonto-only core still works: clawback detection + chronology + response checklist. Say plainly which mode is active.

## Workflow

### 1. Detect open disputes
- **With a Stripe or PayPal MCP connected**: list open disputes → id, amount, currency, reason code, status, **evidence due date**. This is the authoritative source, especially for deadlines.
- **Qonto-only fallback**: scan `list_transactions` per account (`per_page: "50"`, last 3–6 months, extend on request) for **clawback debits**: label/reference containing `dispute` / `chargeback` / `reversal` (also FR variants `litige`, `contestation`, `impayé`), usually from a PSP counterparty (Stripe, PayPal, Adyen, Mollie…), often paired with a small **dispute-fee debit** from the same counterparty on the same day.
- **Honest caveat — Stripe netting**: Stripe often nets a dispute *inside* the next payout instead of emitting a separate debit. If no clawback line exists, flag unusually low payouts as candidates and recommend connecting the Stripe MCP rather than guessing.

### 2. Find the matching money trail
For each dispute, rebuild the chronology in Qonto: **original incoming payment** (amount match ± fee, date window around the charge date, counterparty via `get_transaction`) → payout → **clawback debit** → fee. For card-settled flows match on `emitted_at`, not `settled_at` (1–2 days of drift). Check `list_transaction_attachments` on the clawback: an existing attachment may mean the dispute is already being handled.

### 3. State the response deadline
- Use the **dispute's own evidence-due date** (Stripe `evidence_details.due_by`, PayPal response window) — never estimate a real deadline loosely.
- Qonto-only mode: give the typical windows (card networks ~7–21 days from the chargeback date; PayPal ~10 days) **explicitly labeled as indicative**, and tell the user to read the real date on the PSP portal.
- Sort open disputes by urgency; flag anything due within 72 hours first.

### 4. Assemble the defense file
Collect what actually wins disputes, matched to the reason code, each piece **listed with its source** (system · identifier · date):
- **Shopify MCP** → the order (`get-order` / `list-orders`): items, amounts, billing/shipping address, fulfillment status, **tracking number = proof of shipment/delivery** when present.
- **Gmail MCP** → customer threads (`search_threads` on the customer's email / order reference): order confirmations, delivery confirmations, complaint history, any "thanks, received it".
- **Qonto** → the matching client invoice if any (`list_client_invoices`), the refund transaction if a refund was already issued (strongest possible answer to a "duplicate/refund not received" dispute).
Missing pieces are listed as **missing**, with where to find them (carrier site, CRM, inbox) — a checklist, not a shrug.

**Never fabricate evidence.** The deliverable is a **dated synthesis memo** that *cites* the source documents (their system, id, date and what they prove). It is not a receipt, not an invoice, not a generated "proof" — the real evidence files are gathered and submitted by the user. Write this distinction into the memo itself.

### 5. Attach the memo to the transaction — only with explicit consent
With the user's explicit confirmation in the current conversation: `request_attachment_upload` on the **clawback transaction** → upload the memo → **confirm via `list_transaction_attachments`** before reporting success. Result: the disputed debit permanently carries its full story (dispute id, chronology, evidence list, outcome placeholder) — accounting traceability, useful whether the dispute is won or lost.

### 6. Report — and hand over the submission
**Always** reply in the conversation with markdown tables:
1. **Open disputes** (dispute · amount · reason · clawback found ✅/❓ · response due · urgency).
2. **Money trail** per dispute (date · event · amount · Qonto transaction).
3. **Evidence checklist** (piece · source · status ✅ collected / ⚠️ missing + where to get it).
4. A **response draft**: the memo's argument restated in the structure of the PSP's response form, ready to paste.

Then say it plainly: **the defense is submitted on the Stripe/PayPal portal, by the user** — the skill prepares everything, submits nothing. Never present a response as filed.

## Guardrails
- NEVER generate fake evidence: the attachment is a dated synthesis memo citing source pieces, not a fabricated document.
- NEVER claim the defense was submitted or the dispute won — submission happens on the PSP portal, by the user.
- Deadlines come from the dispute itself; generic windows are always labeled indicative.
- Attachment upload only with explicit consent, and only reported as done after `list_transaction_attachments` confirms it.
- Empty account, no disputes found, no PSP counterparty → say so; never invent a dispute. Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50).
- Related skills: `qonto-shopify-bridge` (order-to-payout reconciliation), `qonto-fraud-sentinel` (unusual debits).
