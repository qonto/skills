# 📖 Setup & usage guide — qonto-einvoice-ready

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto clients*" → your client records show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-einvoice-ready/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Nothing else to configure
- The public registry API (`recherche-entreprises.api.gouv.fr`) is **public, no key, no account**
- Optional: know your company size (large / mid-cap / SME) — the skill usually finds it in the registry, otherwise it asks

## 2️⃣ Typical run: audit + fix (~5 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Am I ready for the e-invoicing mandate?**" | Readiness score + your timeline + incomplete records listed |
| 2 | Read the audit (record by record: SIREN, intra-EU VAT, address) | You know exactly what would block a Factur-X |
| 3 | Say: "**Complete my client records**" | The skill queries the public registry and shows a **line-by-line preview** |
| 4 | Check the preview (homonyms → the skill asks), then confirm ("yes, update") | `update_client` field by field, outcome reported |
| 5 | Re-read the score | Readiness before/after + action plan for the rest |

## 3️⃣ On-demand usage

- "**Which e-invoicing timeline applies to my company?**" → receiving 2026-09-01 + your issuing date (2026 or 2027)
- "**Which clients would block a Factur-X today?**" → incomplete records, field by field
- "**Am I exposed to e-reporting?**" → foreign + B2C clients spotted in records and money flows
- "**Find this client's SIREN**" → public registry lookup, preview, confirmation

## 4️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: score, incomplete records, timeline, e-reporting exposure | **Always** — the baseline |
| **Fix preview** | One table: client · field · current → proposed · source, pending confirmation | Every proposed fix |
| **Readiness report** | **HTML** file/artifact: before/after gauge, countdown, action plan | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| Error on `list_transactions` | Missing `bank_account_id`/`iban` | Expected — the skill always calls `get_organization` first |
| Truncated / slow responses | Page size too large | The skill paginates `per_page` ≤ 50 everywhere |
| Client not found in the registry | Trade name ≠ legal name | Give the skill the SIREN, or refine with the zip code; otherwise the record is skipped |
| Several homonym companies | Common names in the registry | The skill shows the candidates (name, city, SIREN) and **asks** — never auto-matches |
| VAT number labeled "derived" | Computed from the SIREN (FR key + 2 digits) | Expected — have the client confirm it |
| Public registry unavailable | data.gouv API down / maintenance | The audit and score still run; only the live fix waits |
| Update not applied | Confirmation not given in the conversation | By design: no `update_client` without an explicit "yes" after the preview |
| Organization country ≠ FR | The reform is French only | The skill switches to a generic completeness audit (stated plainly) |

## 🔒 Security reminder

The skill's only write is `update_client`: it **never touches money**, only client records. Every change
is shown in a preview (current → proposed value, with its source) and written only after **your** explicit
confirmation — field by field, never in bulk. And the choice of your accredited e-invoicing platform (PDP)
is yours: the skill informs, it doesn't decide.
