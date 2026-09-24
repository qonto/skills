---
name: qonto-project-burn
description: Project-level burn tracker that bridges Qonto and the team's tracker. Maps Qonto labels to projects, computes each project's real spend (dedicated SaaS, freelancers, ads, hardware) against its declared budget, projects the overrun date at the current run rate, and — with explicit consent — posts the status where the team lives, as a Linear/Jira comment plus an alert issue when a threshold is crossed. Use for "what did project Alpha actually cost?", "combien a coûté le projet X ?", "are we over budget?", "post the burn status to Linear", "which project burns fastest?".
permissions:
  mcp:
    qonto: [get_organization, get_subscription, list_cash_flow_categories, list_client_invoices, list_labels, list_transactions, modify_transaction_cash_flow_category]
  network: []
  env: []
  tools: [Read]
---

# Qonto Project Burn

Teams plan in Linear or Jira; the money lives in Qonto. Nobody knows what project X really cost. This skill maps **Qonto labels ↔ projects**, computes real burn vs declared budget, projects the overrun date — and brings the answer to the team's tracker instead of asking the team to open the bank. Qonto side: read-only. The notable write lives in Linear/Jira, always previewed and confirmed.

## Prerequisites
1. `get_organization` **first** → accounts, currency, `bank_account_id` (required by `list_transactions`). Nothing hardcoded; adapts to any organization.
2. `list_labels` → the label tree is the candidate project list. No labels at all? Degrade honestly: propose a mapping from recurring counterparties instead, everything tagged 🟡, and explain how to label transactions in the Qonto app.
3. **Country-agnostic**: labels + transactions, no tax rules — works identically for every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT).
4. **Project-tracker MCP is optional, detected dynamically**: if a Linear MCP is available, use it; else Jira/Atlassian; else say so plainly and run the degraded mode — full per-project report in the conversation + HTML dashboard. The core works on Qonto alone.

## Workflow

### 1. Read the account
`get_organization`, then `list_labels` (paginate `per_page: "50"`). Present the labels found. ⚠️ Do NOT call `list_cash_flow_categories` for the mapping — it returns **403 missing oauth scope** on the claude.ai connector; labels are the project dimension here.

### 2. Build the label ↔ project mapping
Propose a simple config table: **Qonto label → project name → tracker project (if MCP detected) → declared budget → period**. Budgets are **declared by the user** (or read from the tracker project description when one is formatted there) — never invented. Show the table, let the user correct any line, then output a compact paste-ready block so it can be **remembered in the conversation or the Claude project instructions**. Nothing is written to Qonto.

### 3. Compute real burn per project
`list_transactions` per account, `per_page: "50"`, side `debit`, over the project's lifetime — scan **24–36 months** when history allows, so *annual* renewals (yearly SaaS licences, domain fees) show up, not just monthly ones. Then:
- Group debits by mapped label; deduct refunds/credits on the same counterparty; use `emitted_at` for card spend (1–2 days ahead of `settled_at`).
- A transaction carrying several labels counts **once**, under the mapping's first matching label — say so.
- **Orphans**: unlabelled debits whose counterparty matches a project's recurring suppliers are listed separately, never silently attributed. The MCP has **no tool to attach a label** to a transaction, so offer two clean-ups: (a) a paste-ready list to label in the Qonto app (one-time), and (b) optionally, `modify_transaction_cash_flow_category` to file orphans under a cash-flow category the user names — a light, reversible write, only after explicit confirmation.

### 4. Budget vs run rate
Per project: **spent · declared budget · % consumed · monthly run rate** (average of the last 3 full months, recent months weighted) · **projected overrun date** = today + (budget − spent) ÷ run rate. Confidence tags: 🟢 fully labelled history / 🟡 orphans pending or history < 3 months. Default thresholds: ⚠️ 80 % · 🔴 100 % (user-adjustable).

### 5. Write where the team lives — only with explicit consent
If a Linear (or Jira/Atlassian) MCP is detected and the user confirms:
- **Status comment** on the mapped project/issue: `"Burn: X € / Y € — Z % · projected overrun: <date> · top 5 lines"` (amounts from Qonto, wording shown verbatim **before** posting).
- **Alert issue** when a threshold is crossed: title `"⚠️ Budget <project> Z %"`, body listing the Qonto transactions (date · counterparty · amount) that justify it, plus the projected overrun date.
Never post without a preview and an explicit "yes" in the current conversation; never present a post as done if the MCP call failed. No tracker MCP? Skip this step and say so — the report below is the full deliverable.

### 6. Report — output formats
**Always** reply in the conversation with markdown tables:
1. **Per-project table**: project · spent · budget · % · run rate · projected overrun date · status ✅/⚠️/🔴.
2. **Orphan list** (count + total) with the two clean-up options.
3. Narrative alerts by severity.

**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): an **HTML dashboard** — one bar per project (spent vs budget), run-rate sparkline, overrun markers. If the host cannot render files, say nothing about it: the tables are the deliverable.

For the **company-wide** view (runway, all-costs cockpit), see the `qonto-ceo-cockpit` skill — this skill is the **project-level** granularity.

**Scope boundaries**: for the full per-project P&L (revenue AND costs, margin) written into **Notion**, see `qonto-project-pnl` — this skill is the **cost-vs-budget tracker with alerts posted to Linear/Jira**. For the company-wide view, see `qonto-ceo-cockpit`.

## Guardrails
- NEVER write to Linear/Jira without showing the exact content and getting explicit confirmation in the current conversation; never present a pending or failed write as done.
- The label → project attribution is **always shown and correctable** — never silently reassign a transaction.
- Budgets are user-declared facts, spend is Qonto data; the skill never invents a budget or an amount.
- `list_cash_flow_categories` / `get_subscription` → 403 on the claude.ai connector: expected, fall back to labels.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50). Degrade honestly on missing labels, short history, or absent tracker MCP.
