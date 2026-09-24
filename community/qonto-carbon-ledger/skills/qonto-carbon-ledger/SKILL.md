---
name: qonto-carbon-ledger
description: Spend-based carbon footprint estimator for Qonto accounts. Classifies real debits into emission categories (energy, travel, digital & cloud, purchased goods, services, catering) and applies sourced, dated monetary emission factors (kgCO2e/€, ADEME-style spend-based method) to produce an approximate annual footprint, dominant categories, multi-year trend, and the 3 most effective levers given actual spending. Read-only, honest about ±50% uncertainty — a pre-assessment, never a regulatory report. Use for "what's my company's carbon footprint?", "bilan carbone de ma boîte ?", "quels postes émettent le plus ?", "how much CO2 does my spending represent?", "empreinte carbone depuis mes dépenses".
permissions:
  mcp:
    qonto: [get_organization, list_cash_flow_categories, list_labels, list_supplier_invoices, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto Carbon Ledger

Your bank statement is secretly a carbon ledger — this skill reads it. Small businesses never do a carbon assessment because they have no data; but bank debits ARE data. 100 % read-only: the skill estimates and explains, it never writes anything and never sells offsets.

## Prerequisites
1. `get_organization` → accounts, country, legal identity. **Nothing hardcoded**: every figure comes from the user's own transactions.
2. **Country-aware**: embedded monetary factors are calibrated for **France / EU** spending. For other Qonto countries the *method* is identical but factors should be adapted (electricity mix, price levels) — say so plainly, still produce the estimate, and tag it accordingly.
3. Empty or very short history (< 6 months) → say what can and can't be estimated; annualize with an explicit warning, never silently extrapolate.

## Workflow

### 1. Read the ledger (24–36 months)
`list_transactions` per account (requires `bank_account_id`/`iban` from `get_organization`), paginate `per_page: "50"` in 3-month windows, `side: debit`. Cover **24–36 months when history allows**: the annual trend and seasonal purchases (heating, year-end equipment) only show across full years. Also pull `list_labels` (user's own tags help classification) and `list_supplier_invoices` (supplier names + amounts refine category mapping).

### 2. Scope — what counts, what doesn't
The spend-based method covers **purchased goods, services and energy** (a scope-3-upstream-style view). Exclude and SAY you exclude: internal transfers between sub-accounts, salaries and payroll charges, taxes (DGFIP/URSSAF), VAT payments, loan principal repayments, dividend distributions — financial flows carry no monetary emission factor. Show the excluded total so the user sees the estimate's basis.

### 3. Classify debits into emission categories
Normalize counterparty names (case, accents, multiple spellings merged as one), then map each debit to a category using counterparty + label + supplier invoice context:
énergie (fuel / electricity / gas separated when the counterparty allows — the factors differ ×10), transport & travel (air vs rail vs road separated when possible), digital cloud & SaaS, purchased goods & equipment, services & professional fees, catering & food, insurance & banking fees.
⚠️ `list_cash_flow_categories` returns **403 missing oauth scope** on the claude.ai connector → use **labels** as the classification fallback, never that tool. Ambiguous debits go to a visible "unclassified" bucket with a mid-range factor — disclose its share; if it exceeds ~20 % of spend, say the estimate is weak and ask the user to label top counterparties.

### 4. Convert to excl-VAT amounts
Monetary factors apply to **€ excluding VAT**. Use each transaction's `vat_amount` when present; when null, estimate net = amount ÷ 1.20 (standard French rate) and disclose how many debits were estimated. Large one-off purchases (vehicle, machine ≥ ~5 000 €) are flagged separately so a single investment doesn't masquerade as a recurring emission.

### 5. Apply monetary emission factors (embedded, sourced, dated)
Embedded static table — indicative central values derived from the **spend-based method with monetary ratios (ADEME Base Empreinte-style, 2023–2024 vintage)**. Every displayed line carries its factor + source + vintage. If a **Datagouv MCP** is available, offer to cross-check against current ADEME datasets; otherwise use the embedded table and say so.

| Category | Factor (kgCO2e / € excl. VAT, indicative central value) |
|---|---|
| Energy — vehicle fuel | ~1.5 |
| Energy — electricity (FR mix) | ~0.25 |
| Energy — gas / heating | ~1.9 |
| Travel — air | ~1.2 |
| Travel — rail (FR) | ~0.05 |
| Travel — road, taxi/VTC, freight | ~0.5 |
| Digital, cloud & SaaS | ~0.3 |
| Purchased goods & equipment | ~0.5 |
| Services & professional fees | ~0.15 |
| Catering & food | ~0.7 |
| Insurance & banking fees | ~0.1 |

All factors carry **±50 % or more uncertainty** — that is inherent to the monetary method (a cheap flight ≠ low emissions). Print the uncertainty on every figure, not just once in a footnote.

### 6. Report — output formats
**Always** reply in the conversation with markdown tables:
1. **Approximate annual footprint**: ~N tCO2e/year, written with its band (e.g. "~9 tCO2e (range 4.5–13.5)") — never a falsely precise "9.37".
2. **Breakdown by category** (category · spend € · factor + source/vintage · tCO2e · share %), dominant categories highlighted.
3. **Trend** across the 24–36 months read (per year or rolling 12 months), with the caveat that spend changes ≠ emission changes if prices moved.
4. **Top-3 levers**, ranked by estimated impact given the REAL amounts (e.g. rail instead of short-haul air on the routes actually paid, green electricity contract, refurbished equipment) — each with estimated tCO2e saved and cost direction (free / saves money / costs money). Never sell or recommend carbon offsets.

**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): generate an **HTML dashboard** — footprint gauge with uncertainty band, category bars, trend, levers. If the host cannot render files, say nothing about it: the markdown tables are the deliverable.

Cross-reference: pairs naturally with `qonto-sector-benchmark` (same spirit — your real flows × public reference data).

## Guardrails
- **This is an order-of-magnitude pre-assessment, not a regulatory carbon report (BEGES / CSRD / GHG Protocol).** Say it in every report; for an official assessment, recommend a specialized provider. Never present the output as compliant or auditable.
- Every factor displayed with its source and vintage; every figure with its uncertainty band. No false precision, ever.
- Read-only: zero write tools. Never propose paid "compensation"/offsets.
- Country ≠ FR → identical method, factors flagged as needing adaptation; never pretend local calibration.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50). `get_organization` always first.
