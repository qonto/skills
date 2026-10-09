# 🧾 qonto-receipt-hunter — Zero missing receipts: the receipt hunter

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> Every business has a drawer of shame: transactions with no receipt. This skill empties it — it finds the gaps, hunts the originals down in Gmail and Drive, and attaches them.

---

## 🎯 Why this matters (usefulness)

Roughly one transaction in five is missing its receipt. Every one of them is recoverable VAT left on the table, a deduction at risk, and a question your accountant will ask. `qonto-receipt-hunter` turns the chore into a hunt:

1. **Prioritized inventory** — transactions missing a receipt (`attachment_ids` empty + `attachment_required`), ranked by urgency: recoverable VAT at stake, amount, age — tagged 🔴 urgent · 🟠 soon · 🟢 low
2. **Hunt across connected sources** — Gmail (merchant + amount + date window around `emitted_at`) and Google Drive, detected dynamically
3. **Confirmed attaching** — the match is shown (transaction ↔ original document), you confirm, then `request_attachment_upload` + `upload_attachment`; never in bulk
4. **Hunt report** — attached ✅, found-to-attach 📎, not found ❌ with one concrete lead each (merchant portal, secondary inbox, Qonto's native auto-collection, supplier duplicate) + completeness score before/after

**The guardrail that matters most**: the skill attaches **originals only** (merchant PDFs, email attachments). It never generates or reconstructs a receipt — a fabricated document has zero probative value and is a tax-audit liability.

Would someone use this on a Monday morning? It's the end-of-month chore everyone postpones — now it runs itself while you watch the receipts snap into place.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Works for every Qonto country.** The 20/120 VAT-ceiling estimate applies to France only; elsewhere only tagged `vat_amount` is used — rates are never guessed | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Gmail MCP | Powers the email hunt. Absent: the skill says so and still delivers the prioritized inventory + where to look | ⭕ recommended |
| Google Drive MCP | Powers the file hunt | ⭕ optional |
| Scope | Last 90 days by default — widen (quarter, fiscal year) on request | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Inventory the gaps**: paginated scan (≤ 50) of all transactions; a gap = `attachment_ids` empty + `attachment_required` true + `attachment_lost` false. Client payments and not-required transactions are set aside — they never pollute the score
2. **Rank by urgency**: recoverable VAT at stake (`vat_amount`, else a disclosed ceiling estimate), amount, age. Headline: "X missing receipts, ~Y € of recoverable VAT at stake"
3. **Hunt Gmail**: merchant name variants + amount + a date window around **`emitted_at`** (not `settled_at` — card payments settle 1–2 days late), with amount tolerance (tips, foreign currency, partial captures)
4. **Hunt Google Drive**: PDFs by merchant/date/amount, candidate downloaded and read before anything is proposed
5. **Confirmed attaching**: coherence check (merchant, amount, date), match shown, explicit confirmation **per receipt**, then `request_attachment_upload` → `upload_attachment` → verified with `list_transaction_attachments`
6. **Hunt report**: ✅ / 📎 / ❌ with leads, completeness score before/after

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The security model**: solid arrows are risk-free reads; the dashed write **only adds a document to a transaction** — it never touches money — and requires explicit per-receipt confirmation in the conversation. Above all: **originals only** — the skill locates and transports existing documents, it never creates one.

## 🧪 Holds up on messy data

- Merchant label garbled ("SUMUP *COFFEE PARIS")? → name variants from `clean_counterparty_name` and the raw label, retried merchant-only if the amount misses
- Amount doesn't match the email? → disclosed tolerance handles tips, foreign-currency conversion and partial captures
- Card settled two days after purchase? → the hunt window is anchored on `emitted_at`, the actual purchase date
- Connector can't pull an email attachment binary? → the skill hands you the exact email pointer for a one-drag manual attach — and says so instead of pretending
- No Gmail/Drive MCP at all? → the Qonto-only core still delivers: prioritized inventory + VAT at stake + where to look
- Non-French organization? → no invented VAT rates; untagged amounts reported as "VAT unknown"
- Several plausible matches? → the skill asks, it never guesses

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (prioritized inventory, VAT at stake, hunt report) | **Always** — the baseline |
| **Qonto attachments** | Real attachments on the transactions, visible immediately in the Qonto app | On every confirmation |
| **Completeness report** | Before/after score + remaining leads; **HTML** version when the host renders files (claude.ai artifacts, Claude Desktop, Claude Code), tables otherwise | End of session |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem → the prioritized inventory (7 missing receipts, VAT at stake quantified) → the live Gmail hunt → **5 receipts found and attached, one click each** → the final report with leads for the remaining 2. It runs live on a real production account.

## 💡 Roadmap ideas

- Gmail draft emails asking suppliers for duplicates (drafts only — the user sends)
- Monthly ritual: completeness score tracked month over month (streak)
- More mailboxes (Outlook/M365) detected dynamically — same hunt logic, different MCP
- Duplicate-attachment cleanup (`remove_transaction_attachment`, behind the same confirmation guardrails)
- Fine-grained amount/VAT verification by reading the PDF (multi-line invoices, currencies)

## 🛡 Guardrails

- **NEVER fabricates a receipt**: no generated PDFs, no reconstructed invoices, no doctored screenshots — with no original, the transaction stays ❌ with a lead
- Never attaches without explicit confirmation of the displayed match; several plausible candidates → it asks; no silent batches, ever
- Matches on `emitted_at` with a disclosed amount tolerance
- Absent Gmail/Drive MCPs announced plainly — the Qonto-only inventory ships anyway
- IBANs and card numbers masked · pagination ≤ 50 everywhere

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
