# 💬 Example prompts — qonto-invoice-chaser

Invoke with `/qonto-invoice-chaser <your request>` — or just ask in plain language: the skill's description triggers it automatically.

## Getting started
- "Which invoices should I chase today?"
- "Who owes me money right now, and since when?"

## Going further
- "Has invoice INV-2026-042 actually been paid? Check against my incoming transactions"
- "Draft a courteous nudge for client Acme — they're a week late but usually reliable"
- "Prepare the formal notice for the invoice that's 50 days overdue, with the late-payment interest"
- "What's my DSO looking like this quarter, and who are my worst payers?"
- "Any 'unpaid' invoices that were in fact settled by bank transfer? Propose marking them paid"
- "Write the reminder in the client's language and put it in my email drafts"

## Chain it
- "Check whether that chronic late payer is in legal trouble" — cross-check with `qonto-counterparty-watch`
- "Add a payment link so they can settle in one click" — hand over to `qonto-pay-me-now`
- "Fold the outstanding receivables into my cash projection" — continue with `qonto-tax-pilot`

> ⚠️ This skill only proposes: invoices are marked paid and reminder emails are drafted after your explicit confirmation — nothing is ever sent on its own.
