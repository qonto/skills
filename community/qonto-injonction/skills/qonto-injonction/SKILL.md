---
name: qonto-injonction
description: "Court-ready payment-order file builder for Qonto accounts (France). When reminders have failed, turns an unpaid client invoice into a ready-to-file \"injonction de payer\" dossier — CERFA 12946 form pre-filled field by field for the commercial court, late-payment interest computed (ECB refi + 10 pts, floor 3× the French legal rate, art. L441-10) plus the €40 recovery indemnity, a numbered exhibit list built from Qonto receipts, the competent court identified from the debtor's registered office (public company-registry API, no key), and a prior BODACC check: debtor in collective proceedings → NO injunction, the skill reorients to a proof of claim (2-month deadline). Use for \"prépare une injonction de payer\", \"ce client ne paiera jamais, on fait quoi ?\", \"take this invoice to court\", \"calcule les intérêts de retard sur cette facture\", \"mon débiteur est-il en liquidation ?\", \"prepare the court file for invoice X\"."
permissions:
  mcp:
    qonto: [get_attachment, get_client, get_client_invoice, get_organization, list_client_invoices, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto Injonction

The judicial step after friendly reminders failed. Read-only by design: the skill assembles a complete, signable court dossier — **zero write tools, no legal act is ever executed by the skill**. The user signs and files. That's a feature, not a gap.

## Prerequisites
1. `get_organization` FIRST → creditor identity (legal name, legal form, registration/SIREN, registered office, country) and `bank_account_id`s / IBANs (`list_transactions` requires them).
2. **Country-aware**: the CERFA 12946 payment-order procedure exists in **France** only. Other Qonto countries (DE, ES, IT, AT, NL, BE, PT…): the skill still builds the factual dossier — proven non-payment, interest per the EU Late Payment Directive (2011/7/EU) generically, numbered exhibits — but produces **no form** and says which local procedure to ask a professional about. Never invent foreign forms or rates.
3. **Public French APIs, optional but keyless**: `recherche-entreprises.api.gouv.fr` (company registry) and the BODACC open-data API (collective proceedings). If the host cannot reach the web, the skill says so and asks the user for the two facts it needs (debtor's registered office; any known insolvency) instead of guessing.
4. The claim should be **certain, liquid and due** (art. 1405 CPC) and past the amicable stage — ideally a formal notice already sent (see `qonto-invoice-chaser` for the reminder ladder, `qonto-prescription-guard` for the limitation clock: 5 years, art. L110-4 C. com.).

## Workflow

### 1. Target the invoice and the parties
`list_client_invoices` (unpaid statuses, `per_page: "50"`) → pick the invoice(s) with the user. `get_client_invoice` → amounts, issue date, `due_date`, days overdue, attachment id. `get_client` → debtor identity: legal name, SIREN/VAT number, billing address, email. Missing SIREN → look it up by name + city on the registry API and **have the user confirm the match** (homonyms are common); never assume.

### 2. Prove non-payment — the dossier's spine
Scan `list_transactions` (credit side, per account, since the invoice's issue date, paginated ≤ 50): no incoming transaction may match the invoice (amount ±0.01, normalized counterparty ≈ client name, or reference contains the invoice number).
- Full match found → **stop**: the invoice looks paid; propose reconciliation instead (see `qonto-invoice-chaser`).
- Partial payment(s) → deduct from the principal, list them as exhibits (payments on account), claim only the balance.
- Disputed invoice (credit notes, written contestation mentioned by the user) → warn: an injunction against a **contested** claim will likely meet opposition; suggest professional advice first.

### 3. BODACC check — before anything else is drafted
Query the BODACC open-data API (no key) for the debtor's SIREN in the **collective-proceedings** announcements (sauvegarde, redressement, liquidation).
- **Proceeding found → NO injunction.** Individual lawsuits are frozen. The skill reorients: file a **proof of claim (déclaration de créance)** with the court-appointed receiver within **2 months** of the BODACC publication (art. L622-24 C. com.) — and drafts that statement instead: principal, interest stopped at the judgment date, exhibits, receiver's address when published.
- Nothing found → say so explicitly (with the check date) and proceed.

### 4. Identify the competent court
`recherche-entreprises.api.gouv.fr` (no key) on the debtor's SIREN → registered office address, administrative status (active/closed). The competent court is the **commercial court (tribunal de commerce) of the debtor's registered office** (art. 1406 CPC). Name it precisely (e.g. the greffe covering that city) and flag if the company is administratively closed — a different problem than non-payment.

### 5. Compute the claim — every euro justified
| Item | Rule |
|---|---|
| Principal | Invoice total incl. VAT − payments on account (proven in step 2) |
| Late-payment interest | Contract rate if stated on the invoice/terms; else **ECB refinancing rate + 10 points** (art. L441-10 C. com.), **floor: 3× the French legal interest rate**. Semester-based rate (rate in force on Jan 1 / Jul 1), computed from the day after `due_date` to the filing date, day count /365. Show the formula, the rate used and its semester |
| Recovery indemnity | **€40 per unpaid invoice** (art. D441-5 C. com.), no proof needed |
| Total claimed | Principal + interest + indemnity, each line separate on the form |

All amounts are **indicative computations to be validated** — state it, and show the day-by-day basis so a lawyer can check in seconds.

### 6. Assemble the dossier — ready to sign
1. **CERFA 12946 pre-fill**: a field-by-field table (court · creditor identity · debtor identity · origin of the claim with invoice number and dates · principal · interest with rate and start date · €40 indemnity · total · exhibit list · date/place) with the exact value to copy into each box. The skill never files anything.
2. **Numbered exhibit list (bordereau de pièces)**: P1 invoice (retrieved via `get_attachment` when stored in Qonto), P2–P3 reminders, P4 formal notice + proof of registered mail, P5 statement of account (the step-2 transaction scan, as evidence of non-payment), P6 debtor's registry extract. Missing pieces are listed as **to provide**, never invented.
3. **Infogreffe filing guide**: online filing on infogreffe.fr, court fee **~€35** (checked at filing time), each exhibit as **PDF < 2 MB**, then: judge's order → service by a court bailiff (commissaire de justice) within 6 months → debtor has 1 month to oppose → enforceable title.

### 7. Report — output formats
**Always** reply in the conversation with markdown:
1. **Claim table** (principal · interest with formula · indemnity · total).
2. **CERFA pre-fill table** (form field → value to copy).
3. **Exhibit list** with status (✅ retrieved from Qonto / 📋 to provide).
4. **Route banner**: injunction OK (BODACC clean, checked on DATE) or reorientation to proof of claim with its 2-month deadline.

**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): generate the dossier as a printable **HTML document** (cover sheet, claim computation, CERFA pre-fill, bordereau) the user can save as PDF. If the host cannot render files, say nothing about it: the markdown tables are the deliverable.

## Guardrails
- **This is not legal advice** — say it once per dossier. Interest amounts are indicative computations to be validated (lawyer, court bailiff, or the greffe).
- **Zero writes, ever**: the skill stops at a ready-to-sign dossier. Never present the injunction as filed, served, or granted; only the user signs and files.
- France-only for the form; other countries get the factual dossier, never a foreign form or rate invented.
- Debtor in collective proceedings → never suggest the injunction; reorient to the proof of claim and its 2-month clock.
- Contested claims and prescription risks (> 5 years, art. L110-4) are flagged, not silenced — see `qonto-prescription-guard`.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50). Examples in docs are invented (INV-YYYY-NNN).
