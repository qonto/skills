# 📖 Setup & usage guide — qonto-project-pnl

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Connect the Notion connector (recommended)
1. Same place: Settings → **Connectors** → search **Notion** → *Add* (OAuth)
2. Grant access to your workspace (or a dedicated section — the skill will only ever write in **its own** database)
3. Check: "*List my recent Notion pages*" → pages show up

> ⭕ Without Notion: the skill still works — P&L as conversation tables + an HTML dashboard.

### Step 3 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-project-pnl/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 4 — Label your transactions per project (recommended)
In the Qonto app: create **one label per project** and apply it to the relevant transactions.
Without labels, the skill proposes a mapping from recurring counterparties (everything tagged 🟡) — but labels remain the royal road.

## 2️⃣ Monthly usage (the ritual, ~3 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Build the per-project P&L and update my Finance database in Notion**" | Account read, label → project mapping proposed |
| 2 | Check / correct the mapping, confirm (remembered for next runs) | Cashed revenue + attributed costs computed |
| 3 | Read the P&L (margin, burn, ⚠️ alerts) and the Notion write preview, say "yes" | "Finance" database created or **updated in place** — never a duplicate |
| 4 | Open your project page in **Notion** | The P&L entry shows "updated 1 min ago" ✅ |

## 3️⃣ On-demand usage

- "**What's the real margin on project Aurora?**" *(invented name — use yours)* → that project's P&L, cashed vs costs
- "**Which project is losing money?**" → ranking by margin, 🔴 alerts
- "**Show me the label → project mapping before computing**" → the mapping table alone, correctable
- "**What's my monthly burn per project?**" → 3-month rolling burn, per project
- "**Build the P&L without touching Notion**" → tables + HTML dashboard only

## 4️⃣ Output formats (where does the P&L land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (per-project P&L, alerts, orphans) | **Always** — the baseline |
| **"Finance" database in Notion** | Dedicated "Finance — P&L (generated)" database, one entry per project, refreshed on every run | When the Notion connector is present + explicit consent |
| **Interactive dashboard** | **HTML** file/artifact: revenue vs costs bars, margin, burn, alerts | When the host renders files; automatic fallback to tables otherwise |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` errors right away | `bank_account_id`/`iban` is required | The skill **always** calls `get_organization` first |
| `403 missing oauth scope` on `list_cash_flow_categories` | Outside the claude.ai connector scope | Expected — the skill works with **labels**, never with that tool |
| Huge or truncated responses | Missing pagination | The skill paginates `per_page` ≤ 50 everywhere |
| No projects detected | No Qonto labels | Mapping proposed from recurring counterparties (🟡); label in the app going forward |
| The Finance database doesn't appear in Notion | Notion connector absent or not authorized | Settings → Connectors → Notion; meanwhile, degraded mode (tables + dashboard) |
| Risk of a duplicate entry in Notion | Project renamed between runs | The skill matches by **project name**: confirm the rename in the mapping instead of creating a twin |
| Revenue shows zero despite existing invoices | Invoices unpaid, or payments not matched | The skill only counts **cashed** money; check invoice statuses and confirm the proposed matching |
| An annual cost is missing (licence, domain…) | Scanned history too short | The skill covers 24–36 months when history allows — annual cadences only show there |

## 🔒 Security reminder

On the Qonto side the skill is **read-only**: zero writes, no money moves, anywhere.
On the Notion side it only writes in **its own** dedicated database, marked as generated,
after a preview and your explicit "yes" — never in your existing pages. Re-running the
skill updates the database in place, with no duplicates and no deletions.
