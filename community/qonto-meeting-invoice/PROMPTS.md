# 💬 Example prompts — qonto-meeting-invoice

Invoke with `/qonto-meeting-invoice <your request>` — or just ask in plain language: the skill's description triggers it automatically.

## Getting started
- "Here's the call transcript — draft the quote" *(paste the text)*
- "Turn this morning's sales call into a quote"

## Going further
- "Extract the negotiated terms and show me the transcript line behind each one"
- "The client said yes on the call — draft the invoice directly instead of a quote"
- "Match what was discussed against my product catalog and flag any price differences"
- "It's a new prospect — read the details back to me before creating the client record"
- "The transcript is in my notes app — fetch it from there and draft the quote"
- "List the ambiguities first: anything unclear about prices, VAT or payment terms"

## Chain it
- "Quote accepted — invoice it and add a payment link" — hand over to `qonto-pay-me-now`
- "If they go quiet after the invoice, set up the chase" — continue with `qonto-invoice-chaser`
- "Check this new client's legal health before we commit" — run `qonto-counterparty-watch`

> ⚠️ Quotes and invoices are created as drafts and confirmed line by line: nothing is sent to a client without your explicit "yes, send it".
