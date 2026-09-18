---
name: qonto-infra-margin
description: Infrastructure unit-economics radar for SaaS and tech founders on Qonto. Isolates real infra spend from the account's debits (Vercel, Supabase, Sentry, OpenAI, Anthropic, AWS, Scaleway, OVH…), cross-references product telemetry from connected MCPs (Vercel projects/deployments, Supabase usage) and computes true unit economics — €/user, €/project, month-by-month gross-margin drift, and the side-projects that bleed money without traffic. Use for "what does my infra cost per user?", "combien me coûte mon infra par utilisateur ?", "how much am I spending on AI APIs?", "which side-project is bleeding money?", "is my gross margin drifting?".
permissions:
  mcp:
    qonto: [get_organization, list_cash_flow_categories, list_supplier_invoices, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto Infra Margin

SaaS founders know their MRR by heart — almost none know their **infra cost per user**. This skill computes it from what actually left the bank account, not from vendor dashboards. **Read-only: zero write tool. It reads, computes, reports — it cannot touch anything.**

## Prerequisites
1. `get_organization` → accounts, currencies, country. `list_transactions` requires `bank_account_id`/`iban`, so this call always comes first. Nothing hardcoded — the skill adapts to any organization.
2. **Two operating modes, detected dynamically**:
   - **Qonto-only core** (always works): infra debits isolated and classified, monthly total per vendor family, trend. Already useful on its own.
   - **Enriched mode**: a **Vercel MCP** (`list_projects`, `list_deployments`) and/or a **Supabase MCP** (`list_projects`, `execute_sql`) connected → per-project cost allocation, measured user counts, €/user. A Sentry MCP adds error-volume context (optional). Absent MCPs are named plainly ("connect the Vercel MCP for per-project allocation") and the skill continues.
3. **Country-agnostic**: works identically for all Qonto countries (FR, DE, ES, IT, AT, NL, BE, PT). The source of truth is the account side: USD vendor bills are analyzed at their EUR debit amount, FX included — vendor-dashboard totals will differ, and the skill says so.

## Workflow

### 1. Map the accounts
`get_organization` → list every account, note currency and balance. Ask nothing yet: the whole analysis starts from raw debits.

### 2. Isolate infra spend (12–24 months; extend to 36 when hunting yearly plans)
`list_transactions` per account, `side: debit`, paginate `per_page: "50"` in 3-month windows. Recognize infra vendors **by general knowledge from the first occurrence** — no config file, no keyword list to maintain:

| Family | Typical vendors |
|---|---|
| Cloud & hosting | AWS, Google Cloud, Azure, Scaleway, OVHcloud, Hetzner, DigitalOcean, Fly.io, Railway, Render, Heroku |
| Frontend & edge | Vercel, Netlify, Cloudflare |
| Data & backend | Supabase, MongoDB Atlas, Neon, PlanetScale, Firebase, Upstash |
| AI APIs | OpenAI, Anthropic, Mistral, Replicate, ElevenLabs, fal.ai, Hugging Face |
| Observability | Sentry, Datadog, Better Stack, Grafana Cloud |
| Dev tooling | GitHub, GitLab, Docker, npm, JetBrains |

- **Normalize spellings**: `AWS EMEA SARL`, `AMZN WEB SERVICES` and `Amazon Web Services` are ONE vendor; `OPENAI *CHATGPT` and `OPENAI LLC` are one. Merge case/prefix variants before totaling.
- Most infra is **card-paid**: match vendor invoices to debits by `emitted_at`, not `settled_at` (1–2 day gap).
- **Yearly plans**: a single yearly charge (JetBrains, domain renewals, annual Vercel/GitHub plans) only shows its cadence across 24–36 months — scan that far before calling a cost "one-off".
- Cross with `list_supplier_invoices` when present: invoice-level detail (line items, VAT) sharpens the per-project mapping.
- Ambiguous counterparty (an agency? a reseller?) → ask the user once; never silently classify.

### 3. Pull product telemetry (only from MCPs actually connected)
- **Vercel MCP**: `list_projects` → the real project list; `list_deployments` per project → last deployment date and activity level.
- **Supabase MCP**: `list_projects` → per-project instances; `execute_sql` for the user count — **strictly read-only, single `SELECT count(*)` queries**. The "users" table varies by app: propose `auth.users` as the default, **ask the user to confirm the table/filter before running**, and never run anything but a SELECT.
- **Sentry MCP** (optional): error volume per project, as context only.
- No product MCP connected → **degraded mode, announced**: skip €/user and per-project allocation, keep classification, totals and trend (steps 5–6 adapt).

### 4. Allocate costs to projects
Map each vendor bill to a real project. Supabase bills often split per project (invoices help); Vercel bills are team-level → **prorate by deployment activity** (or evenly if activity is flat), and **state the proration rule on the line** — an allocation is an editorial choice, never a hidden one. Shared costs with no sane key (domain portfolio, password manager) stay in a visible "shared" bucket instead of being smeared.

### 5. Compute the unit economics
- **Monthly infra total** and 12-month trend, per family and per vendor.
- **€/user** = monthly infra ÷ **measured** user count — only when step 3 produced a real number. Also per-vendor: Supabase cost ÷ users in that database.
- **€/project** = allocated monthly cost per project (proration rule shown).
- **Gross-margin drift**: infra as % of monthly revenue, month by month. Revenue = the user's stated MRR, or — announced as a **proxy** — the account's monthly client credits. Never invent MRR.

### 6. Find the bleeders — report
- **Side-projects that bleed**: still billed, **zero deployments in 90 days** (Vercel) or zero/frozen user count (Supabase) → name them, with monthly cost and last-activity date.
- **AI API drift**: AI spend growing faster than the user count → flagged with both curves.
- **Paid tiers idling**: databases or plans billed above obvious usage → suggest the downgrade question, never claim the right tier (pricing knowledge may be stale — check current vendor pricing before quoting figures).

**Always** reply in the conversation with markdown tables:
1. **Infra P&L** — vendor × month grid, family subtotals, trend arrows.
2. **Unit economics** — €/user (global + per vendor), €/project with proration rule, margin-drift line.
3. **Bleeders list** — project · monthly cost · last activity · evidence.

**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): an **HTML dashboard** — stacked monthly cost bars per family, €/user gauge, margin-drift curve, bleeders spotlight. If the host cannot render files, say nothing about it: the tables are the deliverable.

## Guardrails
- **Read-only end to end**: no Qonto write tool, and `execute_sql` limited to single read-only `SELECT count` queries confirmed by the user — never DDL/DML, never on unconfirmed tables.
- **Never invent a product metric**: no user count measured → no €/user, said plainly. Estimates ≠ accounting; allocation prorata always announced.
- Vendor pricing changes: never assert "you're on the wrong plan" from memory — show the numbers, let the user check the vendor's current pricing.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50). Announce degraded mode honestly (no MCP, short history, non-EUR accounts).
