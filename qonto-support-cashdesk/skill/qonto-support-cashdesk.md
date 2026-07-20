---
name: qonto-support-cashdesk
description: Customer-support billing desk for Qonto accounts. Takes a customer conversation ("I never received my invoice", "the payment link expired", "you charged me twice" — pulled from Intercom when that MCP is connected, or simply pasted into the chat), matches the customer against Qonto clients (confirmed by the user), verifies the facts against invoices, payment links and incoming transactions, then answers with the fix attached — resend the invoice, create a fresh payment link, or a credit note when a double collection is PROVEN by two dated credits — every write explicitly confirmed, the customer reply delivered as a draft to review. Use for "je n'ai pas reçu ma facture", "le lien de paiement a expiré", "vous m'avez facturé deux fois", "a customer says they paid twice", "handle this billing complaint", "answer this support ticket about an invoice".
---

# Qonto Support Cashdesk

The billing counter of customer support. The customer's memory says one thing; the Qonto account knows the truth. This skill checks the truth first, then acts: verify → prove → fix → reply. Read-heavy; every write (resend, new link, credit note) is confirmed by the user before it happens.

## Prerequisites
1. `get_organization` FIRST → organization, legal country, bank accounts (`list_transactions` requires `bank_account_id`/`iban` later). Nothing hardcoded — the skill adapts to whatever account it runs on.
2. **Country: universal.** Clients, invoices, payment links and transactions exist in every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT…). No local tax rule is involved; amounts follow the account's currency.
3. **Optional MCPs, detected dynamically**: Intercom (pull the support conversation directly) · Gmail (create the reply as a draft). If absent, say so once and continue — the core works in pure Qonto: the user pastes the conversation, the reply is delivered as copy-paste text.

## Workflow

### 1. Read the conversation
From Intercom if connected, otherwise ask the user to paste it. Extract: the claim type (invoice not received / link expired / charged twice / other), identity clues (email, name, company), and any quoted references (invoice number, amount, dates). If the claim doesn't fit the three counters, say so and offer the verification that still applies.

### 2. Match the client — never act on a guess
`list_clients` (paginate `per_page: "50"`), match by **email first** (most reliable), then by name/company (normalize case and accents). Show the candidate(s) — masked to what's needed — and **have the user confirm the match** before anything else. Two plausible candidates → list both and ask. No match → say so plainly; never pick "the closest one".

### 3. Verify against Qonto — the facts, not the memory
- **Invoices**: `list_client_invoices` filtered on the confirmed client → status (draft/unpaid/paid/canceled), amounts, issue & due dates; `get_client_invoice` for the detail (recipient email, payment link attached to the invoice).
- **Payment links**: `list_payment_links` + `get_payment_link` → real status (open, expired, paid, canceled), amount, creation date.
- **Incoming payments**: `list_transactions` per account (side: credit), windowed around the invoice dates, `per_page` ≤ 50. Match credits to the invoice by amount + reference + counterparty; a card-settled payment can lag 1–2 days (`emitted_at` vs `settled_at`) — match on `emitted_at`.

### 4. Diagnose with cited evidence
| Customer claim | What the skill checks | Honest outcomes |
|---|---|---|
| "Never received the invoice" | Invoice exists? Status? Recipient email on the client record correct? | Invoice found → propose resend (fix the email first if wrong). No invoice → say so: nothing to resend, propose creating one is out of scope here |
| "The payment link expired" | `get_payment_link` status, amount, dates | Expired/canceled → propose a fresh link. Actually **paid** → tell the user, no new link |
| "You charged me twice" | Two credits matching the same invoice: same amount, close dates — **both cited (date + amount)** | Two credits found → duplicate **proven**, propose a credit note. **One credit only → no credit note**; report exactly what was found |

Every conclusion carries its proof. One credit, a partial payment, a currency mismatch → the skill reports the discrepancy instead of forcing a diagnosis.

### 5. Act — each write individually confirmed
- **Resend**: `send_client_invoice` after the user confirms invoice + recipient email.
- **Fresh link**: `create_payment_link` with the same amount/items, after confirmation (companion skill for proactive links: `qonto-pay-me-now`).
- **Credit note**: `create_credit_note` **only when the double collection is proven by two dated credits in the transactions, the proof has been shown, and the user explicitly confirms in the current conversation**. A credit note is a real accounting document — never issue one as a "commercial gesture" decided by the skill. The credit note documents the correction; **the refund itself is a bank transfer the user makes in the Qonto app (SCA)** — the skill never moves money and never claims it did.

### 6. Reply draft + report
Compose the customer reply: factual, short, apologies **only when the error is proven** (cite the correction: credit note number, new link, resent invoice). If the Gmail MCP is present, create it as a **draft** (never send); otherwise deliver it as copy-paste text. Close with a one-table recap in the conversation: claim → evidence → action taken/pending → reply status.

## Guardrails
- NEVER act on an unconfirmed client match; never present a write as done when it is pending or failed.
- A credit note requires: proof (two dated credits cited) + explicit user confirmation. No proof → no credit note, whatever the customer insists on.
- The skill never sends the customer reply itself — draft only, the user reviews and sends.
- Refunds are transfers: user-initiated in the Qonto app with SCA. Out of the skill's hands, and said plainly.
- Duplicates on the **purchase** side (supplier charged you twice) are the job of `qonto-supplier-detective` — redirect there.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50). Rehearsals: invoices created via MCP are REAL → use a fictional client, draft status, then `delete_client_invoice` / `delete_client`.
