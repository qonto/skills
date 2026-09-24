---
name: qonto-supplier-detective
description: Forensic audit of supplier invoices and payments on a Qonto account. Sweeps every supplier invoice and every debit to find money leaking out — duplicate invoices, invoices paid twice, invoice-vs-payment amount gaps, and the highest-value security signal, a known supplier whose payment IBAN suddenly changed (the number-one supplier wire-fraud pattern). 100% read-only; every finding ships with the exact references needed to claim the money back. Use for "lance l'audit fournisseurs", "did I pay anything twice?", "find duplicate supplier invoices", "est-ce qu'un fournisseur a changé d'IBAN ?", "how much can I recover from my supplier payments?".
permissions:
  mcp:
    qonto: [change_supplier_invoice_status, get_organization, get_supplier_invoice, list_supplier_invoices, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto Supplier Detective

The detective touches nothing — it hands you the case file. A read-only forensic sweep of supplier invoices and debits: duplicates, double payments, amount gaps, and IBAN changes on known suppliers — every finding evidence-backed and ranked by recoverable amount.

## Prerequisites
1. `get_organization` → accounts, `bank_account_id`/IBAN (required by `list_transactions`), country, currency. Nothing hardcoded: the skill adapts to whatever organization it finds.
2. **Country-agnostic**: the detectors compare the account's own data with itself — no national rules involved. They work on any Qonto country (FR, DE, ES, IT, AT, NL, BE, PT).
3. **Graceful degradation**: no supplier invoices imported → transaction-only pass (duplicate debits, IBAN watch on transfers), stated plainly. Empty account → say what can't be checked; never invent findings.

## Workflow

### 1. Full sweep + normalization
- `list_supplier_invoices`, paginate `per_page: "50"` until exhausted (1,000+ invoices is normal — summarize progress every ~300 instead of dumping raw data). Status filters aren't exposed on this MCP: filter client-side on `status`.
- `list_transactions` per account, debits, 12–24 months in 3-month windows, `per_page: "50"`. Match card payments by `emitted_at`, not `settled_at` (1–2 day drift).
- **Normalize supplier names** (bank labels are messy): uppercase, strip SEPA/transfer prefixes and payment references, drop legal suffixes (SARL, SAS, SASU, SA, EURL, GmbH, S.L., Srl…), collapse whitespace — so "OVH SAS", "OVH.COM" and "VIR SEPA OVH" merge. Keep raw labels for display. Normalize invoice numbers too (strip spaces, dashes, leading zeros).
- **Identify credit notes and incoming refunds up front** — they are exculpatory evidence for the detectors, not anomalies.

### 2. D1 — Duplicate invoices
- Native signal first: invoices flagged `has_duplicates` → pull each twin via `get_supplier_invoice`.
- Own pass: same normalized supplier + same `total_amount` within 45 days, or same normalized `invoice_number` on the same supplier.
- ⚠️ **The false-positive trap: subscriptions.** Same supplier + same amount every month is a recurring plan, not a duplicate. Check the cadence first — 3+ hits at ~30/90-day intervals → recurring, excluded. True duplicates sit off-cycle: the same amount twice within days.
- Classify: benign duplicate (same invoice imported twice, one payment — housekeeping, no money lost) vs **both paid** → escalate to D2.

### 3. D2 — Paid twice (the money finder)
- One invoice matched to **2+ debits** of ≈ the invoice amount; or two D1 twins each matched to a different debit; or same supplier + same amount, two debits < 7 days apart, one invoice on file.
- **Clear the legitimate multi-debit cases first**: partial/instalment payments (the debits **sum to** the invoice total) and deposit + balance. A true double payment totals ≈ 2× the invoiced amount.
- If a matching refund arrived later → the case is closed; report it as recovered, not recoverable.
- Every finding carries the **evidence triplet**: invoice reference(s) + both transaction references with dates + the recoverable amount.

### 4. D3 — Invoice ↔ payment gaps
- Invoice total/payable amount vs matched debit(s): paid **more** than invoiced beyond rounding (> €0.05) → presumed overpayment, with both references.
- Before flagging: look for a credit note or refund explaining the gap; foreign-currency invoices → "to verify (FX)", not an anomaly.
- Underpayments are mentioned (supplier-chase risk) but never counted in the recoverable total.

### 5. D4 — IBAN change on a known supplier (security-grade)
- Wherever a beneficiary IBAN is exposed (supplier invoice payment details via `get_supplier_invoice`, transfer transactions), track it per normalized supplier over time.
- A supplier paid on IBAN A for months, then an invoice or payment carrying IBAN B → **treat as a security alert, pinned on top of the report regardless of amount**: this is the number-one supplier wire-fraud pattern (fake "our bank details changed" emails).
- The recommendation, verbatim: **verify by phone with the supplier at the number you already know — never the number or reply-to in the message that announced the change.**
- Say it may be legitimate (companies do switch banks); the point is verification **before the next payment**. If no IBAN is exposed for a supplier, disclose the coverage gap instead of implying the check was done.

### 6. Report — output formats
**Always** reply in the conversation with markdown:
1. Header: N invoices + M debits scanned, period covered.
2. 🚨 **IBAN alerts** first (if any), with the phone-verification instruction.
3. **Findings table** sorted by recoverable € (detector · supplier · amount · evidence refs · confidence 🟢 strong / 🟡 presumption to verify · suggested action).
4. **Total to claim (estimated)** + the cleared cases (subscriptions excluded, instalments recognized, refunds already received) — show what was checked, not just what was found.

On request, per finding: a **ready-to-send claim email** (dates, amounts, invoice number, both transfer references — IBANs masked).
**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): an **HTML case file** — findings board, evidence cards, recoverable total, IBAN alert banner. If the host cannot render files, say nothing about it: the markdown report is the deliverable.

## Guardrails
- **100 % read-only** — no Qonto write tool is ever called. The detective hands over the case file; the user makes the calls.
- Wording discipline: "presumed duplicate", "to verify" — never assert fraud or error as fact. Every finding shows its evidence; anything unverifiable is labeled as such.
- The IBAN alert always carries the verify-by-phone-at-the-known-number instruction; never suggest replying to the message that announced the change.
- Subscriptions, instalments, deposits, credit notes and refunds are cleared **before** anything is flagged — a false accusation costs more trust than a duplicate costs money.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50); summarize progress on large sweeps.
