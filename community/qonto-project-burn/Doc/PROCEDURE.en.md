# 📖 Setup & usage guide — qonto-project-burn

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-project-burn/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Connect Linear or Jira (optional but recommended)
1. Settings → **Connectors** → search **Linear** (or **Jira / Atlassian**) → *Add*
2. Done — the skill **detects the MCP automatically** at run time
3. No tracker connected: clean **degraded mode** — full per-project report in the conversation + HTML dashboard

> 💡 Bonus: a few transactions labelled per project in Qonto (app → transaction → Labels)
> make the mapping instant. Without labels, the skill proposes a mapping from recurring suppliers.

## 2️⃣ First run (the mapping, ~3 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**What did each project cost?**" | The skill reads accounts and labels, proposes the label → project table |
| 2 | Correct any wrong line, **declare each project's budget** | Mapping table validated, shown in full |
| 3 | Paste the returned config block into your **Claude project instructions** | The mapping is remembered across future conversations |
| 4 | Read the report: spent, %, run rate, projected overrun date | You know exactly where every project stands ✅ |

## 3️⃣ Regular usage (the Monday-morning ritual, ~2 min)

| # | Action | Result |
|---|---|---|
| 1 | "**Where does the project burn stand?**" | Per-project table ✅/⚠️/🔴, orphans listed |
| 2 | "**Post the status to Linear**" | Preview of the exact comment text (+ alert issue if a threshold is crossed) |
| 3 | Confirm explicitly ("yes, post it") | Comment posted on the Linear/Jira project; "⚠️ Budget [project] Z %" issue created if a threshold is crossed |
| 4 | The team sees the status **in its own tool**, backed by the Qonto transactions | The finance comes to the team ✅ |

## 4️⃣ Copy-paste prompts

- "**What did project Alpha cost, in total and this month?**" → detailed burn, top suppliers
- "**Which projects are past 80 % of their budget?**" → threshold alerts
- "**At this pace, when do we cross the budget?**" → projected overrun dates
- "**Show me the unattributed transactions**" → orphans + clean-up options
- "**Post every project's status to Linear**" → preview, then write (with your consent)

## 5️⃣ Output formats (where does the burn land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (burn per project, orphans, alerts) | **Always** — the baseline |
| **Linear/Jira comment** | "X € / Y € — Z % · projected overrun on [date]" on the mapped project | Tracker MCP detected + explicit consent |
| **Linear/Jira alert issue** | "⚠️ Budget [project] Z %" + the justifying transactions | Threshold crossed + explicit consent |
| **Interactive dashboard** | **HTML** file/artifact: spent-vs-budget bars, run rate, markers | When the host renders files; automatic fallback to tables |

## 6️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails right away | Missing `bank_account_id`/`iban` | The skill **always** calls `get_organization` first |
| `403 missing oauth scope` on `list_cash_flow_categories` | Outside the claude.ai connector scope | Expected — the mapping runs on **labels** |
| Huge / truncated responses | Missing pagination | `per_page` ≤ 50 everywhere, 3-month windows |
| The skill can't label a transaction | The Qonto MCP has **no tool** to attach labels | Paste-ready list provided → label in the app (once); or optional cash-flow-category filing (confirmed) |
| An amount counted twice | Multi-label transaction | Counted **once**, first matching label in the mapping — disclosed in the report |
| Nothing written to Linear | Linear/Jira MCP absent or not connected | Dynamic detection: the skill says so and switches to degraded mode (report + dashboard) |
| Card spend dates look off | `settled_at` lags 1–2 days | The skill matches on `emitted_at` |

## 🔒 Security reminder

On the Qonto side the skill **only reads**: no transfer, no payment, no write that touches money.
The one notable write is a **comment or issue in Linear/Jira** — always previewed in full and posted
**only** after your explicit consent in the conversation. The optional orphan tidy-up (cash-flow
category) is light, reversible, and also confirmed before every write.
