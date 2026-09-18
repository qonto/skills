# 🧭 qonto-oss-navigator — EU e-commerce VAT, before it catches up with you

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> One-Stop Shop (OSS) navigator: the €10,000 threshold gauge, a country-by-country quarterly OSS draft, and an optional provision behind SCA
> ⚠️ **Preparation aid, NOT a filing** — the OSS return is filed on the seller's national portal

---

## 🎯 Why this matters (usefulness)

Past **€10,000 of cross-border B2C sales to other EU countries** in a year (one single threshold, ALL distance sales cumulated — not per country), VAT is due **at the customer's country rate**, declared through the One-Stop Shop. Most e-commerce sellers discover this too late — often during their first audit. `qonto-oss-navigator` turns a Qonto account into an OSS watchtower:

1. **Sales by shipping country** — real order-level countries when the Shopify MCP is connected; otherwise inference from client invoices and Qonto payment data — **announced as partial**, never dressed up as full coverage
2. **The €10,000 gauge** — cumulated cross-border B2C sales this year (with the previous-year check the rule requires): "you're at X € of 10,000 €", crossing dated or estimated from the current run rate
3. **Quarterly OSS draft** — country by country: net base, the customer country's rate (embedded, vintage-dated table for all 27 member states), VAT due, total, deadline and filing portal
4. **Optional provision** — a transfer request for the OSS total to the tax sub-account; money moves **only** after the user's own SCA approval in the Qonto app

And **intra-EU B2B sales** (valid customer VAT number)? **Excluded from OSS** — reverse charge. The skill isolates and reports them separately, never mixed into the gauge.

Would someone use this on a Monday morning? Every EU seller shipping abroad has this exact blind spot — and the answer takes one question.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Designed for a seller established in the EU.** The €10,000 threshold and the rate table are EU-wide rules — valid for every Qonto country (FR, DE, ES, IT…). Only the **filing portal** is national (France: impots.gouv.fr; Germany: BZSt; otherwise your national OSS portal) | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Shopify MCP | **Optional, detected dynamically**: real shipping countries per order (`list-orders`, `run-analytics-query`). Absent → Qonto-only mode, announced as partial | ⭕ recommended |
| A "tax" sub-account | Created once in the Qonto app — detected by name (tax/taxe/impôt/TVA/OSS) | ⭕ recommended — otherwise the skill computes without acting |
| Cross-border EU sales | No B2C sales to other EU countries → the skill says so and stops there — no invented gauge | ℹ️ detected |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Identity & sources**: `get_organization` first (country of establishment, accounts, tax sub-account), Shopify MCP probe → the skill states its mode up front: **Shopify** (real countries) or **Qonto-only** (partial inference)
2. **Sales by shipping country**: Shopify orders net of refunds, or client invoices + currency hints (SEK, PLN, DKK, CZK…) on the Qonto side. Domestic sales and non-EU exports excluded; intra-EU B2B isolated (reverse charge)
3. **Threshold gauge**: cumulated cross-border B2C sales for the current calendar year AND the previous-year check (the rule looks at both) — crossing dated or estimated
4. **Customer-country rates**: static table for all 27 member states, **vintage-dated (2026-07)** — the vintage is displayed and the skill asks to verify before any filing; reduced rates asked about, never guessed
5. **Quarterly OSS draft**: country by country (base · rate · VAT due), ECB last-day-of-quarter conversion for non-euro currencies, deadline (end of the month following the quarter) and portal
6. **Provision** (explicit user consent only): `create_multi_transfer_request` with the country-by-country breakdown in the request note → **SCA approval** in the Qonto app

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The security model** (not a limitation): solid arrows are risk-free reads; the dashed arrow requires explicit consent given in the conversation and only produces a *request*. The account holder's own SCA (2FA) in the Qonto app is what moves money. Neither Claude nor the MCP can.

## 🧪 Holds up on messy data

- No Shopify MCP? → Qonto-only mode, coverage announced as **partial**, the gauge presented as a floor, with a clear recommendation to connect Shopify or provide an order export
- PSP payouts aggregate orders and hide the country → the skill says so instead of pretending
- Invoices without a client country or VAT number? → counted as "unattributed", disclosed, never guessed
- No cross-border EU sales at all? → the skill says the OSS doesn't apply yet and stops — no invented gauge
- B2B invoices with a valid VAT number → reverse-charge line, kept out of the gauge and the draft
- Seller established outside the EU → the skill says the Union-scheme rules differ and stops estimating

## ✨ The "it just works" moment

> "EU B2C sales: you're at **€8,420 of €10,000** — estimated crossing in **October** at the current pace. Here's your OSS draft for the quarter, country by country, and the **€612 provision** to set aside." *(invented figures)*

One question, three answers: where you stand, what you'll declare, what to set aside.

## 📤 Output formats (where does the draft land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (gauge, country-by-country OSS draft, excluded flows) | **Always** — the baseline |
| **Interactive dashboard** | **HTML** file/artifact: gauge bar, per-country table, quarter timeline | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |
| **Qonto request note** | Country-by-country breakdown attached to the transfer request, visible at SCA approval time | Every time a provision is created |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the threshold trap → the gauge → the country-by-country OSS draft → the provision + SCA approval → the dashboard. It runs live on a real production account.

## 💡 Roadmap ideas

- **IOSS** (imports ≤ €150) — the import twin of the One-Stop Shop, same engine, different scheme
- Reduced rates by product category — cross Shopify products with each country's reduced-rate categories
- OSS deadline reminders pushed to the user's calendar when a calendar MCP is detected
- Quarter-by-quarter gauge history
- WooCommerce / other order sources behind the same "shipping country per order" interface

## 🛡 Guardrails

- **Preparation aid, NOT a filing**: the OSS return is filed on the national portal; accountant validation recommended in every report
- The rate table carries its **vintage (2026-07)** and must be verified before filing; reduced rates asked about, never guessed
- **Intra-EU B2B excluded from OSS** (reverse charge) — reported separately, never in the gauge
- Qonto-only inference announced as **partial** (a floor); never an invented country breakdown
- NEVER creates a transfer request without explicit confirmation in the current conversation; never presented as executed — pending the user's SCA approval
- IBANs masked (last 4 digits) · pagination ≤ 50 everywhere · empty account → the skill says so and stops

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML, FR/EN). See also: `qonto-vat-return` (domestic VAT) · `qonto-tax-pilot` (tax provisioning).*
