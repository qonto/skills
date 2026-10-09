# 💸 qonto-reimburse-batch — N reimbursements, one approval

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> Every claim is verified (receipt · card duplicate · expense policy) before it enters **one grouped transfer request** — approved in a single SCA gesture. *All examples in this doc are invented.*

---

## 🎯 Why this matters (usefulness)

Teammates pay out of pocket — client dinners, taxis, small gear — and the reimbursement sits in a spreadsheet for weeks. Nobody enjoys chasing it, nobody enjoys checking it. `qonto-reimburse-batch` does both:

1. **Collects the claims** — from a Slack expenses channel or a Notion base when that MCP is connected; otherwise pasted straight into the conversation or as a markdown table. The core stays 100 % Qonto
2. **Three checks per claim** — receipt present and consistent (amount/date) · not a duplicate of a company-card expense already in the account (`list_transactions`, transaction cited) nor of a past reimbursement · expense policy respected (per-category caps you define)
3. **ONE grouped request** — the N validated claims become a single `create_multi_transfer_request`: N pending transfers, IBANs taken from the claims (never invented)
4. **One-gesture SCA approval** — the owner gets a push notification and approves the whole batch with their own 2FA in the Qonto app; money moves **only** there

Would someone use this on a Monday morning? It's literally the end-of-month expenses ritual — minus the spreadsheet.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Universal (SEPA)**: reimbursements are EUR SEPA transfers — every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT). Non-SEPA IBAN or non-EUR claim → on hold, stated plainly | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Employee IBANs | Provided by the claims or a user-maintained employee sheet — the skill **never** invents an IBAN; a claim without one stays on hold | ✅ |
| Expense policy | Per-category caps (meals, taxi, equipment…) you define once; no policy → the skill says so and runs the other checks | ⭕ recommended |
| Slack or Notion (MCP) | Claims source, detected dynamically; otherwise **degraded mode**: claims pasted in the conversation | ⭕ optional |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Collect the claims**: Slack (expenses channel) or Notion when the MCP is present, otherwise pasted in the chat. Each claim is normalized — employee, amount, date, category, reason, IBAN, receipt — and the normalized table is shown before any check
2. **Check the receipts**: present + amount and date consistent with the claim; missing or mismatched → ⚠️ on hold, never silently corrected or dropped
3. **Hunt duplicates**: `list_transactions` scans company-card spend around the claim date (**`emitted_at` ±5 days** — cards settle 1–2 days late): same amount, counterparty close to the claim's merchant → ❌ **documented presumption**, transaction cited (date · amount · counterparty). Recent outgoing transfers are scanned too, so a claim can't be reimbursed twice
4. **Apply the expense policy**: each claim against your caps; over cap → flagged with the gap, three ways out: cap it, accept it, reject it — you decide
5. **One grouped request** (explicit consent on the final list only): a single `create_multi_transfer_request` — one transfer per employee, readable reference like "NDF 2026-07 — client dinner", batch summary in the request note (visible at approval time)
6. **SCA approval**: Qonto push → the owner approves all N transfers **in one gesture** with their own 2FA → final report: who gets paid back, how much, and why any claim was set aside (evidence attached)

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The security model** (not a limitation): solid arrows are risk-free reads; the dashed arrow requires explicit consent given in the conversation and only produces a *request*. The account holder's own SCA (2FA) in the Qonto app is what moves money. Neither Claude nor the MCP can.

## 🧪 Holds up on messy data

- Free-text Slack messages, half-filled Notion rows? → normalized first, the skill asks only for what's genuinely missing
- No Slack or Notion MCP? → says so once, continues with claims pasted in the conversation — the checks and the batch are unchanged
- Missing receipt, amount mismatch, missing IBAN? → ⚠️ on hold with the exact reason; the rest of the batch ships anyway
- Card settlement delays (`emitted_at` vs `settled_at`), same-amount coincidences → duplicate findings are cited presumptions, never silent verdicts
- Claimant not in `list_memberships`? → flagged, not blocked (contractors exist)
- Non-EUR or non-SEPA claim → excluded from the batch and stated plainly, never guessed around

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: verdicts (claim · checks · verdict), batch content, holds | **Always** — the baseline |
| **Grouped Qonto request** | N pending transfers in the Requests section, batch summary in the note (visible at SCA approval) | Every validated batch |
| **Reimbursement report** | Markdown recap — or an HTML artifact when the host renders files; automatic fallback to tables | After approval (status checked via `list_requests`) |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem → claims collected & checked → the verdicts (one duplicate rejected, with the cited card transaction as proof) → **the one-gesture SCA approval filmed on a phone** → the final report. All claims in the demo are invented.

## 💡 Roadmap ideas

- Verdict posted back into each claim's Slack thread (when the Slack MCP is present)
- Post-execution reconciliation — tick off the outgoing transfers against the batch (reuses the "NDF" references)
- OCR on attached receipts (amount/date extracted automatically) — strengthens check #1 on messy data
- Per-team caps via `list_teams` — different policies for sales, tech, management
- Monthly accounting export of reimbursements — pairs with `qonto-accountant-handoff`

## 🛡 Guardrails

- NEVER creates the transfer request without explicit confirmation of the final list in the current conversation; never presented as executed — it is pending the user's SCA approval
- A duplicate is a **documented presumption** (transaction cited), never a silent rejection — the user decides
- No failed claim enters the batch without an explicit user override (recorded in the note)
- IBANs never invented; masked (last 4 digits) in every output · pagination ≤ 50 everywhere
- Rehearsals: `decline_request` afterwards (`request_type: "multi_transfers"`, plural)

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML, FR/EN).*
