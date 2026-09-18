# 📖 Setup & usage guide — qonto-crm-truth

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Connect the CRM (HubSpot or Airtable)
1. Same path: Settings → **Connectors** → search **HubSpot** or **Airtable** → *Add* (OAuth)
2. Check: "*List my Airtable bases*" (or "*my HubSpot companies*") → the CRM answers
3. **No CRM connected?** The skill still works, in report mode (Qonto clients scored, in the conversation) — it just won't offer writes

### Step 3 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-crm-truth/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

## 2️⃣ Typical usage (the pipeline review, ~5 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Which of my won deals never got paid?**" | Bank read (24 months) + CRM read |
| 2 | **Review the mapping table** CRM record ↔ Qonto client (🟢 exact · 🟡 likely · 🔴 ambiguous) and confirm / fix it | Matching locked in — never silent |
| 3 | Read the report: won-not-cashed deals, real revenue, LTV, observed delays, A/B/C scores | You know who actually pays, and when |
| 4 | Say "**yes, write it into the CRM**" after the field-by-field preview | Airtable columns / HubSpot properties filled ✅ |
| 5 | Open the CRM: sort by "Payer score" | Sales prioritizes clients who actually pay |

## 3️⃣ On-demand usage

- "**Is my top CRM account really my top payer?**" → CRM ranking vs bank ranking
- "**Score my Qonto clients**" (no CRM) → scored report in the conversation
- "**What's [client]'s average payment delay?**" → observed day +X, median and mean
- "**Which clients are drifting?**" → old last payments, growing delays
- Chain it: "**Chase the unpaid invoices you found**" → hands over to `qonto-invoice-chaser`

## 4️⃣ Output formats (where does the truth land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: scored clients, won-not-cashed deals, mapping table, write-back summary | **Always** — the baseline |
| **CRM write-back** | HubSpot custom properties / Airtable columns — skill-dedicated fields, never native ones | After confirmed matching + explicit go |
| **HTML one-pager** | CRM ranking vs bank ranking, score distribution | When the host renders files; fallback to tables otherwise |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails right away | Missing `bank_account_id`/`iban` | Expected — the skill calls `get_organization` first |
| Huge / truncated responses | Pagination too wide | The skill paginates `per_page` ≤ 50 everywhere |
| Airtable filter matches nothing (*select* field) | Choice IDs required, not labels | The skill calls `get_table_schema` before filtering |
| `create_field` rejected on Airtable | Insufficient rights on the base (creator needed) | Grant rights, or let the skill reuse existing columns |
| Same client shows up twice | Multiple spellings (case, accents, legal suffixes) | Normalized and merged — visible in the mapping table |
| A CRM record stays "unmatched" | No reliable key (name/email/VAT) | The skill asks — it never writes on an unconfirmed match |
| No CRM detected | HubSpot/Airtable not connected | Degraded mode announced: scored report in the conversation |

## 🔒 Security reminder

On the **Qonto** side the skill only **reads** — zero bank writes, it cannot touch money.
The only writes target the **CRM**, and only behind two locks: the mapping table **you** confirm,
then the exact preview of every value **you** approve. Scores describe payment behavior observed
on this account — not general creditworthiness.
