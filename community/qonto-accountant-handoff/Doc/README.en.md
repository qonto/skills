# 🗂 qonto-accountant-handoff — The monthly handoff to your accountant, minus the chore

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> **Zero writes on Qonto** — the only writes happen outside Qonto: a Google Drive filing and a Gmail draft, and nothing is ever sent without you.

---

## 🎯 Why this matters (usefulness)

Every month, the same message: *"could you send me March's documents?"* — followed by an evening of digging through emails and download folders. `qonto-accountant-handoff` builds the complete handoff pack straight from the Qonto account:

1. **Statements & invoices, gathered** — the period's official statements (`list_statements` / `get_statement`) plus every client and supplier invoice, with statuses
2. **Receipt completeness report** — each transaction checked against its attachments: ✅ attached · ⚠️ missing · ➖ not needed, with **the precise list of what's missing** (date, counterparty, amount)
3. **Annotated, never booked** — labels, VAT, factual notes ("this refund corresponds to the May 12 payment"); **no accounting entry is ever invented** — the accountant stays the professional
4. **A drafted handoff letter + organized filing** — the month in ten lines, the 2–3 points worth attention, the open questions; a YYYY/MM tree on Google Drive plus a recap email draft to the firm via Gmail, when those MCPs are present

Would someone use this on a Monday morning? It's literally the first Monday of the month — and the first time it ran, the accountant asked if someone new had been hired.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Works for every Qonto country** — statements, invoices and receipts are universal. Local tax remarks only when detected, never invented rules | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| A closed month | Statements only exist once the month is over; in-progress month → partial pack, stated plainly | ℹ️ |
| Google Drive MCP | For the YYYY/MM filing tree — otherwise a structured local pack (markdown + CSV) | ⭕ optional |
| Gmail MCP | For the recap email draft to the firm — otherwise the letter stays in the pack | ⭕ optional |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Scope the period**: `get_organization` first (accounts, country), previous complete month by default (or a quarter on request), detection of the Google Drive and Gmail MCPs — present or not, the skill says so and carries on
2. **Statements**: `list_statements` then `get_statement` per account — the period's official PDFs; an account with no statement is flagged, never papered over
3. **Receipt status**: `list_transactions` (paginated ≤ 50, card settlement delays `emitted_at` vs `settled_at` handled at month boundaries) + `list_transaction_attachments` per transaction → ✅/⚠️/➖ and the precise missing list; suggested next step: run **qonto-receipt-hunter** on that list *before* sending
4. **Factual annotations**: labels, `vat_amount` (the count of untagged debits is disclosed — the VAT view is a floor), plain-language notes the accountant can use; anything that smells like bookkeeping becomes a **question** in the letter instead
5. **Invoices & the handoff letter**: client and supplier invoices for the period with statuses, then the drafted letter — the month in ten lines, the points worth attention, the open questions
6. **File & recap**: an `Accounting/YYYY/MM/` tree on Drive when the MCP is there (otherwise a local pack described file by file) + a Gmail **draft** to the firm — nothing leaves without the user

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The key point**: on the Qonto side, everything is a read — no write tool is used, there is literally nothing to approve. The only two "writes" happen outside Qonto: a folder filed on the user's own Google Drive (announced first), and a **draft** email in their own Gmail — the user always hits send themselves.

## 🧪 Holds up on messy data

- Month not closed yet? → partial pack, clearly labelled as such, statements listed as "pending month close"
- Missing receipts? → they're the headline of the letter, not a footnote — precise list with date, counterparty, amount, plus a pointer to qonto-receipt-hunter
- Untagged VAT on debits? → the VAT view is announced as a floor, count of unknowns disclosed
- Refunds and internal transfers → matched and named factually ("reverses the May 12 payment"), never allocated to an account
- No Drive, no Gmail? → the same pack lands as a structured local folder; the user forwards it their way
- Empty account or an account opened mid-month → the skill says what exists and what doesn't, instead of pretending

## 🗂 What's in the pack

| Item | MCP source | Shape in the pack |
|---|---|---|
| Handoff letter | Drafted by the skill (from the data it read) | `00-handoff-letter` — markdown + Gmail draft body |
| Bank statements | `list_statements` + `get_statement` | `01-statements` — official PDFs per account |
| Client invoices | `list_client_invoices` | `02-client-invoices` — list + statuses (paid / pending) |
| Supplier invoices | `list_supplier_invoices` | `03-supplier-invoices` — list + statuses |
| Receipt status | `list_transactions` + `list_transaction_attachments` | `04-receipts-status` — coverage table + **missing list** (CSV) |
| Annotated transactions | `list_transactions` (labels, VAT, factual notes) | CSV/markdown attached to the status |

## 📤 Output formats (where does the pack land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: pack contents, receipt coverage, missing list, the letter | **Always** — the baseline |
| **Google Drive folder** | `Accounting/YYYY/MM/` tree (letter, statements, invoices, receipt status) | When the Drive MCP is detected — filing announced first |
| **Gmail draft** | Recap email to the firm, letter as body, link to the Drive folder | When the Gmail MCP is detected — **never sent by the skill** |
| **Local pack** | Structured folder of markdown + CSV, described file by file | Without Drive/Gmail — forward it however you like |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the monthly chore → the pack building itself (statements, invoices, missing receipts listed) → the factual annotations and the letter → **the Drive tree filling up + the Gmail draft** (the "it just works" moment) → the local fallback. It runs live on a real production account.

## 💡 Roadmap ideas

- Automatic chaining with **qonto-receipt-hunter** — the missing list goes straight to the receipt chase before the handoff
- **qonto-monthly-close** verdict embedded in the letter as a quality badge
- Accountant-tool-friendly CSV export (normalized for the firm's software) — the format changes, the facts don't
- A start-of-month reminder when a calendar MCP is detected — optional multi-MCP, in the spirit of the kickoff
- Pack history (cumulated YYYY/MM) with open-question tracking — March's question doesn't get lost again in June

## 🛡 Guardrails

- **The skill does not do the accounting**: no journal entries, no chart-of-accounts allocation, no tax advice — factual annotation only; the accountant validates everything
- Nothing leaves without the user: the Gmail recap is a draft, the Drive filing is announced, no data flows to an MCP that wasn't detected and named
- A pack with missing pieces is **never** presented as complete — the missing list leads the letter
- Masked IBANs (last 4 digits) · pagination ≤ 50 everywhere · `403` on `list_cash_flow_categories` (claude.ai connector) → label fallback

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
