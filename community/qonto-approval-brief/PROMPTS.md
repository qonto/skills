# 💬 Example prompts — qonto-approval-brief

Invoke with `/qonto-approval-brief <your request>` — or just ask in plain language: the skill's description triggers it automatically.

## Getting started

- "Brief me on my pending requests."
- "Which of these transfer requests are safe to approve?"

## Going further

- "Can I approve Alex's transfer request? Give me the evidence."
- "Have we ever paid this beneficiary before — how many times, what amounts?"
- "Do we know this IBAN, or is it a never-seen one?"
- "Why is this request flagged 🔶? What exactly should I verify, and with whom?"
- "Is this amount consistent with what we usually pay this supplier?"
- "Decline the duplicate request and tell the requester why."

## Chain it

- "The never-seen IBAN worries me — run a deeper check with qonto-counterparty-watch."
- "Cross-check this pattern against past anomalies with qonto-fraud-sentinel."
- "Give me this brief board as an HTML page I can review on my phone before approving in the app."

> ⚠️ The skill can never approve anything — approvals always happen in the Qonto app behind your own SCA, and declines are only sent with a stated reason after your explicit confirmation.
