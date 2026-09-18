# 🗂 qonto-approval-brief — Instruct every team request like a CFO, before you approve

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> Read-heavy, one write (`decline_request`, always confirmed) — **the skill cannot approve: approvals stay in the Qonto app, behind your own SCA. By design.**

---

## 🎯 Why this matters (usefulness)

Team transfer and card requests pile up in Qonto — and the owner approves half-blind, or three days late. Every request deserves five minutes of digging; nobody has them. `qonto-approval-brief` does a CFO's instruction work on every pending request:

1. **Beneficiary history** — paid N times before? usual amounts? cadence? A 3rd identical payment isn't judged like a first-ever transfer
2. **IBAN signal** — seen before in the account's history (reassuring, dated) or never seen (**a vigilance signal, not an accusation**)
3. **Coherence & context** — amount vs habit (×4 → strong flag), budget/label fit, the quote found in Gmail when that MCP is connected
4. **One decision brief per request** — ✅ recommended / 🔶 verify, every claim citing its evidence; motivated declines via MCP (confirmed), **approvals in the Qonto app with your own 2FA**

Sample brief lines (invented): "✅ recommended: 3rd identical payment to this provider" · "🔶 verify: never-seen IBAN, amount ×4 the usual".

Would someone use this on a Monday morning? Monday morning is exactly when the weekend's request pile is waiting.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Universal** — the instruction relies on the account's own history, not national rules; works for every Qonto country (FR, DE, ES, IT…) | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| A role that reviews requests | Owner/Admin/Manager: pending requests must be visible — otherwise `list_requests` comes back empty and the skill says which case it is | ✅ |
| Pending requests | Otherwise nothing to instruct — the skill says so and stops cleanly | ⭕ |
| A few months of history | Below that, every payee looks "new" — the skill announces it and degrades honestly | ⭕ |
| Slack · Gmail (optional MCPs) | Digest and email context — detected dynamically, never required | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Inventory the pending requests**: `get_organization` then `list_requests` (paginated ≤ 50) — transfers, multi-transfers, cards — with requester (`list_memberships`), beneficiary, amount, reason, date
2. **Beneficiary history**: `list_transactions` over 12–24 months, counterparty spellings normalized and merged — paid N times before? amounts? cadence?
3. **IBAN signal**: the request's IBAN compared to IBANs seen in past outgoing transfers — seen before (dated) or never seen (vigilance, not accusation; direct check with the requester recommended, by phone, not by replying to the invoice email)
4. **Coherence & context**: amount vs the historical median (×2 flag, ×4 strong), recent duplicate cited, labels/team (`list_labels`), the Gmail quote cited when that MCP is present — otherwise the skill says so and continues
5. **Decision briefs**: one per request, ✅ recommended / 🔶 verify, every claim sourced — recommendation ≠ decision, the owner decides
6. **Motivated decline · SCA approval**: declines via `decline_request` (confirmed, reason attached, visible to the requester); **approvals happen in the Qonto app with your own 2FA — the skill cannot approve**

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The security model** (not a limitation): solid arrows are risk-free reads; the dashed arrow is a **motivated decline only**, requiring explicit confirmation in the conversation. Approval doesn't exist in this skill: `approve_request` is **never** called. Approving = the Qonto app + your own SCA (2FA). Nothing this skill does can move a euro.

## 🧪 Holds up on messy data

- No pending requests? → says so and stops — nothing invented
- Empty `list_requests` because of the role? → says exactly that instead of pretending "all clear"
- Short history? → every payee looks "new"; the skill announces the degradation instead of crying wolf
- Same supplier under three spellings (caps, accents, abbreviations)? → normalized and merged into one counterparty
- Card requests carry no IBAN → the brief adapts: requested limits vs the team's usual card spend
- Gmail or Slack MCP absent → said once, then the core continues on Qonto data alone

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Brief table + one expanded brief per 🔶 request + the explicit next step | **Always** — the baseline |
| **Brief board** | **HTML** file/artifact: one card per request, verdict and evidence | When the host renders files; automatic fallback to tables otherwise |
| **Decline reason** | Text attached to the decline via `decline_request`, visible to the requester in Qonto | Every decline (confirmed) |
| **Slack digest** | Brief summary posted to the channel of your choice | When a Slack MCP is connected (optional) |

## ⚡ The "it just works" moment

4 pending requests → **4 sourced briefs in 30 seconds**; decline the dubious one in a word, approve the other 3 in the app in 20 seconds — instead of 20 minutes of digging. (Invented example.)

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the request pile → the sourced briefs → the dubious request (never-seen IBAN, ×4 the usual) declined in one word → **the approvals in the Qonto app, behind SCA, filmed on a phone** → wrap-up. All demo requests are invented.

## 🤝 Companion skills

- **qonto-fraud-sentinel** — watches *past* transactions; `qonto-approval-brief` instructs *future* requests: two sides of the same vigilance
- **qonto-reimburse-batch** — *creates* grouped reimbursement requests; this skill then *instructs* them like any other pending request

## 💡 Roadmap ideas

- Learned approval policy (per-category/label thresholds) — briefs become "within / outside policy"
- Supplier-invoice matching (`list_supplier_invoices`) — a request backed by its invoice is one more cited proof
- Scheduled daily Slack digest — optional multi-MCP, detected dynamically
- Memory of past verifications — an IBAN checked once with the requester becomes "known"

## 🛡 Guardrails

- **Recommendation ≠ decision**: every brief cites its evidence; the skill never says "approved" or "safe" — it says "recommended, because…"
- **Never** declines without explicit confirmation in the current conversation; the reason always travels with the decline (the requester sees it)
- "Never-seen IBAN" is a **signal, not an accusation** — phrased that way in every brief
- The skill **never approves**: `approve_request` is not used — approving = the Qonto app + your own SCA
- Masked IBANs (last 4 digits) · pagination ≤ 50 everywhere · short history announced · invented examples labelled as such

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
