# 🛩 qonto-ceo-cockpit — "My Company", the founder's cockpit generated on demand

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> One prompt → one self-contained interactive dashboard. **100 % read-only — zero writes, nothing to approve.**

---

## 🎯 Why this matters (usefulness)

A bank shows you a list of lines. To actually *see* your company — where the money comes from, where it goes, where you'll stand in three months — you need a spreadsheet… or three weeks of your accountant's time. `qonto-ceo-cockpit` does it in one prompt: "**show me my company**" → an interactive, self-contained HTML dashboard built from the account's real data:

1. **Flow view** (Sankey-style) — revenue sources → company → spending categories, ribbon thickness ∝ amount, month/year toggle, hover tooltips
2. **Month / year / forecast cards** per category + KPIs: consolidated balance, month net, tax-vault gauge (when a tax sub-account exists), 3-month forecast
3. **3-month forecast** — detected recurring flows + open client invoices (each client's usual payment delay factored in) + supplier invoices, every figure tagged 🟢 real / 🟡 estimated
4. **Day-rate × billable-days hypothesis panel** — the day rate is detected from invoice line items; move a slider and **the whole projection recalculates live, without a single new API call** (everything is embedded in the page)
5. **Eye toggle** on sensitive lines — present the dashboard without showing everything, typically in a banker meeting

Would someone use this on a Monday morning? It's the Monday-morning screen: open, look, decide.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | Adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Universal core**: flows, cards, recurrences and forecast work in every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT). Only tax-line naming is refined for France; elsewhere, neutral "Taxes" label, no invented local rules | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Qonto labels | Primary grouping key for spending categories (the cash-flow categories endpoint is outside the connector scope — 403); without labels, grouping falls back to normalized counterparties | ⭕ recommended |
| ≥ 6 months of history | Below that, the forecast degrades honestly (🟡 tags + warning) | ⭕ |
| Day-based invoicing | Needed for the hypothesis panel; otherwise the panel is omitted and the skill says why | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Discover**: `get_organization` (accounts, balances, country), tax sub-account detection (vault gauge), `list_labels`
2. **Read 12 months of flows**: `list_transactions` paginated ≤ 50 in 3-month windows — inflows by source (normalized counterparty), outflows by label or counterparty, internal transfers netted out, an explicit "Uncategorized" bucket (never silently spread)
3. **Invoices & recurrences**: unpaid client invoices (historical payment delay per client) + upcoming supplier invoices + recurring-flow detection (stable counterparty, amount ±10 %, monthly/quarterly/yearly cadence, ≥3 hits) — and **day-rate detection** from day-unit invoice lines (median)
4. **3-month forecast**, month by month: recurrences on their typical dates + invoice flows + an irregular-spend baseline, with the 🟢/🟡 layers never blended without saying so
5. **Hypotheses embedded**: day rate + billable days pre-filled, data and formulas shipped as JSON inside the page → instant client-side recalc, zero MCP calls
6. **Cockpit rendered**: one self-contained HTML file (claude.ai artifact / local file) — automatic fallback to structured markdown tables when the host can't render files

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The key point**: this skill is **read-only**. No dashed arrow on the diagram — no write, no transfer, nothing to approve. The only deliverable is a local file you can open, refresh, or share. And the eye toggle is a **presentation** feature: the data stays inside the page, on your machine — nothing leaves anywhere. For a genuinely redacted export (banker, partner), the skill regenerates the file **without** the hidden lines in the data itself.

## 🧭 The cockpit zones

| Zone | Content | Source | Interactive |
|---|---|---|---|
| Flow view | Sources → company → categories, ribbons ∝ amounts | 12 months of transactions, labels | Month/year toggle, hover, click → detail card |
| KPIs | Consolidated balance · month net · tax vault · 3-month forecast | Balances + flows + tax sub-account | Recomputed as lines are hidden |
| Category cards | Month / year / forecast, cadence badges, 🟢🟡 tags | Flows + recurrences + invoices | Eye toggle per card |
| Hypothesis panel | Day rate × billable days (3 months + rest of year) | Day rate detected from invoices | **Sliders, live recalc, no MCP call** |

## 🧪 Holds up on messy data

- No labels? → grouping falls back to normalized counterparties, and the cockpit says so
- Uncategorized transactions? → explicit bucket with its count, never silently spread across categories
- No day-based invoicing? → hypothesis panel omitted, with the reason
- No tax sub-account? → vault gauge hidden, everything else intact
- Empty account? → honest empty-state cockpit, no invented numbers
- Non-French company? → fully functional; only tax naming goes neutral

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Interactive dashboard** | One **self-contained HTML** file: inline CSS/JS, zero external dependency (CSP-safe), pure CSS/SVG bars and ribbons, light/dark theme | **The deliverable** — whenever the host renders files (claude.ai artifacts, Claude Desktop, Claude Code) |
| **Conversation reply** | Structured markdown tables: KPIs, month + year flows, 3-month forecast, priced day-rate scenarios | Automatic fallback when the host can't render files |
| **"Presentation" export** | The same HTML regenerated **without** sensitive lines in the data | On request, for sharing |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem (a bank = a list of lines) → "show me my company" → the dashboard building itself → **the day-rate slider: +€50 and the annual projection moves live** → the eye icon hiding a line for the banker → the skill-family wrap-up. It runs live on a real production account.

## 💡 Roadmap ideas

- Skill-family slot-ins: `qonto-tax-pilot` → vault gauge + tax deadlines, `qonto-subscription-guardian` → detailed subscriptions card (detected in the conversation, never required)
- Year-over-year comparison per category (trend arrows) — the 12-month history is already read
- Multi-currency consolidation for non-EUR accounts
- "Board meeting" mode: print-ready PDF straight from the HTML (`window.print()` + print CSS, still zero dependencies)
- More sliders: new hire, founder salary, one-off purchase — the client-side recalc engine is already there

## 🛡 Guardrails

- **100 % read-only skill**: no write tool, no transfer, nothing to approve — and it says so plainly when asked
- Eye toggle = presentation, not security: never presented as a redacted document; a truly excluded regeneration is offered for sharing
- Forecast and hypotheses are 🟡 estimates, not accounting — accountant validation recommended
- IBANs masked (last 4 digits) · pagination ≤ 50 everywhere · never an invented category, tax rule, or number

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
