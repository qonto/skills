# 📖 Setup & usage guide — qonto-supplier-detective

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-supplier-detective/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Maximize the detection surface (recommended)
1. In the **Qonto app**: import/centralize your **supplier invoices** (Purchases section) — the more there are, the more the detective sees
2. That's it: the skill is **100% read-only**, there is nothing else to configure or authorize

> ℹ️ Without imported supplier invoices, the skill runs a transaction-only pass
> (twin debits + IBAN watch on transfers) and says so plainly.

## 2️⃣ Quarterly usage (the audit, ~10 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Run the supplier audit**" | Full paginated sweep (progress summarized every ~300 invoices), names normalized, subscriptions and credit notes cleared |
| 2 | Read the **IBAN alerts 🚨** at the top of the report | For each change: call the supplier **at the number you already know**, before the next payment |
| 3 | Go through the findings table (recoverable amount, evidence, confidence 🟢🟡) | You know what to claim, from whom, with which exact references |
| 4 | Say: "**Draft the claim email for finding #1**" | Ready-to-send draft: invoice number, both transfer references, dates, amount |

## 3️⃣ On-demand usage

- "**Did I pay anything twice this quarter?**" → targeted D2 pass on the period
- "**Has any supplier changed their IBAN recently?**" → IBAN watch alone, with a coverage note
- "**Check the invoices from [supplier]**" → mini-audit on one counterparty
- "**That's a subscription, not a duplicate**" → the skill clears the line and updates the total
- "**Compare invoice #X with what I actually paid**" → D3 pass on a single invoice

## 4️⃣ Output formats (where does the case file land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown report: IBAN alerts 🚨 on top, findings ranked by recoverable amount, estimated total, cleared cases | **Always** — the baseline |
| **Interactive case file** | **HTML** file/artifact: findings board, evidence cards, recoverable gauge | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to markdown otherwise |
| **Claim email** | Ready-to-send draft, IBANs masked | On request, finding by finding |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` demands an account | `bank_account_id`/`iban` are required | The skill calls `get_organization` first — always |
| Huge responses / audit crawling | Pagination too wide | `per_page` ≤ 50 everywhere, 3-month windows on transactions |
| Can't filter invoices by status | Status filters not exposed on this MCP | The skill filters client-side on `status` |
| A subscription shows up as a duplicate | History too short to see the cadence | Say so ("that's a subscription") → cleared; ≥ 6 months of history recommended |
| Card payment not found when matching | `settled_at` drifts 1–2 days | The skill matches by `emitted_at` |
| No IBAN alert despite a real change | IBAN not exposed for that supplier (card payment, direct debit) | Coverage note in the report — check the beneficiary in the Qonto app |

## 🔒 Security reminder

The skill is **100% read-only**: it calls no Qonto write tool, changes nothing, pays nothing.
It builds the case file; **only you** act on it. And the golden rule for an IBAN change — the classic
anti-wire-fraud practice: **call your supplier at the number you already know** (old contract, official
website), never at the number or address in the email announcing the change. When in doubt, don't pay.
