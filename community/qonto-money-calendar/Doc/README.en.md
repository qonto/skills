# 📆 qonto-money-calendar — Your cash flow in your calendar, both ways

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> Two directions: Qonto → calendar (deadlines become events) · calendar → Qonto (billable days become invoices)

---

## 🎯 Why this matters (usefulness)

Money lives in deadlines, not in lists. And you live in your calendar — not in an accounting export. `qonto-money-calendar` turns Google Calendar into the dashboard of your money month:

1. **Direction 1 — push**: every upcoming money date lands in the calendar — supplier invoices to pay, client invoices to collect, recurring charges detected over 24–36 months of history (rent, subscriptions, tax direct debits, monthly / quarterly / yearly cadences) — **amount in the title, D-3 reminder** on every event
2. **Direction 2 — read**: billable days tagged `[Client]` in event titles are counted, and the skill drafts the **end-of-month invoice** (days × confirmed day rate) in Qonto
3. **Recap before writing**: no event is created without a confirmed recap in the conversation; re-runs are idempotent (marked events get updated, never duplicated)
4. **The day rate is never guessed**: deduced from the Qonto invoicing history (past invoices, product catalog), then **always confirmed** before any math

Would someone use this on a Monday morning? Open your calendar: the week's money is already there — and last month's work is already invoiced.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| **Google Calendar MCP** | **Required for both directions.** Absent: direction 1 degrades to a markdown schedule in the conversation, direction 2 is unavailable — and the skill says so | ⭕ strongly recommended |
| Country | **Universal** — invoice due dates and history-detected recurrences, never invented local tax rules. Full French tax schedule → the `qonto-tax-pilot` skill | ℹ️ all Qonto countries |
| 24–36 months of history | Needed to see yearly cadences (insurance, renewals, yearly tax debits); below that, honest degradation | ⭕ |
| The `[Client]` tag convention | For direction 2: an event titled `[Acme] onsite sprint` = 1 billable day (explained on first use) | ⭕ direction 2 only |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Account snapshot**: `get_organization` first (organization, accounts, invoicing settings), then Google Calendar MCP detection — present → full mode; absent → table-only, direction 2 unavailable
2. **Collect the deadlines**: supplier invoices to pay (`due_date`), client invoices to collect, recurrences detected over 24–36 months (normalized counterparty, stable amount ±10 %, monthly/quarterly/yearly cadence, ≥3 hits — 2 for yearly), projected onto their next dates
3. **Direction 1 — push**: recap in the conversation (date · title · amount · source 🟢 seen / 🟡 estimated) → on explicit confirmation, events created in the calendar with the amount in the title, a D-3 reminder, and a `[qonto-money-calendar]` marker so re-runs update instead of duplicating
4. **Direction 2 — read**: billable days tagged `[Client]` read over the period (one event day = 1 day, half-days via `0.5` in the title), counted per client with the list of dates
5. **Confirmed day rate**: proposed from history (`list_client_invoices` for that client, `list_products` "day"-type items), source shown, **then confirmed by the user** — never assumed
6. **End-of-month invoice**: `create_client_invoice` as a **DRAFT** (days × rate, VAT from the catalog or the invoicing settings — never guessed) → the user reviews and sends from Qonto

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**Two writes, two locks**: calendar events exist only after a recap confirmed in the conversation; the Qonto invoice exists only as a **draft**, after the day rate and lines are confirmed. The skill moves no money and sends nothing: paying happens in the Qonto app (SCA), sending the invoice happens after review. **That's the security model, not a limitation.**

## 🧪 Holds up on messy data

- No Calendar MCP? → the schedule ships as a markdown table, direction 2 says it's unavailable — no pretending
- Short history? → yearly cadences flagged as unreliable, monthly ones still detected; everything estimated is labeled 🟡
- Tagged client not found in Qonto? → the skill asks, offers `create_client` with confirmed details, creates nothing on its own
- No past invoice and no catalog day rate? → the skill asks for the rate outright instead of defaulting
- Re-run after edits? → events carrying the skill's marker are updated in place, never duplicated
- Empty account, zero invoices → direction 1 says what it found (nothing), direction 2 still works from the calendar

## 📆 What lands in the calendar (direction 1)

| Event type | Qonto source | Example title (invented) | Reminder |
|---|---|---|---|
| Supplier invoice to pay | `list_supplier_invoices` (due_date) | `💸 Nimbus supplier — €890` | D-3 |
| Client invoice to collect | `list_client_invoices` (unpaid) | `💰 Invoice INV-2026-042 due — €4,800` | D-3 |
| Monthly recurrence | 24–36 months of history | `💸 Rent — €1,200` | D-3 |
| Quarterly / yearly recurrence | 24–36 months of history | `💸 Yearly insurance — €640 (estimated)` | D-3 |
| Detected tax direct debit | History (direct debits) | `💸 VAT debit — ~€2,100 (estimated)` | D-3 |

*All amounts above are invented examples. Recurrence-based amounts are labeled "estimated" in the event.*

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: schedule, pre-write recap, day counts, invoice summary | **Always** — the baseline |
| **Google Calendar** | Dated events, amount in the title, D-3 reminder, anti-duplicate marker | When the Calendar MCP is present **and** the recap confirmed |
| **Qonto invoice** | `create_client_invoice` **draft**, visible in the Invoicing section | Direction 2, after rate & lines confirmed |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem (money lives in deadlines) → direction 1: the recap, then the calendar filling up → the `[Client]` convention and the confirmed day rate → **the split-screen moment: 12 tagged days on one side, a draft invoice appearing in Qonto on the other** → wrap-up. It runs live on a real production account (all figures shown in the docs are invented examples).

## 💡 Roadmap ideas

- Live reconciliation: mark events ✅ once the matching payment clears in the account
- A dedicated "Money" calendar, separate from the personal one
- Full estimated tax schedule pushed as events — cross-skill with `qonto-tax-pilot` (it computes, this skill schedules)
- Quote-before-invoice for newly tagged clients (`create_quote` exists in the MCP)
- A "your money week" recap event every Monday morning

## 🛡 Guardrails

- **No calendar event without a confirmed recap** in the current conversation; idempotent re-runs (marked events updated, no duplicates)
- **The day rate is never guessed**: deduced from history, then explicitly confirmed — every time
- Invoices created via MCP are **real** → always DRAFT, review before sending; rehearsals use a fictional client + draft + `delete_client_invoice`
- Estimated amounts (recurrences) always labeled as estimates — never presented as booked
- The skill moves no money: paying stays in the Qonto app (SCA), sending an invoice stays an explicit decision
- Masked IBANs (last 4 digits) · pagination ≤ 50 everywhere

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
