# 🕵️ qonto-supplier-detective — The detective for your supplier payments

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> **100% read-only** — the detective touches nothing; it hands you the case file.

---

## 🎯 Why this matters (usefulness)

In most companies, a small share of supplier payments are simply mistakes — duplicates, invoices paid twice, overpayments — and nobody ever goes looking, because the search means grinding through hundreds of invoices by hand. `qonto-supplier-detective` does the grinding. It hunts 4 anomalies:

1. **Duplicate invoices** — same supplier + same amount within days, or same invoice number; the native `has_duplicates` signal double-checked via `get_supplier_invoice`; **subscriptions excluded by cadence detection** (same amount every month ≠ duplicate!)
2. **Paid twice** — 1 invoice, 2 debits: the finding that pays. Partial payments and deposits recognized as legitimate (the debits *sum to* the invoice, not 2×)
3. **Invoice ↔ payment gaps** — paid more than invoiced beyond rounding; credit notes and refunds checked before anything is flagged
4. **IBAN watch** 🚨 — a known supplier whose payment IBAN suddenly changed is treated as a **security alert**, pinned on top of the report: it's the number-one supplier wire-fraud pattern. The instruction, every time: **verify by phone at the number you already know** — never the one in the email announcing the change

Every finding ships with its evidence: invoice number, transfer references, dates, recoverable amount. Nothing is asserted — everything is "presumed, to verify", with the full case file to claim the money back.

Would someone run this on a Monday morning? It's the audit nobody has time to do by hand — and it can literally pay for itself on the first run.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **No national rules involved**: the detectors compare the account's own data with itself. Works on every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT) | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Supplier invoices imported into Qonto | The more there are, the larger the detection surface. Without them: a transaction-only pass (twin debits + IBAN watch on transfers), stated plainly | ⭕ recommended |
| ≥ 6 months of history | Below that, subscription-cadence detection and IBAN tracking lose reliability — the skill says so | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Full sweep**: every supplier invoice (paginated ≤ 50 until exhausted — progress summarized every ~300 invoices) + every debit over 12–24 months. Supplier names **normalized** (SEPA noise, SARL/SAS/GmbH suffixes, whitespace) so "OVH SAS", "OVH.COM" and "VIR SEPA OVH" merge; invoice numbers cleaned; **credit notes and refunds identified up front** — they are exculpatory evidence, not anomalies
2. **Duplicate invoices**: the native `has_duplicates` signal + an own pass (same supplier + same amount within 45 days, or same invoice number). **THE false-positive trap: subscriptions** — same amount every month at a regular cadence is a legitimate recurrence, excluded before anything is flagged
3. **Paid twice**: one invoice matched to 2+ debits, or two twin invoices each paid. Instalment payments are cleared first (the debits *sum to* the invoice total); a true double payment totals ≈ 2× the invoice
4. **Invoice ↔ payment gaps**: presumed overpayment beyond €0.05 rounding, after searching for an explaining credit note; foreign currencies reported as "to verify (FX)", never accused
5. **IBAN watch** 🚨: the payment IBAN is tracked per supplier; a change is handled like a security incident, with the classic anti-fraud practice: phone verification at the **already-known** number
6. **Recovery report**: findings ranked by recoverable amount, estimated total to claim, cleared cases shown (subscriptions, instalments, refunds already received), ready-to-send claim emails on request. **Zero writes.**

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The key point**: everything is a solid arrow — reads, nothing but reads. The skill never calls a Qonto write tool; it has nothing to get approved, nothing to execute. The only "action" happens outside the account: you, on the phone with your supplier, or your claim email. The detective builds the case; you make the calls.

## 🧪 Holds up on messy data

- Bank labels are messy? → supplier names normalized (SEPA prefixes, legal suffixes, references) before any matching; raw labels kept for display
- Same amount every month? → cadence detection says *subscription*, not duplicate — the single biggest false-positive source, handled by design
- One invoice, three debits? → if they sum to the invoice total, it's an instalment plan, cleared and said so
- A refund already arrived? → the case is reported as *recovered*, not *recoverable*
- No supplier invoices imported? → transaction-only pass (twin debits, IBAN watch on transfers), announced plainly
- No IBAN visible for a supplier? → the coverage gap is disclosed, never papered over
- Empty or non-French account? → the skill says what it can and cannot check, and never invents a finding

## 🕵️ The 4 detectors — and the traps they avoid

| Detector | What it hunts | The false positive it clears first |
|---|---|---|
| D1 · Duplicates | Same supplier + amount within 45 days, or same invoice number; native `has_duplicates` | **Subscriptions**: same amount at a regular monthly cadence = recurrence, not duplicate |
| D2 · Paid twice | 1 invoice ↔ 2+ debits; two twins each paid | **Partial payments / deposits**: debits sum to the invoice (≠ 2×); refund received = case closed |
| D3 · Gaps | Paid > invoiced beyond €0.05 rounding | **Credit notes** explaining the gap; foreign currency → "to verify (FX)" |
| D4 · IBAN watch 🚨 | Known supplier paid on IBAN A → suddenly IBAN B | **Legitimate bank switch**: the alert demands verification, it doesn't accuse — but always **before the next payment** |

## 📤 Output formats (where does the case file land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown report: IBAN alerts 🚨 on top, findings table ranked by recoverable amount, estimated total, cleared cases | **Always** — the baseline |
| **Interactive case file** | **HTML** file/artifact: findings board, evidence cards, recoverable gauge, IBAN alert banner | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to markdown otherwise |
| **Claim email** | Ready-to-send draft: invoice number, both transfer references, dates, amount — IBANs masked | On request, finding by finding |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem → the sweep (the volume on screen) → the case file with an IBAN alert → **the double payment, quantified, with its claim email ready to send** → the read-only wrap-up. It runs live on a real production account.

## 💡 Roadmap ideas

- Send the claim through a Gmail MCP when one is detected — optional multi-MCP enrichment, the core stays Qonto-pure
- Flag disputed invoices via `change_supplier_invoice_status` — would leave read-only territory, so strictly opt-in
- Post-cancellation billing detection: a subscription that keeps charging after a declared cancellation — reuses the cadence engine
- Scheduled quarterly audit with a diff against the previous report — turns the IBAN watch into true monitoring
- Multi-currency reconciliation with daily FX rates — turns "to verify (FX)" into verdicts

## 🛡 Guardrails

- **100% read-only**: no Qonto write tool is ever called — nothing to approve, nothing executed
- Wording discipline: "presumed", "to verify" — never "fraud" or "error" asserted as fact; every finding shows its evidence
- The IBAN alert **always** carries the instruction: verify by phone at the known number, never through the contact details in the email announcing the change
- Subscriptions, instalments, deposits, credit notes and refunds are cleared **before** anything is flagged — a false accusation costs more trust than a duplicate costs money
- IBANs masked (last 4 digits) · pagination ≤ 50 everywhere · progress summarized on large sweeps

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
