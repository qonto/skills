# 💸 qonto-pay-me-now — From quote to cash, no friction

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> Payment-link creation is supported by the Qonto MCP. Follow its current schema and official documentation.

**Privacy default:** raw Qonto URL and QR encoding that URL, no Short.io calls. Before shortening or reading click stats, explain that Short.io receives and stores the payment URL and tracks payer clicks, then ask for explicit approval in the current conversation. Connection or invoice-send approval is not consent. Approved links use random slugs, no invoice/client identifiers or other Qonto metadata. Keep the raw URL visible; the QR always encodes it. Without approval, clicks are unknown, not "not clicked".

---

## 🎯 Why this matters (usefulness)

The freelance black hole: the client says yes to your quote… and then nothing happens. The invoice waits. The payment waits even longer. Every day between the handshake and the money is cash you've earned but can't touch. `qonto-pay-me-now` runs the whole cycle in one conversation:

1. **Accepted quote detected** — `list_quotes` cross-checked against `list_client_invoices`: only the accepted quotes that were **never invoiced** surface, with client, amount and date
2. **Invoice generated from the quote** — draft first, REAL document: nothing goes out without your explicit confirmation
3. **Qonto payment link** — raw Qonto URL + its **QR code**; Short.io shortening and payer tracking only after disclosure and explicit approval
4. **Follow-up & gentle nudge** — link clicked but unpaid after 48 h → a soft reminder is proposed, never sent on its own

The payment cycle shrinks from "whenever they think of it" to "they click, they pay." Would someone use this on a Monday morning? It's what you run the second a client says yes.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **The quote → invoice → payment link cycle is identical for every Qonto country** (FR, DE, ES, IT, AT, NL, BE, PT). Reminder wording: France fully covered; elsewhere the skill adapts and never invents local legal mentions | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Payment links activated | One-time activation in the Qonto app. If `create_payment_link` is refused, the skill says so and continues invoice-only | ⭕ recommended |
| Quotes created in Qonto | The skill starts from `list_quotes`; without quotes it can also start from any existing unpaid invoice | ⭕ |
| Short.io / Gmail MCP | Optional enrichments, detected dynamically: trackable short link + click stats / sending. Absent → raw Qonto link + copy-ready text | ⭕ optional |

## ⚙️ How it works

![How it works](assets/flow.en.png)

Legacy diagram: privacy rules above replace its automatic Short.io/readable-slug step and its claim about unsupported payment links.

1. **Detection**: `get_organization`, then `list_quotes` paginated ≤ 50 — accepted quotes cross-checked against existing invoices; only the never-invoiced ones are surfaced
2. **Invoice from the quote**: `create_client_invoice` as a **draft** (client, lines, amounts, VAT carried over) → review → sent only after your explicit go. Bonus: on cash-basis VAT (`on_receipts`), a faster payment literally accelerates your VAT cycle too
3. **Payment link**: `create_payment_link` on the invoice amount, invoice number for reconciliation. Follow the supported tool's current schema
4. **Short link + QR**: raw Qonto URL/QR by default. After privacy disclosure and explicit approval, `create-short-link` with a random slug and no invoice/client metadata. Otherwise skip Short.io and tracking
5. **Controlled delivery**: `send_client_invoice` and/or a Gmail draft carrying the link — you review, you send. Never presented as sent while pending
6. **Follow-up**: link status (`get_payment_link`) + clicks (`link-statistics`) + real cash in (`list_transactions`) → clicked-but-unpaid at D+2 = gentle nudge proposed; paid outside the link = `mark_client_invoice_as_paid` proposed with the transaction as evidence

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The security model**: this skill cannot move money out. A payment link is a way to **RECEIVE** a payment from your client — it has nothing to do with outbound transfers (which the MCP cannot execute anyway: any transfer request requires your own SCA in the Qonto app). The only three writes: an invoice (draft first, sent after your go), a payment link you can deactivate anytime in the app, and a paid-marking on an invoice — always proposed with the matching transaction as evidence, never automatic.

## 🧪 Holds up on messy data

- No accepted quotes? → the skill says so and offers to start from any unpaid invoice — the rest of the cycle is identical
- Payment-link feature not activated? → one-time activation explained, cycle continues invoice-only
- Short.io or Gmail absent? → raw Qonto link + copy-ready text, stated plainly, no tracking silently faked
- Client paid by plain transfer outside the link? → matched in `list_transactions` (amount ± 0.01, counterparty, reference), invoice marking proposed with evidence
- Non-French account? → same cycle everywhere; wording adapted, no invented legal mentions
- Pagination ≤ 50 everywhere · invoice numbering left to the organization's settings · amounts always from the quote, never invented

## 📊 The follow-up matrix (D+2)

| Link clicked? | Payment received? | Proposed action |
|---|---|---|
| ❌ No | ❌ No | Check delivery; offer to resend through another channel |
| ✅ Yes | ❌ No (> 48 h) | **Gentle nudge** — "the link is still active" — drafted, never auto-sent |
| ✅ Yes | ✅ Yes | Loop closed ✅ — confirmed in the report |
| ❌ No | ✅ Yes | Paid by plain transfer → reconciliation + `mark_client_invoice_as_paid` proposed |

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: quote → invoice → link pipeline, then the follow-up matrix | **Always** — the baseline |
| **The payment link (+ optional short link)** | Raw Qonto URL; Short.io URL only after explicit approval | Every cycle |
| **QR code** | Image file/artifact encoding the raw Qonto URL | When the host renders files; otherwise the raw link is enough |
| **Follow-up report** | Clicks vs cash table + proposed nudges | On demand / at D+2 |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the black hole → detection & invoice → payment link + short link → **the QR code scanned on a phone, the Qonto payment page appearing** → follow-up & nudge. It runs live on a real production account. *The invoice is out, the payment link is live — before the handshake ends.*

## 💡 Roadmap ideas

- Deposit at signature: a partial payment link (e.g. 30 %) the moment the quote is accepted
- D+2 follow-up reminder pushed to the user's calendar when a calendar MCP is detected
- Multilingual client messages (client's language detected) — Qonto is pan-European
- Collection dashboard: click-to-payment rate per client, from `link-statistics` + `list_transactions`
- Local legal mentions per country (DE · ES · IT…) — v1 = identical cycle everywhere, v2 = local wording

## 🛡 Guardrails

- Invoices via MCP are REAL: draft first, sent only after explicit confirmation; rehearsals on a fictional client + `delete_client_invoice` afterwards
- **No outbound payments**: the payment link receives, it never debits. Unrelated to outbound transfers — those always require the user's own SCA in the Qonto app
- Nothing is sent (invoice, email, nudge) without confirmation in the current conversation; never presented as sent/paid while pending
- Amounts always come from the quote or invoice, never invented · IBANs masked (last 4 digits) · pagination ≤ 50 everywhere
- Honest degradation: no quotes, no payment-link feature, no Short.io, non-French account → the skill says what works and keeps going with that

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
