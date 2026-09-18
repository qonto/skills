---
name: qonto-prescription-guard
description: Legal expiry radar for unpaid client invoices on Qonto accounts (France). Every unpaid invoice has a legal death date — 5 years between businesses (art. L110-4 French Commercial Code), 2 years against a consumer (art. L218-2 French Consumer Code). The skill scans the full invoice history, qualifies each receivable B2B/B2C, detects clock-resetting events (partial payments found in transactions), and outputs an "act before…" schedule sorted by urgency × amount. 100% read-only, not legal advice. Use for "quelles factures vont être prescrites ?", "which unpaid invoices are legally dying?", "combien de temps me reste-t-il pour agir contre ce client ?", "audit prescription de mes créances", "is this old invoice still recoverable?".
permissions:
  mcp:
    qonto: [get_client, get_organization, list_client_invoices, list_clients, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto Prescription Guard

Every unpaid invoice carries a countdown: once the limitation period (*prescription*) runs out, the debt is legally unrecoverable in court. This skill finds the countdown on every receivable and tells the user when to act. **100% read-only — zero writes.** It is an analysis aid, **not legal advice**.

## Prerequisites
1. `get_organization` first → organization country, bank accounts (`bank_account_id`/`iban` needed later for `list_transactions`).
2. **Country-aware**: limitation rules are **France only**. For other Qonto countries (DE, ES, IT, AT, NL, BE, PT…), say so plainly and degrade to an **age-of-receivables report** (oldest first, amounts at risk by age bucket) with **no legal qualification and no invented deadlines**.
3. Works on any account, empty ones included: no unpaid invoices → say so and stop cleanly.

## Embedded French limitation rules (static — no external lookup)
| Situation | Period | Legal basis |
|---|---|---|
| Both parties are businesses (commerçants), or debt arose in the debtor's commercial activity | **5 years** | art. **L110-4** Code de commerce |
| Professional selling goods/services **to a consumer** (private individual, non-professional purpose) | **2 years** | art. **L218-2** Code de la consommation |
| Starting point | Day the creditor knew the facts enabling action — for an invoice, prudently the **issue date** (conservative; some case law uses due date, which gives *more* time — never overstate time left) | art. **2224** Code civil |
| Interruption → **full period restarts** at the act's date | Debtor's acknowledgment of the debt (a **partial payment** counts as tacit acknowledgment), legal action (summons, *injonction de payer*), enforcement act | art. **2240–2244** Code civil |
| ⚠️ NOT interruptive | Reminder emails, dunning letters, even a registered *mise en demeure* — the single most common misconception | settled case law |

Notes to surface when relevant: after interruption a **new period of the same duration** runs (art. 2231); limitation is a defense the debtor must raise, a judge won't apply it automatically (art. 2247) — but treat the date as the practical death of the claim.

## Workflow

### 1. Inventory the receivables
`list_client_invoices` with `status: "unpaid"`, paginate `per_page: "50"`, over the **entire history** (old invoices are exactly the point). For each: number, outstanding amount, currency, issue date, due date, `client_id`. Skip drafts and canceled invoices. If an invoice was likely paid outside Qonto, flag it and suggest the user mark it paid in the app rather than assume.

### 2. Qualify each debtor: B2B or B2C
`list_clients` / `get_client` per debtor. Heuristic, stated as such:
- Client record has a **SIREN/SIRET, VAT number, or registration number**, or `type` is a company → **likely a business → 5 years** (L110-4).
- Individual name, no business identifiers → **possibly a consumer → 2 years** (L218-2) — but **never assert B2C with certainty**: a sole trader buying for business purposes falls back to 5 years. When ambiguous, **ask the user** ("Is ACME DUPONT a business customer or a private individual?") and compute **both dates** until answered, keeping the **shorter one highlighted** (prudent).

### 3. Detect interruptive acts
- **Partial payments (detected)**: scan `list_transactions` (per account from step 0, `side: credit`, paginated ≤ 50, windowed) for incoming payments from the same counterparty (normalize case/accents; match on invoice number in the reference or label, or client name + amount below the invoice total). A match after the issue date → **clock probably reset at the payment date**. Always announce it as a heuristic: *"partial payment detected on [date] → limitation period probably reset — confirm with a lawyer."*
- **Acknowledgment of debt / legal action (declared)**: these leave no bank trace — **ask the user once**, per at-risk invoice: signed acknowledgment? payment plan accepted in writing? summons or *injonction de payer* filed? If yes, reset the clock at the declared date and tag the line "user-declared".

### 4. Compute the death date
Per invoice: `deadline = start date + period`, where start = issue date, replaced by the **latest interruptive act** when one exists. Derive time left and bucket: 🔴 < 6 months · 🟠 6–12 months · 🟡 1–2 years · 🟢 > 2 years · ⚫ **past deadline → probably time-barred** (say "probably": suspensions or unseen acts may have shifted it).

### 5. Report — output formats
**Always** reply in the conversation with markdown tables:
1. **"Act before…" schedule**: invoice · client · outstanding € · B2B/B2C (with ❓ when assumed) · start date · interruptions found · **act before [date]** · time left · bucket — sorted by urgency × amount (soonest deadline first, ties broken by amount).
2. **Headline numbers**: total € at risk within 6 / 12 months; total € probably already time-barred; the single biggest saveable amount.
3. **Resets found**: each detected partial payment with its heuristic disclaimer.

**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): an **HTML timeline** — one bar per receivable from start date to death date, today marker, color by bucket, width by amount. If the host cannot render files, say nothing about it: the tables are the deliverable.

### 6. Hand off to action
- Deadline far but invoice merely late → suggest the **`qonto-invoice-chaser`** skill for friendly dunning (reminders do NOT stop the clock — chase early).
- Deadline < 6 months → recommend a **bailiff (commissaire de justice) or lawyer now**: only a legal act (summons, *injonction de payer*) or a signed acknowledgment resets/interrupts the period.
- Probably time-barred → list them separately; the user decides with counsel; the skill never declares a debt definitively dead or alive.

## Guardrails
- **This is not legal advice.** Every report states it: dates are prudent estimates from public rules; a lawyer or bailiff must validate before acting or giving up.
- **Never certain on B2C**: the 2-year qualification is always presented as an assumption to confirm.
- Interruption detection is a **bank-side heuristic** — payments made elsewhere, cash, or written acknowledgments are invisible; the skill asks instead of assuming.
- France only for legal dates; elsewhere → age report, clearly labeled, zero invented rules.
- 100% read-only: the skill never modifies invoices, clients, or transactions, and never creates anything.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50). Degrade honestly on sparse history.
