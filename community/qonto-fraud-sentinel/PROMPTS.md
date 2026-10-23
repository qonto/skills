# 💬 Example prompts — qonto-fraud-sentinel

Invoke with `/qonto-fraud-sentinel <your request>` — or just ask in plain language: the skill's description triggers it automatically.

## Getting started
- "Run my morning security check"
- "Anything unusual on my account?"

## Going further
- "Is this €249 debit normal for that merchant? Compare it to what I usually pay them"
- "Did anyone charge me twice this week?"
- "Which SEPA direct debits are new this month — any mandate used for the first time?"
- "Scan the whole week, not just since yesterday"
- "Any burst of small card debits that looks like card testing?"
- "Trust Acme — stop alerting me on them, they're a legitimate new supplier"

## Chain it
- "Yes, lock that card while I check with the merchant" — proposed only when a card is implicated
- "Dig into the supplier history behind that alert" — go deeper with `qonto-supplier-detective`
- "Check whether that new counterparty even legally exists" — verify with `qonto-counterparty-watch`

> ⚠️ The only action this skill can take is locking a card — always proposed first, executed only on your explicit confirmation, and reversible anytime in the Qonto app.
