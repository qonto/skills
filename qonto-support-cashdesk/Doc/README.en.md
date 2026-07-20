# 🧾 qonto-support-cashdesk — The billing counter of customer support

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> The customer says "you charged me twice" — the skill **proves it** (or disproves it) in the transactions, then replies with the fix attached.

---

## 🎯 Why this matters (usefulness)

"I never received my invoice." "The payment link expired." "You charged me twice." Three support messages that pull the founder away from real work — while **the answer already sits in Qonto**. `qonto-support-cashdesk` turns the account into a billing counter:

1. **Conversation read** — pulled from Intercom when that MCP is connected, otherwise pasted into the chat: claim type, identity clues and quoted amounts extracted
2. **Client matched, never guessed** — `list_clients` by email first, then name/company; candidates shown and **confirmed by the user** before anything happens
3. **Reality checked** — invoices (status, dates), the payment link's real state (open, expired, paid), incoming payments in the transactions: every conclusion cites its evidence
4. **Fix attached** — resend the invoice (`send_client_invoice`), fresh payment link (`create_payment_link`), or a **credit note** (`create_credit_note`) when the double collection is **proven by two dated credits** — every write confirmed, the customer reply delivered as a draft to review

Would someone use this on a Monday morning? Support inboxes fill up over the weekend — Monday morning is exactly when these three messages are waiting.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | Adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Universal** — clients, invoices, payment links and transactions exist in every Qonto country (FR, DE, ES, IT…); no local tax rule involved | ℹ️ all countries |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Qonto invoicing in use | Client invoices and payment links must be issued through Qonto to be verifiable | ✅ |
| Intercom MCP | To pull support conversations directly | ⭕ optional — otherwise paste the conversation |
| Gmail MCP | To create the reply as a **draft** (the skill never sends) | ⭕ optional — otherwise copy-paste text |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Read the conversation**: from Intercom when present, otherwise pasted — the skill extracts the claim type (invoice not received / expired link / double charge), identity clues (email, name, company) and quoted references (invoice number, amount)
2. **Match the client**: `list_clients` by email first (most reliable), then normalized name/company — candidates shown and confirmed; two look-alikes → both listed; no match → said plainly
3. **Check the facts**: `list_client_invoices` (status, amounts, dates, recipient email), `list_payment_links` + `get_payment_link` (open / expired / paid), `list_transactions` on the credit side windowed around the invoice dates (`emitted_at` for card settlement lag)
4. **Evidence-based diagnosis**: invoice never received, expired link, or double collection — **two credits cited with date + amount**; only one credit found → no credit note, a factual report of what exists
5. **Fix attached** (each write confirmed): resend the invoice, create a fresh payment link, or a credit note when the duplicate is proven — the credit note documents the correction; **the refund itself is a transfer the user makes in the Qonto app (SCA)**
6. **Customer reply**: a factual draft to review — apologies only when the error is proven, the correction cited (credit note number, new link); Gmail draft when that MCP is present, otherwise copy-paste

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The key point**: reads (solid arrows) are risk-free; writes (dashed) — resend, link, credit note — each require explicit confirmation in the conversation. A credit note is a **real accounting document**: it is only ever proposed with the proof on the table, never as a "commercial gesture" decided by the skill. And the skill **never** sends the customer reply itself: draft only.

## 🧪 Holds up on messy data

- Customer email not in the clients list? → search by name/company, candidates listed, never guessed
- Two similar clients? → both shown, the user picks
- "Charged twice" but only **one** credit found? → no credit note; the skill reports exactly what it found
- Amounts that don't line up (partial payment, currency)? → the discrepancy is cited, not smoothed over
- Payment link claimed expired but actually **paid**? → the skill says so — no pointless new link
- Intercom or Gmail MCP absent? → said once, then the skill continues in pure Qonto mode
- Pagination ≤ 50 everywhere · masked IBANs · card settlement lag handled (`emitted_at` vs `settled_at`)

## 🧾 The three counters

| Customer says | The skill checks | Honest outcome |
|---|---|---|
| "Never received the invoice" | Invoice exists? Status? Recipient email correct on the client record? | Found → resend proposed (email fixed first if wrong) · no invoice → nothing to resend, said as is |
| "The payment link expired" | Real link status (`get_payment_link`): open, expired, paid | Expired → fresh link proposed · already **paid** → flagged, no new link |
| "You charged me twice" | Two credits for the same invoice: same amount, close dates — **both cited** | Duplicate **proven** → credit note proposed · **one credit → no credit note** |

Example (invented): invoice INV-2026-042 for €480, two €480 credits collected one day apart → duplicate proven, a €480 credit note proposed with both dates cited in the reply.

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Diagnosis + cited evidence + recap table (claim → evidence → action → status) | **Always** — the baseline |
| **Customer reply draft** | Ready-to-review text; **Gmail** draft when that MCP is present (never sent by the skill) | Every conversation handled |
| **Qonto documents** | Invoice resent by Qonto · payment link · credit note (numbered accounting document) | Case by case, after confirmation |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the three support messages → the confirmed client match → **the duplicate proven in the transactions, then the credit note and the apology draft in one pass** → the two other counters at speed. All demo data is invented.

## 💡 Roadmap ideas

- **Proactive** duplicate-collection detection (periodic scan) — the sales-side twin of `qonto-supplier-detective`
- Per-client dispute history (repeat complaints, average resolution time) — reuses the client matching
- Reply in the customer's language, detected from the conversation — Qonto is pan-European
- Guided refund: preparing the transfer request for SCA approval in the app — same security model as `qonto-tax-pilot`

## 🛡 Guardrails

- NEVER acts on an unconfirmed client match; never presents a write as done when it is pending or failed
- **Credit note = proof + confirmation**: two dated credits cited and an explicit yes in the current conversation — otherwise no credit note, however hard the customer insists
- The skill never sends the customer reply itself — draft only, the user reviews and sends
- Refunds are transfers the user makes in the Qonto app (SCA) — the skill never moves money, and says so
- Purchase-side duplicates (a supplier charged you twice) belong to `qonto-supplier-detective`
- Masked IBANs (last 4 digits) · pagination ≤ 50 everywhere · rehearsals on a **fictional client** (MCP invoices are real → draft, then delete)

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
