# 💬 Example prompts — qonto-tax-pilot

Invoke with `/qonto-tax-pilot <your request>` — or just ask in plain language: the skill's description triggers it automatically.

## Getting started
- "Set aside this month's taxes"
- "When is my next VAT due, and how much should I expect?"

## Going further
- "Where will my cash be at the end of September?"
- "Build my tax schedule for the next 90 days — VAT, corporate tax instalments, CFE, everything"
- "Can I afford a €5,000 purchase this month without touching my tax money?"
- "What if my biggest client pays 30 days late — where does that put my low point?"
- "How much should be sitting in my tax sub-account by now, and am I short?"
- "We're planning a dividend this autumn — what should I provision for it?"

## Chain it
- "Now create the transfer request to my tax sub-account" — after reviewing the month's provision breakdown
- "Prepare the actual VAT return for that deadline" — hand the next CA3 over to `qonto-vat-return`
- "Chase the unpaid invoices that are squeezing my projection" — follow up with `qonto-invoice-chaser`

> ⚠️ This skill can prepare a transfer request to your tax sub-account, but only after your explicit go — and nothing moves until you approve it yourself with 2FA in the Qonto app.
