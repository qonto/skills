# Cash and working-capital check

A treasury assessment for Qonto business owners. It answers four questions: what is happening to my cash, why, when could I run short, and what can I do about it.

## What it does

1. **Reads your Qonto data**: accounts (including closed ones), 6 to 12 months of transactions, client and supplier invoices if you use them, cards and plan.
2. **Categorises your transactions** into your Qonto cash flow categories. This step matters most for businesses that do not use Qonto's invoicing or supplier invoice features. The skill excludes internal transfers, owner contributions and loan drawdowns, applies country rules (tax offices, social security, payroll, utilities for FR, DE, IT, ES and NL), and asks you once about whatever it cannot classify.
3. **Asks for your typical payment terms** when invoices are missing, so client and supplier payment delays can be estimated.
4. **Checks Overdraft, Pay Later and the Flex card**: whether you use them, could use them, or neither.
5. **Builds a 13-week forecast** in three layers: without financing, with what you use today, and optimised. Adds base, downside and severe scenarios.
6. **Recommends actions**: free operational levers first (invoice unbilled work, chase late clients, align payment dates), then the cheapest Qonto product mix that keeps cash above a safety buffer.
7. **Measures how fast money moves**: days your clients take to pay you and you take to pay suppliers (DSO and DPO), computed from your Qonto invoices' issue, due and payment dates, with terms, days early or late and on-time rates for each client and supplier.
8. **Gives you an interactive cash simulator**: a page where you can test your own assumptions (clients paying later, removing any client, payroll, an unexpected cost), see how the Flex card, Pay Later and an overdraft change your next 13 weeks, and explore client and supplier concentration, payment behaviour, open invoices and monthly flows.

## Writes to your account

The skill is read-only by default. It can **propose** two writes, and only makes them after you explicitly say yes:

- `create_cash_flow_category`: adds a missing category, such as "Owner contributions".
- `modify_transaction_cash_flow_category`: saves the categories it inferred onto your transactions. It never overwrites a category you set, unless you confirm that specific change.

It never moves money and never requests financing on your behalf.

## Example prompts

- "Will I run short of cash in the next three months?"
- "Est-ce que ma trésorerie tient jusqu'à la fin de l'année ?"
- "Can you categorise my transactions and tell me where my cash goes?"
- "Would Pay Later or an overdraft help with my September supplier bills?"
- "Wie lange reicht meine Liquidität, wenn mein größter Kunde 30 Tage später zahlt?"

## Limits

- Financing suggestions are analysis, not credit decisions. Every product stays subject to Qonto's eligibility review. Rates and terms are read from Qonto's public pricing, never assumed.
- The Qonto MCP does not expose overdraft or Pay Later limits, so the skill asks you for them.
- Without invoices, payment delays are estimates based on the terms you state.
- Tax dates are used only to time cash flows. They are not tax advice.

## Qonto MCP tools used

Read: `get_organization`, `list_bank_accounts`, `list_cash_flow_categories`, `list_transactions`, `get_transaction`, `list_client_invoices`, `list_supplier_invoices`, `list_credit_notes`, `list_clients`, `get_client`, `list_labels`, `list_requests`, `list_cards`, `get_subscription`, `get_qonto_public_pricing`.

Write, only with your confirmation: `create_cash_flow_category`, `modify_transaction_cash_flow_category`.
