# 📖 Setup & usage guide — qonto-accountant-handoff

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-accountant-handoff/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Connect Google Drive and Gmail (optional, recommended)
1. Still in **Connectors**: add **Google Drive**, then **Gmail** (Google OAuth)
2. Done — the skill **detects them automatically** on every run

> ⚠️ Both connectors are **optional**. Without them, the skill produces the same pack
> locally (structured folder of markdown + CSV) and you forward it however you like.

## 2️⃣ Monthly usage (the start-of-the-month ritual, ~5 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Prepare the June pack for my accountant**" | Statements + invoices + receipt status, tables shown |
| 2 | Read the **missing list** (date, counterparty, amount) | You know exactly which receipts to chase — run **qonto-receipt-hunter** if needed |
| 3 | Review the **handoff letter** (attention points, questions) and amend it if needed | The letter says what YOU want to tell the firm |
| 4 | Confirm the filing → `Accounting/YYYY/MM/` tree on Drive + Gmail **draft** created | The pack is filed, the email is ready |
| 5 | In **Gmail → Drafts**: proofread → **send it yourself** | Handoff done ✅ — the skill never sends |

## 3️⃣ On-demand usage

- "**What's missing before I send March to my accountant?**" → receipt status + the precise missing list
- "**Prepare the Q2 pack**" → same pack, quarter scope
- "**Rework the handoff letter: add the question about the leasing contract**" → amended letter, pack updated
- "**How is receipt coverage looking this month?**" → coverage table, without generating the whole pack

## 4️⃣ Output formats (where does the pack land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: pack contents, coverage, missing list, the letter | **Always** — the baseline |
| **Google Drive folder** | `Accounting/YYYY/MM/`: letter, statements, invoices, receipt status | When the Drive MCP is detected — filing announced first |
| **Gmail draft** | Recap email to the firm, letter as body, link to the folder | When the Gmail MCP is detected — **never sent by the skill** |
| **Local pack** | Structured folder of markdown + CSV, described file by file | Without Drive/Gmail |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails right away | `bank_account_id`/`iban` is required | The skill **always** calls `get_organization` first |
| Huge responses / slowness | Missing pagination | The skill paginates everywhere with `per_page` ≤ 50 |
| No statement for the requested month | The month isn't closed yet (or the account opened mid-month) | Wait for month close — meanwhile, a partial pack, labelled as such |
| Month-boundary transactions missing / extra | Card settlement delays: `emitted_at` vs `settled_at` (1–2 days apart) | The skill shows both dates and flags edge cases |
| `403 missing oauth scope` on `list_cash_flow_categories` | Outside the claude.ai connector scope | Expected — the skill uses labels instead |
| No Drive filing / no Gmail draft | MCP not connected | Expected — a local pack is produced; connect the connectors (step 3) for the automation |
| Attachment download link expired | Attachment URLs are short-lived | Ask again — the skill fetches the links at filing time, not before |

## 🔒 Security reminder

On the Qonto side, the skill is **read-only** — no write tool is used, nothing to approve.
The only two writes happen on your side: a folder on **your** Google Drive (announced first),
and a **draft** in **your** Gmail. You always hit send yourself. And the skill does not do the
accounting: it prepares the material — your accountant stays the professional.
