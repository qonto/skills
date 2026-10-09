# 📖 Setup & usage guide — qonto-cash-to-stock

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-cash-to-stock/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Connect the Shopify MCP (optional but recommended)
1. Settings → **Connectors** → search **Shopify** → *Add* → sign in to your store
2. Check: ask Claude "*What are my inventory levels?*" → your products show up

> ℹ️ Without Shopify, the skill runs in a **clean degraded mode**: velocity estimated from
> Qonto incoming payments + the product catalog — every derived figure is tagged 🟡 estimated.

## 2️⃣ Typical usage (the restock ritual, ~3 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**How many units can I reorder without endangering the account?**" | Truly free cash computed (balances − suppliers − detected taxes − fixed costs − buffer) |
| 2 | Read the commitments calendar and the 90-day curve | You see the dated low point and what causes it |
| 3 | Read the **four numbers**: free cash · stock-out date · fundable units · latest order date | The whole decision on one screen, every figure tagged 🟢🟡🔵 |
| 4 | Answer the skill's questions when needed (landed unit cost, supplier lead time) | Never silently guessed — asked once |
| 5 | Decide, then confirm explicitly ("yes, prepare the supplier transfer") | Transfer request created, full calculation in the note |
| 6 | On your **phone**: Qonto push notification → open → check the note → **approve (SCA)** | The supplier payment goes out ✅ — you always have the last word |

## 3️⃣ Copy-paste prompts

- "**How many units can I order without putting the account in danger, and by when?**"
- "**What's my truly free cash after the next 90 days of commitments?**"
- "**When will I run out of stock?**" (Shopify connected → per product)
- "**What if I split the order in two?**" / "**What if I wait until after the VAT deadline?**"
- "**OK, prepare the supplier transfer request for €[amount]**" (fictitious placeholder — use your own)

## 4️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (commitments, curve summary, four numbers, request recap) | **Always** — the baseline |
| **Interactive dashboard** | **HTML** file/artifact: free-cash curve, deadlines as markers, stock-out countdown, fundable-units gauge | When the host renders files; automatic fallback to tables otherwise |
| **Qonto request note** | Text attached to the transfer request, **visible at SCA approval time** | Every time a request is created |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails or complains about the account | Missing `bank_account_id`/`iban` | Expected — the skill **always** calls `get_organization` first |
| `422` when creating the transfer request | Missing `credit_account_currency` field (undocumented) | The skill always sends it |
| Can't decline a test request | `decline_request` requires `request_type: "multi_transfers"` (plural) | Handled by the skill |
| "The skill can't see my sales or my stock" | Shopify MCP not connected | Connect the Shopify connector, or accept the degraded mode (🟡 receipts-based estimate) |
| Very slow or truncated responses | Pagination too wide | The skill paginates `per_page` ≤ 50 everywhere |
| Fundable units look off | Wrong landed unit cost provided | The skill asks for it — double-check the value (shipping and duties included) |
| A known tax deadline is missing from the calendar | That tax was never debited on this account (short history) | The skill only projects what it observes — mention the deadline in the conversation |

## 🔒 Security reminder

The skill **cannot** move money. It creates a *request* that **only you** can approve with your
own 2FA in the Qonto app. You can decline it in one tap. Every request carries the full
calculation in its note — you approve with complete information. The ordering decision stays human.
