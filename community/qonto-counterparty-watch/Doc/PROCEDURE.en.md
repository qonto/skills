# 📖 Setup & usage guide — qonto-counterparty-watch

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Connect the Datagouv MCP (recommended)
1. Same path: Connectors → search **Datagouv** (data.gouv.fr) → *Add*
2. This is what activates **legal-health checks** (SIRENE + BODACC)
3. Without it: the skill says so and delivers Qonto-only scoring (exposure + delays) — already actionable

### Step 3 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-counterparty-watch/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

> 💡 Reliability bonus: fill in the **VAT number** (`tax_identification_number`) on your Qonto client records —
> the skill extracts the SIREN from it, turning legal checks from a name match into a certainty.

## 2️⃣ Weekly usage (the Monday-morning ritual, ~3 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Rank my clients and suppliers by risk**" | Counterparty inventory + sorted 🟢🟡🔴 risk table |
| 2 | Read the priority alerts (exposure × BODACC cross-signals) | You know who to chase **this week**, and why |
| 3 | Check the coverage note (verified / not verifiable) | You know what was actually checked, and when |
| 4 | 🔴 case with an open procedure: confirm on bodacc.fr → registered-mail dunning, claim declaration if needed | The invoice gets a chance to be saved ✅ |

## 3️⃣ On-demand usage

- "**Is my client X in receivership?**" → dated SIRENE + BODACC check, with the exposure next to it
- "**Who owes me money, and for how long?**" → unpaid invoices in ageing buckets (0–30 / 31–60 / 61–90 / 90+)
- "**Which clients are paying later and later?**" → delay trends per client (actual vs `due_date`)
- "**Which suppliers am I most dependent on?**" → annualized spend + legal health for each

## 4️⃣ Output formats (where does the risk table land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (sorted risk table, alerts, coverage) | **Always** — the baseline |
| **Interactive dashboard** | **HTML** file/artifact: exposure × health matrix, ageing chart, alert cards | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |
| **Coverage note** | Verified / not verifiable / registry unavailable counters | Every report |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails right away | Missing `bank_account_id`/`iban` | Expected — the skill **always** calls `get_organization` first |
| Huge / truncated responses | Pagination too wide | The skill paginates `per_page` ≤ 50 everywhere |
| The same counterparty shows up twice | Bank label ≠ client record name (SEPA noise, legal suffixes) | Normalization merges them; otherwise align the Qonto client record name |
| Counterparty "not verifiable" | No SIREN (client record without a VAT number) or no registry match | Fill in the VAT number on the Qonto client record → SIREN extracted |
| No legal health in the report | Datagouv MCP not connected | The skill announces it and continues Qonto-only; connect Datagouv (step 2) |
| A known procedure isn't found | BODACC coverage through data.gouv can be partial | The skill owns it: "nothing found" ≠ "guaranteed healthy"; confirm on bodacc.fr |

## 🔒 Security reminder

The skill is **100 % read-only**: it calls no Qonto write tool, creates nothing, sends nothing.
There is nothing to approve — the worst it can do is tell you an uncomfortable truth about a client.
Legal alerts are **signals**, not legal advice: for an open procedure, confirm on bodacc.fr and
talk to your lawyer or accountant before acting.
