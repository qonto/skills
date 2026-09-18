# 📖 Setup & usage guide — qonto-asset-registry

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-asset-registry/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Nothing else
The skill is **100% read-only**: no configuration, no sub-account, no write permission.
It works with what your account already contains — transactions, supplier invoices, attachments.

## 2️⃣ Typical usage (the yearly check-up — or before renewing your insurance, ~5 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**What equipment does my company own?**" | 24–36 month scan → register sorted by category/value, statuses ✅ 💰 ❓ 🔁, 📎 column |
| 2 | Review the "❓ to confirm" lines (generalist merchants) | You confirm or reclassify in one sentence — nothing is guessed |
| 3 | "**Show the indicative depreciation**" | Usual life, annual charge, estimated net book value — for your accountant to validate |
| 4 | "**Generate the insurance inventory**" | Ready-to-send table: description, date, purchase value, receipt |
| 5 | For the missing 📎: chain with `qonto-receipt-hunter` | Receipts recovered before you ever need them |

## 3️⃣ Copy-paste prompts

- "**What equipment does my company own? Build the asset register.**"
- "**Use an €800 threshold instead of €500.**" (threshold is configurable)
- "**Which assets have no linked receipt?**"
- "**Generate the insurance inventory, ready to send to my insurer.**"
- "**What is my IT hardware still worth today?**" (estimated net book value)
- "**Build an HTML dashboard of the register.**"
- "**I sold [that asset]: take it off the register.**" (disposals are yours to declare)

## 4️⃣ Output formats (where does the register land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: register, depreciation, summary (N assets · total value · receipt gauge) | **Always** — the baseline |
| **Dashboard / export** | Self-contained **HTML** file/artifact in the Qonto palette: register by category, completeness gauge, insured total | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); fallback to tables otherwise |
| **Insurance inventory** | Ready-to-send table (description, purchase date, value, receipt) | On demand — ideally before the claim |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` asks for an account | The tool requires `bank_account_id`/`iban` | The skill calls `get_organization` first, always |
| Huge responses / slow scan | Insufficient pagination | `per_page` ≤ 50, 3-month windows — handled by the skill |
| A card purchase can't be found at the invoice date | Card settlement delay (1–2 days) | Match by `emitted_at`, not `settled_at` — handled |
| The same asset shows up 3 times | Installment payments | Installments merged into **one** asset at full value |
| A line stays "❓ to confirm" | Generalist merchant, mute label | Open the receipt (`get_attachment`) or state the nature in one sentence |
| 📎 missing receipt on a line | No attachment on the transaction | Chain with `qonto-receipt-hunter` to recover it |
| Leased hardware counted in the total | — | Doesn't happen: recurring payments to a financer → "🔁 financed, not capitalized here", excluded from totals |
| No €500 threshold proposed | Non-French organization | Expected — the mechanics are universal, but the threshold and lives are French practice; the register stays complete |

## 🔒 Security reminder

The skill **writes nothing** — that's its strongest guarantee: no write tool is ever called,
no category changed, no document uploaded, no request created. It reads your account,
computes, and presents the register. The €500 threshold and the depreciation lives are
**customary indications, not accounting entries**: the final call belongs to your accountant.
