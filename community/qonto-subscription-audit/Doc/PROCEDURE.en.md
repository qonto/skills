# 📖 Setup & usage guide — qonto-subscription-audit

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-subscription-audit/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Connect the Gmail MCP (optional)
1. Settings → **Connectors** → search **Gmail** → *Add*
2. With Gmail: negotiation emails AND the monthly digest land as **drafts** in your mailbox (never sent)
3. Without Gmail: the skill outputs the text to copy-paste — everything else works the same

## 2️⃣ Typical usage (the monthly audit, ~5 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Audit my subscriptions**" | 24–36 month scan: full inventory, cadences (monthly/quarterly/yearly), **total annualized cost** |
| 2 | Read the statuses (✅👥🧟🎣) and the **🌱 New** section | You know who charges you what, what's duplicated, what's dormant — and what just started |
| 3 | Confirm or dismiss the proposed zombies 🧟 and newborns 🌱 | The skill never decrees — you confirm usage |
| 4 | Read the hikes table and the **cumulated annual overcost** | You know what silent inflation costs you per year, FX/VAT/usage excluded |
| 5 | Say: "**Show me the dashboard**" | Dashboard built directly in Claude; "export it as HTML" → self-contained file in Qonto colors |
| 6 | Say: "**Write the negotiation email for [supplier]**", then confirm | Gmail draft (or text): tenure, volume, hike record → **review, adjust, send it yourself** ✅ |

> 💡 To **protect a subscription with a capped virtual card** (monthly cap, charges beyond it declined): that's the **`qonto-subscription-guardian`** skill — the audit finds, the guardian protects.

## 3️⃣ On-demand usage

- "**How much do I pay in subscriptions per year?**" → the shock number + portfolio sorted by annual cost
- "**What am I still paying for that I don't use?**" → 🧟 candidates + 🎣 converted trials, to confirm
- "**Is this €19 charge from [merchant] a subscription?**" → 🌱 analysis: the signals and a "probable / unlikely, to confirm" verdict
- "**Who raised their prices this year?**" → dated hikes (old → new, %, tag 🟢🟡🔴)
- "**Did my cloud unit price go up, or just my usage?**" → implicit price when isolable, said plainly otherwise
- "**Prepare my subscription digest for the month**" → draft email: actives, month total, 3-month forecast, hikes, new 🌱 lines (when a mail MCP is present)

## 4️⃣ Output formats (where does the audit land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: shock number, portfolio by status, New 🌱 section, hikes, variable usage kept separate | **Always** — the baseline |
| **Dashboard in Claude** | Rendered directly in the conversation (artifact): annual cost, category breakdown, statuses ✅👥🧟🎣🌱, hikes with deltas, 3-month forecast | When the host allows it |
| **HTML export** | The same dashboard as one self-contained file, Qonto palette (violet #6B4EFF / black #1D1B29 / white, light/dark) | On request — keep it or share it |
| **Emails** | Gmail draft (MCP present + your consent) or copy-paste text: negotiation + monthly digest | **Never sent** without you |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| "`list_transactions` fails" at start | Missing `bank_account_id`/`iban` | Expected — the skill always calls `get_organization` first |
| Huge / truncated responses | Pagination too wide | The skill paginates `per_page` ≤ 50, 3-month windows |
| `403 missing oauth scope` on `list_cash_flow_categories` | Outside the claude.ai connector scope | Expected — the skill relies on counterparties and labels instead |
| A known yearly subscription doesn't show up | Scanned history < 24 months: only one occurrence visible | The skill says so honestly; rerun with more history if the account has it |
| A supplier shows up twice | Card/SEPA variants not merged (unusual label) | Tell it: "merge X and Y" — normalization takes the hint |
| Wrong cadence detected on card payments | Matching done on `settled_at` (1–2 day drift) | The skill uses `emitted_at` for cadence math |
| A "hike" on a USD-billed subscription | Exchange-rate wobble, not price | The skill flags the series as FX-exposed and won't conclude |
| A flagged 🌱 isn't actually a subscription | Early detection is probabilistic (< 3 occurrences) | Answer "no": the line is dismissed — 🌱 is a hypothesis, never a verdict |
| No Gmail draft created | Gmail MCP absent or unauthorized | The skill says so and outputs copy-paste text — nothing lost |
| No dashboard shown | The host doesn't render artifacts/files | The markdown tables remain the complete deliverable |

## 🔒 Security reminder

The skill is **100 % read-only** on Qonto: no writes, no transfers, no cards created —
for the capped card, that's the `qonto-subscription-guardian` skill, with your consent and your SCA.
Emails (negotiation, digest) are **drafts** — you review, edit, and send them (or not) yourself.
No recipient is ever added without you. IBANs are masked in every report.
