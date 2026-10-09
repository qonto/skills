# 📖 Setup & usage guide — qonto-brand-shield

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-brand-shield/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — INPI access (optional)
1. The data.inpi.fr API requires an **INPI account** and then an **API access request** (form on data.inpi.fr) — not instant
2. **Without it, the skill still works**: it delivers the whole financial side, then hands you a pre-filled search link on data.inpi.fr — the manual check takes ~2 minutes
3. The skill only integrates registry facts **reported by the API or by you** — never scraping, never guessing

## 2️⃣ Typical usage (~5 min, INPI check included)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Is my brand protected?**" | 12–36 month scan → investment total per brand (design, domains, ads, print) |
| 2 | Read the table (buckets, amounts, 🟢🟡 tags) | You know what the brand has already cost you, bucket by bucket |
| 3 | Click the pre-filled data.inpi.fr link, look for 2 minutes, report back what you see | Protection status integrated into the report (registered? by you? classes? renewal?) |
| 4 | Read the **exposure** + the **pre-filing dossier** (name, suggested classes, indicative cost) | Informed decision: file (~€190–270) or accept the risk |

## 3️⃣ On-demand usage

- "**How much have I invested in my brand over the last 18 months?**" → total per brand and per bucket
- "**Suggest my Nice classes**" → 1–3 classes from real activity, to validate
- "**Prepare my INPI pre-filing dossier**" → name, classes, indicative cost, inpi.fr link
- "**Is my trademark renewal coming up?**" → the 10-year window (when the filing is known)

## 4️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (investment, status, exposure, alerts) | **Always** — the baseline |
| **Interactive one-pager** | **HTML** file/artifact: exposure gauge, buckets, INPI status, dossier | When the host renders files; automatic fallback to tables |
| **Pre-filing dossier** | Structured text, ready to take to inpi.fr | Every unprotected brand |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails | The tool requires `bank_account_id`/`iban` | The skill calls `get_organization` first — always |
| Huge responses / slowness | Pagination too wide | The skill paginates `per_page` ≤ 50, in 3-month windows |
| `403 missing oauth scope` on `list_cash_flow_categories` | Outside the claude.ai connector scope | Expected — the skill classifies by counterparty + labels, not categories |
| The attachment doesn't reveal the brand name | Document without a usable mention | Fallback on label + counterparty; attachment tagged 🟡 |
| Domains not seen as an annual expense | History too short | Annual cadences are detected over 24–36 months |
| "I don't have INPI API access" | Account + access request required | The honest degraded mode: pre-filled data.inpi.fr link + 2-minute checklist |

## 🔒 Security reminder

The skill is **100 % read-only**: it creates no MCP write — no transfer, no invoice, nothing to
approve. The trademark filing happens on inpi.fr, decided by you, after human validation.
Trademark similarity is an indicative alert, **not legal advice**: for the filing itself,
an IP professional is recommended.
