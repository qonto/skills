---
name: qonto-crm-truth
description: CRM reality check for Qonto accounts. Reconciles CRM records (HubSpot or Airtable) with actual bank activity — flags "closed-won" deals that never generated cash, computes real revenue per client, LTV, observed average payment delay and an A/B/C payer reliability score, then, after an always-confirmed entity matching and an explicit go, writes those truths back into the CRM (HubSpot custom properties / Airtable columns). Use for "which won deals were never paid?", "quels deals gagnés n'ont jamais été encaissés ?", "score my clients by how they actually pay", "sync real revenue into my CRM", "mon top client CRM est-il vraiment mon top payeur ?".
permissions:
  mcp:
    qonto: [get_client, get_organization, list_client_invoices, list_clients, list_credit_notes, list_quotes, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto CRM Truth

In a CRM, a deal marked "won" is fiction until the money hits the account. This skill makes the CRM tell the bank's truth. Zero Qonto writes — the only writes go to the CRM, always previewed, always behind explicit confirmation, and only onto confirmed entity matches.

## Prerequisites
1. `get_organization` FIRST → accounts, balances, org country and legal identity (`list_transactions` requires `bank_account_id`/`iban`).
2. **CRM MCP (HubSpot or Airtable)** — required for the write-back. If neither is connected, say so plainly and run **degraded mode**: a "Qonto clients, scored" report delivered in the conversation (already useful on its own).
3. **Country-universal**: no local tax rule involved — works identically for all Qonto countries (FR, DE, ES, IT, AT, NL, BE, PT).
4. Client invoices in Qonto are recommended (they anchor payment delays and matching); without them, degrade to counterparty-level analysis of incoming credits and say so.

## Workflow

### 1. Bank truth first (24 months)
- `list_transactions` per account, `side: credit`, paginate `per_page: "50"` in 3-month windows, up to 24 months.
- `list_clients` (paginate ≤ 50) + `get_client` for identity fields (name, email, VAT number / tax identification number).
- `list_client_invoices` with statuses (unpaid / paid / canceled), amounts, `issue_date`, `due_date`.
- Attach every settled credit to a client: paid invoices carry the client link; otherwise match on **normalized counterparty** (case/accents folded, legal suffixes SARL/SAS/GmbH/S.L. stripped) — the same client appears under several spellings; merge them as ONE counterparty. Deduct refunds/credit notes (`list_credit_notes` when useful) from collected revenue.

### 2. Compute per-client metrics (from the bank, never from the CRM)
- **Real revenue**: cash actually collected over the period · **LTV**: all-time collected cash.
- **Observed payment delay**: settlement date − invoice `issue_date` (median and mean, "pays at day +X"); lateness = settlement date − `due_date`.
- **Last payment date** per client.
- **Payer reliability score**:

| Score | Definition |
|---|---|
| **A** | Median settlement within `due_date` + 5 days, nothing currently overdue |
| **B** | Pays reliably but late — median lateness ≤ 30 days past due |
| **C** | Median lateness > 30 days, or any invoice unpaid > 60 days past due, or a won deal never cashed |
| **—** | Fewer than 2 paid invoices → **unrated**, never a guessed score |

The formula is always disclosed with the results.

### 3. Read the CRM (detected dynamically)
- **HubSpot MCP present** → read companies/contacts and deals (stage, amount, close date) with the connector's read tools.
- **Airtable MCP present** → `search_bases` to find the CRM base, `get_table_schema` on the companies/deals tables (required before filtering single-select fields — choice IDs), then read records.
- **Neither** → degraded mode: output the scored-clients report (step 2) in the conversation and stop before matching. Never pretend a CRM was read.

### 4. Assisted entity matching — THE guardrail
- Propose CRM record ↔ Qonto client pairs on three keys: **normalized name**, **email/email domain**, **VAT number / SIREN** when present.
- Show the full mapping table with a confidence tag per pair: 🟢 exact (VAT/email match) · 🟡 likely (name match) · 🔴 ambiguous (skill ASKS, never picks).
- The user confirms or edits the mapping **before anything else happens**. Reconciliation is assisted, NEVER silent. Unconfirmed pairs are excluded from analysis and writes.

### 5. Fiction vs reality
- **Won-but-never-cashed**: deals marked closed-won ≥ 45 days ago (configurable) with no matching cash from that client covering the deal amount — listed with deal, amount, age.
- **Ranking gap**: top clients by CRM revenue vs top clients by bank-confirmed cash ("your #1 CRM account is your 7th real payer").
- **Chronic late payers** and clients gone quiet (no payment in N months despite open deals).
- Unpaid invoices discovered here can be handed to **qonto-invoice-chaser** to act on them.

### 6. Write the truth into the CRM — only with explicit consent
- Fields written (skill-dedicated, never overwriting CRM-native fields): `Real revenue (bank)`, `LTV (bank)`, `Avg payment delay (days)`, `Payer score (A/B/C)`, `Last payment date`, `Won not cashed (flag/amount)`.
- Show the exact record-by-record, field-by-field preview and get an **explicit go** in the current conversation.
- **Airtable**: `create_field` for missing columns (needs creator rights on the base), then `update_records_for_table` in batches, only on confirmed matches.
- **HubSpot**: create/update the equivalent custom properties on companies via the connector's property-write tools.
- Report what was written, where, and for how many records — and what was skipped (unmatched/unconfirmed).

### 7. Report — output formats
**Always** reply in the conversation with markdown tables: (1) scored clients (revenue, LTV, delay, score, last payment), (2) won-but-never-cashed deals, (3) the confirmed mapping table, (4) write-back summary. **When the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code), also generate an HTML one-pager: CRM ranking vs bank ranking side by side, score distribution. If it can't, say nothing — the tables are the deliverable.

## Guardrails
- **Zero Qonto writes** — read-only on the bank side. The only writes target the CRM.
- NEVER write to the CRM without (a) a confirmed matching table and (b) an explicit go on a shown preview, in the current conversation. Never present a write as done if it failed or was partial.
- Scores describe **payment behavior on this account only** — not creditworthiness; say so in reports.
- Degrade honestly: < 2 paid invoices → unrated; no invoices → counterparty-level only; no CRM → conversation report.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50). Rehearse writes on a duplicated Airtable base or test properties — CRM writes are real.
