---
name: qonto-true-margin
description: Real-cost pricing for e-commerce on Qonto. Rebuilds the true contribution margin per product from what actually left the bank account — PSP fees really debited, EUR/USD FX costs, real carrier invoices, supplier COGS — allocates them pro-rata (announced as a heuristic), flags products sold at a loss, and proposes corrected prices, applied in Shopify (update-product) only after explicit line-by-line validation. Use for "quelle est ma vraie marge par produit ?", "which products am I selling at a loss?", "my dashboard says 42% margin — is that real?", "reprice my catalog from my real bank costs", "combien me coûte vraiment ce produit, tout compris ?".
permissions:
  mcp:
    qonto: [get_organization, list_cash_flow_categories, list_supplier_invoices, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto True Margin

The e-commerce dashboard shows a "margin" built from theoretical costs. The bank account knows the truth: PSP fees actually debited, FX spreads on foreign-currency purchases, real carrier invoices, supplier payments. This skill rebuilds the **real contribution margin per product** from Qonto debits, then turns it into a pricing decision. **Zero write on the Qonto side.** The only write is on the Shopify side (`update-product`) — one product at a time, each behind an explicit user confirmation.

**Positioning vs `qonto-shopify-bridge`**: the bridge is the accounting record of the *past* — it reconciles payouts against the bank and observes the real fees. `qonto-true-margin` **consumes** those observed costs to produce a decision about the *future*: new prices. Shared input, opposite output. Run the bridge when a payout looks wrong; run true-margin when a price needs fixing.

## Prerequisites
1. `get_organization` first → accounts, currencies, country (`list_transactions` requires `bank_account_id`/`iban`). Nothing hardcoded — the skill adapts to any organization.
2. **Two operating modes, detected dynamically**:
   - **Enriched (recommended)**: a **Shopify MCP** is connected → per-product sales (`run-analytics-query`, `get-product` — note the hyphens: Shopify tools, not Qonto) and price application (`update-product`). A **Stripe MCP**, if present, adds per-charge fee detail — optional.
   - **Qonto-only degraded mode**: real margin by **cost family** (PSP, FX, shipping, COGS) against global inflows — no per-product granularity, and the skill says so plainly instead of pretending.
3. **Country-agnostic**: works identically for all Qonto countries (FR, DE, ES, IT, AT, NL, BE, PT). Multi-currency reported per currency, never converted silently.

## Workflow

### 1. Real costs from the bank (Qonto)
`list_transactions` per account, `side: debit`, paginate `per_page: "50"`, cover 12–24 months. Classify by normalized counterparty (merge spelling variants) into cost families:
- **PSP fees**: separate fee debits (Stripe billing, PayPal fees, SumUp…) when they exist. ⚠️ Shopify Payments usually **nets its fees inside the payout** — there is no separate debit. The effective rate must then come from gross (store) vs net (bank): compute it when the Shopify MCP is present, otherwise mark PSP cost **"unknown, not zero"**. Never substitute an announced rate for an observed one.
- **FX costs**: debits whose local currency ≠ account currency (`local_amount`/`local_currency` vs settled amount) → real conversion cost, plus any explicit FX-fee lines.
- **Shipping**: carrier counterparties (Colissimo/La Poste, Chronopost, Mondial Relay, DHL, UPS, FedEx, GLS, Sendcloud…). Card-paid shipping: reconcile on `emitted_at`, not `settled_at` (1–2 day drift).
- **Supplier COGS**: `list_supplier_invoices` + recurring supplier debits; match invoice → product when the description names one, else leave for allocation.
Everything else (rent, SaaS, salaries) = fixed costs: **excluded** from contribution margin, disclosed in the report.

### 2. Per-product sales (Shopify, if connected)
`run-analytics-query` → revenue, units and refunds per product over the same window; `get-product` for current prices and variants. Refunds reduce net revenue. If no Shopify MCP: announce it ("connect the Shopify MCP for per-product margins") and deliver the degraded by-family analysis — it is already useful.

### 3. Allocate — a heuristic, and it says so
The user picks the key: **pro-rata revenue** (default) or **pro-rata units** (better for shipping-heavy catalogs). The chosen method is printed on every table. COGS uses invoice→product matches first; allocation covers only the rest. This is an *estimate of cost attribution*, not accounting truth — the skill repeats that with the results.

### 4. True contribution margin per product
Per product: net revenue − COGS − PSP fees − FX − shipping = **contribution margin** (€ and %). Shown side-by-side with the theoretical/dashboard margin when the user provides it (never invented). Sort order: **loss-makers first**, then near-zero margins (< 5 pts), then the rest. Each line carries the share of allocated vs directly-matched costs.

### 5. Propose new prices
For each flagged product: the **break-even price** and a **target price** for the margin the user wants (ask for the target; show the formula and the allocation caveat). **A suggestion is not a pricing strategy**: elasticity and volume effects are not modeled — the skill says so honestly in every proposal, and suggests a competitor check before applying.

### 6. Apply — one product at a time, on explicit validation
Present a line-by-line proposal table (product · current price · suggested price · real margin before/after). The user validates **each line explicitly** — a global "apply everything" is not accepted; the skill re-asks per line. For each confirmed line only: Shopify `update-product`, then re-read the product to confirm the new price before reporting it as done. **No Qonto write exists in this skill.**

### 7. Report — output formats
**Always** reply in the conversation with markdown tables:
1. **Cost-family totals** (PSP · FX · shipping · COGS), each tagged observed 🟢 / derived 🟡 / unknown ⚪.
2. **True margin per product** vs theoretical, loss-makers flagged, allocation method printed.
3. **Price proposals** awaiting line-by-line validation.
4. After application: **before/after confirmation** per product, re-read from Shopify.

**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): an interactive **HTML dashboard** — waterfall from dashboard margin to real margin, loss-maker list, per-product price simulator. If the host cannot render files, say nothing about it: the markdown tables are the deliverable.

## Guardrails
- **NEVER** update a price without explicit per-product confirmation in the current conversation; never present an update as done without re-reading it from Shopify.
- The allocation is a **stated heuristic** (pro-rata revenue or units, method always displayed); real margins are estimates, not accounting.
- Price suggestions ≠ pricing strategy: elasticity not modeled — repeated with every proposal.
- **Zero Qonto write tool.** Qonto reads only: `get_organization`, `list_transactions`, `list_supplier_invoices`.
- Degrade honestly: no Shopify MCP → by-family margins only, stated plainly; PSP fees netted in payouts → "unknown, not zero"; < 3 months of history → low-confidence tags.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50). Report per currency, never convert silently.
