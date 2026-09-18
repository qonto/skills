# 🗄 qonto-asset-registry — The asset register nobody keeps

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> **100% read-only**: the register writes itself, your accountant keeps the pen.

---

## 🎯 Why this matters (usefulness)

Nobody keeps the fixed-asset register. And the day something gets stolen or the office floods, the insurer asks for **the inventory with purchase values and receipts** — which nobody has. Yet your Qonto account already knows everything you own. `qonto-asset-registry` reads it:

1. **Equipment detection** across 24–36 months of real purchases (transactions + supplier invoices) — IT, furniture, machines, vehicles, tools, telephony, recognized by Claude's general knowledge **from the first occurrence** (specialist vendors, invoice labels)
2. **€500 pre-tax threshold** — French tax practice: below = expense, above = fixed asset (threshold configurable); leasing detected and flagged "financed, not capitalized here", never counted
3. **The asset register** — date, supplier, description, pre-tax / incl-tax amount, **linked receipt** (the transaction's attachment), status — with a receipt-completeness gauge
4. **Two golden outputs** — **indicative depreciation** (usual useful lives, straight-line, estimated net book value — for the accountant to validate) and the **insurance inventory**, ready to send *before* you need it

Would someone use this on a Monday morning? Ask anyone who just got the insurer's email after a break-in.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | Adapts to any organization (`get_organization` first, nothing hardcoded) | ✅ |
| Country | **Universal mechanics.** The €500 threshold and the depreciation lives are **French** practice; other Qonto countries (DE, ES, IT…) → register and insurance inventory without local tax suggestions, stated plainly | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| 24–36 months of history | Below that, the register is presented as partial, with the covered period stated | ⭕ |
| Receipts attached to transactions | The more there are, the stronger the inventory; missing ones are listed 📎 (pointer to `qonto-receipt-hunter`) | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Scan the purchases** (24–36 months, debits, pagination ≤ 50, 3-month windows) + `list_supplier_invoices` — supplier-invoice descriptions are often cleaner than transaction labels, matched by amount and date. Card purchases dated by `emitted_at` (settlement lags 1–2 days)
2. **Recognize the equipment** with Claude's world knowledge, **from the first occurrence** — no recurrence needed to spot a computer reseller or an office-furniture supplier. Ambiguous generalist merchant → line marked "❓ to confirm", never guessed. Installment purchases merged into a single asset
3. **Apply the €500 pre-tax threshold** (configurable): expense or fixed asset; leasing (recurring monthly payments to a financing company) flagged "🔁 financed, not capitalized here"
4. **Link the receipts**: `list_transaction_attachments` + `get_attachment` per asset; missing → 📎 with a pointer to `qonto-receipt-hunter`; completeness gauge computed
5. **Indicative depreciation**: usual lives (IT & phones 3 years, tools 5, machines 5–10, vehicles 4–5, furniture 10), straight-line, estimated net book value, end-of-life date — customs, not accounting entries
6. **Register + insurance inventory**: tables in the conversation, HTML dashboard when the host renders files, handoff to the accounting firm via `qonto-accountant-handoff`

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The key point**: this skill is **100% read-only** — no write tool is ever called. No category changed, no document uploaded, no request created. It reads, computes, and presents. The accounting decision (capitalize, depreciate, dispose) stays entirely with you and your accountant.

## 🧪 Holds up on messy data

- Cryptic transaction labels? → supplier invoices matched by amount and date carry the cleaner description
- Purchase at a generalist marketplace? → "to confirm", with the attached receipt opened when available — never guessed
- Equipment paid in installments? → merged into one asset at full value, not three half-assets
- Leased hardware? → detected via recurring payments to a financer, flagged and excluded from the total
- No receipt attached? → line flagged 📎 with the count disclosed, and `qonto-receipt-hunter` suggested to recover them
- Non-French organization? → the register and the insurance inventory still work; the skill just skips the French threshold and lives, and says so

## 📤 Output formats (where does the register land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: register sorted by category/value, depreciation, summary (N assets · total value · receipt gauge) | **Always** — the baseline |
| **Dashboard / export** | Self-contained **HTML** file/artifact in the Qonto palette: register by category, receipt-completeness gauge, insured total, depreciation timeline | When the host renders files; automatic fallback to tables |
| **Insurance inventory** | Ready-to-send table: description, purchase date, purchase value, receipt reference | On demand — ideally before the claim |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem (the inventory your insurer demands and nobody has) → the scan → the register with linked receipts → the "it was all already there" moment → the dashboard and the insurance inventory. It runs live on a real production account.

## 💡 Roadmap ideas

- **Country modules** (DE · ES · IT · AT · NL · BE · PT thresholds and useful lives) — the mechanics are already universal
- Disposal detection from incoming credits (equipment resale), always proposed for confirmation
- Reconciliation with a physical inventory (photos, asset tags)
- End-of-depreciation alerts (renewal budgeting)
- CSV export for the accounting firm, alongside `qonto-accountant-handoff`

## 🛡 Guardrails

- **100% read-only** — no write tool is ever called
- The €500 threshold and the depreciation lives are **customary indications, not accounting entries** — the accountant makes the final call, restated in every report
- Ambiguous nature → "to confirm", never invented; disposals/write-offs declared by the user, never assumed
- Example figures are invented and presented as such · IBANs masked (last 4 digits) · pagination ≤ 50 everywhere

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
