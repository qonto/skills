# 📖 Setup & usage guide — qonto-true-margin

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Connect the Shopify MCP (recommended)
1. Same path: Connectors → search **Shopify** → *Add* → OAuth login to your store
2. Check: "*List my Shopify products*" → your products show up
3. Optional: add the **Stripe** connector for per-charge fee detail

> ⭕ Without Shopify, the skill runs in an **announced degraded mode**: true margin by cost family (PSP, FX, shipping, COGS), no per-product granularity — and it says so plainly.

### Step 3 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-true-margin/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

## 2️⃣ Typical usage (the monthly margin audit, ~5 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**What's my true margin per product?**" | Debits classified (PSP 🟢🟡⚪, FX, shipping, COGS) + Shopify per-product sales |
| 2 | Pick the allocation key (pro-rata revenue or units) | Method printed on every table — a stated estimate |
| 3 | Read the dashboard-margin vs real-margin table | Loss-makers on top, per-product gap quantified |
| 4 | Ask: "**Propose the new prices**" | Break-even + target price per flagged product, assumptions shown |
| 5 | Validate **line by line** ("yes for product X") | `update-product` for that product only → price re-read from Shopify → before/after confirmed |

## 3️⃣ Copy-paste prompts

- "**What's my true margin per product, based on what actually leaves my Qonto account?**"
- "**Which products am I selling at a loss?**"
- "**My dashboard says 40% margin on this product — is that real?**"
- "**Allocate my costs pro-rata to units instead of revenue**"
- "**Propose a price targeting a 25% contribution margin on this product**"
- "**Apply the new price for [product]**" *(validation is still requested product by product)*

## 4️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (cost families, margins, proposals, before/after) | **Always** — the baseline |
| **Interactive dashboard** | **HTML** file/artifact: waterfall from dashboard to real margin, loss-makers, price simulator | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback otherwise |
| **Shopify confirmation** | `get-product` re-read after every `update-product` | Every validated application |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails right away | Missing `bank_account_id`/`iban` | The skill always calls `get_organization` first |
| PSP fees nowhere in the debits | Shopify Payments nets its fees **inside** the payout — no separate debit | Effective rate derived from gross vs net (needs the Shopify MCP); otherwise shown as "unknown, not zero". See also `qonto-shopify-bridge` for payout↔bank reconciliation |
| `403 missing oauth scope` on `list_cash_flow_categories` | Outside the claude.ai connector scope | Expected — the skill classifies by normalized counterparty and labels instead |
| Huge / truncated responses | Pagination too wide | `per_page` ≤ 50 everywhere, 3-month windows |
| Card-paid shipping missing on the expected date | `emitted_at` vs `settled_at` drift (1–2 days) | The skill reconciles on `emitted_at` |
| Shopify tool "update_product" not found | Spelling: Shopify tools are **hyphenated** | `update-product`, `get-product`, `run-analytics-query` |
| Price doesn't seem applied | Update not confirmed | The skill re-reads the product after every `update-product` and only reports "done" after the re-read |

## 🔒 Security reminder

On the **Qonto** side, the skill is **read-only**: no banking write tool exists in it, nothing can move on the account.
The only write is on the **Shopify** side: one price update, product by product, **only** after your explicit
validation of that specific line — a global "apply everything" is refused and re-asked line by line. And every margin
shown carries its allocation method: it's an estimate built for a decision, not accounting.
