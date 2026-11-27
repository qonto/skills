# 📖 Setup & usage guide — qonto-oss-navigator

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-oss-navigator/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Two recommended extras
1. **Shopify MCP** (recommended): Settings → Connectors → **Shopify** → *Add*. This is what gives **real shipping countries** per order. Without it, the skill runs in Qonto-only mode and announces partial coverage
2. **A "tax" sub-account**: in the **Qonto app**: Accounts → **Create sub-account**, named with a recognizable keyword ("Taxes & VAT", "Tax", "OSS"…). The skill detects it by name

> ⚠️ Both are optional: without Shopify the skill infers (and says so); without a sub-account it computes everything but won't propose transfers.

## 2️⃣ Typical usage (the quarterly ritual, ~5 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Where do I stand on the €10,000 EU threshold?**" | Gauge: cumulated cross-border B2C EU sales this year, crossing dated or estimated |
| 2 | Say: "**Draft my OSS return for the quarter**" | Country-by-country table: net base · rate · VAT due · total, deadline and filing portal |
| 3 | Read the breakdown (Shopify or Qonto-only mode, rate-table vintage, excluded B2B line) | You know exactly where every figure comes from — and what's left to verify |
| 4 | Confirm explicitly ("yes, create the request") if you want to provision | Transfer request created to the tax sub-account, breakdown in the note |
| 5 | On your **phone**: Qonto push notification → open → check the note → **approve (SCA)** | The quarter is provisioned ✅ |
| 6 | File the return on **your national OSS portal** before the deadline | The skill prepared — you file |

## 3️⃣ Copy-paste prompts

- "**Where do I stand on the €10,000 EU sales threshold?**" → the gauge, with the computation mode stated
- "**What VAT rate applies to my German / Spanish / Italian customers?**" → the customer country's rate (vintage-dated table)
- "**Draft my OSS return for last quarter**" → a country-by-country table ready to copy
- "**Provision my OSS VAT**" → a transfer request (after your explicit confirmation)
- "**Show me my intra-EU B2B sales**" → flows excluded from OSS (reverse charge), listed separately

## 4️⃣ Output formats (where does the draft land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (gauge, country-by-country draft, excluded flows) | **Always** — the baseline |
| **Interactive dashboard** | **HTML** file/artifact: gauge bar, per-country table, quarter timeline | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |
| **Qonto request note** | Country-by-country breakdown attached to the request, **visible at SCA approval time** | Every time a provision is created |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails right away | Missing `bank_account_id`/`iban` | The skill **always** calls `get_organization` first |
| Huge / truncated responses | Pagination too wide | `per_page` ≤ 50 everywhere, windowed scans |
| `403 missing oauth scope` on `list_cash_flow_categories` | Outside the claude.ai connector scope | Expected — the skill uses labels instead |
| `422` when creating the transfer request | Missing `credit_account_currency` field (undocumented) | The skill always sends it |
| Can't decline a test request | `decline_request` requires `request_type: "multi_transfers"` (plural) | Handled by the skill |
| Shopify tools not found | Tool names use **dashes**: `list-orders`, `run-analytics-query` | Handled by the skill; check the Shopify MCP is actually connected |
| Gauge lower than expected | Qonto-only mode: PSP payouts aggregate orders and hide the country | Coverage announced as partial (a floor) — connect Shopify or provide an order export |
| Sub-account not detected | Name lacks a keyword (tax/taxe/impôt/TVA/OSS) | Rename the sub-account in the app |

## 🔒 Security reminder

The skill **cannot** move money or file anything. It prepares: a gauge, a draft, and at most a
transfer *request* that **only you** can approve with your own 2FA in the Qonto app. You can
decline it in one tap. The rate table carries its vintage — verify it before any filing, and
have the return validated by your accountant.
