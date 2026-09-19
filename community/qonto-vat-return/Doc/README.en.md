# 🧾 qonto-vat-return — Your French VAT return, box by box, ready to copy

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> Prepares the French CA3 VAT return (form 3310-CA3) straight from real Qonto data · **entirely read-only, zero writes**
> ⚠️ **A preparation aid, NOT a filing** — the skill never transmits anything; accountant validation recommended

---

## 🎯 Why this matters (usefulness)

Every month, the same chore: reconstruct collected VAT and deductible VAT, then copy the right amounts into the right boxes on the tax portal — hoping you didn't mix up a line. `qonto-vat-return` does the preparation work from the Qonto account:

1. **Collected VAT per rate** — bases and tax at 20 / 10 / 5.5 / 2.1% → boxes 08, 09, 9B, 11, line 16; **on debits or on receipts depending on the detected chargeability** (`vat_payment_condition: "on_receipts"` → collected VAT follows the month's *received payments*, matched to client invoices)
2. **Deductible VAT** — summed `vat_amount` on debits + supplier invoices (deduped), fixed assets (box 19) split out when detectable, the rest in box 20 — **announced as a floor** with the count of untagged debits
3. **Net VAT** — line 28 payable, or lines 25/27 credit to carry forward; computed in cents plus the whole-euro rounding the form expects
4. **Consistency checks** — against previous months, against past DGFIP payments, against bank statements — every discrepancy flagged ⚠️ before you copy anything

All of it lands in **one "form box → amount → justification" table**, ready to copy into the tax portal. That's the Monday-morning (well, filing-morning) ritual, minus the spreadsheet.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **The CA3 is a French form.** Other Qonto countries (DE, ES, IT…): graceful degradation — a generic collected/deductible VAT summary, never foreign VAT mapped onto French boxes | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Standard VAT regime (CA3) | The simplified regime (CA12 + instalments) is **out of scope** — the skill detects it, says so, and reminds that it is **abolished on 2027-01-01** (art. 38, 2025 Finance Act) | ℹ️ detected |
| Invoices in Qonto | The more client/supplier invoices live in Qonto, the sharper the table; otherwise the skill works from transactions and states its limits | ⭕ recommended |
| ≥ 6 months of history | Feeds frequency detection and the consistency checks; below that, honest degradation | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Scoping — detected, never asked**: filing frequency from DGFIP payment history (monthly debits → monthly CA3; quarterly → quarterly CA3, allowed when annual VAT < €4,000); simplified regime → out of scope, stated, with the 2027-01-01 abolition warning; **chargeability** read from client invoices (`vat_payment_condition`) — debits or receipts, handled per invoice when the portfolio is mixed
2. **Collected VAT per rate**: on debits → invoices issued in the period; **on receipts → incoming transactions matched to client invoices** (amount + counterparty + reference), taking the matched invoices' VAT breakdown; credit notes deducted; receipts with no matching invoice → listed separately, never silently taxed or ignored
3. **Deductible VAT**: `vat_amount` on debits + `total_tax_amount` on supplier invoices, deduped; fixed assets (box 19) when detectable, otherwise everything in box 20 with an explanation; prior credit (box 22) from the previous return — **total announced as a floor**; **reverse charge (EU purchases / imports): foreign counterparties detected → flagged "verify with your accountant", never computed silently**
4. **Net position**: line 23 (total deductible) → line 28 net VAT due, or lines 25/27 credit to carry forward (line 26 refund: mentioned, the user's call with their accountant); cents + the form's whole-euro rounding
5. **Consistency checks**: net VAT vs the median of past DGFIP payments (⚠️ if deviation > 30%, explained); bases and rate mix vs previous months; transactions vs statement totals (`list_statements`); unmatched receipts listed
6. **Report**: box-by-box CA3 table with justifications, checks table ✅/⚠️, deadline reminder (between the 15th and 24th of the following month) — plus an HTML dashboard when the host renders files

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The key point**: this skill is **entirely read-only** — no write tool, no dashed arrow in the diagram. It cannot file, cannot pay, cannot modify anything. The only action that follows is yours: copying the boxes into the tax portal, ideally after your accountant's review.

## 🧪 Holds up on messy data

- Cash-basis VAT (`on_receipts`)? → collected VAT follows received payments matched to invoices — the case most tools get wrong
- Untagged VAT on debits? → deductible total announced as a **floor**, count of unknowns disclosed, no rate ever guessed
- Incoming payments with no matching invoice? → listed with amounts, the user decides with their accountant
- Foreign suppliers (EU / import reverse charge)? → candidate transactions flagged for the accountant, never auto-computed
- Simplified regime, non-French company, empty account? → the skill says what it can and can't prepare instead of pretending
- Card settlement delays (`emitted_at` vs `settled_at`), credit notes, multi-account orgs — handled

## 📤 Output formats (where does the return land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Box-by-box CA3 table (box → label → amount → justification) + checks table ✅/⚠️ | **Always** — the baseline |
| **Interactive dashboard** | **HTML** file/artifact: form-like view, per-rate split, history vs past DGFIP payments | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |
| **Nothing else** | No transmission, no Qonto write | Never — by design |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the monthly chore → regime detection (cash-basis!) → the box-by-box table → **the net VAT matching the accountant's manual calculation to the cent** → consistency checks + dashboard. It runs live on a real production account.

## 💡 Roadmap ideas

- Receipt pre-check: `list_transaction_attachments` on deducted debits, missing receipts flagged — a stronger audit trail
- Chains with `qonto-tax-pilot`: the prepared CA3 feeds the tax-vault provision (both skills share the same chargeability detection)
- Optional multi-MCP enrichment: draft email to the accountant when a mail MCP is detected — the core stays 100% Qonto
- **European VAT modules** (DE USt-VA, ES modelo 303, IT LIPE…) — Qonto is pan-European; same engine, different box mapping

## 🛡 Guardrails

- **A preparation aid, NOT a filing**: no write tool, no transmission — the skill cannot submit anything; the user (or their accountant) copies the values themselves
- **Accountant validation recommended in every report** — especially reverse charge, fixed assets and prior credit
- Never invents: no French boxes for non-French organizations, no VAT rate guessed on untagged debits, no reverse-charge amounts computed silently
- Deductible = an announced **floor** with the count of untagged debits; unmatched receipts listed
- IBANs masked (last 4 digits) · pagination ≤ 50 everywhere

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
