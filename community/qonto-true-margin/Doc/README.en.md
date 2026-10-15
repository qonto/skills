# ⚖️ qonto-true-margin — Pricing from real banking costs

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> The e-commerce dashboard's "margin" is a fiction; **the bank account knows the real one**. Zero write on the Qonto side — the only write is Shopify prices, line by line, on explicit validation.

---

## 🎯 Why this matters (usefulness)

Every e-commerce dashboard shows a margin built from theoretical costs. What **actually** leaves the bank account — PSP fees really debited, EUR/USD FX costs, real carrier invoices, supplier purchases — tells a different story. `qonto-true-margin` rebuilds the truth and turns it into a pricing decision:

1. **Real costs classified from Qonto debits** — observed PSP fees (or "unknown, not zero" when they're netted inside payouts), FX, carriers, supplier COGS (`list_supplier_invoices`) — each family tagged 🟢 observed · 🟡 derived · ⚪ unknown
2. **True contribution margin per product** — Shopify per-product sales − real costs allocated **pro-rata (an announced heuristic**: revenue or units, user's choice, method printed on every table)
3. **Loss-making products identified** — sorted first, with the gap vs the dashboard's theoretical margin in plain sight
4. **New prices proposed, then applied** — break-even + target price; applied in Shopify (`update-product`) **only after explicit line-by-line validation** — never in bulk

Would someone run this on a Monday morning? "Which of my products actually made money last month?" is *the* Monday-morning question for a store owner.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Universal** — works identically for all Qonto countries (FR, DE, ES, IT, AT, NL, BE, PT). The truth is the account debit; multi-currency reported per currency, never converted silently | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Shopify MCP connected | Per-product sales + price updates. Without it: **announced degraded mode** — global margin by cost family, no product granularity | ⭕ recommended |
| Stripe MCP connected | Per-charge fee detail | ⭕ optional |
| ≥ 3 months of history | Below that: lower confidence tags + honest warning | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Real costs from the bank**: 12–24 months of Qonto debits (paginated ≤ 50), classified by family — PSP fees (⚠️ Shopify Payments nets its fees **inside** the payout: no separate debit → effective rate derived from gross vs net when Shopify is connected, otherwise "unknown, not zero"), FX (local currency ≠ account currency), shipping (carrier counterparties; card payments reconciled on `emitted_at`), supplier COGS (`list_supplier_invoices` + recurring supplier debits). Everything else = fixed costs, excluded from contribution margin, disclosed separately
2. **Per-product sales** (with the Shopify MCP): revenue, units, refunds per product over the same window, plus current prices
3. **Heuristic allocation**: pro-rata revenue (default) or pro-rata units (better for shipping-heavy catalogs) — the user picks, and the method is **printed on every table**. Supplier invoices naming a product are matched directly; allocation covers only the rest
4. **True margin per product**: net revenue − COGS − PSP − FX − shipping, in € and % — loss-makers at the top
5. **New prices**: break-even + target price for the margin the user wants (asked, never assumed). A number, **not a pricing strategy** — elasticity isn't modeled, and the skill says so with every proposal
6. **Validated application**: line-by-line table (product · current price · suggested price · margin before/after) → the user confirms **each line** → `update-product` per confirmed product → the product is re-read from Shopify before anything is reported as done

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The security model**: on the Qonto side the skill is **read-only** — no banking write tool exists in it, nothing can move on the account. The only write is on the **Shopify side** (price updates), and it requires explicit validation of each product in the conversation. A global "apply everything" is refused and re-asked line by line.

## 🆚 How it differs from `qonto-shopify-bridge`

| | `qonto-shopify-bridge` | `qonto-true-margin` |
|---|---|---|
| Nature | **Accounting record of the past** | **Pricing decision for the future** |
| Question | "Did Shopify actually pay me?" | "Does this product actually make me money?" |
| Core | Reconciles payouts ↔ bank, observes effective fees | **Consumes** those observed costs → true margin per product → new prices |
| Writes | None (fully read-only) | None on Qonto; Shopify prices on line-by-line validation |

**Shared input, opposite output**: run the bridge when a payout looks wrong; run true-margin when a price needs fixing. See `qonto-shopify-bridge` for the reconciliation side.

## 🧪 Holds up on messy data

- PSP fees invisible (netted inside payouts)? → derived from gross vs net when Shopify is connected, otherwise labelled **"unknown, not zero"** — never an announced rate passed off as observed
- No Shopify MCP? → degraded mode stated plainly: real margin by cost family, no per-product claim
- Supplier invoices that don't name a product? → allocated pro-rata, with the directly-matched share shown per line
- Card-paid shipping settling 1–2 days late (`emitted_at` vs `settled_at`), refunds reducing net revenue, multi-currency debits — all handled
- Thin history (< 3 months)? → low-confidence tags and an honest warning, not fake precision

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (cost families, per-product margins, price proposals, before/after) | **Always** — the baseline |
| **Interactive dashboard** | **HTML** file/artifact: waterfall from dashboard margin to real margin, loss-maker list, price simulator | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |
| **Shopify confirmation** | `get-product` re-read after every `update-product` — the reported price is the re-read one, not the requested one | Every validated application |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the dashboard margin that lies → the real costs read from the bank debits → **the reveal** (the best-seller sold at a loss — "42% on the dashboard, 11% in reality") → the new price validated line by line and applied in Shopify → the final dashboard. The detailed shooting script is kept internal (out of the repo).

## 💡 Roadmap ideas

- Weight/order-based shipping allocation (Shopify data) — replaces the pro-rata for the shipping family
- Per-charge fee detail via the Stripe MCP — already planned as optional, upgrades 🟡 to 🟢
- Monthly true-margin drift tracking — alert when a product slips under its threshold
- Compared pricing scenarios (2–3 target-margin hypotheses) in the HTML simulator

## 🛡 Guardrails

- **NEVER** applies a price without explicit validation of that specific product in the current conversation; never reported as done without a Shopify re-read
- The allocation is a **stated heuristic** — method (pro-rata revenue or units) printed on every table; true margins are estimates, not accounting
- Suggestion ≠ pricing strategy: elasticity not modeled — said honestly with every proposal
- **Zero Qonto write tool**; invisible PSP fees → "unknown, not zero"
- Honest degradation without Shopify (by-family margins only) · masked IBANs · pagination ≤ 50 · per-currency reporting

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
