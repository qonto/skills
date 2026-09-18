# 📖 Setup & usage guide — qonto-sector-benchmark

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Connect the Datagouv MCP (recommended)
1. Same path: Settings → **Connectors** → search **Datagouv** (data.gouv.fr, the French open-data portal) → *Add*
2. Check: "*Search data.gouv for INSEE structural business statistics*" → datasets show up

> ⚠️ Without Datagouv: the skill still works — internal ratios + the "you vs you a year ago"
> self-benchmark. It will tell you explicitly at launch.

### Step 3 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-sector-benchmark/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 4 — Keep your NAF activity code handy (optional)
It's on your company registration documents. If `get_organization` doesn't expose it, the skill will ask — or infer it from your activity and **have you confirm it**.

## 2️⃣ Typical usage (the quarterly ritual, ~3 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Am I normal? Benchmark me against my sector**" | The skill reads the organization, confirms the sector (NAF), announces the mode (sector or internal) |
| 2 | Let the analysis run (24 months of transactions + invoices) | Your 5 real ratios appear, computations disclosed |
| 3 | Check the detected software subscription list | One sentence fixes any misclassified counterparty |
| 4 | Read the scorecard | Ratio · your value · reference (source · vintage · granularity) · verdict · year-over-year trend |
| 5 | Dig into the main finding ("why are my client delays drifting?") | The skill breaks it down per client, from Qonto data |

## 3️⃣ Prompts to copy-paste

- "**Am I normal? Benchmark me against my sector**" → the full health report
- "**How fast do my clients pay me, and is that good?**" → payment-delay focus, sourced sector reference
- "**Am I paying too much for software for a company like mine?**" → SaaS focus, detected list + verdict
- "**Compare me to myself a year ago**" → self-benchmark only (works everywhere, even without Datagouv)
- "**Redo the report at NAF division level**" → forces the coarser granularity if you doubt the exact class

## 4️⃣ Output formats (where does the check-up land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown scorecard: ratio · value · sourced reference · verdict · trend, + 2–3 narrative findings + the full source list | **Always** — the baseline |
| **Interactive scorecard** | **HTML** file/artifact: 5 gauges against the sector ranges, sources footnoted | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); fallback to markdown otherwise |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `403 missing oauth scope` on `list_cash_flow_categories` | Outside the claude.ai connector scope | Expected — the skill classifies via recurrence detection + labels |
| "Datagouv MCP not detected" | Connector absent or disconnected | The skill continues in self-benchmark mode; reconnect for sector data |
| No dataset at my exact NAF class | INSEE doesn't publish everything at class level | Comparison at division level, **announced on the line** — intended behavior |
| `query_resource_data` fails on a resource | Non-tabular or oversized resource | The skill tries another resource of the dataset or an aggregated one — never a number from memory |
| Client payment delay "not computable" | Few or no invoices issued through Qonto | The ratio only covers Qonto-issued invoices; tell the skill if you invoice elsewhere |
| Seasonality "unavailable" | Less than 12 full months of history | Honest by design — come back in a few months |
| The proposed sector is wrong | NAF absent from account data, inference off | Give the correct NAF code in the conversation — the skill always confirms before use |

## 🔒 Security reminder

The skill is **100 % read-only**: it calls no write tool — no transfer, no invoice, no modification.
Nothing to approve, nothing that can move. On the numbers side: every sector comparison carries
its source, vintage and granularity — when no reliable reference exists, the skill says so
instead of making one up.
