---
name: qonto-approval-brief
description: Approval copilot for pending team requests in Qonto. Reads every pending transfer, multi-transfer and card request, then instructs each one like a CFO would — beneficiary payment history (paid N times before? usual amounts?), IBAN seen-before or never-seen signal, amount vs habit, budget/label coherence, optional email context — and delivers one evidence-cited decision brief per request (✅ recommended / 🔶 verify). Declines with a stated reason after explicit confirmation; approvals always stay in the Qonto app behind the owner's own SCA — the skill cannot approve, by design. Use for "brief me on my pending requests", "should I approve this transfer request?", "which requests are safe to approve?", "instruis mes demandes en attente", "je peux approuver cette demande de virement ?".
permissions:
  mcp:
    qonto: [approve_request, decline_request, get_organization, list_labels, list_memberships, list_requests, list_supplier_invoices, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto Approval Brief

Team requests pile up; owners approve half-blind or three days late. This skill does a CFO's instruction work on every pending request and hands back decision briefs. Read-heavy, one write (`decline_request`, always confirmed). Approving is deliberately left to the Qonto app + the owner's SCA — that's the security model, not a limitation.

## Prerequisites
1. `get_organization` first → accounts (`bank_account_id`/`iban`, required later by `list_transactions`), organization name, country.
2. The connected user must be able to review team requests (Owner/Admin/Manager). If `list_requests` comes back empty, say which it is: no pending requests (good news) or no visibility (role) — never pretend "all clear".
3. **Universal**: the instruction relies on the account's own history, not on national rules — works for every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT…).

## Workflow

### 1. Inventory the pending requests
`list_requests` (pending), paginate `per_page: "50"`. For each request capture: type (transfer, multi-transfer, card), requester, beneficiary name + IBAN, amount, reason/note, date. `list_memberships` → map the requester id to a name and role. Zero pending requests → report it and stop cleanly; nothing to instruct.

### 2. Instruct each request (the CFO pass)
Build the evidence per request:
- **Beneficiary history**: `list_transactions` on the debited account, 12–24 months, `per_page` ≤ 50. Normalize the counterparty (case, accents, merged spellings — the same supplier shows up under several graphies) and count past payments to that name: how many, which amounts, what cadence. A 3rd identical payment to a known provider is not judged like a first-ever transfer.
- **IBAN signal**: compare the request's IBAN to IBANs seen in past outgoing transfers. Seen before → reassuring; say when it was last paid. **Never seen → a vigilance signal, not an accusation** — a new supplier is normal exactly once. Recommend a direct check with the requester (by phone, not by replying to the invoice email — the classic invoice-fraud vector).
- **Amount vs habit**: ratio against the beneficiary's historical median. ×2 → flag; ×4 → strong flag, both numbers shown.
- **Duplicate check**: same beneficiary + same amount already paid in the last ~10 days → possible double payment, cite the transaction (date, amount).
- **Budget / label coherence**: `list_labels` + the requester's team — does this kind of counterparty usually come from this requester or label? Soft signal only, never decisive alone.
- **Card requests carry no IBAN**: instruct on the requester instead — requested limits vs the team's usual card spend from history.
- **Context (optional MCP)**: if a Gmail MCP is connected, search the counterparty name → a quote or thread found is cited (subject, date). Not connected → say so once and continue: the core works on Qonto data alone.

### 3. Deliver one decision brief per request
Two verdict levels — **✅ recommended** / **🔶 verify** — and every claim cites its evidence (dates, amounts, counts). Example lines (invented): "✅ recommended: 3rd identical payment to this provider, same amount since March" · "🔶 verify: never-seen IBAN and amount ×4 the usual". **Recommendation ≠ decision**: the owner decides, always.

### 4. Decline — only with explicit consent
If the owner decides to refuse: `decline_request`, with the motivated reason attached — the requester sees the refusal and its reason in Qonto, so write it for them. ⚠️ Verified trap: for a multi-transfer request, `request_type` must be `"multi_transfers"` (**plural**). NEVER decline without explicit confirmation in the current conversation.

### 5. Approvals — deliberately NOT this skill
`approve_request` exists on the MCP; this skill **never calls it**. Policy: approving means moving money, and that belongs to the Qonto app with the owner's own SCA (2FA) — push notification → Requests → approve. The skill's job ends at the brief. Nothing this skill does can move a euro, and that's the argument to state plainly when asked.

### 6. Report — output formats
**Always** reply in the conversation with markdown:
1. **Brief table** (request · requester · beneficiary · amount · verdict · key evidence).
2. One expanded brief per 🔶 request (full evidence, suggested verification).
3. The next step spelled out: "decline X here (I will ask you to confirm) — approve the rest in the Qonto app with your 2FA."

**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): an HTML brief board, one card per request with its verdict and evidence. When a Slack MCP is connected: an optional digest to the channel of the user's choice. Host can't render / MCP absent → the markdown tables are the deliverable; say nothing about missing extras.

## Guardrails
- **Recommendation ≠ decision**: every brief cites its evidence; the skill never says "approved" or "safe", it says "recommended, because…".
- NEVER decline without explicit confirmation in the current conversation; the reason always travels with the decline.
- "Never-seen IBAN" is a **signal, not an accusation** — phrase it that way in every brief.
- The skill never approves: no `approve_request`, ever. Approvals = Qonto app + the owner's own SCA.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50). Short history → say every payee looks "new" and degrade honestly. All examples are invented and labelled as such.
