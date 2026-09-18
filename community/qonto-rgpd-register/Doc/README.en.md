# 🗂 qonto-rgpd-register — Your bank account knows your data processors better than you do

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> **Zero write, by design**: the skill reads the spending, classifies, drafts — and stops there.
> Every output carries the same banner: **draft register, not legal advice — validate with a DPO or lawyer.**

---

## 🎯 Why this matters (usefulness)

The record of processing activities (GDPR Article 30) is the document **90% of small businesses don't have** — and the first thing a supervisory authority asks for. Yet the list of processors handling your personal data is already written somewhere: **in your debits**. `qonto-rgpd-register` reads it:

1. **Processor detection** — the SaaS tools that process personal data (CRM, email marketing, analytics, AI, cloud, payroll, support), recognized by Claude's general knowledge from their **first occurrence** in the debits — no recurrence needed
2. **Classification by processing activity** — purpose, typical data categories, data subjects, EU / non-EU headquarters and hosting — every attribute tagged **"to validate"**
3. **Draft Article 30 register in the CNIL card format** — one card per activity (purpose, legal basis to choose, data, recipients, processors, retention to set, transfers, security measures), controller header filled from `get_organization`
4. **Actionable flags** — 🔴 non-EU transfer → standard contractual clauses to verify · 🟠 DPA to locate or sign · 🟡 tool gone from the debits for 6 months → retire it from the register?

Would someone use this on a Monday morning? It's the Monday a client's security questionnaire lands, a prospect asks for your processor list, or an authority letter arrives — and the answer is generated from a bank statement.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **GDPR = the whole EU — a pan-European skill.** Every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT) is covered: in France the register follows the **CNIL** card model; elsewhere, same register, references switch to the local authority (BfDI/LfDI, AEPD, Garante, DSB, AP, APD/GBA, CNPD) | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Spending history | Ideally 12–24 months; thin account → the skill says what it couldn't detect and still delivers the register skeleton | ⭕ |
| A DPO or lawyer to validate | The skill produces a **draft**: legal qualification, legal bases and retention periods remain human decisions | ✅ at the end |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Controller identity**: `get_organization` → legal name, form, address, country = the mandatory register header. Honest reminder along the way: the Article 30(5) "under 250 employees" exemption is narrower than people think — any **non-occasional** processing (payroll, CRM, prospecting) already makes the register mandatory
2. **Spending scan** (12–24 months, `side: debit`, pagination ≤ 50, 3-month windows) + `list_supplier_invoices` (cleaner legal names than card labels). Spellings normalized and merged: `GOOGLE *WORKSPACE`, `GOOGLE IRELAND LTD`, `Google Cloud EMEA` = one vendor. Last-seen date tracked (`emitted_at` for cards) to feed the freshness flag
3. **Classification**: for each recognized SaaS — does it process personal data on the company's behalf? Category (CRM, email marketing, analytics, AI, cloud, payroll, support, e-commerce/payments), typical data, EU/non-EU HQ and hosting — **all tagged "to validate"**. Out-of-scope spend (bank fees, travel, hardware) is listed in an appendix: nothing silently disappears
4. **Register cards**: grouped by **purpose, not by vendor** (prospects & customers, marketing communication, audience measurement, support, HR & payroll, accounting, IT hosting). `list_memberships`: several active members → the skill suggests the HR block even before a payroll tool shows in the debits
5. **Flags**: 🔴 non-EU vendor or hosting → transfer mechanism to verify (adequacy, SCCs, DPA annexes) · 🟠 DPA to locate or sign, vendor by vendor · 🟡 gone from the debits ≥ 6 months → still used? retire from the register (and request data deletion) · 🟡 reseller/marketplace masking the real vendor → the skill **asks**, never guesses
6. **Delivery**: summary table + one card per activity + prioritized to-do in markdown; print-ready HTML register when the host renders files. Everywhere: **draft register, not legal advice**

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**Zero write, by design**: four read tools, no write tool. The skill changes nothing on the account, contacts no vendor, sends nothing. It turns data you already have (your debits) into a document you don't (your register) — and validation stays human.

## 🧪 Holds up on messy data

- Empty or thin history? → register skeleton with the controller block filled, missing parts named explicitly
- Cryptic card labels? → cross-checked against supplier invoices; still unknown → "unidentified — check the invoice", never a guess
- One vendor, five spellings? → normalized and merged into a single processor entry
- Reseller or app-store charge hiding the real product? → flagged, and the skill asks the user
- Genuinely ambiguous roles (payment providers are often independent controllers)? → stated as ambiguous, "to validate" — never a definitive call
- Non-French EU company? → same GDPR, same register, local-authority references — no France-only assumption

## 📤 Output formats (where does the register land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: processor summary, one card per activity, prioritized to-do | **Always** — the baseline |
| **Print-ready register** | **HTML** file/artifact: controller header, Article 30 cards, processor annex, to-do | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |
| **Disclaimer banner** | "Draft register, not legal advice — validate with a DPO or lawyer" | On **every** output, no exception |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem (the document nobody has) → the spending scan → classification & cards → **the full Article 30 register generated from a bank statement** → the DPA/transfer to-do. It runs live on a real production account.

## 💡 Roadmap ideas

- Optional multi-MCP enrichment: scan Gmail/Drive for already-signed DPAs when those MCPs are detected — otherwise the skill says so and continues
- Register diff: rerun 6 months later → new processors in, retired ones out (reuses the last-seen date)
- Ready-to-send "DPA request" and "data deletion request" letter templates — still zero write, text to copy
- DPIA appendix: point out activities likely to require an impact assessment — always "to validate", never a definitive qualification

## 🛡 Guardrails

- **Never a definitive legal qualification** (processor vs controller vs joint controllership, legal basis, retention) — every card is tagged "to validate", undecided fields stay visible placeholders
- Never invents vendor facts: unknown HQ or hosting → stated as unknown, with "check the invoice / the vendor's DPA page" as the next step
- A register draft ≠ GDPR compliance: it's one required document, not the whole program — DPO/legal validation recommended in every report
- 100% read, zero write · IBANs masked (last 4 digits) · pagination ≤ 50 everywhere · all examples in the docs are invented

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
