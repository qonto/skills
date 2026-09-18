---
name: qonto-fraud-sentinel
description: Morning bodyguard for Qonto accounts. Screens the latest transactions against a numbered baseline built from 3–6 months of history and flags what's unusual — never-seen beneficiary, amount 3×+ the counterparty's average, duplicate direct debit, odd hour or channel, bursts of small card debits (stolen-card testing pattern), first SEPA direct debit from a new creditor. Every alert shows the transaction, why it's unusual (with numbers), and the recommended action; a card lock (change_card_status) is proposed — never executed automatically. Use for "run my morning check", "anything unusual on my account?", "un truc bizarre sur mon compte ?", "did I get charged twice?", "is this €249 debit normal?", "watch my account".
permissions:
  mcp:
    qonto: [change_card_status, get_organization, list_cards, list_cash_flow_categories, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto Fraud Sentinel

The account's bodyguard. Thirty seconds every morning (or on demand): the latest transactions screened against a numbered baseline. Read-heavy, one safe write: `change_card_status` locks a card **only** when a card is implicated and the user explicitly confirms in the conversation.

**Editorial rule above everything: a signal is NOT a fraud.** The skill says "unusual — verify", never "fraud detected". A legitimate new supplier is, by definition, "never seen": false positives are expected, explained, and dismissible in one message.

## Prerequisites
1. `get_organization` first → accounts, balances, country (`list_transactions` requires `bank_account_id`/`iban`). `list_cards` → card inventory (id, last 4 digits, holder, status) to attribute card alerts.
2. **Country-agnostic by design**: the six signals are behavioral and SEPA-universal — they work identically on every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT). Only wording adapts.
3. **Baseline needs 3–6 months of history.** Under 3 months, announce **cautious mode** plainly: thinner baselines, more false positives, every alert phrased more tentatively. Never fake confidence.

## Workflow

### 1. Build the baseline (3–6 months)
`list_transactions` per account, paginate `per_page: "50"`. For each **normalized counterparty** (uppercase, strip reference numbers/dates from labels): occurrence count, mean and max amount, cadence, first/last seen, typical `operation_type` and hours. Per category/side: typical debit size and daily rhythm. For card transactions, reason on **`emitted_at`**, not `settled_at` (1–2 day settlement lag would corrupt timing and duplicate detection). If the user has marked **trusted counterparties** earlier in the conversation or project, load that list.

### 2. Scan the window
Default: transactions since the last scan, or the last 48–72 h on a first run. The user can widen it ("this week", "since the 1st"). Outgoing transactions only, `status: completed` + `pending`.

### 3. Screen against six signals
1. **Never-seen beneficiary** — first outgoing occurrence of a counterparty absent from the baseline.
2. **Unusual amount** — ≥ 3× that counterparty's average; for a new counterparty, ≥ 3× the category's typical debit.
3. **Duplicate debit** — same counterparty, same amount (±1 %), 1–5 days apart (`emitted_at` for cards).
4. **Unusual hour / channel** — card payment at an hour never seen for that counterparty, or an `operation_type` never used with it (e.g. a transfer where only direct debits existed).
5. **Card-testing burst** — ≥ 3 small debits (bottom decile of the account's card amounts, or < €10) within minutes to a few hours, especially on new counterparties: classic stolen-card testing pattern.
6. **First SEPA direct debit from a new creditor** — `direct_debit` operation from a creditor absent from the baseline (a new mandate just got used).

Trusted counterparties skip signals 1 and 6 but stay screened for amounts and duplicates.

### 4. Report — output formats
**Always** reply in the conversation with a markdown table: transaction (date · counterparty · amount · account/card, IBAN and PAN masked to last 4) · signal · **the numbered baseline** ("first time in 6 months", "€612 vs €148 average over 14 debits = ×4.1") · recommended action · severity 🔴 check now / 🟠 check today / 🟡 FYI. If nothing triggers: say "nothing unusual" with the scan window and baseline depth — a clean report is the product, not an excuse to invent findings. End with: "reply *trust <counterparty>* to stop the never-seen alerts for it" — record those in the conversation/project. **When the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code), also offer a compact HTML morning report; otherwise the table is the deliverable.

### 5. Act — card lock, only with explicit consent
Recommended actions scale with severity: verify with the counterparty → dispute/oppose via the Qonto app → **lock the card**. If (and only if) a card is implicated and the user **explicitly confirms in the current conversation**, call `change_card_status` to lock it — present it beforehand as a proposal, afterwards as "card locked, you can unlock it anytime". **Unlocking, definitive opposition, SEPA mandate revocation and card replacement stay in the Qonto app** — say so. Never lock automatically, never present a failed call as done.

### 6. Optional daily digest (multi-MCP)
If a **Gmail MCP** is detected, offer to draft a daily digest email of the morning scan. If absent, say the core works in pure Qonto and continue — never block on an optional enrichment.

## Guardrails
- **Never say "fraud"** — say "unusual", "worth verifying". A first payment to a new supplier is normal life, not an incident.
- NEVER `change_card_status` without explicit confirmation in the current conversation; never on a hunch; never present it as executed if the call failed or is pending.
- Under 3 months of history: cautious mode announced, alerts phrased tentatively. Empty scan window → say so, don't invent.
- Mask IBANs and card numbers (last 4 digits). Paginate everything (`per_page` ≤ 50). Card timing on `emitted_at`.
- In rehearsals, prefer locking a virtual/dormant card and unlock it immediately in the app.

*See also: `qonto-supplier-detective` — historical supplier invoices and money recovery. Sentinel is its daily, security-focused sibling: real-time watch, not archaeology.*
