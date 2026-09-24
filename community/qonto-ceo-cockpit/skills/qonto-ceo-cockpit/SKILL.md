---
name: qonto-ceo-cockpit
description: One-prompt CEO cockpit for Qonto accounts. Builds a self-contained interactive HTML dashboard of the whole company — where money comes from and where it goes (month + year flow view), month/year/forecast cards, a 3-month projection from recurring flows and open invoices, a live day-rate × billable-days hypothesis panel that recalculates without any new API call, and an eye toggle to hide sensitive lines when presenting. Use for "montre-moi ma boîte", "show me my company", "where does my money go?", "build my CEO dashboard", "prepare the view for my banker meeting", "what if I raise my day rate by €50?".
permissions:
  mcp:
    qonto: [get_organization, list_cash_flow_categories, list_client_invoices, list_labels, list_supplier_invoices, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto CEO Cockpit

"My Company", generated on demand. 100 % read-only: the skill reads the account, then hands the user a single HTML file that IS the deliverable — flows, cards, forecast and live what-if sliders, all embedded, zero external dependency.

## Prerequisites
1. `get_organization` → accounts, balances, country, legal identity. Nothing hardcoded: every number on the cockpit comes from the connected account. Detect a tax sub-account by name (taxe/tax/impôt/TVA) → feeds the vault gauge; absent → gauge hidden.
2. **Country-agnostic core**: money flows have no borders — the flow view, cards, recurrences and forecast work for every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT). Only tax-line naming (VAT/IS/URSSAF) is refined for France; elsewhere, use neutral labels ("Taxes") and never invent local tax rules.
3. Works from the first transaction. Under 6 months of history, the forecast degrades honestly (🟡 tags + warning); with zero transactions, the skill says so and renders an empty-state cockpit instead of pretending.

## Workflow

### 1. Discover the account
`get_organization` first (`list_transactions` requires `bank_account_id`/`iban`). Note each account's balance for the consolidated-balance KPI. `list_labels` once: labels are the primary grouping key for spending categories (`list_cash_flow_categories` returns **403 missing oauth scope** on the claude.ai connector — labels are the reliable path).

### 2. Read the flows (12 months)
`list_transactions` per account, `per_page: "50"`, paginated in 3-month windows, current month first, then back 12 months.
- **Inflows** grouped by source: normalized counterparty (client names), account interest, internal/shareholder contributions.
- **Outflows** grouped by label when present, else by normalized counterparty; keep an explicit "Uncategorized" bucket with its transaction count — never silently spread it.
- Internal transfers between the org's own accounts are netted out of the flow view (they are not income or spend); the tax-vault transfer feeds the vault gauge instead.

### 3. Invoices and recurrences
- `list_client_invoices`: unpaid invoices at `due_date`, shifted by each client's historical payment delay → dated forecast inflows. Line items with a day unit ("day"/"jour") → **detect the day rate** (median `unit_price`).
- `list_supplier_invoices`: scheduled/to-pay → dated forecast outflows.
- **Recurring flows** from history: normalized counterparty, stable amount (±10 %), monthly/quarterly/yearly cadence, ≥3 hits (2 for yearly) → subscriptions, rent, payroll, bank fees.

### 4. Build the 3-month forecast
Month by month: recurrences on their typical dates + invoice flows + a baseline for irregular spend (median of past months). Every figure carries a tag: 🟢 seen in history / 🟡 estimated. Totals show both layers separately — the cockpit never blends real and estimated without saying so.

### 5. Embed the hypotheses
If a day rate was detected (service business): pre-fill the hypothesis panel — day rate + billable days per month (defaults from invoice history). If no day-based invoicing exists, omit the panel and say why. **All data and formulas are embedded in the page as a JS object**: moving a slider recalculates the revenue projection, the 3-month cards and the year-end estimate instantly, client-side — no MCP call, no reload.

### 6. Render the cockpit
Generate a **single self-contained HTML file** (artifact on claude.ai, file in Claude Desktop / Claude Code):
- **Flow view** (Sankey-style, inline SVG built by the page's own JS): sources → company → spending categories, ribbon thickness ∝ amount, month/year toggle, hover tooltips.
- **KPI row**: consolidated balance · month net (in − out) · tax-vault gauge (if sub-account found) · 3-month forecast net.
- **Category cards**: month / year / 3-month forecast per line, confidence tags, cadence badges for subscriptions.
- **Hypothesis panel**: day-rate and billable-days sliders, live recalc (step 5).
- **Eye toggle** per line: one click hides a sensitive line from the view and from visible totals; hidden lines are listed as chips to restore. **Presentation feature, not security**: the data stays in the local file's source. For a shareable/banker export, regenerate on request with hidden lines *excluded from the data itself*.
- Constraints: inline CSS/JS only, **no external resource** (CDN, fonts, images — artifact CSP blocks them), bars/ribbons in pure CSS + inline SVG (no chart library), light/dark theme via `prefers-color-scheme`, brand palette violet `#6B4EFF` / dark `#1D1B29` / white.
- Refresh on demand: re-running the prompt regenerates the file with fresh data.

**Fallback** — when the host cannot render files: deliver the same content as structured markdown (KPI table, in/out flow tables month + year, 3-month forecast table, hypothesis math shown for 2–3 day-rate scenarios). Don't mention the HTML at all in that case.

## Cross-skill integration (optional, detected — never required)
This cockpit is the natural final screen of the qonto skill family: if their outputs are available in the conversation, slot them in — `qonto-tax-pilot` → tax-vault gauge and tax deadlines, `qonto-subscription-guardian` → detailed subscriptions card, `qonto-invoice-chaser` → expected-receipts dates. Absent, the cockpit computes its own simpler versions from raw data.

## Guardrails
- **Read-only skill**: no write tool, no transfer, no payment — nothing to approve, nothing at risk. Say it plainly when asked.
- Masking is presentation-only; never present a masked view as a redacted document. Offer a truly excluded regeneration for sharing.
- Forecast and hypotheses are estimates, not accounting: 🟡 everywhere they apply, accountant validation recommended.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50). Never invent a category, a tax rule, or a number the account doesn't support.
