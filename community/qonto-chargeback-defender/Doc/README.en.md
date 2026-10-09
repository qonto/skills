# 🛡 qonto-chargeback-defender — Payment disputes, from detection to defense file

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> The skill prepares everything — detection, money trail, sourced defense file, deadline — and **the user alone submits** the response on the Stripe/PayPal portal.

---

## 🎯 Why this matters (usefulness)

A chargeback is a triple hit: the money is **pulled back** out of the account, a **fee** is added (often €15–20, indicative), and the response window is **short** (typically 7–21 days) — and most merchants never respond at all. That's revenue lost by default, not by decision. `qonto-chargeback-defender` turns a Qonto account into a defense desk:

1. **Open disputes detected** — via the Stripe/PayPal MCP when connected (reasons, amounts, real deadlines); otherwise by spotting clawback debits in Qonto transactions (labels dispute / chargeback / reversal, plus the paired fee)
2. **The debit found** — the clawback matched to the original incoming payment: full money trail, charge → payout → clawback → fee
3. **A sourced defense file** — Shopify order, proof of delivery when available, Gmail customer threads: every piece listed with its source; missing pieces listed with where to find them
4. **Accounting traceability** — with explicit consent, a dated synthesis memo is attached to the clawback transaction in Qonto (upload confirmed); the disputed debit carries its full story

Would someone use this on a Monday morning? A chargeback notification **is** the Monday morning email you dread — this turns it into a ten-minute task with a deadline you won't miss.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | Adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Universal**: chargebacks follow card-network and PSP rules, not national tax law — identical behavior for every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT) | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Stripe / PayPal MCP | Authoritative source for disputes and **deadlines**. Without it: honest Qonto-only mode (clawback detection + chronology + response checklist) — already useful | ⭕ recommended |
| Shopify · Gmail MCPs | File enrichment (order, tracking, customer threads) — detected dynamically, announced when absent | ⭕ |
| Payments through a PSP | Stripe, PayPal, Adyen, Mollie… that's where chargebacks are born | ✅ de facto |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Detect disputes**: Stripe/PayPal MCP when present (open disputes, reasons, real deadlines); otherwise scan Qonto transactions for clawback debits — `dispute` / `chargeback` / `reversal` labels, usually from a PSP counterparty, often paired with a same-day fee debit. The active mode is stated plainly
2. **Find the debit**: original incoming payment matched (amount ± fee, date window, counterparty via `get_transaction`), full chronology rebuilt. Card flows matched on `emitted_at`, not `settled_at`
3. **State the deadline**: the dispute's own evidence-due date, never loosely estimated; in Qonto-only mode, typical windows are given **explicitly as indicative** with a pointer to the portal. Disputes sorted by urgency
4. **Assemble the defense file**: evidence matched to the reason code (Shopify order, delivered tracking, Gmail threads, an already-issued refund found in Qonto), every piece **with its source**, missing pieces **listed with where to get them**
5. **Attach the memo** (explicit consent only): `request_attachment_upload` → upload → **confirmed via `list_transaction_attachments`** before success is reported
6. **You submit**: a response draft pre-structured like the PSP's form, ready to paste on the Stripe/PayPal portal before the deadline. The skill prepares — it never submits

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The integrity model**: the attached memo is a **dated synthesis document that cites the source pieces** (system · identifier · date · what each piece proves). It is not a receipt, not an invoice, not generated "proof" — no evidence is ever fabricated. The real evidence files are gathered and submitted by the user. That distinction is written into the memo itself.

## ⚖️ Dispute reasons × what wins

| Reason code | What wins | Where the skill finds it |
|---|---|---|
| Product not received | Proof of delivery / "delivered" tracking | Shopify (fulfillment + tracking) |
| Fraudulent / unrecognized | Matching billing-shipping addresses, returning customer, order history | Shopify + Stripe (charge details) |
| Product not as described | Product listing, customer threads, return policy offered | Shopify + Gmail |
| Duplicate / already refunded | **The refund already issued** — the strongest possible answer | Qonto (refund transaction) + Stripe |
| Subscription canceled | Cancellation date vs charge date, terms, threads | Stripe + Gmail |

## 🧪 Holds up on messy data

- No Stripe/PayPal MCP? → Qonto-only mode, stated plainly: clawback detection + chronology + response checklist
- No visible clawback line? → **Stripe often nets the dispute inside the next payout**: the skill flags unusually low payouts as candidates and recommends the Stripe MCP instead of guessing
- Missing piece (no tracking, no customer thread)? → listed as missing, with where to look — a checklist, not a shrug
- No disputes found? → the skill says so and never invents one
- Unknown deadline? → typical windows labeled indicative + explicit pointer to the portal

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: open disputes (urgency-sorted), money trail, evidence checklist ✅/⚠️ | **Always** — the baseline |
| **Defense memo** | Dated, sourced synthesis document, attached to the clawback transaction in Qonto | Per dispute, explicit consent only |
| **Response draft** | The argument restructured to match the PSP's response form, ready to paste | As soon as the dispute reason is known |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem (money pulled back + fee + deadline) → detection → a four-piece defense file, assembled and sourced → the memo attached to the transaction → "all that's left is to submit". The detailed shooting script is kept internal (out of the repo).

## 💡 Roadmap ideas

- Winnability hints per reason code (typical success rates) — helps prioritize when several disputes land at once
- Post-dispute follow-up: detect the re-credit when a dispute is won and close the memo
- Deadline reminders through a calendar MCP, detected dynamically
- Synergy with `qonto-shopify-bridge` (order-to-payout reconciliation) and `qonto-fraud-sentinel` (unusual debits as clawback candidates)

## 🛡 Guardrails

- **Never** fabricates evidence: the memo is a dated synthesis citing the originals — the distinction is written into the memo
- **Never** says "response submitted" or "dispute won": submission happens on the Stripe/PayPal portal, by the user
- Deadlines come from the dispute itself; generic windows are always labeled indicative
- Attachment upload only with explicit consent, reported as done only after `list_transaction_attachments` confirms it
- IBANs masked (last 4 digits) · pagination ≤ 50 everywhere · every example amount in these docs is invented

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML, FR/EN).*
