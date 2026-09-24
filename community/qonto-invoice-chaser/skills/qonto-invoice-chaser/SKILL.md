---
name: qonto-invoice-chaser
description: Intelligent late-invoice chaser for Qonto accounts. Detects overdue client invoices, cross-checks them against real incoming transactions (an "unpaid" invoice may already be paid — proposes marking it), profiles each client's payment behavior, then drafts the right graduated reminder — courteous nudge (~D+7), firm reminder (~D+21), formal notice with legal interest and the €40 recovery indemnity (~D+45, France). Delivers as Gmail drafts when the Gmail MCP is connected, ready-to-copy text otherwise. Use for "relance mes impayés", "who owes me money?", "has invoice X been paid?", "write a reminder for this invoice", "quel est mon encours client ?", "prepare a formal notice".
permissions:
  mcp:
    qonto: [create_payment_link, delete_client_invoice, get_client, get_organization, list_client_invoices, list_transactions, mark_client_invoice_as_paid]
  network: []
  env: []
  tools: [Read]
---

# Qonto Invoice Chaser

Chase late payers without burning the relationship — and never chase a client who already paid. Read-heavy, two light writes: `mark_client_invoice_as_paid` (always proposed, never silent) and Gmail **drafts** (the user reviews and sends).

## Prerequisites
1. `get_organization` FIRST → organization, legal country, `bank_account_id`s / IBANs (`list_transactions` requires them).
2. **Country-aware**: the formal-notice legal kit (late-payment interest, €40 recovery indemnity — art. L441-10 & D441-5 of the French Commercial Code) applies to **France**. Other Qonto countries (DE, ES, IT, AT, NL, BE, PT…): graduated reminders still work; reference the EU Late Payment Directive (2011/7/EU) generically and never invent country-specific rates or legal wording.
3. **Gmail MCP optional, detected dynamically**: present → reminders land as Gmail drafts; absent → say so once and output ready-to-copy text. The core works on Qonto alone.

## Workflow

### 1. Scan receivables
`list_client_invoices` filtered on unpaid statuses, paginate `per_page: "50"`. Per invoice: number, client, total incl. VAT, issue date, `due_date`, days overdue (vs today). Compute outstanding total and aging buckets (0-30 / 31-60 / 60+ days).

### 2. Cross-check against real cash — before any reminder
An invoice can be paid yet never marked (bank transfer outside a payment link, manual reconciliation forgotten). For every unpaid invoice, scan `list_transactions` (credit side, per account, since issue date):
- **Strong match** = exact amount ±0.01 AND (normalized counterparty ≈ client name OR reference/label contains the invoice number).
- Strong match → show the transaction as evidence and **propose** `mark_client_invoice_as_paid`; act only on explicit confirmation in the current conversation.
- Ambiguous (partial payment, one transfer covering several invoices, close-but-not-exact amount) → present the candidates, never auto-mark, never chase.

**Rule: a reminder is only drafted for invoices that survive this step.** The most expensive email in B2B is the reminder sent to a client who already paid.

### 3. Profile the payer
Per late client, from paid-invoice history and matched transaction dates: invoices paid, average days-to-pay vs due date, trend. Classify and state it in one line ("24 invoices, always paid, avg 5 days late → warm tone"):
- 🟢 **Reliable, exceptionally late** → warmest register, assume oversight.
- 🟡 **Occasionally late** → standard ladder.
- 🔴 **Chronically late** (high average delay, repeated reminders) → skip the warmest register, stay correct and factual.
`get_client` → contact name, email, locale; write the reminder in the client's language when known.

### 4. Draft the graduated reminder
Pick the step from days overdue; adapt the tone from the profile. Firm but respectful — the goal is getting paid AND keeping the client.

| Step | When | Register | Must contain |
|---|---|---|---|
| Courteous nudge | ~D+7 | Warm, assumes oversight | Invoice number, amount incl. VAT, due date, payment means as stated on the invoice |
| Firm reminder | ~D+21 | Firm, factual | Same + days overdue, reference to the first reminder, announced next step |
| Formal notice (mise en demeure) | ~D+45 | Formal, legal | Same + late-payment interest (contract rate, else ECB refi + 10 pts, floor 3× the French legal rate) computed for the elapsed days + **€40 recovery indemnity per invoice** (art. L441-10 & D441-5 C. com) + payment deadline + registered-mail (LRAR) recommendation |

Every number in the email is real — invoice number, amount, days overdue, computed interest. No placeholder, no template smell.

### 5. Deliver — drafts, never silent sends
- **Gmail MCP present**: create a **draft** (recipient = client email from `get_client`, subject carries the invoice number, body = the reminder). Tell the user it awaits review in their drafts. Direct sending ONLY if the host exposes a send capability AND the user explicitly asks in the current conversation.
- **No Gmail MCP**: output the reminder as a ready-to-copy block (subject + body) and mention which MCP would automate the drafting.
- Missing client email → flag it and suggest completing the client record in Qonto; never guess an address.

### 6. Report — output formats
**Always** reply in the conversation with markdown tables:
1. **Receivables snapshot** — outstanding total, aging buckets, DSO estimate.
2. **Per-invoice action table** — invoice · client · amount · days overdue · payer profile · ladder step · status (already paid → to confirm / draft created / text provided).
3. Narrative next steps ("re-run Monday morning; two invoices reach D+21 next week").

**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): generate an **HTML dashboard** — aging bars, top late clients, reminder pipeline — and hand it to the user. If the host cannot render files, say nothing about it: the markdown tables are the deliverable.

## Guardrails
- NEVER mark an invoice paid without showing the matching transaction and getting explicit confirmation in the current conversation.
- NEVER send an email on its own: drafts by default; direct send only on explicit request. Never present a draft as sent.
- Below full matching confidence, ask — a wrong reminder to a client who paid costs more than a question.
- Legal computations (interest, €40 indemnity) are France-only and informative, not legal advice; recommend professional review before a formal notice goes out, and LRAR for its delivery.
- Rehearsals: fictional client + draft invoices + `delete_client_invoice` afterwards; clean up test Gmail drafts.
- Mask IBANs in reports (last 4 digits). Paginate everything (`per_page` ≤ 50).
