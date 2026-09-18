# 📖 Setup & usage guide — qonto-tax-radar

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-tax-radar/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Nothing else
No sub-account to create, no write permission to grant: the skill is **fully read-only**.
Bonus (optional): the more receipts you attach in Qonto, the greener axis 4 (VAT vs receipts) will be.

## 2️⃣ Typical usage (the quarterly ritual, ~5 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Run my tax pre-audit**" | The 8 axes announced, 12 months of transactions screened |
| 2 | Read the report: global banner, 8-axis table 🟢🟡🔴 | You know where you're exposed and for how much |
| 3 | Open the findings detail | Every point = transaction + rule cited + corrective action |
| 4 | Work through the remediation plan (receipts, reclassifications) **with your accountant** | The file gets clean |
| 5 | Re-run the skill next month | The grade improves — the virtuous loop |

## 3️⃣ Copy-paste prompts

- "**Run my tax pre-audit**" → full 8-axis report
- "**Am I ready for a tax audit?**" → same report, preparation angle
- "**Focus on VAT: what am I deducting without a receipt on file?**" → axis 4 only, per-transaction detail
- "**Review this year's restaurants and gifts**" → axes 1–2 only
- "**Re-run the pre-audit and compare with the last report**" → comparative re-run
- "**Generate the pre-audit notice as HTML**" → rich report when the host renders files

## 4️⃣ Output formats (where does the report land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Global banner + 8-axis table + findings detail + remediation plan (markdown) | **Always** — the baseline |
| **Interactive "pre-audit notice"** | **HTML** file/artifact: global grade, per-axis gauges, checklist | When the host renders files; automatic fallback to markdown otherwise |
| **Comparative re-run** | Same report, with the grade's evolution | Every re-run |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails on the first call | Missing `bank_account_id`/`iban` | Expected — the skill **always** calls `get_organization` first |
| `403 missing oauth scope` on `list_cash_flow_categories` | Outside the claude.ai connector scope | Expected — the skill uses `list_labels` instead |
| Huge / truncated responses | Pagination too wide | The skill paginates `per_page` ≤ 50, in quarterly windows |
| A Sunday purchase shows up mid-week | Card settlement delay (`settled_at` +1–2 days) | The skill reads card patterns on `emitted_at` |
| "Lots of false positives" | The skill lacks context by design | Announced in the report: every point is "to document", not a fault — sort them with your accountant |
| Non-French company | The cited rules are French | The skill switches to the universal axes and says so — it never invents local rules |

## 🔒 Security reminder

The skill is **fully read-only**: no write tool is ever called. It cannot modify a transaction, set a
label, or move a cent. And on the analysis side: this is an **educational simulation** — not tax advice,
not the administration's position. Remediation decisions are made **with your accountant**.
