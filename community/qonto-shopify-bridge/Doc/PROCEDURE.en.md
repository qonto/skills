# 📖 Setup & usage guide — qonto-shopify-bridge

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Connect the Shopify MCP (recommended)
1. Same path: Connectors → search **Shopify** → *Add* → your store's OAuth login
2. Check: "*Show me my last 3 Shopify orders*" → orders show up
3. Multiple stores? The skill reconciles store by store

> ⭕ This step is **optional**: without the Shopify MCP, the skill runs in Qonto-only mode
> (payout cadence, totals, rhythm breaks) — and tells you so plainly.

### Step 3 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-shopify-bridge/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

## 2️⃣ Weekly usage (the Monday-morning ritual, ~2 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Did all my Shopify payouts arrive last week?**" | Timeline of expected vs received payouts, per PSP |
| 2 | Read the reconciliation table | "14 expected, 13 received, 1 late by 4 days" — you know where you stand |
| 3 | If a payout is missing: read the generated **support ticket draft** | Date, expected amount, orders inside, statement reference — ready to send |
| 4 | Send the ticket **yourself** to Shopify/Stripe support | The skill only prepares the text — you take the action |

## 3️⃣ On-demand usage

- "**What do Stripe fees really cost me?**" → effective rate computed payout by payout, compared to your plan's advertised rate (if you provide it)
- "**What's my net cash collected this month, after commissions?**" → the true margin, not the dashboard's gross
- "**Reconcile my Shopify sales with my account for March**" → full month reconciliation
- "**Were my refunds actually passed through?**" → refunds/chargebacks checked on both sides

## 4️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (reconciliation, fees, net collected, anomalies) | **Always** — the baseline |
| **Interactive dashboard** | **HTML** file/artifact: payout timeline (gaps highlighted), fee-rate trend, net-per-month bars | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables |
| **Support ticket draft** | Ready-to-send text, every reference included | Every time a missing payout is detected |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails right away | Missing `bank_account_id`/`iban` | The skill **always** calls `get_organization` first |
| Huge / truncated responses | Pagination too wide | `per_page` ≤ 50 everywhere — handled by the skill |
| `403 missing oauth scope` on `list_cash_flow_categories` | Outside the claude.ai connector scope | Expected — the skill relies on counterparties and labels instead |
| Shopify tools not found | Shopify MCP not connected, or naming mixed up: Shopify tools are **hyphenated** (`get-order`, `list-orders`, `run-analytics-query`) | Connect the Shopify MCP; otherwise the skill continues Qonto-only |
| False "missing payout" on PayPal | Manual (on-demand) withdrawals, no fixed cadence | The skill recognizes the pattern and requalifies the cadence |
| Payout not found on the date the store claims | 2–3 business-day banking delay; the Qonto date is `settled_at` | The skill matches by date window + amount proximity, never same-day equality |
| Amounts never matching exactly | Grouped payouts: *n* orders − fees − refunds = 1 transfer | Normal behavior — the skill reconstructs the group |

## 🔒 Security reminder

This skill is **pure read**: no write tool, on the Qonto side or the Shopify side.
It creates nothing, modifies nothing, and cannot touch any money. The only thing it produces
is information — and a ticket draft that **only you** decide to send.
