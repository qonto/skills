---
name: qonto-oss-navigator
description: EU e-commerce VAT navigator (OSS One-Stop Shop) for Qonto accounts. Tracks the single €10,000 EU threshold for cross-border B2C distance sales, breaks sales down by customer country (Shopify shipping countries when connected, otherwise partial inference from Qonto data — announced as such), applies a vintage-dated VAT rate table for all 27 member states, drafts the quarterly OSS return country by country (base, rate, VAT due), and — with explicit consent — provisions the amount via a transfer request the user approves with SCA. Use for "am I over the EU distance-selling threshold?", "où j'en suis sur le seuil des 10 000 € ?", "prepare my OSS return for the quarter", "quelle TVA appliquer à mes clients allemands ?", "what VAT rate for my Spanish customers?", "provisionne ma TVA OSS".
permissions:
  mcp:
    qonto: [create_multi_transfer_request, decline_request, get_organization, list_cash_flow_categories, list_client_invoices, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto OSS Navigator

Most e-commerce sellers discover the EU One-Stop Shop **after** crossing the threshold. This skill watches the €10,000 gauge, drafts the quarterly OSS return country by country, and sets the money aside. **Preparation aid, NOT a filing**: the actual OSS return is filed on the seller's national portal (France: impots.gouv.fr, "guichet unique OSS"). Read-heavy, one optional write behind SCA.

## Prerequisites
1. `get_organization` FIRST → accounts (`list_transactions` requires `bank_account_id`/`iban`), country of establishment, optional tax sub-account (name contains "taxe"/"tax"/"impôt"/"TVA"/"OSS").
2. **Designed for a seller established in the EU.** The €10,000 threshold and the rate table are EU-wide rules, valid for every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT). Only the filing portal is national — name the right one from the detected country (France: impots.gouv.fr; Germany: BOP/BZSt; otherwise: "your national OSS portal"). Seller established outside the EU → say the Union scheme rules differ and stop estimating.
3. **Shopify MCP: optional, detected dynamically.** Connected → real shipping countries per order (`list-orders`, `run-analytics-query` — tool names use dashes). Absent → say so plainly and continue in Qonto-only inference mode (explicitly partial).

## The rule (explain it in one breath when relevant)
Since July 2021, one **single EU-wide threshold: €10,000 net per calendar year**, cumulating ALL cross-border B2C distance sales of goods + digital (TBE) services to other EU countries — not per country. It is assessed on the **current AND previous calendar year**. Below: home-country VAT allowed. Above (from the transaction that crosses it): **VAT at the customer's country rate**, declared either via VAT registration in each country or via one quarterly **OSS return** filed at home. Voluntary OSS opt-in below the threshold is possible (binds for 2 years).

## Workflow

### 1. Identity & data sources
`get_organization` → country, accounts, tax sub-account. Probe Shopify MCP availability. State up front which mode applies: **Shopify mode** (order-level shipping countries) or **Qonto-only mode** (inference, partial by nature).

### 2. Sales by customer country
- **Shopify mode**: `run-analytics-query` / `list-orders` → B2C orders by shipping country over the current and previous calendar year, net of refunds. Exclude domestic sales (seller's own country) and non-EU exports — neither counts toward the threshold.
- **Qonto-only mode**: `list_client_invoices` (client country, VAT number) + `list_transactions` on credits (paginate `per_page: "50"`, windowed). Currency hints for non-euro member states (SEK→SE, PLN→PL, DKK→DK, CZK→CZ, HUF→HU, RON→RO, BGN→BG). PSP payouts (Shopify/Stripe/PayPal) aggregate many orders and hide the country → **announce coverage as partial and treat the gauge as a floor**; recommend connecting Shopify or providing an order export.
- **B2B intra-EU sales (valid customer VAT number) are EXCLUDED from OSS** — reverse charge applies. Flag them in a separate line ("n invoices, X € — reverse charge, EC sales list, not OSS"), never mix them into the gauge.

### 3. The €10,000 gauge
Cumulated cross-border B2C sales, current year (and previous-year check): "You're at **X € of 10,000 €**". If under: estimated crossing month from the current run rate. If crossed: date of crossing, and everything from that transaction onward is due at destination rates. Tag each figure 🟢 order-level data / 🟡 inferred floor.

### 4. Destination VAT rates (embedded static table)
**Rate table vintage: 2026-07 — verify against the European Commission "Taxes in Europe" database before any filing.** Standard rates:

| Rate | Member states |
|---|---|
| 17% | LU |
| 18% | MT |
| 19% | DE · CY |
| 20% | AT · BG · FR |
| 21% | BE · CZ · ES · LT · LV · NL · RO |
| 22% | IT · SI |
| 23% | IE · PL · PT · SK |
| 24% | EE · EL |
| 25% | DK · HR · SE |
| 25.5% | FI |
| 27% | HU |

Default to the standard rate. If the products may qualify for reduced rates (books, food, children's items…), **flag it and ask — never guess a reduced rate**.

### 5. Quarterly OSS draft
Country by country: **taxable base (net) · rate applied · VAT due**, plus the total. Non-EUR sales converted at the ECB rate of the last day of the quarter (state this). Include the deadline — **end of the month following the quarter** (30/04 · 31/07 · 31/10 · 31/01) — and the national filing portal. Corrections of past quarters go into the current return (post-2021 rules). If the user isn't OSS-registered yet, say registration comes first (takes effect the following quarter) and where to do it.

### 6. Provision — only with explicit consent
If a tax sub-account exists and **the user explicitly confirms**, `create_multi_transfer_request`: `debit_iban` = main account; transfer needs `credit_iban`, `credit_account_name`, **`credit_account_currency`** (422 if omitted), `amount`, `currency`, `reference` ("PROVISION TVA OSS Qn-YYYY"). Put the country-by-country breakdown in the request `note` — the approver sees it at SCA time. Then say plainly: **the request is pending in the Qonto app; nothing moves until the user approves with their own SCA.** Never present it as executed. In rehearsals, `decline_request` afterwards (`request_type: "multi_transfers"`, plural).

## Output formats
**Always** reply in the conversation with markdown tables:
1. **Threshold gauge** — cumulated B2C cross-border sales / €10,000, crossing date (actual or estimated), confidence tags.
2. **OSS draft table** — country · base · rate · VAT due · total, with deadline and portal.
3. **Excluded flows** — domestic sales (→ see `qonto-vat-return`), B2B reverse-charge, non-EU exports.

**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): an **HTML dashboard** — gauge bar, country map/table, quarter timeline. If the host cannot render files, say nothing about it. When a provision is created, the request note carries the full breakdown.

## Guardrails
- **Preparation aid, NOT a filing.** The OSS return is filed on the national portal (France: impots.gouv.fr, guichet OSS). Recommend accountant validation in every report.
- The rate table carries its vintage (2026-07) and must be verified before filing. Reduced rates are asked about, never guessed.
- B2B intra-EU (reverse charge) is excluded from OSS and reported separately; domestic VAT belongs to `qonto-vat-return`; the provisioning pattern is shared with `qonto-tax-pilot`.
- Qonto-only inference is announced as **partial** (a floor), never presented as complete country coverage. Never invent a country breakdown.
- NEVER create a transfer request without explicit confirmation in the current conversation; never present it as executed — it is pending the user's SCA approval.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50). Empty or short history → degrade honestly, no invented sales.
