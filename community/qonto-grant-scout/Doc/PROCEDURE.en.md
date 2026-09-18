# 📖 Setup & usage guide — qonto-grant-scout

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Connect the Datagouv MCP (recommended)
1. Same path: Settings → **Connectors** → search **Datagouv** (data.gouv.fr) → *Add*
2. Check: ask Claude "*Search data.gouv for business aid datasets*" → results show up

> ⚠️ Without Datagouv, the skill runs in an **honest degraded mode**: full spending profile
> + generic aid families + the official portals to explore. It says so plainly.

### Step 3 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-grant-scout/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

## 2️⃣ Typical usage (~5 min, worth repeating every quarter)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**What public funding could I target, based on my real spending?**" | Company profile (sector, region, size) + spending-signals table |
| 2 | Check/correct the displayed profile (inferred sector? region?) | The skill restarts from the corrected profile — searches get sharper |
| 3 | Let the Datagouv search run | Shortlist of leads: scheme · why your account matches · criteria to confirm · dated source · next step |
| 4 | Pick a lead: "**Draft the brief for the training-fund lead**" | Ready-to-send text block (for the accountant, the training fund, the regional desk) |
| 5 | **Verify with the issuing body** before filing anything | The skill delivers leads, never acquired rights |

## 3️⃣ Copy-paste prompts

- "**What public funding could I target, based on my real spending?**" → the full journey
- "**My company's profile, as seen by my account**" → profile + signals only, no search
- "**We're investing in equipment this year — what exists in my region?**" → targeted search on one category
- "**Analyze my training spend: is there aid for that?**" → the demo's flagship scenario
- "**Re-check: any new leads since last time?**" → the quarterly re-scan

## 4️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: profile + signals, sourced and dated shortlist, limits | **Always** — the baseline |
| **Grant radar** | **HTML** file/artifact: signals × aid families, leads at the intersections, 🟢🟡🔵 tags | When the host renders files; automatic fallback to tables otherwise |
| **Per-lead brief** | Ready-to-send text block: signal, scheme, criteria to confirm, source | On request, for each retained lead |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails right away | Missing `bank_account_id`/`iban` | The skill **always** calls `get_organization` first |
| `403 missing oauth scope` on `list_cash_flow_categories` | Outside the claude.ai connector scope | Expected — the skill uses labels (`list_labels`) instead |
| Huge / truncated responses | Pagination too wide | The skill paginates `per_page` ≤ 50 everywhere |
| "No aid dataset found" | Referential unavailable or renamed on data.gouv.fr | The skill widens the search, then switches to degraded mode (aid families + official portals) and says so |
| `query_resource_data` fails on a resource | Non-tabular resource (PDF, malformed CSV) | The lead becomes a sourced link to the dataset page — stated as such |
| Stale leads / scheme closed | Dataset not refreshed | Every lead carries the dataset date; > ~18 months = 🟡 degraded tag — always verify at the source |
| Empty sector in the profile | `get_organization` without a NAF code | The skill infers it from the flows and says so; correct it in the conversation and it restarts from the right one |
| Card spending on the wrong dates | Matching on the wrong timestamp | The skill uses `emitted_at`, not `settled_at` (1–2 day gap) |

## 🔒 Security reminder

The skill is **read-only**: no Qonto writes, no application filed, no commitment made.
On the data side: only **generic keywords** (sector, region, aid family) ever reach Datagouv —
never an amount, a counterparty name, or an IBAN. And every lead is a **lead to verify** with the
issuing body: the skill never says "you are eligible".
