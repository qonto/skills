---
name: qonto-shopify-bridge
description: E-commerce payout reconciliation for Qonto accounts. Matches Shopify/Stripe/PayPal payouts against the money that actually lands on the Qonto account — missing or late payouts, effective fee rate vs announced, refunds and chargebacks not passed through, and the true net margin per period. Works Qonto-only; enriches with the Shopify (or Stripe) MCP when connected. Use for "did Shopify actually pay me?", "où sont passés mes payouts Shopify ?", "what do Stripe fees really cost me?", "reconcile my store sales with my bank account", "is a payout missing this week?".
permissions:
  mcp:
    qonto: [get_organization, get_statement, list_cash_flow_categories, list_statements, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto Shopify Bridge

Every Shopify merchant lives with the same blind spot: gross sales in the store, net payouts on the account — and between the two, fees, refunds and delays. This skill reconciles the two sides. **Read-only: zero write tool. It reads, matches, documents — it cannot touch anything.**

## Prerequisites
1. `get_organization` → accounts, currencies, country. `list_transactions` requires `bank_account_id`/`iban`, so this call always comes first. Nothing hardcoded — the skill adapts to any organization.
2. **Two operating modes, detected dynamically**:
   - **Qonto-only core** (always works): identifies PSP inflows, their cadence, totals per period, rhythm breaks (missing payout).
   - **Enriched mode**: if a **Shopify MCP** is connected (tools `get-order`, `list-orders`, `run-analytics-query` — note the hyphens, these are Shopify tools, not Qonto), the skill reconciles gross sales against net payouts. Same idea with a Stripe MCP if present. If neither is connected, say so plainly and continue Qonto-only — the core is already useful.
3. **Country-agnostic**: payout reconciliation works identically for all Qonto countries (FR, DE, ES, IT, AT, NL, BE, PT). Currency nuances are reported per currency, never converted silently.

## Workflow

### 1. Map the money in (Qonto)
`list_transactions` per account, `side: credit`, paginate `per_page: "50"`, cover 12–24 months. Isolate PSP inflows by normalized counterparty: SHOPIFY / SHOPIFY PAYMENTS, STRIPE, PAYPAL, SUMUP, ADYEN, MOLLIE, KLARNA… Group by PSP and, when the label allows it, by store (multi-store merchants get one lane per store). Use `settled_at` as the arrival date.

### 2. Learn the payout rhythm (Qonto-only, already useful)
Per PSP: cadence (daily on business days, weekly on a fixed weekday, on-demand), typical delay, typical amount band, totals per week/month. Build the **expected-payout calendar** and flag every gap: expected-but-missing and unusually late arrivals. ⚠️ PayPal is often on-demand withdrawals — detect that pattern and don't cry "missing payout" on manual transfers.

### 3. Enrich with the store (if the Shopify MCP is detected)
`run-analytics-query` → gross sales, refunds, order counts per period; `list-orders` / `get-order` for order-level detail when a specific payout needs explaining. Multi-store: reconcile each store separately. If the MCP is absent: announce it ("connect the Shopify MCP for sales-side reconciliation") and continue with steps 1–2 outputs.

### 4. Reconcile sales ↔ payouts
A payout groups **n orders minus fees minus refunds**, arriving with a delay (typically 2–3 business days). Match sales windows to received payouts by date + amount proximity. Compute the **effective fee rate** = (gross − net) ÷ gross per payout and per month. Compare it to the rate the user's plan announces (e.g. "2.9% + €0.30") **only if the user states their plan** — never assume a fee schedule, always show the computed number.

### 5. Detect and document the gaps
- **Missing payout**: the store says paid, nothing on the account past the typical delay → draft a **support ticket** with every reference (payout date, expected amount, order range, account statement covering the window via `list_statements` / `get_statement`).
- **Late payout**: arrived, but N days beyond the learned delay.
- **Fee drift**: effective rate moving month-over-month → show the trend.
- **Refunds/chargebacks not passed through**: refunded in the store, no matching deduction on the account (or the reverse).
Every anomaly carries its evidence; nothing is asserted without a reference.

### 6. Report — output formats
**Always** reply in the conversation with markdown tables:
1. **Reconciliation summary** — "14 payouts expected, 13 received, 1 late by 4 days"; per PSP and per store.
2. **Fees table** — gross · net · fees · effective rate per month, vs announced rate when known.
3. **Net cash collected** per period and **true margin after commissions**.
4. Anomaly list by severity, each with its references; the **support-ticket draft** when a payout is missing.

**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): an interactive **HTML dashboard** — payout timeline with gaps highlighted, fee-rate trend, net-per-month bars. If the host cannot render files, say nothing about it: the markdown tables are the deliverable.

## Guardrails
- **Read-only skill**: no write tool, no money movement, nothing created or modified on either side.
- Never invent a fee schedule or a payout that isn't in the data; computed rates only, with the sample size shown.
- A "missing payout" is a **hypothesis with evidence**, not an accusation — the report says what was checked and hands the user the ticket; support has the final word.
- Multi-currency: report per currency, never convert silently. Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50).
- Degrade honestly: < 3 months of PSP history → cadence tagged as low-confidence; no Shopify MCP → Qonto-only outputs, stated plainly.
