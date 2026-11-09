# Laboris for Qonto

French employment law for Qonto customers, sourced by [Laboris](https://laboris.fr): every rule cites the article of the Code du travail, the collective agreement clause, the court decision or the official page (URSSAF, BOSS, BOFiP) it comes from.

## Install

1. Connect Qonto. On claude.ai or Claude Desktop, use the official Qonto connector. In Claude Code:
   `claude mcp add --transport http qonto https://mcp.qonto.com/mcp`
2. Install the plugin from the Qonto marketplace.
3. Connect Laboris. In Claude Code the plugin declares the server: run `/mcp`, pick `laboris` and sign in. On claude.ai or Claude Desktop, add a custom connector at `https://mcp.laboris.fr/mcp`.
4. No Laboris account yet: create one at [laboris.fr/signup](https://laboris.fr/signup), confirm the email, then sign in again from the assistant (step 3). A new account starts a free trial; afterwards an [Essentiel or Pro plan](https://laboris.fr/prix) is needed.

## Skill

| Skill | Ask | What you get |
|---|---|---|
| `hire-and-exit` | "Je veux embaucher un développeur en CDI" · "How much will a rupture conventionnelle cost?" | The formalities and their deadlines, the salary against the legal and agreement minimums, what the collective agreement changes (trial period, notice, severance), the payments the exit opens computed and written out, and the cash they need against the Qonto balance |

## How it works

Qonto identifies the company and supplies its cash and current payroll outflows. The public French company registry gives the collective agreement the company declares, as a hint the user confirms. Laboris searches the Code du travail, the Code de la sécurité sociale, the collective agreements, case law, URSSAF, BOSS and BOFiP, and returns excerpts with their URL. Every instruction the skill follows is in this plugin: nothing is loaded from Laboris at run time.

## Data

Laboris receives the abstract facts a legal rule depends on (exit type, seniority, headcount, working time), never a name, an individual salary, an IBAN, a counterparty or a transaction. The company's legal name is looked up in the public French company registry to find its collective agreement. Transactions and balances stay between Qonto and the assistant. Laboris privacy policy: [laboris.fr/politique-confidentialite](https://laboris.fr/politique-confidentialite).

## Scope

Reads Qonto and writes nothing to it: no transfer, no category, no invoice. French law only.
