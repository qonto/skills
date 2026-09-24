---
name: qonto-asset-registry
description: Fixed-asset register and insurance inventory built from Qonto account data. Scans 24–36 months of Qonto transactions and supplier invoices, recognizes equipment purchases (IT, furniture, machines, vehicles, tools, phones), applies the €500 pre-tax threshold (French practice, configurable), links each asset to its transaction receipt, computes indicative straight-line depreciation, and produces an insurance inventory. 100% read-only. Use only when the user asks to analyze their Qonto account for an asset register, equipment inventory, insurance inventory, or hardware valuation. Do not use for general inventory or accounting questions that do not require Qonto account analysis.
permissions:
  mcp:
    qonto: [get_attachment, get_organization, list_supplier_invoices, list_transaction_attachments, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto Asset Registry

Your account knows what you own. The register writes itself; the accountant keeps the pen. **Zero write tools** — this skill only reads, computes, and reports.

## Prerequisites
1. `get_organization` **always first** → accounts (`list_transactions` requires `bank_account_id`/`iban`), country, legal form.
2. **Country-aware**: the detection mechanics are universal. The **€500 pre-tax threshold** and the usual depreciation lives are **French practice**. For other Qonto countries (DE, ES, IT, AT, NL, BE, PT…), build the register and the insurance inventory without any local tax suggestion, and say so plainly.
3. Works on any history length; below 24 months, present the register as partial and say which period was covered.

## Workflow

### 1. Scan the purchases (24–36 months)
`list_transactions` per account, debits, `per_page: "50"`, in 3-month windows. In parallel, `list_supplier_invoices` — their descriptions and pre-tax amounts are often cleaner than transaction labels; match them to transactions by amount and date. Keep for each candidate: date (`emitted_at` for card purchases — settlement lags 1–2 days), counterparty, label, amount incl. tax, `vat_amount` when tagged (→ pre-tax amount; otherwise estimate from the total and disclose it).

### 2. Recognize equipment — general knowledge, first occurrence
Use Claude's world knowledge of vendors and invoice labels to classify purchases into **IT hardware, furniture, machines, vehicles, tools, telephony** — an equipment vendor (e.g. a computer store, an office-furniture supplier, a machinery dealer) is recognized **from its first occurrence**, no recurrence needed. Rules:
- **Generalist merchants** (large marketplaces, supermarkets…): classify the line **"to confirm"** unless the label or the attached receipt makes the nature clear. Never guess.
- **Leasing / hire-purchase**: recurring monthly payments to a financing company → flag **"financed, not capitalized here"** and exclude from the register total.
- **Installment purchases**: equal payments to the same equipment vendor over 3–12 months → merge into **one** asset at full value.
- Ignore consumables, software subscriptions, and services — this register is physical equipment.

### 3. Apply the €500 pre-tax threshold (France; configurable)
French tax tolerance: below **€500 pre-tax** → expense; at or above → **fixed asset**. The user can change the threshold ("use €800"). Each line gets a status: ✅ fixed asset · 💰 expensed (< threshold) · ❓ to confirm · 🔁 financed (leasing). Non-French organization → skip this classification, keep the raw register.

### 4. Link the receipts
For each asset's transaction: `list_transaction_attachments` → if present, `get_attachment` for the URL (probative value: file name, size). Missing → mark the line **📎 missing**. Compute a **receipt-completeness gauge** (assets with receipt / total).

### 5. Indicative depreciation
Straight-line over usual French useful lives: **IT & telephony 3 years · tools 5 · machines 5–10 · vehicles 4–5 · furniture 10**. For each asset: annual charge, estimated **net book value** today, end-of-life date. Frame it every time: these are **customary indications, not accounting entries** — the accountant makes the final call (durations, pro rata, actual entries). Disposals/write-offs are **declared by the user, never assumed**: a sold laptop stays listed until the user says so.

### 6. Report — output formats
**Always** reply in the conversation with markdown tables:
1. **Asset register** sorted by category then value: date · supplier · description · pre-tax / incl-tax amount · receipt (📎) · status.
2. **Indicative depreciation** table: asset · life · annual charge · estimated net book value (with the accountant caveat).
3. **Insurance inventory** — the document the insurer asks for after a theft or a claim: description, purchase date, purchase value, receipt reference. Ready to send.
4. Summary line: N assets · total purchase value · receipt gauge · items to confirm.

## Guardrails
- **100% read-only**: never call any write tool, ever. No category changes, no uploads, no requests.
- The €500 threshold and the depreciation lives are **customary practice, not accounting entries** — final decision belongs to the accountant; say it in every report.
- Never invent an asset's nature: ambiguous purchase → "to confirm". Never assume a disposal or write-off.
- Any example figures in explanations are invented and presented as such. Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50).
