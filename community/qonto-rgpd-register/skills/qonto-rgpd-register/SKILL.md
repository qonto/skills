---
name: qonto-rgpd-register
description: GDPR Article 30 register drafted from a Qonto account's spending. Detects the SaaS tools that process personal data (CRM, email marketing, analytics, AI, cloud, payroll, support) in the debits, classifies them by processing activity (purpose, typical data categories, EU / non-EU vendor location) and generates a draft record of processing activities in the CNIL card format — one card per activity, processor list, and flags (non-EU transfer → SCCs to verify, DPA to locate or sign, tool gone from the debits for 6 months → retire it?). Use for "génère mon registre RGPD", "quels outils traitent des données personnelles ?", "draft my Article 30 register", "which of my tools send data outside the EU?", "do I have DPAs to sign?".
permissions:
  mcp:
    qonto: [get_organization, list_cash_flow_categories, list_memberships, list_supplier_invoices, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto RGPD Register

Your bank account knows your data processors better than you do. Read-only, zero write: the skill detects, classifies and drafts; a human validates. Every output carries the same disclaimer — **draft register, not legal advice, to be validated by a DPO or lawyer**.

## Prerequisites
1. `get_organization` first → legal name, legal form, address, country. That block becomes the mandatory Article 30 header (data controller identity), and `list_transactions` requires `bank_account_id`/`iban` anyway.
2. **Pan-European by design**: all Qonto countries are in the EU, so GDPR applies everywhere. In France the register follows the **CNIL card model**; elsewhere the structure is identical and references switch to the local supervisory authority (BfDI/LfDI, AEPD, Garante, DSB, AP, APD/GBA, CNPD).
3. Vendor knowledge = Claude's general knowledge (headquarters, processor role, typical data categories). A SaaS is recognized from its **first occurrence** — no frequency threshold — and every classification is tagged "to validate".
4. Empty or thin history → the skill says what it could not detect and still delivers the register skeleton with the controller block filled.

## Workflow

### 1. Identify the controller
`get_organization`: legal name, legal form, address, country → the register header. State the Article 30(5) nuance honestly: the under-250-employee exemption is narrower than people think — **non-occasional processing** (payroll, CRM, prospecting) already requires the register, so in practice almost every company needs one.

### 2. Scan the spending (12–24 months)
`list_transactions` per account (`side: debit`), paginate `per_page: "50"` in 3-month windows; complement with `list_supplier_invoices` (cleaner vendor names than card labels). **Normalize counterparty spellings and merge** — the same vendor shows up as `GOOGLE *WORKSPACE`, `GOOGLE IRELAND LTD`, `Google Cloud EMEA`: one vendor. Track each vendor's **last-seen date** (use `emitted_at` for card payments — `settled_at` lags 1–2 days) for the freshness flag.

### 3. Classify each vendor — general knowledge, tagged "to validate"
For each recognized SaaS: does it process personal data on the company's behalf? Categories kept: **CRM · email marketing · analytics · AI · cloud/hosting · payroll & HR · customer support · e-commerce & payments**. Non-processors (bank fees, travel, hardware, meals…) are discarded but listed in an "out of scope" appendix so nothing silently disappears. For each keeper: typical purpose, typical data categories, data subjects, vendor HQ, typical hosting region (EU / non-EU / EU-region available as an option). Some roles are genuinely ambiguous (payment providers often act as independent controllers) — say so instead of deciding. Unknown vendor → "unidentified — check the invoice", never a guess presented as fact.

### 4. Build the register cards (one per processing activity)
Group by **purpose, not by vendor**: prospect & customer management, marketing communication, audience measurement, customer support, HR & payroll, accounting & invoicing, IT & hosting. `list_memberships`: several active members → suggest the **HR block** (payroll, expense management, staff accounts) even if no payroll tool shows in the debits yet. Each card, CNIL format: purpose · legal basis (placeholder — the company chooses) · data categories · data subjects · recipients · processors with location · retention (placeholder — the company decides) · non-EU transfers + mechanism to verify · security measures (placeholder).

### 5. Raise the flags
- 🔴 **Non-EU vendor or hosting** → transfer mechanism to verify: adequacy decision, standard contractual clauses (SCCs), the vendor's DPA annexes.
- 🟠 **DPA to locate or sign** — most SaaS publish one; the to-do lists where to look, vendor by vendor.
- 🟡 **Gone from the debits ≥ 6 months** → still in use? Candidate to retire from the register — and to close the account (data deletion request to the vendor).
- 🟡 **Reseller masking the real vendor** (marketplaces, app stores, payment facilitators) → ask the user which product sits behind the charge; never guess.
Cross-reference: same raw material as `qonto-subscription-audit` — that skill reads **cost**, this one reads **legal obligation**.

### 6. Deliver — output formats
**Always** reply in the conversation with markdown:
1. **Summary table** — vendor · category · purpose · EU/non-EU · flags, one line per detected processor.
2. **One register card per processing activity** (Article 30 fields, "to validate" tags visible).
3. **Prioritized to-do** — DPAs first, non-EU transfers second, retirements third.

**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): a print-ready **HTML register document** (controller header, cards, processor annex, to-do) the user can hand to their accountant, DPO or a supervisory authority on request. If the host cannot render files, say nothing about it: the markdown is the deliverable. Every output ends with the disclaimer: **draft register, not legal advice — validate with a DPO or lawyer**.

## Guardrails
- **Never a definitive legal qualification** (processor vs controller vs joint controllership, legal basis, retention) — every card is marked "to validate", placeholders stay visibly placeholders.
- Never invent vendor facts: unknown HQ or hosting → stated as unknown, with "check the invoice / the vendor's DPA page" as the next step.
- A register draft ≠ GDPR compliance: it is one required document, not the whole program. Recommend DPO/legal validation in every report.
- Read-only by design — zero write tool, nothing on the account changes. Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50). All examples in the documentation are invented.
