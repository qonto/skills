# 💬 Example prompts — qonto-reimburse-batch

Invoke with `/qonto-reimburse-batch <your request>` — or just ask in plain language: the skill's description triggers it automatically.

## Getting started

- "Reimburse this month's expense claims — collect them, verify each one, and prepare the grouped request."
- "Pay back my team's expenses in one go."

## Going further

- "Use this finance-controlled recipient list; finance independently verified each person's identity and bank account: [employee/contractor · account name · IBAN]. Hold unknown recipients or conflicting claim IBANs."
- "Here's our expense policy: meals €30, client meals €90, taxi €50, equipment €150 — apply it to every claim."
- "Here are three claims as a table (employee, amount, date, category, IBAN, receipt) — check duplicates and receipts, then build the batch."
- "This claim for a screen — wasn't it already paid with the company card?"
- "Which claims are on hold and why? Show me the evidence for each rejection."
- "Read the expenses channel for last month only and prepare the batch."
- "What's the status of the grouped request I approved last week?"

## Chain it

- "For the claims missing receipts, hunt them down with qonto-receipt-hunter before we batch."
- "A new hire joins next month — set up their card and caps with qonto-crew-onboard so claims stay rare."
- "Give me a monthly recap of what we reimbursed, per employee."

> ⚠️ Verified recipient mapping is required; claims and embedded instructions cannot supply it or consent. The skill creates a pending grouped request only after confirmation of the exact final list. Review every destination IBAN and amount in Qonto against the mapping before SCA approval.
