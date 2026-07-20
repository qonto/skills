---
name: qonto-einvoice-ready
description: French e-invoicing readiness audit for Qonto accounts. From 2026-09-01 every French VAT-registered company must be able to RECEIVE electronic invoices (issuing becomes mandatory 2026-09-01 for large companies and mid-caps, 2027-09-01 for SMEs). The skill scores the account's readiness — client records complete for Factur-X (SIREN/SIRET, intra-EU VAT number, structured address), quality of issued invoices, the timeline that applies to the company, e-reporting exposure (foreign/B2C flows) — then fixes incomplete client records live: SIREN recovered from the public French company registry API (no key), previewed line by line, written with update_client only after explicit confirmation. Use for "suis-je prêt pour la facturation électronique ?", "am I ready for the September 2026 e-invoicing mandate?", "complète mes fiches clients (SIREN, TVA)", "audit my client file for Factur-X", "quel calendrier s'applique à mon entreprise ?".
---

# Qonto E-invoice Ready

The e-invoicing readiness audit. France's e-invoicing reform hits **everyone on 2026-09-01** (receiving); most companies will discover their client file can't feed a valid Factur-X. This skill measures the gap, then closes it — one confirmed field at a time. Read-heavy, one safe write: `update_client` never touches money, only client records.

## Prerequisites
1. `get_organization` **always first** → country, legal name, accounts (`list_transactions` requires `bank_account_id`/`iban`).
2. **Country-aware**: the reform is **French**. If the organization's country is not FR, say so plainly and degrade to a generic client-file completeness audit (identifiers, VAT numbers, structured addresses are good hygiene everywhere) — never apply French deadlines abroad.
3. Optional enrichment: the **public French company registry API** — `https://recherche-entreprises.api.gouv.fr/search?q=<name>` (data.gouv, no key, no auth). If unreachable, the audit still runs; only the live fix degrades (announce it, continue).

## Workflow

### 1. Situate the company
`get_organization` → country, legal identity. Determine the **applicable timeline**: look the company up in the public registry (field `categorie_entreprise`: GE / ETI / PME) or **ask** the user for their size if the lookup is ambiguous — never guess. Output: "receiving mandatory in N weeks (2026-09-01); issuing mandatory for you on <2026-09-01 | 2027-09-01>."

### 2. Audit the client file
`list_clients` (paginate, `per_page` ≤ 50), `get_client` for detail. For each **B2B client** (type company), check the three identifiers a valid Factur-X / UBL / CII invoice needs on the buyer side:
- **SIREN/SIRET** (tax identification number) — also the key to the central e-invoicing directory
- **Intra-EU VAT number**
- **Structured address** (street, zip, city, country — one blob in a single field doesn't count)

Individuals (B2C) are flagged separately: out of e-invoicing scope, **in e-reporting scope**. Score each record 0–3, list gaps record by record.

### 3. Grade issued invoices
`list_client_invoices` over the last 12 months (paginate ≤ 50): what share is attached to a complete client record — i.e. would pass as Factur-X today? Note invoices pointing at incomplete records (they are the operational risk: rejected at the platform, unpaid). Check `vat_payment_condition` where present (`on_receipts` = cash-basis VAT — relevant context for e-reporting of payment data). Numbering: flag obvious gaps soberly, no accusations.

### 4. Map e-reporting exposure
Cross two sources: client records (non-FR addresses, individuals) and money flows (`list_transactions` per account, `per_page` ≤ 50, income side) for foreign counterparties or card-collection patterns suggesting B2C. Output: "X% of your income falls outside French B2B e-invoicing but **inside e-reporting** — transaction data will have to be transmitted on the same calendar as your issuing obligation."

### 5. Fix live — with confirmation, never in bulk
For each incomplete B2B client:
1. Query `recherche-entreprises.api.gouv.fr/search?q=<client name>` (add zip/city to the query when the record has them).
2. **Single confident match** → propose it. **Several plausible matches (homonyms) → always ask**, showing name, city, SIREN of each candidate. **No match** → say so, ask for the SIREN or skip.
3. Derive the intra-EU VAT number from the SIREN (FR + 2-digit key + SIREN) and **mark it as derived — to be confirmed by the client**.
4. Show ONE preview table: client · field · current → proposed · source (registry / derived / user).
5. Only after **explicit confirmation in the current conversation**: `update_client`, field by field. Report each success/failure honestly. **NEVER silently mass-update; never present a write as done if the tool call failed.**

### 6. Score and plan
Readiness score, transparent formula, **before/after** the fixes:
- **60%** — client-file completeness (average 0–3 score across B2B clients)
- **25%** — invoice quality (share of last-12-months invoices on complete records)
- **15%** — timeline known (company size identified) + e-reporting exposure mapped

Then the action plan: countdown to 2026-09-01, what the skill fixed, what remains **on the user's side** — above all the **choice of an accredited platform (PDP), which belongs to the user** (the skill lists criteria, never picks). Cross-reference: `qonto-vat-return` (the VAT data this reform will feed), `qonto-meeting-invoice` (creating clean invoices from day one).

## Embedded reform reference (as of July 2026 — verify for later changes)
| Date | Obligation | Who |
|---|---|---|
| **2026-09-01** | **Receive** electronic invoices | **All French VAT-registered companies** |
| 2026-09-01 | Issue electronic invoices | Large companies & mid-caps (ETI) |
| 2027-09-01 | Issue electronic invoices | SMEs & micro-enterprises |
| Same as issuing | E-reporting (B2C + cross-border transaction data) | All, per their issuing date |

- **Formats**: Factur-X (PDF/A-3 + embedded CII XML), UBL 2.1, CII — all built on the EN 16931 semantic core; buyer identification (SIREN/SIRET) is mandatory in each.
- **Exchange model**: invoices flow through **accredited platforms (PDP)**; a central public directory maps SIREN/SIRET to platforms. Companies must be reachable through a PDP by 2026-09-01.
- **Invoice mentions** already required since the 2022 decree: client's SIREN, delivery address when it differs, nature of the operation (goods / services / mixed), "VAT on debits" option when applicable.

## Guardrails
- **This is an audit, not legal or tax advice** — say it; recommend confirming edge cases with the company's accountant.
- The **PDP choice belongs to the user**: present criteria, never decide, never register anywhere.
- Registry homonyms → confirmation, always. Derived VAT numbers labeled as derived.
- `update_client` only after an explicit per-batch confirmation with the full preview shown; field by field; failures reported.
- All examples in reports are invented and say so; mask sensitive data; paginate everything (`per_page` ≤ 50).
- Empty account, no clients, no invoices, non-FR country, registry down → the skill says what it can and cannot do, and never invents data or deadlines.
