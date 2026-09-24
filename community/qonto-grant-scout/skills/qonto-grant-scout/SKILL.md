---
name: qonto-grant-scout
description: Public-funding scout for Qonto accounts. Builds the company's real profile from the account — sector, location, size, actual spending structure (training, equipment, digital, hiring, export, energy) — then cross-references it with French public aid referentials on data.gouv.fr (via the Datagouv MCP when present) to shortlist plausible grants and subsidies. Every lead carries eligibility criteria to confirm, a dated source, and a concrete next step; the skill never claims eligibility. Use for "quelles aides publiques pour ma boîte ?", "je dépense beaucoup en formation, il existe des aides ?", "what grants could my company target?", "am I leaving public money on the table?".
permissions:
  mcp:
    datagouv: [get_dataset_info, query_resource_data, search_datasets]
    qonto: [get_organization, list_labels, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto Grant Scout

Your bank account knows what you invest in; public databases know who gets helped for it. This skill introduces them. **Read-only, zero writes**: it profiles, searches, and shortlists — it never claims eligibility and never fills an application.

## Prerequisites
1. `get_organization` FIRST → legal form, sector (NAF code when present), address/region, creation date, accounts (`list_transactions` requires `bank_account_id`/`iban`). If the sector field is absent, infer it from counterparties and flow patterns — and say so, with lower confidence.
2. **Country-aware**: aid schemes are national/regional → **cross-referencing is France only**. For other Qonto countries (DE, ES, IT, AT, NL, BE, PT…), say so plainly and degrade to what stays valid everywhere: the spending profile and the generic aid families that exist across the EU — never cite a specific foreign scheme.
3. **Datagouv MCP: optional, detected dynamically.** Present → dataset search (`search_datasets`, `get_dataset_info`, `query_resource_data`). Absent → announce it and still deliver the spending profile + generic aid families with the official portals to explore (aides-entreprises.fr, bpifrance.fr, the region's economic-development site, France Num).

## Workflow

### 1. Profile the company
From `get_organization`: legal form, sector/NAF, region (from address), company age, size proxy (incoming volume over the last 12 months). Build a one-paragraph profile the user can correct before anything else happens. Every later search inherits this profile.

### 2. Read the flows (12–24 months)
`list_transactions` per account, paginate `per_page: "50"`. Classify **debits** into aid-relevant spending categories: training (training bodies, e-learning, certifications) · equipment/CAPEX · digital (software, SaaS, web) · R&D-like (prototyping, technical subcontracting, specialized tooling) · hiring/payroll trend · international (foreign counterparties, FX) · energy/vehicles/works. Use `list_labels` for the user's own categorization when available. Match card spending by `emitted_at`, not `settled_at`. Annualize each category and keep the evidence (n transactions, top counterparties, trend).

### 3. Extract "aidable" signals
A signal = category + annual amount + trend + evidence. Keep the significant ones: recurring training spend, an equipment purchase or a visible CAPEX ramp, payroll growth, export activity, energy/efficiency spending, sustained digital investment. Show the signals table before searching — this is the "your account says this about you" moment.

### 4. Search the public aid referentials (when the Datagouv MCP is present)
- `search_datasets` on aid referentials: national aid databases for companies, ADEME aids, France Num, Bpifrance, regional aid schemes (search with the region's name).
- `get_dataset_info` → **last-update date: every lead inherits it.** The referentials on data.gouv.fr are heterogeneous and sometimes stale — prefer datasets updated within ~18 months; older ones are still usable but the lead is tagged accordingly.
- `query_resource_data` to filter rows by region, sector, aid family. Some resources are not queryable (PDF, malformed CSV): fall back to the dataset's page as a link-only source, and say so.

### 5. Cross and shortlist
Match signals × schemes. Each lead carries: **what the scheme covers** · **why this account matches** (the signal, with amounts) · **eligibility criteria TO CONFIRM** (size, sector, region, dates — whatever the dataset exposes) · **source link + dataset date** · **one concrete next step** (who to contact, where to file: OPCO, ADEME portal, region's desk, Bpifrance advisor). Rank by plausibility. NEVER say "you are eligible" — always "worth checking, and here's why".

### 6. Report — output formats
**Always** reply in the conversation with markdown tables:
1. **Company profile** (as read from the account) + signals table (category · €/year · trend · evidence).
2. **Aid shortlist** (scheme · why you match · criteria to confirm · source + dataset date · next step), each line confidence-tagged: 🟢 fresh dataset + strong signal / 🟡 older dataset or inferred signal / 🔵 generic family, no dataset match.
3. Honest limits paragraph: what was searched, what wasn't found, which datasets were stale.

## Guardrails
- **Zero writes.** Only generic search keywords (sector, region, aid family) are sent to Datagouv — never amounts, transaction details, counterparty names, IBANs, or account identifiers.
- **Never claims eligibility.** Schemes open, close, and change: every lead is dated, sourced, and phrased as "to verify". Recommend confirming with the issuing body (OPCO, ADEME, region, Bpifrance) or the accountant before any application.
- Honest degradation: Datagouv MCP absent, empty account, sector undetectable, non-French company → the skill states what it can and cannot do, and never invents a scheme, an amount, or a deadline.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50).
