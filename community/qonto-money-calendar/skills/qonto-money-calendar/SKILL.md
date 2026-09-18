---
name: qonto-money-calendar
description: Two-way bridge between a Qonto account and Google Calendar. Direction 1 pushes every upcoming money date into the calendar — supplier invoices to pay, client invoices to collect, recurring charges detected from history (rent, subscriptions, tax direct debits) — with the amount in the event title and a D-3 reminder. Direction 2 reads billable days tagged [Client] in calendar event titles and drafts the end-of-month invoice (days × confirmed day rate) in Qonto. Use for "put my money dates in my calendar", "mets mes échéances dans mon agenda", "what's due this month?", "génère ma facture du mois depuis mon agenda", "invoice my tagged days for June".
permissions:
  mcp:
    qonto: [create_client, create_client_invoice, create_quote, delete_client_invoice, get_organization, list_client_invoices, list_clients, list_products, list_supplier_invoices, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto Money Calendar

Money lives in deadlines, not in lists. This skill makes the calendar the single place where the money month is visible — and billable. Two directions: **push** (Qonto deadlines → calendar events) and **read** (tagged billable days → draft invoice in Qonto). Two writes, both gated: no calendar event without a confirmed recap, no invoice beyond DRAFT.

## Prerequisites
1. `get_organization` first → organization, country, bank accounts (`list_transactions` requires a `bank_account_id`/`iban`), invoicing settings. Nothing hardcoded; the skill adapts to whatever it finds.
2. **Google Calendar MCP — required for both directions.** Detect it dynamically. Present → full mode. Absent → say so plainly and degrade: direction 1 outputs the schedule as a markdown table in the conversation; direction 2 is **unavailable** (there is nothing to read) and the skill says exactly that instead of pretending.
3. **Country-agnostic**: due dates, recurrences and invoices work identically in every Qonto country. Tax-related events are only what the **history shows** (detected direct debits) — never invented local deadlines. For a full French tax schedule with amount estimation, point the user to the `qonto-tax-pilot` skill.

## Workflow

### Direction 1 — push the money month into the calendar

#### 1. Collect every dated item
- `list_supplier_invoices` (paginate `per_page: "50"`) → invoices still to pay, with `due_date` and amount → "to pay" events.
- `list_client_invoices` → unpaid invoices with due dates → "to collect" events (money in, not out — label them differently).
- `list_transactions` per account over **24–36 months** (3-month windows, `per_page: "50"`) → recurring flows: normalized counterparty (case/accents merged), stable amount (±10 %), monthly / quarterly / **yearly** cadence — yearly ones (insurance, domain renewals, CFE-like tax debits) only become visible across 24–36 months, ≥3 hits (2 for yearly). Project each recurrence onto its next expected dates.

#### 2. Recap BEFORE writing — always
Show one markdown table: date · event title · amount · source (invoice / recurrence 🟢 seen ≥3× / 🟡 estimated) · reminder. The user confirms, edits, or drops lines. **No event is created without this confirmed recap.**

#### 3. Create the events
On explicit confirmation only, via the Google Calendar MCP: one all-day event per deadline, **amount in the title** (e.g. `💸 Rent — €1,200` / `💰 Invoice INV-2026-042 due — €4,800`), **reminder at D-3**, details in the description including the marker `[qonto-money-calendar]`. Before creating, search existing events for that marker in the same window → update instead of duplicate (safe re-runs). Amounts from recurrences are labeled *estimated* in the description.

### Direction 2 — read billable days, draft the month's invoice

#### 4. Read the tagged days
Convention (explained to the user on first run, documented in the PROCEDURE): a billable day is a calendar event whose title contains `[ClientName]` — e.g. `[Acme] onsite sprint`. One event day = 1 billable day; multi-day events count each day; an explicit `0.5` in the title counts a half-day. Read the requested period from Google Calendar, then show the count per client: `[Acme] → 12 days in June`, with the list of dates so the user can spot mistakes.

#### 5. Confirm the day rate — never guess it
Deduce a **proposed** day rate from Qonto history: `list_client_invoices` filtered on that client (recent unit prices on day-based lines) and `list_products` (a "day"/"jour"/"TJM" catalog item). Show where the number comes from, then **ask for explicit confirmation**. No history and no catalog match → ask the user outright. The rate is never assumed, defaulted, or silently reused.

#### 6. Draft the invoice
Match `[ClientName]` against `list_clients`; ambiguous or missing → ask (offer `create_client` only with confirmed details). Then `create_client_invoice` as **DRAFT**: one line "Consulting services — {month}" (or the matched catalog product), quantity = counted days, unit price = confirmed rate, VAT from the catalog product or the client's invoicing settings — **never a guessed VAT rate**. Report: "Draft created in Qonto — review and send it from the app (or ask me to send it after you've checked)." Never send without a separate explicit request.

## Output formats
1. **Always** in the conversation: the schedule table (direction 1) and the billable-days recap + invoice summary (direction 2), as markdown.
2. **Google Calendar**: the events themselves — the calendar becomes the dashboard.
3. **Qonto**: the draft invoice, visible in the Invoicing section.
Without the Calendar MCP: output 1 only, stated plainly.

## Guardrails
- **No calendar event without a confirmed recap** in the current conversation; re-runs update marked events instead of duplicating.
- **The day rate is never guessed**: deduced from history, then confirmed by the user — every time.
- Invoices created via MCP are **REAL documents**: stay in DRAFT, let the user review; rehearsals use a fictional client + draft + `delete_client_invoice`.
- Estimated amounts (recurrences) are labeled as estimates; the skill never presents a projection as a booked amount.
- This skill moves no money and pays nothing — it schedules and drafts. Anything payment-related stays in the Qonto app under the user's own SCA.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50).
