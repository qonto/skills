# 📊 qonto-sector-benchmark — "Am I normal?" Finally, an answer with numbers

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> The founder's comparative health check-up: your real ratios (from Qonto) next to official sector statistics (INSEE, via the Datagouv MCP) · **100 % read-only, zero writes**

---

## 🎯 Why this matters (usefulness)

"Am I normal?" is the question every founder quietly asks and never gets answered. You *feel* your costs are heavy or your clients pay slowly — but heavy **compared to what**? `qonto-sector-benchmark` answers in one prompt:

1. **Your real ratios**, computed from the Qonto account — fixed-cost share, software subscription weight, observed client payment delay, revenue seasonality, cash in days of expenses
2. **The official sector reference** — French public statistics (INSEE structural business data, payment delays) fetched live through the Datagouv MCP, at the finest NAF level available
3. **Statistical honesty as the core feature** — every comparison carries its **source + vintage + granularity** ("NAF 62.02A, INSEE Ésane, 2023 data"); no exact dataset → comparison one level up, *stated on the line*; a sector figure is never, ever made up
4. **You vs you a year ago** — a temporal self-benchmark computed every time, which doubles as the full degraded mode when Datagouv is absent or the company isn't French

Typical output: "your clients pay you at 38 days; your sector's median is 51 — you collect **faster** than your peers" / "your fixed costs weigh 61 % vs ~45 % in your sector: that's where to dig."

Would someone use this on a Monday morning? It's the quarterly Monday — the one where you ask yourself how the business is *really* doing.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Sector comparison: France only** (INSEE statistics). Other Qonto countries (DE, ES, IT…): graceful degradation — internal ratios + temporal self-benchmark, never mapped onto French data | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Datagouv MCP | Detected dynamically: present → live sector references; absent → the skill says so and switches to self-benchmark mode | ⭕ recommended |
| NAF activity code | Read from `get_organization` when exposed; otherwise asked (it's on any company registration doc) or inferred from the activity **and confirmed** before use | ⭕ |
| ≥ 12 months of history | Seasonality needs a full year; the self-benchmark ~24 months. Below that, the skill computes what it can and tags the rest unavailable | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Identity & sector**: `get_organization` first — country, legal form, NAF code. Missing NAF → asked or inferred, then confirmed. Non-French company → internal-only mode announced **before** the analysis, not after
2. **Internal ratios** (24 months, paginated ≤ 50): fixed costs (recurrences ±10 %, ≥ 3 hits), software subscriptions (detected list shown, correctable), client payment delay (median issue → payment, Qonto-issued invoices only — disclosed), seasonality (coefficient of variation + peak/trough months), cash in days of expenses
3. **Sector references** through the Datagouv MCP: `search_datasets` (INSEE Ésane, payment delays) → `get_dataset_info` (vintage, producer, granularity checked **before** use) → `query_resource_data` filtered on the NAF code
4. **Honest comparison**: every line carries source + vintage + granularity; NAF class not published → division level, *stated on the line*; no reference at all → internal value only, marked "no public reference found"
5. **Self-benchmark**: the same five ratios on the previous 12-month window, with trend arrows — also the complete fallback mode
6. **Health report**: markdown scorecard (always) + HTML scorecard when the host renders files

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**Zero writes, by design**: the skill only reads — the Qonto account on one side, public open data on the other. Nothing to approve, nothing that can move. The only "risk" here is statistical, and it's handled by the golden rule: source + vintage + granularity on every figure, or no figure at all.

## 🧪 Holds up on messy data

- No NAF code in the account data? → asked or inferred from the activity, and **confirmed** before any comparison
- Exact sector class not published by INSEE? → comparison at the division level, announced on the very line it affects
- No Datagouv MCP, or no usable dataset? → the report stays useful: internal ratios + "you vs you a year ago"
- Non-French company? → the skill says up front what it can and can't compare, instead of pretending
- Few invoices issued through Qonto? → payment delay computed on those only, and disclosed as such
- Short history? → seasonality tagged unavailable rather than computed on noise; card settlement delays handled (`emitted_at` vs `settled_at`)

## 📤 Output formats (where does the check-up land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown scorecard: ratio · your value · sector reference (source · vintage · granularity) · verdict · year-over-year trend, then 2–3 narrative findings and the full source list | **Always** — the baseline |
| **Interactive scorecard** | **HTML** file/artifact: the five ratios as gauges against the sector range, sources footnoted | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to markdown otherwise |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the "am I normal?" question → real ratios computed → sourced INSEE references → **the reveal** (the subscriptions were fine all along; the client payment delays were the real problem) → the final health report. It runs live on a real production account.

## 🧭 Where it sits in the family

The **quarterly or annual comparative health check-up** — deliberately not a daily-piloting tool. For day-to-day cash, flows and forecasting, `qonto-ceo-cockpit` is the right companion skill.

## 💡 Roadmap ideas

- Size-adjusted references (NAF × headcount/revenue bracket) — INSEE publishes some breakdowns by company size
- Country modules (Destatis DE, INE ES, ISTAT IT…) — same architecture, one open-data connector per country
- Check-up history: trajectory across 4–8 quarters, reusing the self-benchmark engine
- Anonymized peer-basket benchmark — a Qonto product idea more than a skill

## 🛡 Guardrails

- **100 % read-only**: no write tool is ever called — nothing to approve, nothing that can move money
- **Never** invents a sector figure: no dataset → the line says so; degraded granularity → announced on the line; vintage always printed
- Bank-data ratios ≠ accounting records: an honest approximation, restated in every report — the accountant's figures prevail
- Sector confirmed, not assumed, when the NAF code isn't in the account data
- IBANs masked (last 4 digits) · pagination ≤ 50 everywhere

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
