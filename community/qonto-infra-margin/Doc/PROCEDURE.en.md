# 📖 Setup & usage guide — qonto-infra-margin

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Connect the product MCPs (recommended, unlocks €/user)
1. Same path: Connectors → add **Vercel**, then **Supabase** (OAuth login with each vendor)
2. Optional: **Sentry** (error-volume context)
3. Check: "*List my Vercel projects*" and "*List my Supabase projects*" → your projects show up

> ⭕ Without these MCPs the skill runs in an **announced degraded mode**: infra debit classification,
> monthly totals, trend — already useful. It will tell you what to connect to go further.

### Step 3 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-infra-margin/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

## 2️⃣ Typical usage (the monthly audit, ~5 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**What does my infra cost, and per user?**" | 12–24 months of debits scanned, infra P&L vendor × month |
| 2 | The skill detects the Vercel/Supabase MCPs and offers telemetry | Real projects and deployments pulled from Vercel |
| 3 | **Confirm the table that counts your users** (e.g. `auth.users`) | A single read-only `SELECT count(*)` runs |
| 4 | Read the unit-economics table | €/user, €/project (proration shown), margin drift |
| 5 | Check the "bleeders" list | Side-projects billed with zero deployments in 90 days, with evidence |

## 3️⃣ Copy-paste prompts

- "**What does my infra cost per user?**" → the full analysis
- "**Isolate my infra spend over the last 12 months**" → the infra P&L alone (works without product MCPs)
- "**How much am I spending on AI APIs, and how is it trending?**" → AI-family focus + trend
- "**Which side-projects are costing me money for nothing?**" → the bleeders, with evidence
- "**Is my gross margin drifting?**" → infra as % of receipts, month by month (proxy announced)

## 4️⃣ Output formats (where does the analysis land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: infra P&L, unit economics, bleeders | **Always** — the baseline |
| **Interactive dashboard** | **HTML** file/artifact: bars per family, €/user gauge, drift curve, bleeders spotlight | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback otherwise |
| **Degraded mode** | Same tables minus €/user and per-project allocation — announced | Without the Vercel/Supabase MCPs |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails right away | Missing `bank_account_id`/`iban` | Expected — the skill always calls `get_organization` first |
| Huge / truncated responses | Pagination too wide | The skill paginates `per_page` ≤ 50, in 3-month windows |
| Totals ≠ the Vercel/AWS dashboard | Billed in USD, debited in EUR (FX included) | Expected — the skill's truth is the account debit; the gap is explained |
| Supplier invoice won't match the card debit | Matching on the wrong date | Match by `emitted_at`, not `settled_at` (1–2 day gap) |
| `execute_sql` fails or unknown table | The "users" table varies by app | The skill proposes `auth.users` by default and **asks you to confirm** — give your table/filter |
| A yearly cost mistaken for a one-off | History window too short | Extend the scan to 24–36 months (yearly cadences only show there) |
| `403 missing oauth scope` on `list_cash_flow_categories` | Outside the claude.ai connector scope | Expected — the skill doesn't need it (labels as fallback if useful) |

## 🔒 Security reminder

The skill is **100% read-only, on both sides**. Qonto side: no write tool, ever — nothing to approve,
nothing executed. Product side: `execute_sql` is limited to single read-only `SELECT count` queries,
on a table **only you** confirm before it runs. No product metric is ever invented:
no measured count → no €/user, and the skill says so.
