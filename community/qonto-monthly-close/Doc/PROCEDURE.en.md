# 📖 Setup & usage guide — qonto-monthly-close

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-monthly-close/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — (Optional) Connect Gmail
1. Settings → **Connectors** → add **Gmail**
2. The skill detects it on its own and offers to hunt the inbox for missing receipts
3. Without Gmail: the skill says so in one line and continues — nothing else changes

> ℹ️ No sub-account, no Qonto-side configuration: this skill is **fully read-only**,
> it needs zero write permissions to do its job.

## 2️⃣ Monthly usage (the first-of-the-month ritual, ~3 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Close my month**" | The skill scopes the month (last full calendar month by default) and announces its plan |
| 2 | Let the review run (~2–3 min depending on volume) | Receipts, VAT, anomalies, unlabeled, unpaid, comparison — in one pass |
| 3 | Read the **closing report**: scorecard + tables + prioritized to-do | You know exactly what to fix, in which order, and why |
| 4 | Work through the to-do: each line points to the dedicated skill or the one-tap action in the Qonto app | Month-end done in ~10 minutes ✅ |

## 3️⃣ On-demand usage

- "**Close my May**" → full review of a specific month
- "**Anything unusual on my account last month?**" → the 3 detectors only (unusual spend, duplicate, new beneficiary)
- "**Which receipts am I missing, biggest first?**" → the stakes-ranked list
- "**Compare June to May**" → top category rises and falls
- "**What's my VAT this month?**" → collected − deductible, with the caveats

## 4️⃣ Output formats (where does the report land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: scorecard, receipts, VAT, anomalies, comparison, unpaid, to-do | **Always** — the baseline |
| **Closing dashboard** | **HTML** file/artifact: scorecard, completeness gauge, VAT tile, anomaly cards, checklist | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails right away | Missing `bank_account_id`/`iban` | Expected — the skill always calls `get_organization` first |
| `403 missing oauth scope` on `list_cash_flow_categories` | Outside the claude.ai connector scope | Expected — the skill uses `list_labels` instead |
| Huge responses / slowness | Pagination too wide | The skill paginates `per_page` ≤ 50 everywhere |
| A card expense from the 30th–31st "missing" from the month | `emitted_at` vs `settled_at` lag (1–2 days) | The skill reasons on `emitted_at` for card operations |
| Collected VAT looks wrong | Cash-basis VAT regime (`on_receipts`) | The skill detects it on the invoices and counts payments received, not invoices issued |
| Too many / zero anomalies | History < 3 months → thin baseline | The skill says so and softens its thresholds; it improves as history grows |

## 🔒 Security reminder

This skill is **fully read-only**: it calls no write tool — nothing is created, modified, sent
or moved on your account. The report **proposes**; you act, either directly in the Qonto app or
by chaining the dedicated skills (`qonto-receipt-hunter`, `qonto-invoice-chaser`, `qonto-tax-pilot`).
And in any case: the Qonto MCP cannot move money — any transfer requires your own SCA (2FA) in the app.
