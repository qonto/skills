---
name: qonto-cash-to-stock
description: Cash-constrained restocking copilot for e-commerce on Qonto. The real ceiling on a restock isn't demand — it's cash. Computes the truly available cash (all account balances minus upcoming supplier invoices, detected tax deadlines and recurring fixed costs), the sales velocity and stock cover (Shopify when connected, estimated from receipts otherwise), then answers THE question — how many units can I order without endangering the account, and by when? With explicit user consent it prepares the supplier transfer request, approved with 2FA in the Qonto app. Use for "combien d'unités puis-je commander sans me mettre en danger ?", "when will I run out of stock?", "can my cash fund this restock?", "quand dois-je passer ma commande fournisseur ?", "prepare the supplier payment".
permissions:
  mcp:
    qonto: [create_multi_transfer_request, decline_request, get_organization, list_products, list_supplier_invoices, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto Cash-to-Stock

The real ceiling on an e-commerce restock isn't demand — it's cash. Read-heavy, one safe write: the skill computes what the account can truly fund and when to order; only the user's own SCA approval in the Qonto app moves money.

## Prerequisites
1. `get_organization` **always first** → accounts, balances, currency, country (`list_transactions` requires `bank_account_id`/`iban`). Nothing hardcoded — the skill adapts to any organization.
2. **Shopify MCP optional, detected dynamically**: when connected, use `run-analytics-query` (units sold per product per day) and `get-inventory-levels` (on-hand stock per SKU). When absent, say so plainly and degrade: velocity estimated from incoming payments + the `list_products` catalog, every derived figure tagged 🟡.
3. **Country-aware**: tax-deadline refinement uses the French calendar (same detection logic as `qonto-tax-pilot`). For other Qonto countries (DE, ES, IT, AT, NL, BE, PT…), only tax debits actually observed in history are projected forward — never invent foreign deadlines.

## Workflow

### 1. Cash snapshot
`get_organization` → every bank account with its balance and currency. Sum authorized balances; note the main account. This is the starting ceiling — real cash, never an assumption.

### 2. Committed outflows — the real ceiling
- `list_supplier_invoices` → invoices with status pending/scheduled and their due dates; these leave first.
- `list_transactions` per account, paginate `per_page: "50"`, 12–24 months back (extend to 24–36 months when scanning for **annual** cadences — yearly patterns only become visible across at least two full years):
  - **Recurring fixed costs**: normalized counterparty, stable amount (±10 %), monthly/quarterly/yearly cadence, ≥3 hits (2 for yearly) — rent, payroll, subscriptions, loan repayments.
  - **Tax deadlines**: scan **outgoing direct debits first** (filter on `operation_type`), then match the tax office under all its spellings (`DGFIP`, `DIRECTION GENERALE DES FINANCES PUBLIQUES`, mixed case) — normalize case/accents and merge as ONE counterparty. This is the same logic as `qonto-tax-pilot`; if that skill is installed, reuse its tax schedule instead of recomputing.
- Build a **dated calendar of committed outflows** over the ordering horizon (default 90 days).

### 3. Truly free cash
Day-by-day over the horizon: total balances + a conservative receipts baseline (median of past weekly receipts; on request, floor receipts at zero for a worst-case view) − committed outflows − **safety buffer** (default one month of fixed costs; user-adjustable, stated in every report). **Free cash for stock = the minimum of that curve**, with its date. Always show the low point — the restock must survive it.

### 4. Velocity, stock and stock-out date
- **With Shopify**: `run-analytics-query` → units sold per product per day over the last 90 days; `get-inventory-levels` → on-hand stock. Stock-out date per product = on-hand ÷ velocity. Flag momentum: if 30-day and 90-day velocities diverge by more than ~30 %, say so and use the recent one.
- **Without Shopify**: estimate revenue velocity from incoming payments on the Qonto account; convert to approximate units with `list_products` prices when a catalog exists. Announce it as an estimate (🟡) and state the assumption — never dress an estimate up as inventory data.

### 5. The answer — four decision numbers
- **Fundable units N** = free cash at the supplier payment date ÷ landed unit cost. Unit cost from supplier invoice history when it can be derived, otherwise **ask — never guess silently**.
- **Latest order date** = stock-out date − supplier lead time (ask once if unknown).
- Output: **free cash after commitments · stock-out date · N fundable units · latest order date**, each tagged 🟢 seen in data / 🟡 estimated / 🔵 depends on user input.
- What-if on request: split the order in two, order fewer units earlier, wait until after a tax deadline, change the buffer.

### 6. Act — only with explicit consent — then report
If the user decides to order, `create_multi_transfer_request`: `debit_iban` = chosen account; the transfer needs `credit_iban`, `credit_account_name`, **`credit_account_currency`** (422 if omitted), `amount`, `currency`, `reference` (e.g. "RESTOCK PO-2026-041" — invented example). Put the full calculation in the request `note` — the approver reads it at SCA time.
Then tell the user plainly: **a push notification and the Requests section of the Qonto app now hold the pending request; nothing moves until they approve with their own 2FA.** Never present it as executed.

**Output formats** — always reply in the conversation with markdown tables: (1) committed-outflows calendar, (2) free-cash curve summary with dated low point, (3) the four decision numbers with confidence tags, (4) the pending-request recap. When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code), additionally generate an **HTML dashboard** (free-cash curve, commitments as markers, stock-out countdown, fundable-units gauge). If it can't, the tables are the deliverable — say nothing about it.

## Guardrails
- NEVER create a transfer request without explicit user confirmation in the current conversation; never present it as executed — it is pending the user's SCA approval.
- Figures are estimates, not purchase advice: the stock decision stays human. State every assumption used (unit cost, lead time, buffer, receipts baseline).
- Honest degradation: Shopify absent, empty catalog, no supplier invoices, or < 3 months of history → say what can and cannot be computed; never fill gaps with invented numbers. All documentation examples are fictitious and labeled as such.
- For reconciling *past* Shopify payouts against Qonto, defer to `qonto-shopify-bridge` — this skill decides the *next* order.
- In rehearsals, `decline_request` afterwards (`request_type: "multi_transfers"`, plural).
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50).
