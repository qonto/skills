# 📖 Setup & usage guide — qonto-tax-pilot

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-tax-pilot/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Create the tax sub-account (recommended)
1. In the **Qonto app**: Accounts → **Create sub-account**
2. Name it with a recognizable keyword: "**Taxes & VAT**", "Tax", "Impôts"…
3. Done — the skill **detects it automatically** by name

> ⚠️ This step is manual because the Qonto MCP has no account-creation tool.
> Without a sub-account: the skill still computes and reports everything, it just won't propose transfers.

## 2️⃣ Monthly usage (the first-of-the-month ritual, ~3 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Set aside this month's taxes**" | Net VAT + IS/12 + CFE/12 computed, full breakdown shown |
| 2 | Read the breakdown (collected, deductible, confidence tags) | You know where every euro comes from |
| 3 | Confirm explicitly ("yes, create the request") | Transfer request created to the sub-account |
| 4 | On your **phone**: Qonto push notification → open → check the note (the calculation is in it) → **approve (SCA)** | Money set aside ✅ |

## 3️⃣ On-demand usage

- "**Where will my cash be at the end of September?**" → 90-day projection + tax schedule
- "**When is my next VAT due and how much?**" → dated, amount-estimated schedule
- "**What if my client pays 30 days late?**" → what-if simulation
- "**Can I afford this €5,000 purchase?**" → impact on the low point

## 4️⃣ Output formats (where does the schedule land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (schedule, provision, alerts) | **Always** — the baseline |
| **Interactive dashboard** | **HTML** file/artifact: 90-day curve, schedule with ✅/⚠️, vault gauge | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |
| **Qonto request note** | Text attached to the transfer request, **visible at SCA approval time** | Every time a provision is created |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `422` when creating the request | Missing `credit_account_currency` field (undocumented) | The skill always sends it |
| Can't decline a test request | `decline_request` requires `request_type: "multi_transfers"` (plural) | Handled by the skill |
| Sub-account not detected | Name lacks a keyword (tax/taxe/impôt/TVA) | Rename the sub-account in the app |
| No push notification | Qonto notifications disabled | Qonto app → Settings → Notifications |

## 🔒 Security reminder

The skill **cannot** move money. It creates a *request* that **only you** can approve with your
own 2FA in the Qonto app. You can decline it in one tap. Every request carries the full
calculation in its note — you approve with complete information.
