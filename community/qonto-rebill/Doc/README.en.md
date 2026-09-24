# 💶 qonto-rebill — The expenses you advanced for clients, literally recovered

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> Pure Qonto, end to end: transactions, labels and attached receipts in → a line-by-line rebill invoice out, **as a draft**, sent only after explicit confirmation.

---

## 🎯 Why this matters (usefulness)

Freelancers and agencies advance money for their clients — plugins, stock photos, hosting, train tickets, mission meals — and **forget to rebill half of it**. That's not a reporting problem; it's money already spent and never recovered. `qonto-rebill` goes and gets it:

1. **Finds client-attributable expenses** — client-named Qonto labels, teams, or history-assisted attribution, one transaction at a time (nothing is ever attributed silently)
2. **Groups them per client and period** — and inventories the **receipts already attached** to each transaction (gaps flagged per line)
3. **Explains the VAT choice, never decides it** — disbursement (client's name, no margin, outside VAT) vs rebilled expense (VAT at the main service's rate): the skill lays out the difference and **asks**
4. **Drafts the rebill invoice line by line** — `create_client_invoice` as a **draft**, optional 5-10% handling fee (user's choice), sent only after explicit confirmation

Would someone use this on a Monday morning? It's the end-of-quarter ritual that pays for itself the first time it runs.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | Adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Universal mechanics** (find → group → draft). The **disbursement regime** is French law (art. 267 II-2° CGI): outside France the skill drafts all the same and defers local VAT treatment to a local accountant — never invented rules | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Client-named labels | Qonto labels named after clients (or teams per mission). **No labels? Interactive attribution** takes over, transaction by transaction — slower, nothing lost | ⭕ recommended |
| Clients in Qonto invoicing | `list_clients` — the invoice needs an existing client; otherwise the skill explains how to create one | ⭕ |
| Receipts attached | Inventoried automatically; to fill the gaps **before** rebilling: `qonto-receipt-hunter` | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Scope**: `get_organization` first (accounts, identity), then the referentials — Qonto labels and invoicing clients, normalized and matched (the label "acme studio" = the client "ACME Studio"). Period agreed with the user (default: last full quarter)
2. **Detect**: debit scan (paginated ≤ 50), grouped by `emitted_at` (card expenses settle 1-2 days later and would leak across period boundaries). Attribution by client labels → teams → **history-assisted attribution**: the skill shortlists candidates (counterparties previously attributed, mission-typed spend: SaaS, stock photos, hosting, transport, meals) and asks one transaction at a time
3. **Group + receipts**: per-client table (date · counterparty · amount · purchase VAT), totals, and for each line the **already-attached receipt** retrieved (`list_transaction_attachments` + `get_attachment`) or the gap flagged
4. **The VAT choice**: disbursement vs rebilled expense — comparison table shown, regime **asked** (per line when mixed), 5-10% handling fee offered (never on a disbursement)
5. **Draft**: `create_client_invoice` as a DRAFT — one line per expense (date, counterparty, amount), VAT per the chosen regime, separate handling-fee line. Nothing is sent
6. **Confirm**: line-by-line review → sending only on explicit confirmation (`send_client_invoice`). Rehearsals: fictitious client + draft + `delete_client_invoice`

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The security model**: solid arrows are risk-free reads; the dashed arrow only produces a **draft invoice** inside Qonto. Sending it to the client requires explicit confirmation in the conversation — and since MCP-created invoices are real, rehearsals run on a fictitious client and end with `delete_client_invoice`.

## ⚖️ Disbursement vs rebilled expense (the table the skill shows)

| Criterion | Disbursement (*débours*, art. 267 II-2° CGI) | Rebilled expense (standard) |
|---|---|---|
| Principle | Paid **in the client's name and on their behalf** (mandate) | Paid in your own name, recharged as part of your price |
| Margin | Forbidden — exact amount, euro for euro | Allowed (handling fee 5-10%…) |
| VAT | **Outside VAT scope**: no VAT on the line, input VAT not deductible | **VAT at the main service's rate** (often 20%) — even if the underlying cost was 10% or VAT-free |
| Receipt | Original invoice **in the client's name**, handed over | Original invoice in your name, kept in your books |
| Books | Third-party account (not revenue) | Revenue |
| Country | French regime | Universal mechanics; outside France → local accountant |

The skill **explains and asks — it never picks a regime on its own**, and every report recommends accountant validation.

## 🧪 Holds up on messy data

- No client labels? → interactive attribution, one transaction at a time, plus an offer to label going forward so next quarter is automatic
- Receipt missing on a line? → flagged, with a pointer to `qonto-receipt-hunter` before sending
- Client not in the invoicing module? → the skill says so and explains how to create it
- Card expenses straddling two periods → grouped by `emitted_at`, not `settled_at`
- Empty account, expense-free period, non-French company → the skill says what it can and cannot do instead of pretending

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: expenses per client (receipt ✅/⚠️), invoice line by line, recovered total | **Always** — the baseline |
| **Draft invoice in Qonto** | `create_client_invoice` as a draft, visible in the Invoicing section | After the regime is agreed; sent only on explicit confirmation |
| **Receipt pack** | Download links (`get_attachment`, time-limited) to forward with the invoice | Every prepared invoice |
| **HTML recap** | Per-client cards, receipts gauge, recovered amounts | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); fallback to tables |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem (advanced expenses everyone forgets) → detection through labels → the VAT choice explained → **the draft invoice, line by line, receipts inventoried** → confirmed send and recap. It runs live on a real account (example figures in the docs are invented).

## 💡 Roadmap ideas

- Learning "rebillable" counterparties per client — accepted attributions pre-fill the next quarter
- Pre-approval quotes (`create_quote`) for large advances — client signs off before you pay
- A scheduled monthly/quarterly ritual: "anything to rebill this month?"
- Chaining: `qonto-receipt-hunter` before (complete the receipts), `qonto-invoice-chaser` after (chase the payment)
- Multi-currency expenses, converted at transaction rate and disclosed per line

## 🛡 Guardrails

- MCP-created invoices are **real**: draft until explicit confirmation, never presented as sent, rehearsals on a fictitious client + `delete_client_invoice`
- **No silent attribution, ever**: every uncertain expense is asked; nothing invented — no amount, no receipt, no client
- The disbursement/rebill choice belongs to the user (with their accountant) — the skill explains and asks
- Honest degradation (no labels, empty account, non-French country) · IBANs masked (last 4 digits) · pagination ≤ 50 everywhere

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
