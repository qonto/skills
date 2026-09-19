---
name: qonto-counterparty-watch
description: "Legal-health radar for the clients and suppliers of a Qonto account. Ranks every counterparty by real exposure (unpaid client invoices, supplier commitments, recurring spend), measures actual payment delays against due dates, and — when a Datagouv MCP is available — cross-checks French public registries (SIRENE deregistrations/cessations, BODACC collective procedures: receivership, liquidation, safeguard) to raise alerts like \"client X owes you N € AND just entered receivership — chase today\". Use for \"who owes me money and are they in trouble?\", \"check my clients' legal health\", \"mon client est-il en redressement ?\", \"which supplier could fail me?\", \"rank my counterparties by risk\"."
permissions:
  mcp:
    datagouv: [query_resource_data, search_datasets]
    qonto: [get_client, get_organization, list_client_invoices, list_clients, list_supplier_invoices, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto Counterparty Watch

Know who owes you, who's slipping, and who's legally sinking — before it costs you the invoice. 100 % read-only: the skill observes and alerts; it never writes anything anywhere.

## Prerequisites
1. `get_organization` → accounts, `bank_account_id`/IBAN (required by `list_transactions`), legal country. Nothing hardcoded: the skill adapts to whatever organization it finds.
2. **Country-aware**: legal-health enrichment relies on **French** public registries (SIRENE, BODACC). For other Qonto countries (DE, ES, IT, AT, NL, BE, PT…), say so plainly and degrade to the Qonto-pure core — exposure ranking + payment-delay scoring work everywhere; never pretend to check a registry that wasn't checked.
3. **Optional enrichment — detect, don't assume**: use the declared Datagouv tools (`search_datasets`, `query_resource_data`) only when available. Do not probe MCP availability through filesystem or native tools. Present → offer legal-health checks and explain that they send SIRENs or exact legal names from Qonto to Datagouv; activate only after the user explicitly confirms. Absent or declined → announce it once ("legal-health checks unavailable, delivering Qonto-only scoring") and continue. The core must never depend on it.

## Workflow

### 1. Build the counterparty inventory
- **Clients**: `list_clients` (paginate `per_page: "50"`) → legal name, `tax_identification_number` when present. Extract the **SIREN**: a French VAT number is `FR` + 2 keys + 9-digit SIREN; keep the 9 digits. `get_client` for details on demand.
- **Suppliers**: `list_supplier_invoices` (supplier names, amounts, statuses) + `list_transactions` per account (12–24 months, 3-month windows, `per_page: "50"`) → recurring debits grouped by normalized counterparty.
- **Name normalization** (bank labels are messy): uppercase, strip SEPA/transfer prefixes and references, drop legal suffixes (SARL, SAS, SASU, SA, EURL, SCI, GmbH…), collapse whitespace. Merge Qonto client records with transaction counterparties on the normalized key; keep the raw label for display.

### 2. Compute exposure per counterparty
- **Clients**: sum of `list_client_invoices` with unpaid/overdue status — amount, count, oldest due date, ageing buckets (0–30 / 31–60 / 61–90 / 90+ days past due).
- **Suppliers**: supplier invoices still to pay + annualized recurring spend from transaction history → dependency weight (what breaks if this supplier fails).

### 3. Measure real payment behavior
Per client, across paid invoices: **observed payment date − `due_date`** (use `paid_at` when present, else the matched incoming transaction's `settled_at`). Output average delay, worst delay, and the **trend** (last 3 invoices vs the previous ones) — a client sliding from 15 to 45 days is a signal even with zero legal events.

### 4. Check legal health (only if Datagouv is available and the user confirmed)
For each counterparty with a SIREN (or an exact legal name match, stated as lower confidence):
- **SIRENE**: administrative status — active, ceased, deregistered.
- **BODACC**: collective-procedure announcements — **redressement judiciaire** (receivership), **liquidation judiciaire**, **sauvegarde** — with publication dates.
- **Honesty is a feature**: every verdict carries its evidence — "✅ verified on BODACC on DD/MM, nothing found" vs "⚠️ not verifiable (no SIREN / no match / registry unreachable)". BODACC coverage through data.gouv can be partial: say so; a clean check is "nothing found", never "guaranteed healthy".

### 5. Score each counterparty 🟢🟡🔴
Composite of **exposure × legal health × payment delay**:
- 🔴 open collective procedure or ceased/deregistered **with money at stake**; or 90+ days overdue on significant amounts
- 🟡 worsening payment trend, high exposure not legally verifiable, or a procedure found with no current exposure
- 🟢 verified healthy (or no signal) and payments on time
Every score is justified in one line — the inputs, not just the color.

### 6. Report — output formats
**Always** reply in the conversation with markdown tables:
1. **Risk table** (counterparty · exposure € · avg delay · legal health + verification date · score 🟢🟡🔴 · one-line why), sorted by risk then exposure.
2. **Priority alerts**, most urgent first — the cross-signal is the point: *"Client X owes you N € (invoice D days overdue) AND BODACC shows a receivership opened on DD/MM → declare your claim and chase today, by registered mail (créance declaration deadline: 2 months from publication)."*
3. **Coverage note**: how many counterparties verified / not verifiable / registry unavailable.

**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): an **HTML dashboard** — risk matrix (exposure vs health), ageing chart, alert cards. If the host cannot render files, say nothing about it: the markdown tables are the deliverable.

## Guardrails
- **100 % read-only** — no Qonto write tool is ever called; the skill has nothing to approve, sign, or execute.
- Never send Qonto-derived SIRENs or legal names to Datagouv without explicit user confirmation in the current conversation.
- Never state a legal status without naming the source and date; never equate "nothing found" with "healthy" when coverage is partial or the SIREN is missing.
- Legal alerts are signals, not legal advice: for an open procedure, recommend confirming on bodacc.fr and talking to a lawyer/accountant before acting.
- Degrade honestly: no Datagouv MCP → Qonto-pure scoring, announced once. Non-French counterparties → exposure + delays only.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50).
