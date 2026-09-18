---
name: qonto-sector-benchmark
description: Sector health check-up for Qonto accounts. Computes the company's real ratios from transactions and invoices (fixed-cost share, software subscription weight, observed client payment delay, revenue seasonality, cash in days of expenses) and compares them against official French sector statistics (INSEE, via the Datagouv MCP when connected) — every figure carrying its source, vintage and NAF granularity. Falls back to a "you vs you a year ago" self-benchmark when sector data is unavailable. Use for "suis-je normal ?", "am I normal?", "how do I compare to my industry?", "do my clients pay me slower than average?", "am I paying too much for software?", "benchmark my company against my sector".
permissions:
  mcp:
    qonto: [get_organization, list_cash_flow_categories, list_client_invoices, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto Sector Benchmark

"Am I normal?" — the question every founder asks and never gets answered. 100 % read-only: the skill computes the company's real ratios from the Qonto account, then puts them next to official French sector statistics — with the source, vintage and granularity printed on every single comparison.

## Prerequisites
1. `get_organization` → accounts, balances, country, legal identity and activity/NAF code. If the NAF code is not exposed, ask the user for it (it's on any KBIS/invoice) or infer it from the declared activity and **confirm before using it** — it drives the whole sector comparison.
2. **Country-aware**: sector comparison uses **French** public statistics (INSEE) only. For other Qonto countries (DE, ES, IT, AT, NL, BE, PT…), say so plainly and degrade to what stays valid everywhere: internal ratios + temporal self-benchmark. Never map a foreign company onto French sector data.
3. **Datagouv MCP optional, detected dynamically**: if present, sector references are fetched live; if absent, the skill says so and continues in self-benchmark mode. The core never requires it.
4. ≥ 12 months of history recommended (seasonality needs a full year; self-benchmark needs ~24). Below that, degrade honestly: compute what is computable, tag the rest as unavailable.

## Workflow

### 1. Identify the company and its sector
`get_organization` first (`list_transactions` requires `bank_account_id`/`iban`). Capture: country, legal form, activity/NAF code, accounts and balances. NAF missing → ask or infer + confirm (step 1 above). Non-French company → announce internal-only mode now, not after the analysis.

### 2. Compute the company's real ratios (24 months)
`list_transactions` per account, paginate `per_page: "50"`, 3-month windows; `list_client_invoices` for payment behavior. Five ratios, each with its exact computation disclosed:
- **Fixed-cost share** — recurring debits (normalized counterparty, amount stable ±10 %, monthly/quarterly cadence, ≥3 hits) ÷ total debits, last 12 months. `list_cash_flow_categories` is **403 on the claude.ai connector** — classify via recurrence detection + labels instead.
- **Software subscription weight** — recurring debits whose counterparty matches known SaaS/software patterns ÷ total debits; list the detected subscriptions so the user can correct.
- **Observed client payment delay** — median days from invoice issue date to payment (`list_client_invoices` paid ones, matched to incoming transactions when needed). Computed **only on Qonto-issued invoices** — say so if the user invoices elsewhere.
- **Revenue seasonality** — monthly credit totals over 24 months: coefficient of variation + peak/trough months. Needs ≥ 12 full months, else tagged unavailable.
- **Cash in days of expenses** — consolidated balance ÷ average daily debits (12 months). Card settlement delays: bucket by `emitted_at`, not `settled_at`.

### 3. Fetch sector references (Datagouv MCP, if present)
`search_datasets` for INSEE structural business statistics (Ésane: margin rates, cost structure by NAF) and payment-delay statistics; `get_dataset_info` to check vintage, producer and granularity **before** using anything; `query_resource_data` on the tabular resource, filtered on the company's NAF code. Prefer official producers (INSEE, Banque de France) over third-party uploads.

### 4. Compare — with statistical honesty (the heart of the skill)
- **Every comparison carries source + vintage + granularity**: "NAF 62.02A, INSEE Ésane, 2023 data". No naked sector numbers, ever.
- Exact NAF class not published → compare at the **division level** (e.g. 62 instead of 62.02A) **and say so on the line itself**.
- No dataset at all for a ratio → that line shows the internal value only, marked "no public reference found" — never a made-up benchmark, never a number from memory.
- Structural statistics lag 2–3 years; print the vintage and remind the user it's an order of magnitude, not a grade.

### 5. Self-benchmark over time — "you vs you a year ago"
Always compute when ≥ 18–24 months of history: same five ratios on the previous 12-month window, with trend arrows. This is also the **full degraded mode** — no Datagouv MCP, foreign company, or no usable dataset → the report stays useful on internal ratios + trajectory alone.

### 6. Report — output formats
**Always** reply in the conversation with a markdown scorecard: one row per ratio — your value · sector reference (source · vintage · granularity) · verdict (above / below / in range) · trend vs last year — followed by 2–3 narrative findings ("your clients pay 13 days slower than the sector median — that's the real problem") and the full source list.
**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): a one-page **HTML scorecard** — the five ratios as gauges against the sector range, sources footnoted. If the host cannot render files, say nothing about it: the markdown scorecard is the deliverable.

## Positioning
This is the **quarterly or annual comparative health check-up**, not a daily-piloting tool. For day-to-day cash and forecasting, point the user to `qonto-ceo-cockpit` (dashboard) or a cash-projection skill.

## Guardrails
- 100 % read-only: no write tool is ever called; nothing to approve, nothing that can move money.
- NEVER invent a sector figure. No dataset → say so. Wrong granularity → announce it on the line. Vintage always printed.
- Ratios are computed from bank data, not accounting records: they approximate reality (say it once in every report) — an accountant's figures prevail.
- Sector detection is confirmed, not assumed, when the NAF code isn't in the account data.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50).
