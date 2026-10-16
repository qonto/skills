# 💬 Example prompts — qonto-subscription-audit

Invoke with `/qonto-subscription-audit <your request>` and explicitly request Qonto account analysis. Follow-up prompts below apply to an existing Qonto audit. General subscription advice and standalone email-writing requests do not activate this skill; ambiguous requests require clarification before account access.

## Getting started
- "Audit subscriptions using my Qonto account transactions"
- "Use my Qonto account to calculate my annual subscription spend"

## Going further
- "What am I still paying for that I probably don't use anymore?"
- "Which suppliers quietly raised their prices this year? Old price, new price, percentage"
- "Is this €19 charge from a new merchant the start of a subscription?"
- "Am I paying twice for tools that do the same job?"
- "Did my cloud bill go up because of price, or because of usage?"
- "Show me the dashboard, then export it as a new HTML file at a path I choose" — the skill asks for the exact path, explains that it stores financial details, and never overwrites an existing file

## Chain it
- "Write the renegotiation email for the supplier with the worst hike record"
- "Now cap the keepers with dedicated virtual cards" — hand the card work over to `qonto-subscription-guardian`
- "Fold the annual subscription cost into my company view" — open `qonto-ceo-cockpit`

> ⚠️ Read-only on your account: the only things this skill produces are email drafts you review and send yourself — nothing is ever sent for you.
