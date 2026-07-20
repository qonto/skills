---
name: qonto-reimburse-batch
description: Batch expense reimbursement for teams on Qonto. Collects employee expense claims from a Slack channel or Notion base (optional — pasted claims work too), verifies each one (receipt present and consistent, no duplicate of a company-card expense or of a past reimbursement, expense policy respected), then builds ONE grouped transfer request — N pending transfers the owner approves in a single SCA gesture in the Qonto app. Use for "rembourse les notes de frais de l'équipe", "process this month's expense claims", "pay back my team's expenses", "did we already pay this by card?", "reimburse everyone in one go".
---

# Qonto Reimburse Batch

Collect the claims, audit every single one, pay everyone back in one approval. Read-heavy, one safe write: the skill verifies and prepares; only the user's SCA approval in the Qonto app moves money.

## Prerequisites
1. `get_organization` first → `bank_account_id`/`iban` of the main account (required by `list_transactions`), balance, country. `list_memberships` → known team members; a claimant matching no membership is flagged, not blocked (contractors exist).
2. **Claims source — detect, don't require**: if a Slack MCP is present, read the expenses channel (e.g. `#notes-de-frais`); if a Notion MCP is present, query the claims database. Neither? Degrade cleanly: claims pasted in the conversation or as a markdown table (employee · amount · date · category · reason · IBAN · receipt). The core — verification + grouped batch — is **100 % Qonto** and works in all three modes.
3. **Employee IBANs** come from the claims themselves or from a user-maintained employee sheet. NEVER invent, guess or "complete" an IBAN; a claim without one goes ⚠️ on hold.
4. **Expense policy**: per-category caps defined by the user (meals, client meals, taxi, equipment…). No policy defined → say so, run the other checks anyway, never invent caps.
5. **Country: universal.** Reimbursements are SEPA transfers in EUR — works for every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT). Non-SEPA IBAN or non-EUR claim → on hold, stated plainly.

## Workflow

### 1. Collect and normalize the claims
From the detected source (Slack / Notion / conversation). Normalize each claim into: employee, amount, currency, expense date, category, reason/merchant, IBAN, receipt (present? amount and date on it?). Show the normalized table before any check — messy inputs (free-text Slack messages, half-filled Notion rows) are expected; ask only for what's genuinely missing.

### 2. Check the receipts
Receipt present, amount matching the claim, date plausible (receipt date consistent with the expense date). Missing or mismatched → ⚠️ **on hold** with the exact reason; never silently corrected, never silently dropped.

### 3. Hunt duplicates — the anti-double-pay pass
Two duplicate classes, both against real account data:
- **Already paid by company card**: `list_transactions` on the claim-date window, paginated `per_page: "50"`. Cards settle 1–2 days late, so match on **`emitted_at` ±5 days** (not `settled_at`), same amount, counterparty/label similar to the claim's merchant or reason. Match → ❌ presumed duplicate, **cite the transaction** (date · amount · counterparty).
- **Already reimbursed**: scan recent outgoing transfers — same IBAN or same amount with a reimbursement-style reference in the last months.

A duplicate is a **documented presumption, not a verdict**: show the evidence, the user decides.

### 4. Apply the expense policy
Compare each claim to the user's caps per category. Over cap → ⚠️ flagged with the gap; three options offered: cap the reimbursement at the ceiling, accept the excess, or reject. Same logic for a per-employee period total if the user set one.

### 5. Build ONE grouped request — only with explicit consent
Present the **verdict table** (✅ in batch / ⚠️ on hold + what's missing / ❌ rejected + cited evidence). After the user explicitly confirms the final list: a **single** `create_multi_transfer_request` — `debit_iban` = main account; one transfer per validated claim with `credit_iban` (exactly as provided), `credit_account_name`, **`credit_account_currency`** (422 if omitted), `amount`, `currency`, `reference` like "NDF 2026-07 — client dinner" (readable for the employee's bank statement AND it feeds future already-reimbursed checks). Put the batch summary in the request **note** — the approver sees it at approval time.
Then tell the user plainly: **a push notification and the Requests section of the Qonto app now hold ONE pending request covering all N transfers; nothing moves until they approve with their own SCA.** One gesture approves the whole team's reimbursements. That's the security model, not a limitation.

### 6. Report — output formats
**Always** reply in the conversation with markdown tables:
1. **Verdict table** (claim · checks passed · verdict), every ❌ carrying its cited transaction.
2. **Batch content** (employee · amount · reference) + total, IBANs masked (last 4 digits).
3. **Holds** with exactly what unblocks each one.
On demand after approval, `list_requests` to confirm the request status, then a final who-got-what recap. When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code), optionally generate an HTML recap; otherwise the tables are the deliverable — say nothing about it.

## Guardrails
- NEVER create the transfer request without explicit confirmation of the final list in the current conversation; never present it as executed — it is pending the user's SCA approval.
- Never put a claim that failed a check into the batch unless the user explicitly overrides — and record the override in the request note.
- Duplicates are presumptions with cited transactions, never silent rejections.
- IBANs never invented; masked (last 4 digits) in every output. Paginate everything (`per_page` ≤ 50).
- In rehearsals, `decline_request` afterwards (`request_type: "multi_transfers"`, plural).
- No Slack/Notion MCP detected → say so once and continue in conversation mode.
