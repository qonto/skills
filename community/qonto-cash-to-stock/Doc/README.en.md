# 📦 qonto-cash-to-stock — Restocking, constrained by cash

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> Read-heavy, one safe write: the supplier transfer request — money moves only after the user's own SCA approval in the Qonto app

---

## 🎯 Why this matters (usefulness)

The real ceiling on an e-commerce restock isn't demand — it's **cash**. Order too much and the account is in danger the day VAT hits; order too little and a stock-out kills the sales momentum. `qonto-cash-to-stock` answers THE question: **"how many units can I order without endangering the account, and by when?"**

1. **Truly free cash** — every account balance − upcoming supplier invoices − tax deadlines detected in history − recurring fixed costs − a safety buffer. The dated minimum of the curve.
2. **Velocity & stock-out date** — Shopify when connected (units/day and on-hand stock per product); otherwise estimated from Qonto receipts + the `list_products` catalog, and clearly labeled as an estimate
3. **The four decision numbers** — free cash · stock-out date · fundable units · latest order date, every figure tagged 🟢 seen in data · 🟡 estimated · 🔵 depends on your input
4. **One safe action** — the supplier transfer request, prepared when the user decides; money moves **only** after their own SCA approval in the Qonto app

Would someone use this on a Monday morning? That's literally when e-commerce founders look at the weekend's sales and wonder whether they can afford to reorder.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | Tax-deadline detection **from history** works everywhere; calendar refinement: **France** (same logic as `qonto-tax-pilot`). Other Qonto countries (DE, ES, IT…): only debits actually observed are projected — never invented deadlines | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Shopify MCP | **Optional, detected dynamically**: units/day and stock per product. Without it, graceful degradation: velocity estimated from receipts + catalog | ⭕ recommended |
| ≥ 3–6 months of history | Below that, honest degradation (🟡 tags + warning); 24–36 months to catch annual tax cadences | ⭕ |
| E-commerce activity with suppliers | Otherwise the skill still shines as a truly-free-cash calculator | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Cash snapshot**: `get_organization` first — every account, balance, currency, country
2. **Committed outflows**: supplier invoices coming due (`list_supplier_invoices`), tax deadlines detected in history (outgoing direct debits first, the tax office merged under all its spellings — the `qonto-tax-pilot` logic; when that skill is installed its schedule is reused), recurring fixed costs (rent, payroll, subscriptions) → a dated 90-day calendar of outgoing money
3. **Truly free cash**: day-by-day curve = balances + a conservative receipts baseline − commitments − safety buffer (one month of fixed costs by default, adjustable). The minimum of the curve is what a restock may consume
4. **Velocity & stock-out**: Shopify when connected (`run-analytics-query` + `get-inventory-levels`) → stock-out date per product; otherwise a receipts-based estimate, tagged 🟡
5. **The answer**: N fundable units (free cash ÷ landed unit cost — asked when unknown, never silently guessed) and the latest order date (stock-out − supplier lead time)
6. **Request + SCA**: with explicit consent, `create_multi_transfer_request` with the full calculation in the note → push notification → **the user's** 2FA approval in the app → final report

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The security model** (not a limitation): solid arrows are risk-free reads; the dashed arrow requires explicit consent given in the conversation and only produces a *request*. The account holder's own SCA (2FA) in the Qonto app is what moves money. Neither Claude nor the MCP can.

## 🔢 The four decision numbers

| Number | How it's built | Tag |
|---|---|---|
| **Free cash after commitments** | Minimum of the 90-day curve: balances − suppliers − detected taxes − fixed costs − buffer | 🟢/🟡 |
| **Stock-out date** | On-hand stock ÷ velocity (Shopify), or receipts + catalog estimate | 🟢 with Shopify · 🟡 without |
| **Fundable units** | Free cash at the payment date ÷ landed unit cost | 🔵 depends on the confirmed cost |
| **Latest order date** | Stock-out date − supplier lead time (asked once) | 🔵 |

> **Example (fictitious figures, for illustration)**: "Free cash after commitments: €8,400. Stock-out expected on Sept 28. Unit cost €6.50 → **1,290 fundable units**; your supplier ships in 3 weeks → **order by Sept 7**." Say yes, and the supplier transfer request is created — pending your approval in Qonto. It just works — and the last word is always a human thumb on SCA.

## 🧪 Holds up on messy data

- No Shopify MCP? → the skill says so and switches to the receipts-based estimate, every derived figure tagged 🟡
- No supplier invoices in Qonto? → commitments built from recurring debits only, stated plainly
- Unit cost or lead time unknown? → asked once, never silently guessed
- Empty account, thin history (< 3 months), non-French company → the skill says what it can and can't compute instead of pretending
- Multi-account orgs, pagination ≤ 50, direct-debit spelling variants (same counterparty under several names) — all handled

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (commitments calendar, curve summary, four decision numbers, request recap) | **Always** — the baseline |
| **Interactive dashboard** | **HTML** file/artifact: free-cash curve, deadlines as markers, stock-out countdown, fundable-units gauge | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |
| **Qonto request note** | Text attached to the transfer request, visible at SCA approval time: the full calculation | Every time a request is created |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the restock dilemma → commitments & truly free cash → dated stock-out & fundable units → **the SCA approval filmed on a phone** → the final dashboard. All on-screen figures come from the demo account; the examples in this documentation are fictitious.

## 🔗 Companion skills

- **`qonto-tax-pilot`** — tax deadlines come from the same detection logic; installed together, cash-to-stock reuses its schedule instead of recomputing
- **`qonto-shopify-bridge`** — reconciles the *past* (Shopify payouts vs Qonto); cash-to-stock decides the *future* (the next order)

## 💡 Roadmap ideas

- Multi-supplier arbitration: split one budget across several orders
- Finer seasonality (velocity weighted by month, sales events) via 12 months of Shopify analytics
- "Latest order date" reminder pushed to a calendar MCP when one is detected
- Supplier payment scenarios (30 % deposit + balance on delivery) → two dated requests instead of one

## 🛡 Guardrails

- NEVER creates a transfer request without explicit confirmation in the current conversation; never presented as executed — it is pending the user's SCA approval
- Estimates ≠ purchase advice: the stock decision stays human; every assumption is displayed (unit cost, lead time, buffer)
- Honest degradation without Shopify, without a catalog, without supplier invoices, or on thin history — the skill never fills gaps with invented numbers
- All examples in this documentation are **fictitious and labeled as such**
- IBANs masked (last 4 digits) · pagination ≤ 50 everywhere · rehearsals cleaned up with `decline_request`

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
