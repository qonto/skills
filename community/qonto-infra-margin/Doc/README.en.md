# 🧮 qonto-infra-margin — What does your infra really cost, per user?

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> **100% read-only, on both sides** — Qonto reads only, and product-side SQL is limited to user-confirmed `SELECT count` queries.

---

## 🎯 Why this matters (usefulness)

Every SaaS founder can recite their MRR. Ask what their infrastructure costs **per user** and you get silence. Vercel, Supabase, OpenAI and AWS bills land as card debits, drown in the transaction list, and gross margin drifts for months before anyone looks. `qonto-infra-margin` answers with what **actually left the bank account** — not vendor dashboards:

1. **Infra debits isolated and classified** — Vercel, Supabase, Sentry, OpenAI, Anthropic, AWS, Scaleway, OVH… recognized from world knowledge **at the first occurrence**, spellings normalized (AWS EMEA SARL = AMZN WEB SERVICES = AWS), grouped into families: cloud, data, AI, observability, tooling
2. **Cross-referenced with product telemetry** — from the MCPs you already have connected: Vercel (projects, deployments), Supabase (projects, DB size, user count via a read-only `SELECT count`), Sentry optional
3. **True unit economics** — €/user, €/project (proration always announced), month-by-month gross-margin drift against receipts
4. **The side-projects that bleed** — billed every month with **zero deployments in 90 days**, user-less databases on a paid tier, AI API spend growing faster than users

Would someone use this on a Monday morning? It's the question every technical founder asks in the shower and never answers: *"wait — how much is all of this actually costing me per user?"*

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Universal** — infra analysis works identically for every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT). Truth = the account-side debit (EUR side of USD bills, FX included) | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Vercel MCP | `list_projects` + `list_deployments` → per-project allocation, dead projects detected | ⭕ recommended — degraded mode otherwise, said plainly |
| Supabase MCP | `list_projects` + `execute_sql` (**read-only** SELECT count, table confirmed by you) → measured €/user | ⭕ recommended — degraded mode otherwise |
| Sentry MCP | Error volume per project, as context | ⭕ optional |
| ≥ 12 months of history | Trends and yearly plans only show over 12–36 months; below that, honest degradation | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Identity & accounts**: `get_organization` first — accounts, currencies, country. Nothing hardcoded
2. **Isolate infra spend** (12–24 months, up to 36 for yearly plans, paginated ≤ 50): vendors recognized without any keyword list to maintain, matched to supplier invoices when they exist, card payments matched by `emitted_at` (not `settled_at`)
3. **Product telemetry**: Vercel/Supabase/Sentry MCPs **detected dynamically**. None connected → the skill says so and continues Qonto-only: classification + monthly total + trend — already useful
4. **Cost allocation per project**: Supabase bills often split per project; a Vercel bill is team-level → **prorated by deployment activity, rule shown on the line**. Costs with no sane allocation key stay in a visible "shared" bucket
5. **Unit economics**: monthly total + trend, €/user (only when a **real count** was measured), €/project, gross-margin drift against stated MRR or account receipts (announced as a proxy)
6. **The bleeders**: projects billed with no deployment in 90 days, paid-tier empty databases, AI API drift → costed report + dashboard

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**Read-only on both sides**: no Qonto write tool is ever called. And on the product side, `execute_sql` is capped at single read-only `SELECT count` queries on a table **you** confirm before it runs — never DDL/DML, never a silently guessed table.

## 🧪 Holds up on messy data

- Vendor billed in USD, debited in EUR? → the skill totals the EUR debit (FX included) and says why vendor dashboards will show a different number
- New AI API that launched last month? → recognized from world knowledge at its first invoice — no dictionary to update
- Ambiguous counterparty (reseller, agency)? → asked once, never silently classified
- No Vercel/Supabase MCP? → degraded mode announced: classification, totals and trend still delivered
- No measured user count? → **no €/user, said plainly** — the skill never invents a product metric
- Yearly plans (JetBrains, domains, annual tiers) → detected across 24–36 months before any cost is called "one-off"

## 📤 Output formats (where does the analysis land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: infra P&L (vendor × month), unit economics (€/user, €/project), bleeders list | **Always** — the baseline |
| **Interactive dashboard** | **HTML** file/artifact: stacked monthly bars per family, €/user gauge, margin-drift curve, bleeders spotlight | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |
| **Degraded mode** | Same tables minus €/user and per-project allocation — announced clearly | Without the Vercel/Supabase MCPs |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the MRR everyone knows → the infra debits isolated from a real account → product telemetry plugged in → **the reveal** (the real €/user, and the side-project that had been bleeding for months) → the final dashboard.

## 💡 Roadmap ideas

- Stripe/payments MCP for a measured MRR (no more proxy) — same dynamic-detection logic as Vercel/Supabase
- Monthly ritual alert: "your gross margin drifted +N points" — pairs naturally with qonto-tax-pilot's first-of-the-month ritual
- Internal benchmark: this month's €/user vs 12 months ago — reuses the history already scanned
- Per-vendor rightsizing hints, with pricing checked online at analysis time — never from model memory
- Cross-check with qonto-subscription-audit (duplicate infra tooling) — both skills share recurrence detection

## 🛡 Guardrails

- **Never invents a product metric**: no measured count → no €/user. All figures in the docs are **fictional examples, flagged as such**
- **Allocation is an editorial choice, shown**: every shared-cost proration is announced on the line, never silent
- **Read-only SQL**: `execute_sql` limited to single `SELECT count` queries on a user-confirmed table
- Vendor pricing never asserted from memory — the account's numbers, yes; "you're on the wrong plan", no (current pricing checked first)
- Masked IBANs (last 4 digits) · pagination ≤ 50 everywhere · honest degradation (missing MCPs, short history)

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
