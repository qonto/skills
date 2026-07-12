# 💬 Example prompts — qonto-counterparty-watch

Invoke with `/qonto-counterparty-watch <your request>` — or just ask in plain language: the skill's description triggers it automatically.

## Getting started
- "Which of my clients and suppliers are risky right now?"
- "Rank my counterparties by how much they could cost me"

## Going further
- "Is my client Acme in receivership or liquidation?"
- "Who owes me money, and for how long? Break it down by ageing bucket"
- "Which clients are paying later and later? Show me the trend, not just the average"
- "Check the legal health of everyone who owes me more than a token amount"
- "Which suppliers am I most dependent on — what breaks if one of them fails?"
- "Re-run the legal checks on my top ten counterparties and tell me what changed"

## Chain it
- "Draft the reminders for the risky clients with overdue invoices" — hand the dunning over to `qonto-invoice-chaser`
- "What does that exposure do to my 90-day cash projection?" — stress-test it with `qonto-tax-pilot`
- "Fold these risk flags into my month-end review" — run `qonto-monthly-close` next
