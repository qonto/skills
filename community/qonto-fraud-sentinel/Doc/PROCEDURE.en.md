# 📖 Setup & usage guide — qonto-fraud-sentinel

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-fraud-sentinel/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — (Optional) Connect Gmail
Same path as the Qonto MCP (Connectors → Gmail). The skill **detects it on its own**: when present, it offers a daily digest draft; when absent, it runs on pure Qonto without asking for anything.

> 💡 Tip: use a **dedicated Claude project** ("Morning scan") — trusted counterparties stay remembered there from one day to the next.

## 2️⃣ Daily usage (the morning routine, ~30 s)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Run my morning check**" | Baseline calibrated (3–6 months) + latest transactions screened against the six signals |
| 2 | Read the report: ranked alerts 🔴🟠🟡 or a numbered "all clear" | Every alert = the transaction + why (baseline) + the recommended action |
| 3 | For a false positive (a legitimate new supplier…): "**trust ACME**" | Remembered — no more never-seen alerts for that counterparty |
| 4 | When a card is implicated and you want to act: "**yes, lock the card**" | `change_card_status` locks the card — reversible in the app anytime |

## 3️⃣ On-demand usage

- "**Anything unusual on my account this week?**" → scan widened to 7 days
- "**Did X charge me twice?**" → targeted duplicate search on that counterparty
- "**Is this €249 debit normal?**" → comparison against that counterparty's and the category's baseline
- "**Which SEPA direct debits are new this month?**" → first uses of mandates

## 4️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown alert table (transaction · signal · baseline · action · severity) or an "all clear" with scan window and baseline depth | **Always** — the baseline |
| **Morning report** | Compact **HTML** file/artifact: ranked alerts, baseline, card status | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to the table |
| **Email digest** | Gmail draft of the daily scan | Only when a Gmail MCP is detected — optional |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails on the first call | Missing `bank_account_id`/`iban` | Expected — the skill **always** calls `get_organization` first |
| Huge / truncated responses | Pagination too wide | The skill paginates `per_page` ≤ 50 everywhere |
| Missed or false card duplicates | Comparing on `settled_at` (1–2 day lag) | The skill dates card transactions on **`emitted_at`** |
| `403 missing oauth scope` on `list_cash_flow_categories` | Outside the claude.ai connector scope | Expected — the skill falls back to transaction-level categories and labels |
| Too many "never seen" alerts | Young account (< 3 months) or many new suppliers | Cautious mode announced — trust-mark the legitimate counterparties, the noise settles within days |
| No email digest | Gmail MCP absent | Optional — the core runs on pure Qonto |

## 🔒 Security reminder

The skill **cannot** move money — no scenario allows it. Its only write is a **card lock**,
reversible, executed only after your explicit confirmation in the conversation. Unlocking,
definitive opposition, SEPA mandate revocation and card replacement happen in the Qonto app,
by you. And remember the skill's editorial line: **a signal is not a fraud** — it's an
invitation to verify, with the numbers laid out.
