# 📖 Setup & usage guide — qonto-carbon-ledger

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-carbon-ledger/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — (Optional) Connect the Datagouv MCP
If a **Datagouv** connector is present, the skill offers to cross-check its embedded factors against current ADEME datasets. Otherwise it uses its embedded (sourced, dated) factors and says so — **nothing else to install**.

> 💡 No sub-account, no write, no approval: the skill is 100 % read-only.

## 2️⃣ Typical usage (the 2-minute footprint)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**What's my company's carbon footprint?**" | 24–36 months of debits read and classified into emission categories |
| 2 | Read the table: footprint ~N tCO2e/year **with its range**, breakdown per category (factor + source + vintage on every line) | You know where every tonne comes from — and how uncertain it is |
| 3 | Check the **top-3 levers**, ranked by estimated impact and cost direction (free / saves money / costs money) | You know where to act first, on your real amounts |
| 4 | (Optional) Ask for the **HTML dashboard** | Footprint gauge + category bars + trend + levers |

## 3️⃣ On-demand usage

- "**Which categories emit the most for me?**" → category breakdown, dominant ones first
- "**Did my footprint go down since last year?**" → trend across 24–36 months
- "**How much does my digital stack weigh?**" → zoom on one category, with its counterparties
- "**How reliable is that number?**" → the skill explains the monetary method, its limits and the ±50 % uncertainty
- "**Prepare a pre-assessment for my carbon consultant**" → export of categories, amounts and factors — stating that the official report remains the consultant's job

## 4️⃣ Output formats (where does the footprint land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: footprint + range, categories, trend, levers | **Always** — the baseline |
| **Interactive dashboard** | **HTML** file/artifact: gauge with uncertainty band, category bars, trend, levers | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails right away | Missing `bank_account_id`/`iban` | The skill **always** calls `get_organization` first |
| Huge / truncated responses | Pagination too wide | `per_page` ≤ 50, 3-month windows — handled by the skill |
| `403 missing oauth scope` on `list_cash_flow_categories` | Outside the claude.ai connector scope | Expected — the skill classifies via counterparties + **labels** instead |
| Many "unclassified" debits | Ambiguous counterparties, no labels | Label your top counterparties in Qonto; above ~20 % the skill warns the estimate is weak |
| Footprint looks huge | A one-off purchase (vehicle, machine) blended into the flow | The skill flags purchases ≥ ~€5,000 apart — check the "one-offs" line |
| Country ≠ France | Factors calibrated for FR/EU | Identical method, factors flagged as needing adaptation — the estimate is still produced and tagged |

## 🔒 Security reminder

The skill is **100 % read-only**: no write tool, no transfer request, no payment — there is nothing
to approve. It **never** sells or recommends carbon offsets. Its figures are **orders of magnitude**
(±50 % and more, printed everywhere): for a regulatory assessment (BEGES / CSRD), use a specialized
provider — the skill itself will remind you.
