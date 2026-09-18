# 📖 Setup & usage guide — qonto-prescription-guard

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.
> ⚖️ Reminder: the skill is **not legal advice** — it alerts, a lawyer validates.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-prescription-guard/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Fill in your client records (recommended)
1. In the **Qonto app**: Invoicing → Clients → open each record
2. Add the **SIREN/SIRET or VAT number** of your business customers
3. Done — the skill will qualify B2B (5 years) vs B2C (2 years) automatically; without identifiers, it **asks** instead of guessing

> ℹ️ No sub-account, no write permission to set up: the skill is **100% read-only**.
> There is literally nothing to approve.

## 2️⃣ Quarterly usage (the ritual, ~5 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Which unpaid invoices are at risk of becoming time-barred?**" | Full scan, "act before…" schedule sorted by urgency × amount |
| 2 | Answer the B2B/B2C questions on ambiguous clients | Refined periods (5 vs 2 years) — both dates shown while ambiguous |
| 3 | Declare what the bank can't see (written acknowledgment, payment order already filed) | Clocks reset at the right dates, lines tagged "user-declared" |
| 4 | Read the 🔴 alerts and the detected resets | You know what to chase, what to hand to a bailiff, and by when |

## 3️⃣ On-demand usage

- "**Is this 2023 invoice still recoverable?**" → single-receivable analysis, interruptive acts searched in the transactions
- "**How many euros become unrecoverable within 12 months?**" → totals at risk per horizon
- "**This client sent me a small transfer in March — what does it change?**" → recompute: partial payment = period probably reset
- "**Show me my receivables timeline**" → HTML timeline (when the host renders files)

## 4️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: "act before…" schedule, totals at risk, detected resets | **Always** — the baseline |
| **Interactive timeline** | **HTML** file/artifact: one bar per receivable, today marker, color by urgency | When the host renders files; automatic fallback to tables otherwise |
| **"Probably time-barred" list** | Separate section, never mixed with living receivables | Every scan |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| Error on `list_transactions` | The tool requires `bank_account_id`/`iban` | The skill always calls `get_organization` first — expected |
| Huge responses / slowness | Pagination too wide | The skill paginates `per_page` ≤ 50 and windows history by quarter |
| Client never qualified as B2B | Record lacks SIREN and VAT number | Answer the skill's question, and fill in the record in the app for next time |
| Partial payment not detected | Collected outside Qonto (another bank, cash) | Declare it to the skill — the heuristic only sees the Qonto account |
| Invoice paid but listed unpaid | Status not updated in Qonto | Mark it paid in the app; the skill flags it but changes nothing (100% read-only) |
| No legal dates in the report | Organization outside France | By design: age-of-receivables only, never an invented rule |

## 🔒 Security reminder

The skill **cannot change anything**: no MCP writes, no transfers, no status changes —
it reads, computes, and alerts. It is **not legal advice**: dates are prudent estimates
based on public rules (art. L110-4 Commercial Code, L218-2 Consumer Code, 2224 and
2240–2244 Civil Code). Before taking legal action — or writing a receivable off —
have a lawyer or bailiff validate.
