# 📖 Setup & usage guide — qonto-ceo-cockpit

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-ceo-cockpit/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Add a few Qonto labels (recommended)
1. In the **Qonto app**: Transactions → select → **Labels** ("Subscriptions", "Contractors", "Travel"…)
2. Labels become the cockpit's spending categories — the more you have, the sharper the flow view
3. Without labels: the skill groups by counterparty and shows an explicit "Uncategorized" bucket

> ℹ️ No need to label everything: the cockpit displays the count of uncategorized transactions and never silently spreads them.

## 2️⃣ Typical usage (Monday morning, ~2 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Show me my company**" | 12 months of flows + invoices + labels read, HTML dashboard generated |
| 2 | Open the dashboard (artifact or file) | Flow view, KPIs, category cards, 3-month forecast |
| 3 | Move the day-rate × billable-days sliders | The 3-month projection and year-end estimate recalculate **live, no new API call** |
| 4 | Click the eye icon on sensitive lines | The line leaves the view, totals recompute, a chip restores it |
| 5 | (Optional) "**Regenerate without the hidden lines**" | "Presentation" export: the hidden data is no longer IN the file |

## 3️⃣ Copy-paste prompts

- "**Show me my company**" → the full cockpit
- "**Where does my money come from and where does it go this year?**" → flow view, year toggle
- "**What if I raise my day rate to €550?**" → priced answer + reminder that the slider does it live
- "**Prepare the banker version, without line X**" → regeneration with genuine exclusion
- "**Refresh the cockpit**" → data re-read, new file

## 4️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Interactive dashboard** | One **self-contained HTML** file: inline CSS/JS, zero external dependency, pure CSS+SVG bars/ribbons, light/dark theme | **The deliverable** — when the host renders files (claude.ai artifacts, Claude Desktop, Claude Code) |
| **Conversation reply** | Markdown tables: KPIs, month + year flows, 3-month forecast, priced day-rate scenarios | Automatic fallback otherwise |
| **"Presentation" export** | The same HTML regenerated without sensitive lines in the data | On request |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails right away | Missing `bank_account_id`/`iban` | Expected — the skill always calls `get_organization` first |
| `403 missing oauth scope` on `list_cash_flow_categories` | Outside the claude.ai connector scope | Expected — the skill uses **labels** as the grouping key |
| Huge / truncated responses | Pagination too wide | The skill paginates `per_page` ≤ 50, in 3-month windows |
| No day-rate panel | No day-unit invoice lines | Expected (not a time-based business) — the skill says so and omits the panel |
| No vault gauge | No sub-account named tax/taxe/impôt/TVA | Create/rename the sub-account in the app, or ignore — everything else works |
| A category looks empty | Unlabeled transactions | "Uncategorized" bucket shown with its count — label in the app, then "Refresh the cockpit" |
| An amount looks doubled | Internal transfer counted as a flow | The skill nets out transfers between the org's own accounts — report any leftover case |

## 🔒 Security reminder

The skill is **100 % read-only**: no transfer, no payment, nothing to approve.
The dashboard is a **local** file — your data never leaves your machine, no external code loads.
The eye toggle is a **presentation** convenience: the data stays in the file's source.
To share, ask for the "presentation" regeneration — there, hidden lines are genuinely excluded.
