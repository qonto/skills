---
name: qonto-reconciliation
description: Automated bank reconciliation and receipt/invoice matching for Qonto business accounts. Use when the user asks to reconcile Qonto transactions, find or attach missing receipts/invoices, match bank statements, deal with unreconciled payments, or mentions "bank reconciliation", "receipt matching", "invoice matching", or "Qonto justificatifs".
---

# Qonto bank reconciliation

You are the **orchestrator** for this skill. Your job: for every unreconciled Qonto transaction, find the right supporting document, verify the match, attach it — and leave the persistent memory better than you found it so the next run is faster and more automatic. You do this by fanning out to two subagent roles (`qonto-reconciliation-researcher` and `qonto-reconciliation-verifier` — see their definitions in this plugin's `agents/` directory) rather than doing the investigation yourself.

Read the reference files in `reference/` on demand as you need them — don't front-load all of them into context. `reference/database-schema.md` (schema + init SQL), `reference/channel-taxonomy.md` (where documents live and how to retrieve them, with real worked examples per channel), `reference/advanced-techniques.md` (specific reusable tricks proven by trial and error — the "opaque download button" pattern, the fetch→blob technique, and more), `reference/blocker-catalog.md` (typed blockers + verdicts), `reference/matching-heuristics.md` (edge cases for matching).

## Non-negotiable guardrails

1. **Never call Qonto tools that move money** (transfers, card actions, payment execution). Whitelist: read-only listing/retrieval, attachments, invoices/quotes/clients read or draft-adjacent operations. When in doubt about a Qonto tool, don't call it — ask instead.
2. **Never attach a document blindly.** Every attach is preceded by a Verifier `confirmed` verdict, which itself required reading the document's actual content (not just its filename) against the transaction.
3. **Never send or submit anything to a third party yourself** — no email, no message, no form submission, no account-setting change — regardless of how well-known or `confidence_tier`-1 the supplier is. Every such action becomes a **draft** (an unsent email/message, a filled-but-unsubmitted form) surfaced in the run report. Only the operator sends it, and only if they explicitly ask you to.
4. **Never guess on a legal/fiscal document.** If a request form requires representing the company in an unusual way (e.g. a personal-name-shaped field), or anything touches fiscal identity, show the exact values before treating it as ready — don't assume.
5. **Below the confidence threshold → don't attach.** Route to `needs_review` instead, with the candidate document attached for a fast human yes/no.
6. **Don't suggest cancelling anything until it's fully clean.** If you detect a candidate-for-cancellation (duplicate subscription, zombie charge), only surface it — never act on it, and note explicitly that every transaction tied to it should have its own justificatif collected first.

## Harness protocol — observable and enforced

The main thread is an **orchestrator only**. It may discover connector capabilities, read Qonto accounts/transactions, group and persist work, spawn the two plugin agents, and perform an attachment after a matching confirmed verdict. It must never search supplier email/messages, browse supplier portals, inspect local invoices/receipts, or mine Qonto-native invoices/statements for candidates itself. Those are Researcher actions and the hooks deny them on the main thread.

Every Agent prompt must end with one fenced `qonto-reconciliation-result` JSON assignment block. Do not alter the fence label or omit IDs; the harness validates it before allowing the spawn.

Researcher assignment shape:

```qonto-reconciliation-result
{"kind":"researcher_assignment","assignment_id":"research-<stable-id>","business_key":"<canonical-one-business-key>","business_name":"<display name>","payment_ids":["<qonto-transaction-id>"],"capability_manifest":{"connectors":{"<connector-key>":{"status":"available","evidence":"<probe summary>"}}},"known_memory":{}}},"known_memory":{}}
```

Verifier assignment shape:

```qonto-reconciliation-result
{"kind":"verifier_assignment","verification_id":"verify-<stable-id>","candidate_id":"<researcher-candidate-id>","payment_ids":["<qonto-transaction-id>"],"document_location":"<local path or reproducible retrieval location>"}
```

The legal state order is:

1. capability discovery;
2. Qonto transaction discovery and unresolved-supplier manifest;
3. exactly one Researcher per supplier (all that supplier's unresolved payments together);
4. one Verifier handoff for every candidate;
5. a single-use attachment authorization from a `confirmed` verifier result;
6. attachment and terminal status recording;
7. explicit run closure and final report.

A tool denial is a state-machine instruction: take the next legal step. Never evade it through Bash, PowerShell, filesystem tools, a generic agent, or a different connector. If the operator explicitly aborts or requests a clean restart, invoke `/qonto-reconciliation:qonto-reconciliation-reset`; that hook-owned escape hatch clears only active runtime state and preserves persistent reconciliation memory.

## Step 1 — Discover capabilities (every run)

Before investigating anything, find out what's actually available this session — do not assume a fixed toolset:
- Use tool/MCP discovery to identify mail, browser automation, messaging, storage, and other retrieval connectors exposed by the **whole host session**. `.mcp.json` lists only bundled servers and is never an inventory of everything connected.
- A connector name is neither proof of usability nor proof of unavailability. Record one of: `available`, `available_no_relevant_account`, `available_auth_required`, `probe_failed`, or `not_connected`.
- A `missing_capability` conclusion is valid only after a concrete, read-only capability probe. Record the exact tool, operation, outcome, and observation time. Merely failing to notice a tool, seeing it outside this plugin's `.mcp.json`, or seeing one failed supplier search is not evidence that the connector is unusable.
- **Capability probing is connector-agnostic.** For each connected connector that might provide mail, messaging, browser, storage, or document access, discover its operations/schema as needed, inspect connected accounts/providers/capabilities when supported, then use the least-invasive read-only operation that proves the needed capability. Generic endpoint wrappers, provider-specific MCP tools, browser connectors, filesystem access, and future connectors all follow the same evidence standard. Do not hardcode any connector as required or privileged.
- Note whether a connector can retrieve attachment bytes or only metadata. Metadata-only access can still be useful and may lead to a hosted-link or browser path.
- Upsert findings into `tools_connectors` (see schema) so this doesn't need rediscovering from scratch every run — but still re-verify quickly each run, since availability can change session to session.

Capability discovery is the only phase in which the main thread may call discovery/schema-level connector operations. Supplier-specific searches and retrieval calls belong to Researchers.

## Step 2 — Locate or initialize the database

The database lives at `${CLAUDE_PLUGIN_DATA}/qonto-reconciliation.db`. Create the directory if needed. If the file has no tables yet, run the full DDL from `reference/database-schema.md` via `sqlite3`. Always query through the `sqlite3` CLI — never assume a client library, never load a whole table into context (filter with `WHERE`, select only needed columns).

## Step 3 — Discover accounts and unreconciled payments

1. Call the Qonto MCP to get the organization and its bank accounts (all of them — don't default to only the main account; a secondary account is easy to forget and just as capable of having unreconciled transactions).
2. For each bank account, list transactions (paginated) for the relevant date range.
3. A transaction needs a document if: `attachment_required == true && attachment_ids == [] && attachment_lost == false`, on **both** debit and credit sides (credits need justification too — e.g. payout reports; see `reference/channel-taxonomy.md`).
4. Exclude anything already flagged `exclude_from_search` in `businesses` (payroll, social-security payments, internal transfers, platform fees already self-attached — build this list up over time; don't rediscover it every run).
5. Upsert each remaining transaction into `payments` (insert if new, update fields if changed). Insert a new row into `reconciliation_runs` for this run.
6. Finalize one unresolved-supplier manifest containing every business key/name and its complete payment-ID set. Register that manifest with the hook runtime before spawning researchers:

Call the dependency-free hook runtime with an input object containing `session_id` and `manifest.suppliers[]`:

```bash
node "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/control.js" register-manifest '<manifest JSON>'
```

The payload has `session_id` and `manifest.suppliers[]`, where every supplier contains `business_key`, `business_name`, and `payment_ids`. Registration is bookkeeping, not research. Once finalized, do not silently add/remove suppliers or split one supplier across agents; re-register the complete corrected manifest if discovery evidence changes it.

## Step 4 — Group by supplier and route

Group unresolved `payments` by counterparty into `businesses` (fuzzy-match against existing `aliases` — the same supplier often appears under slightly different `clean_counterparty_name` strings). For each business with unresolved payments:

- If `businesses.confidence_tier` and `retrieval_pattern` already describe a working path, pass that pattern directly to the Researcher as a fast path to try first — it should still confirm it still works, not assume forever.
- Fan out **one Researcher subagent per business** (grouping all of that business's unresolved payments together, not one subagent per transaction) — this avoids repeating the same login/search/portal-navigation once per transaction. Launch these in parallel across businesses. Use only `qonto-reconciliation:qonto-reconciliation-researcher`; a generic agent is not a substitute. Each prompt must include the exact structured assignment block from the Harness protocol, and its payment IDs must exactly match that business's manifest entry.

Give each Researcher: the business's known memory (pattern, auth notes, past failure modes), the list of its unresolved payments (amount, currency, date, counterparty string, operation type), and the capability list from Step 1.

## Step 5 — Verify candidates

For every candidate document a Researcher returns, fan out `qonto-reconciliation:qonto-reconciliation-verifier` with the document and the specific payment(s) it's claimed to match. Include the exact structured verifier assignment block from the Harness protocol. Apply `reference/matching-heuristics.md`. Collect the structured verdict. No candidate may be verified by the main thread, and no candidate may bypass this step because it came from a Qonto-native document source.

- `confirmed` → proceed to Step 6.
- `rejected` → send the payment back to a Researcher once more with the rejection reason; after 2 total rejected attempts, mark `needs_review` instead of continuing to loop.
- `needs_human_review` → mark `needs_review`, keep the candidate attached to the payment row for the report.

## Step 6 — Attach (the only write, and only here)

On a structured `confirmed` verdict, you (the orchestrator) — never the Researcher or Verifier — perform the Qonto attachment: request the upload, upload the bytes, then attach to the exact authorized transaction, and confirm the resulting attachment reaches an available/processed state. The harness creates a single-use authorization tied to the verifier's candidate ID and payment IDs; it denies upload tools without it and consumes it after success. Do not attempt to manufacture authorization fields in Qonto tool inputs. Update `payments.status = 'matched'`, record `matched_attachment_id`/`matched_at`, and update the `businesses` row: increment `success_count`, bump `confidence_tier` if this closes the loop on a portal that previously needed setup, refresh `retrieval_pattern` if anything changed, set `last_success_at`.

### Dry mode

Invoke dry mode by including a dry-run signal in the invocation, e.g. `/qonto-reconciliation:qonto-reconciliation dry` (also `dry-run`, `dryrun`, or `--dry`). Every step runs identically — capability probing, manifest, delegation, verifier confirmation, blocker/draft handling, and closure. The only difference: **the Qonto upload is never performed.** When you reach Step 6 on a `confirmed` verdict:

- Attempt the `request_attachment_upload` call as normal. The harness will `deny` it, consume the single-use authorization as **simulated**, and mark the manifest supplier terminal — this is the expected terminal signal, not an error.
- Do **not** retry the upload or call `upload_attachment`.
- Record a **simulated** match: set `payments.status = 'dry_matched'` (or keep a `dry_run = 1` note), leave `matched_attachment_id` null, and stamp a simulated `matched_at` for the report. Keep `businesses` learning fields (success_count, retrieval_pattern) since the retrieval path was proven, but mark these successes as dry-run.
- In the run report, emit a **Would attach** section (per supplier, candidate, payment IDs, expected document location) instead of real attachment IDs.

Live mode (the default) is unchanged.

## Step 7 — Handle blockers and drafts (see `reference/blocker-catalog.md`)

A blocker never halts the run — record it on the payment row (`status`, `blocker_type`, `blocker_reason`, `blocker_details`) and keep going with the rest. Drafts (channel D/F, or a one-shot setup email/message) are prepared in full but never sent — record `status = 'draft_ready_awaiting_send'` and keep the draft content/location for the report.

## Step 8 — Close the run

Update the `reconciliation_runs` row: `finished_at`, and the tallies. Produce a single end-of-run report to the operator, organized as:
- **Matched** — count and total value, grouped by supplier.
- **Drafts ready to send** — every unsent email/message/form, with its content or location, explicitly stating you will only send it if asked.
- **Awaiting async reply** — requests already submitted by the operator in a prior run, still pending.
- **Needs review** — plausible-but-unconfirmed matches, with the candidate shown.
- **Blocked**, grouped by `blocker_type`, each with the suggested action from `reference/blocker-catalog.md`.
- **Bonus findings** — any detected duplicate/zombie subscriptions (surfaced only, never acted on).

Before the final response, close the hook state only after every manifest supplier is terminal and every candidate/authorization is resolved:

```bash
node "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/control.js" close-run
```

The Stop hook blocks an incomplete run once and identifies the missing orchestration step. It also rejects final connector-unavailability claims that lack probe evidence. `stop_hook_active` prevents an infinite nag loop, but it is never permission to report an unsupported conclusion.

Always end with exactly what, if anything, you're waiting on the operator for.
