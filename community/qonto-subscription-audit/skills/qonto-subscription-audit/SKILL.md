---
name: qonto-subscription-audit
description: Complete recurring-spend audit for Qonto accounts. Inventories every recurring charge (cards AND direct debits) over 24–36 months, computes the TOTAL annualized subscription cost, classifies each line (✅ active · 👥 duplicate · 🧟 zombie, always user-confirmed · 🎣 trial gone paid), catches nascent subscriptions early (🌱 new counterparties that look like a starting subscription), detects silent price hikes step by step (old → new price, %, FX/VAT excluded), totals the cumulated annual overcost, renders a dashboard directly in Claude plus a self-contained HTML export in Qonto colors, and drafts renegotiation emails and an optional monthly digest (Gmail drafts, never sent). 100% read-only on Qonto. Use for "audite mes abonnements", "audit my subscriptions", "combien je paie d'abonnements par an ?", "which of my suppliers quietly raised their prices?", "what am I still paying for that I don't use?", "is this new charge a subscription?", "écris-moi l'email pour renégocier".
permissions:
  mcp:
    qonto: [get_organization, list_cash_flow_categories, list_supplier_invoices, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto Subscription Audit

Every recurring euro, audited: what you pay, what you forgot, what quietly went up, and what just started. 100 % read-only on Qonto — it inventories, classifies, quantifies and drafts; the only outbound artifacts are email *drafts* the user reviews and sends themselves. To then protect a subscription with a capped virtual card, hand over to **qonto-subscription-guardian** (that skill owns the card writes).

## Prerequisites
1. `get_organization` FIRST → accounts, balances, currency, country (`list_transactions` requires `bank_account_id`/`iban`).
2. **History ≥ 24 months recommended**: a YEARLY subscription only shows up with 2 occurrences — on a 12-month window annual renewals fly under the radar. Below 24 months, audit what's visible and say plainly that yearly lines may be missing.
3. **Country-agnostic core**: inventory, statuses and hike detection work on any Qonto account (FR, DE, ES, IT, AT, NL, BE, PT). Only the inflation benchmark is localized — use the country's recent headline inflation when known, else the euro-area figure, and **state the reference used**.
4. **Optional Gmail MCP**: detect dynamically. Present → offer negotiation emails and the monthly digest as *drafts* (never send). Absent → say so once and output copy-paste text. The core needs Qonto only.

## Workflow

### 1. Learn the past (24–36 months)
`list_transactions` per account, `side: "debit"`, paginate `per_page: "50"` in 3-month windows, as far back as history allows (target 36 months — annual cadences and multi-year creep are invisible on 12). **Normalize counterparties**: strip references, dates, store IDs and card-processor prefixes (`PAYPAL *`, `SUMUP *`, `SQ *`…); merge SEPA-mandate and card variants of the same supplier (e.g. "GOOGLE IRELAND LTD" + "GOOGLE *CLOUD" → one supplier). Use `emitted_at` for cadence math, not `settled_at` (card settlement drifts 1–2 days).

### 2. Inventory the recurring charges — the headline number
A **subscription** = same normalized counterparty + regular cadence (monthly 28–32 d · quarterly 85–95 d · **yearly 350–380 d**) + ≥ 3 occurrences (2 for yearly), card charges AND direct debits alike. Per line: current price, cadence, first seen, last charge, full dated price series (account currency; foreign-currency series flagged — FX noise is not a price move). Where `list_supplier_invoices` has matching invoices, prefer `total_amount` / `total_amount_excluding_vat` — it separates a VAT-rate change from a real price change. Sum everything into the **TOTAL annualized subscription cost** — the audit's headline.

### 3. Classify the portfolio — and catch the newborns
Four statuses, plus a dedicated "New" section:
- ✅ **Active** — regular and confirmed useful by the user (the skill can't see usage; it asks, never decrees).
- 👥 **Duplicate** — two tools doing the same job (two meeting tools, two hosts, two storage providers); quantify the saving of keeping one.
- 🧟 **Zombie** — charged ≥ 6 months, zero variation, dormant category, no other account signal → *probably unused*, **always user-confirmed** before being labeled.
- 🎣 **Trial gone paid** — recent first full-price charge preceded by nothing or a token amount.
- 🌱 **New / probable subscription** — for every recent counterparty with **< 3 occurrences**, score the odds it's a nascent subscription. **First signal: use your own knowledge of merchants.** Many vendors are notoriously subscription businesses — streaming & software (Netflix, Spotify, Adobe, Microsoft 365, Google Workspace), AI (OpenAI, Anthropic), design & dev (Figma, Canva, Slack, Notion, GitHub), **course & creator platforms (Systeme.io, Skool, Kajabi, Podia, Teachable)**, **hosting & domain registrars (OVH, PlanetHoster, Gandi, IONOS, o2switch, GoDaddy — domains renew YEARLY, easy to miss)**, cloud (AWS, Scaleway), mobile/ISP operators… — so a **single first charge** from one of them (normalize the card/SEPA descriptor first) is tagged 🌱 immediately, **no history needed**. Then the behavioral signals: typical round recurring amount, label hints (`subscription`, `monthly`, `plan`), a 2nd occurrence ~30 days after the 1st. Report as "probable subscription, to confirm" in its own **New** section — the early detection that catches a trial before it becomes rent.

Cross-cutting alerts: 💥 double charge (same supplier, same amount, < 72 h) · 🔁 cadence switch (monthly → yearly often hides a repricing).

### 4. Detect price hikes — steps, not noise
A **plateau** = ≥ 2 consecutive charges within ±2 %. A **hike** = a jump from one plateau to a higher one that **persists ≥ 2 cycles**. Explicitly NOT hikes: single outliers, prorated first/last months, FX wobble on non-EUR billing, VAT-rate changes (compare excl-VAT when invoices allow). High-variability series (coefficient of variation ≳ 15 %: API, cloud, ads) = ⚪ **variable usage**: isolate the implicit unit price from invoice line items when possible, otherwise say exactly that — never report it as a hike. Per hike: date, old → new price, %. Per supplier: (current plateau − plateau 12/24/36 months ago) × yearly frequency; the sum = **the cumulated annual overcost**. Benchmark each hike against general inflation: 🟢 ≤ inflation · 🟡 above · 🔴 ≥ 3× inflation or ≥ 10 % in one step.

### 5. Report — tables, dashboard in Claude, HTML export
**Always** reply in the conversation with markdown tables: (a) headline — total annualized cost, zombie/duplicate share, annual overcost of hikes; (b) portfolio sorted by annual cost (supplier · price · cadence · annual cost · status · flags); (c) **New 🌱** section; (d) hikes table with 🟢🟡🔴 tags; (e) variable usage kept separate.
**When the host can render it, build the dashboard directly in Claude** (artifact): total annual cost counter, breakdown by category, lines grouped by status ✅👥🧟🎣🌱, hikes with deltas, **next-3-months forecast** (upcoming charge dates and amounts from the detected cadences). **On request, export the same dashboard as ONE self-contained HTML file** in the Qonto palette (violet #6B4EFF · black #1D1B29 · white, light/dark theme) to keep or share. If the host renders nothing, the tables are the deliverable — say nothing about it.

### 6. Draft the emails — negotiation and monthly digest
- **Renegotiation** (biggest 🔴/🟡 lines by annual overcost): firm-but-courteous draft in the user's language, fed with real account facts — customer tenure (first transaction date), annual volume (12-month spend), hike record (dates + %), market alternatives as leverage. Ask: previous price back, a loyalty rate, or a clear justification.
- **Monthly digest** (offer it when a mail MCP is present): active subscriptions and the month's charges, month total, next-3-months forecast per subscription, hikes and new 🌱 lines since the last digest.
Both via `create_draft` **only after the user confirms** (recipient left blank unless provided) — **never send**. No mail MCP → full text to copy, said in one line.

## Guardrails
- **Zero Qonto writes** — this skill never calls a Qonto write tool. To cap a subscription with a dedicated virtual card, point the user to **qonto-subscription-guardian** — don't attempt it here.
- "Zombie" is a hypothesis, not a verdict — always user-confirmed before recommending a cut. 🌱 lines are "probable, to confirm", never stated as fact.
- Never accuse a supplier of a hike when the data says usage, FX or VAT — when unsure, park the line in variable usage and say why.
- Emails are *drafts*: never sent, no recipient added without the user. Estimates from payment data ≠ contract audit; suggest checking the supplier's invoice before sending.
- Degrade honestly: < 24 months of history → yearly lines may be invisible, say so; empty account or no recurring charges → state it, invent nothing.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50). Don't rely on `list_cash_flow_categories` (403 on the claude.ai connector) — use labels and counterparty names instead.
