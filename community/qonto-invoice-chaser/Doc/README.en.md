# 📨 qonto-invoice-chaser — Chase late invoices without burning the relationship

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> The chaser that cross-checks the bank before it writes: it never chases a client who already paid.

---

## 🎯 Why this matters (usefulness)

B2B invoices in France get paid **11+ days late on average** — and chasing them is the chore everyone postpones: awkward, repetitive, easy to forget. `qonto-invoice-chaser` turns a Qonto account into a collections assistant that never damages a client relationship:

1. **Overdue detection** — late client invoices by `due_date`, days overdue, total outstanding, aging buckets 0-30 / 31-60 / 60+
2. **Cross-check against real cash** — an "unpaid" invoice may be **already paid** (bank transfer outside a payment link, never marked): the skill matches amount / counterparty / reference and **proposes** `mark_client_invoice_as_paid`. It NEVER chases money that already arrived — the most expensive email in B2B
3. **Payer profile & graduated reminders** — a reliable payer having a bad month ≠ a chronic late payer: the tone adapts to history. Courteous nudge (~D+7) → firm reminder (~D+21) → formal notice (~D+45) with legal interest and the **€40 recovery indemnity** (French Commercial Code, art. L441-10)
4. **Gmail drafts** — when the Gmail MCP is connected, the reminder lands as a **draft**: you review, you send. Otherwise, ready-to-copy text. Nothing ever leaves on its own.

Would someone use this on a Monday morning? Chasing receivables **is** the Monday-morning chore — this makes it a two-minute review instead of an hour of awkward writing.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | Adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Full legal kit (interest + €40 indemnity, art. L441-10): France.** Other Qonto countries (DE, ES, IT…): identical graduated reminders, generic reference to EU Directive 2011/7/EU — never invented rates or legal wording | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Client invoices in Qonto | The skill reads `list_client_invoices`; with no Qonto invoicing there is nothing to chase, and it says so | ✅ |
| Gmail MCP | Optional, detected dynamically: present → reminder drafts; absent → ready-to-copy text | ⭕ recommended |
| Invoicing history | Feeds the payer profile; without it, standard tone + a warning | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Scan receivables**: `list_client_invoices` (unpaid statuses, paginated ≤ 50) → days overdue per invoice, total outstanding, aging 0-30 / 31-60 / 60+
2. **Cross-check with real cash**: every "unpaid" invoice is checked against actual credit transactions (`list_transactions`) — exact amount ±0.01, counterparty ≈ client name, reference containing the invoice number
3. **Proposed marking**: strong match → the skill **shows the transaction** and proposes `mark_client_invoice_as_paid`; ambiguous cases (partial payment, grouped transfer) → candidates presented, never auto-marked
4. **Payer profile**: paid invoices, average delay, trend → 🟢 reliable-but-late · 🟡 occasional · 🔴 chronic — stated in one line ("24 invoices, always paid, avg 5 days late → warm tone")
5. **Graduated reminder** drafted with the exact numbers (invoice number, amount incl. VAT, days overdue, computed interest) — see the ladder in SKILL.md
6. **Gmail draft & report**: draft created (MCP present) or copy-ready text, then receivables report — outstanding, aging, DSO, next reminders

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The trust model**: reads (solid arrows) are risk-free; the two writes (dashed) are *proposed* actions — marking an invoice paid requires explicit confirmation in the conversation, and the reminder only ever exists as a **draft** that the user reviews and sends. The skill writes; the user decides.

## 🧪 Holds up on messy data

- Invoice paid by manual transfer, never marked? → caught by the cross-check, marking proposed with the evidence
- Partial payment, or one transfer covering several invoices? → candidates presented, never auto-marked, never chased blindly
- No invoicing history for a client? → standard tone, stated honestly
- Client record missing an email? → flagged, with a suggestion to complete it in Qonto — never a guessed address
- Non-French organization? → graduated reminders still work; no invented legal rates, EU directive referenced generically
- Empty account or no client invoices? → the skill says so and stops, instead of pretending

## 📤 Output formats (where does the reminder land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (outstanding, aging, per-invoice action table) | **Always** — the baseline |
| **Gmail draft** | Complete email (recipient, subject with invoice number, personalized body) in the drafts folder | When the Gmail MCP is connected; automatic fallback to copy-ready text |
| **Copy-ready text** | Subject + body, paste into any email client | Without the Gmail MCP |
| **Interactive dashboard** | **HTML** file/artifact: aging bars, top late clients, reminder pipeline | When the host renders files; fallback to tables otherwise |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem → the scan + cross-check (an already-paid invoice caught before any reminder) → the payer profile → **the draft appearing in Gmail with the exact numbers** → the receivables report. It runs live on a real production account.

## 💡 Roadmap ideas

- Payment link inside the reminder (`create_payment_link`) — the client pays in one click from the email
- **Per-country legal kits** (DE · ES · IT · AT · NL · BE · PT) — each country's transposition of EU Directive 2011/7/EU
- Scheduled Monday-morning run — the ritual becomes an appointment
- Full order-to-cash cycle upstream (quote → invoice → payment matching) feeding the chaser

## 🛡 Guardrails

- NEVER marks an invoice paid without showing the matching transaction and getting explicit confirmation in the conversation
- NEVER sends an email on its own: drafts by default, direct send only on explicit request — never presented as sent when it isn't
- Below full matching confidence: a question, not an action — chasing a client who paid costs more than asking
- Legal computations are France-only and informative, not legal advice; professional review recommended before a formal notice goes out
- Masked IBANs (last 4 digits) · pagination ≤ 50 everywhere · rehearsals on a fictional client with draft invoices, deleted afterwards

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
