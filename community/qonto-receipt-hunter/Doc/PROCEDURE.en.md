# 📖 Setup & usage guide — qonto-receipt-hunter

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-receipt-hunter/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Connect Gmail and Google Drive (recommended)
1. Settings → **Connectors** → add **Gmail**, then **Google Drive** (Google OAuth)
2. These power the hunt: without them, the skill still delivers the prioritized inventory and the VAT at stake — it will simply tell you where to look manually

> ℹ️ The skill detects available connectors on its own. Nothing else to configure.

## 2️⃣ Typical usage (the hunt session, ~5 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Which transactions are missing receipts?**" | Prioritized inventory: X missing receipts, ~Y € of recoverable VAT at stake, tags 🔴🟠🟢 |
| 2 | Say: "**Go hunt them down**" | Gmail and Drive searched (merchant + amount + dates around the purchase); original receipts found |
| 3 | Check each displayed match (transaction ↔ document) and **confirm one by one** | Receipt attached to the transaction, verified, visible in the Qonto app ✅ |
| 4 | Read the final report | ✅ attached / 📎 to attach / ❌ not found with one lead each + before/after score |

## 3️⃣ Copy-paste prompts

- "**Which transactions are missing receipts this quarter?**" → prioritized inventory + VAT at stake
- "**How much VAT am I at risk of losing?**" → the numbers alone, no hunt
- "**Find the [merchant] invoice in my emails**" → targeted hunt for one transaction
- "**Hunt them down and propose the attachments**" → full session (one confirmation per receipt)
- "**This month's completeness report**" → score + remaining gaps + leads

## 4️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (prioritized inventory, VAT at stake, hunt report) | **Always** — the baseline |
| **Qonto attachments** | Real attachments on the transactions, visible immediately in the app | On every confirmation |
| **Completeness report** | Before/after score + leads; HTML version when the host renders files, tables otherwise | End of session |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails | Missing `bank_account_id`/`iban` | `get_organization` first — the skill always does |
| Huge responses / slowness | Pagination too wide | `per_page` ≤ 50 everywhere — handled by the skill |
| The receipt exists in Gmail but the hunt misses it | Search anchored on the settlement date | The skill searches around **`emitted_at`** (the actual purchase date — card payments settle 1–2 days later) |
| Amount not found in emails | Tip, foreign currency, partial capture | Amount tolerance + a merchant-only retry pass |
| Email attachment can't be pulled through the connector | Some connectors expose metadata only | The skill hands you the direct email pointer → one-drag manual attach, stated honestly |
| Upload fails | Two-step flow mis-sequenced | `request_attachment_upload` (opens the slot) **then** `upload_attachment` (pushes the file) — handled by the skill |
| Irrelevant transactions "pollute" the list | Receipt not required, or client payment | `attachment_required: false` and `side: credit` are excluded from the score by design |

## 🔒 Security reminder

The skill **never touches money**: its only write adds a document to a transaction.
Every attachment is confirmed **individually** by you, on a displayed match (merchant, amount, date) —
never a silent batch. Above all: **originals only**. The skill never fabricates, regenerates or
"reconstructs" a receipt — a fake document has zero probative value and exposes you in a tax audit.
No original? The transaction stays listed, with a lead to find it.
