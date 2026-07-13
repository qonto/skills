# Blocker catalog — typed, never silent

A Researcher that cannot complete a payment must yield one of these typed blockers rather than a generic "failed" or, worse, silence. The type drives what the orchestrator puts in the end-of-run report and what action it suggests.

| `blocker_type` | Meaning | Suggested action to surface |
|---|---|---|
| `login_required` | No authenticated session exists for this supplier's portal and no credential is available to establish one. | One-shot human login; once done, this supplier moves to auto (confidence_tier 2). Real trigger: dev-tool/SaaS accounts (their own separate auth domain), note-taking apps normally used via a desktop client rather than the browser, some outreach/podcast-hosting tools. |
| `missing_capability` | A capability the researcher needs (e.g. a browser-automation tool, a specific connector) is not available in this session. | Name exactly what's missing and why it's needed (e.g. "no browser-control tool connected — needed to navigate this portal"). |
| `print_only_needs_fuller_browser` | The receipt is only renderable via a native print dialog; the available browser tool can't produce a real file from it. | Needs a fuller browser-automation capability (programmatic PDF rendering, e.g. a Playwright-style `page.pdf()`), or a one-off human capture in the meantime. Real trigger: a domain registrar's order-receipt modal, some subscription-payment activity views. |
| `window_open_escapes_control` | The portal opens a new tab/window the automation tool doesn't control, losing the session. | Needs a browser tool that controls all tabs, or one human click. Real trigger: an AI chat product's "manage subscription" button opening its Stripe billing portal in an uncaptured new tab. |
| `netted_fees_no_1to1_invoice` | The transaction is a processor fee netted into a payout; no per-transaction invoice exists. | Don't search further for a 1:1 document — locate the periodic fee/payout report instead (see channel-taxonomy.md). Real trigger: a payment processor's own fees on a ticketing/marketplace account, described in-product as fees "absorbed into the plan" rather than billed per charge. |
| `supplier_evasive` | The supplier was asked and responded but denies an invoice exists (despite a legal obligation to issue one in many jurisdictions). | Escalate with a firmer follow-up referencing the legal invoicing obligation, or request a manual confirmation/receipt on letterhead. Draft only — never sent automatically. Real trigger: an AI-tool vendor's support telling the requester "no invoice exists for these one-off top-ups, only for the subscription" — the correct response is citing the invoicing obligation and asking for manual generation, not accepting the first no. |
| `unknown_transaction_nature` | Nobody (including the operator, if asked) can identify what this transaction actually is. | Needs operator input on the nature of the transaction before any document search makes sense. |
| `awaiting_async_delivery` | Not really a blocker — a request (channel D/F) has been submitted and a reply is expected. | No action needed; the next routine run re-checks channel A automatically. Real trigger: an airline's invoice-request-by-form flow — reply can arrive within hours, well before any stated SLA. |
| `draft_ready_awaiting_send` | Not a blocker — a draft (email/message/filled form) is ready but intentionally not sent/submitted per the no-autonomous-send guardrail. | Surface the draft content/location for the operator to review and send themselves. |
| `no_invoice_legally_required` | The transaction is not a supplier purchase at all (payroll, a legal settlement, an internal transfer) — no invoice should be sought. | Mark `excluded`, record `excluded_reason`, and add the counterparty to `businesses.exclude_from_search` so future runs skip it instantly. Real triggers: salary/payroll runs, social-security payment carbon-copies, internal account-to-account transfers, an employee severance settlement — all justified by payroll/HR documents, not a supplier invoice. |
| `ambiguous_form_needs_review` | A request form requires representing the company through a personal-name-shaped field, or otherwise touches legal/fiscal identity in a way not yet validated for this supplier. | Show the exact filled values to the operator before any submission — never guess on a legal/fiscal document. Real trigger: an airline's invoice-request form has no business/individual toggle, but its personal-tax-ID field validates a company registration number — a workable mapping exists, but must still be shown before submitting, every time it's new. |

## Verifier verdicts

The Verifier never blocks in this sense — it always returns one of three verdicts to the orchestrator:

- `confirmed` — amount, date (within the learned tolerance window), currency/FX, and counterparty line up; safe to attach.
- `rejected` — wrong document; include a precise reason (wrong amount, wrong period, wrong counterparty) so the orchestrator can send the Researcher back with concrete guidance rather than a bare "try again."
- `needs_human_review` — plausible but below the confidence threshold (e.g. a scanned document with only partial metadata match). Surfaced in the end-of-run report with the candidate attached for a quick human yes/no, never auto-uploaded.

## Loop bound

If a Verifier `rejected`s a candidate, the orchestrator gives the Researcher one more attempt with the rejection reason. After 2 rejected attempts total for the same payment, stop looping and mark `needs_review` instead — an unbounded retry loop is itself a failure mode.
