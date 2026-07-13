# Qonto Bank Reconciliation (Claude Code plugin)

Automated bank reconciliation and receipt/invoice matching for Qonto business accounts. For every unreconciled transaction (debit or credit), it researches every available channel — email attachments, hosted links, web portals, local files, web search — finds the right supporting document, verifies the match, and attaches it via the Qonto MCP. Learns supplier-specific retrieval patterns over time in a local, persistent database so each run gets faster and more automatic than the last.

No demo video or Loom is provided: a real reconciliation run investigates every unresolved supplier end-to-end (capability probing, per-supplier research, verification, attachment) and can easily take 30 minutes to an hour depending on how many suppliers are unresolved, so a recording wouldn't be a practical way to show it.

## Why this exists

Every quarter, a Spanish SME's accountant needs a supporting document for every debit transaction before the VAT filing deadline (the 15th of the month after each trimester) — Qonto flags each one `attachment_required: true` and only issues its legally-binding PAdES version once a document is attached. Nobody attaches these as transactions happen, so it piles up silently: on one real account (218 transactions in a quarter), 63 debits had no supporting document by the time anyone looked.

The reason this is painful isn't finding *some* documents — it's that every supplier hides its invoice behind a different mechanic. A PDF buried in a Gmail attachment. A Stripe-hosted link that expires after three weeks (but the same email still has it as an attachment). A portal you have to log into and click "download by period." A print-only receipt with no downloadable file at all. A freelancer who hasn't issued an invoice yet and has to be asked. A paper taxi receipt that only exists as a photo. Multiply that by dozens of suppliers, each with their own quirks (a charge in USD settled in EUR, one invoice covering two separate debits, a portal that opens the real download in an uncontrolled browser tab), and reconciling a quarter by hand is hours of repetitive, easy-to-get-wrong clicking — every quarter, forever, with real fiscal risk if the deadline is missed. Doing this manually on one real account, with an agent assisting a human step by step, still took several sessions to go from 63 missing documents down to 26.

This plugin encodes that manual playbook into something repeatable and self-improving: it works out which retrieval channel a supplier's document actually lives behind, sends a dedicated researcher after exactly one supplier at a time so one investigation can't bleed into or corrupt another, verifies every candidate document against the real transaction (amount, date, currency, counterparty) before ever attaching anything, and remembers what worked per supplier — so next quarter's run is faster and more automatic than this one, the same way a human doing this by hand gets faster once they've learned where each supplier's invoice lives. The difference is that it's enforced by a state machine instead of held together by one person's memory of "oh right, that one needs the portal."

## Installation

Zip this plugin's folder (`qonto-reconciliation/`) and upload it in Claude Desktop to install it.

## What's in this plugin

- `skills/qonto-reconciliation/` — the orchestrator skill (`SKILL.md`) plus reference material (`reference/`) covering the retrieval-channel taxonomy, a typed blocker catalog, matching heuristics/edge cases, and the database schema.
- `agents/researcher.md` — subagent role that investigates a single supplier across all available channels until it finds a document or hits a genuine, typed blocker. Full tool access (including any connected MCP — mail, messaging, browser automation), with Qonto write/money tools explicitly blocked.
- `agents/verifier.md` — subagent role that verifies a candidate document against a transaction. Full tool access, with Qonto write/money tools explicitly blocked; never uploads or modifies anything, by instruction.
- `.mcp.json` — bundles the official Qonto MCP server (`https://mcp.qonto.com/mcp`, OAuth). Other host/session connectors still count and are discovered dynamically. Capability checks are connector-agnostic: provider-specific tools, generic endpoint wrappers, browser tools, storage connectors, and future MCPs all follow the same evidence rules.
- `hooks/hooks.json` + `hooks/scripts/harness.js` — a dependency-free Node state machine that enforces capability discovery, one researcher per supplier, verifier-before-attachment, single-use upload authorization, structured handoffs, and run-completeness checks.

## Guardrails (see `SKILL.md` for the full list)

- Never calls Qonto tools that move money (transfers, cards, payments) — read/attachment/invoice tools only.
- Never attaches a document without a verified match.
- **Never sends or submits anything on your behalf** — no emails, no messages, no form submissions, ever, regardless of how well-known a supplier is. Everything that would need to go out is prepared as a draft and surfaced to you to send yourself.
- Never guesses on legal/fiscal documents — shows exact values before treating anything as ready if company identity is involved.
- Detects (but never acts on) potential duplicate/zombie subscriptions as a bonus finding.

## Enforced orchestration

When the skill is explicitly invoked, plugin hooks activate a state machine under `${CLAUDE_PLUGIN_DATA}/runtime/current/`. This state is global, not scoped per session — do not run the reconciliation skill from more than one session at a time.

1. The main thread probes available connector capabilities and discovers unresolved Qonto transactions.
2. It registers the complete supplier/payment manifest.
3. It spawns exactly one plugin Researcher per supplier; the main thread is denied supplier email, portal, local-file, web, and Qonto-native document research.
4. Every returned candidate goes to the plugin Verifier with stable IDs and actual document-content evidence.
5. Only a matching `confirmed` verdict creates a single-use Qonto attachment authorization.
6. Stop is blocked once if delegation, verification, attachment, or run closure is incomplete.

Researcher and verifier final responses use fenced `qonto-reconciliation-result` JSON contracts so the harness validates observable evidence rather than trusting prose. `missing_capability` requires a concrete probe of every relevant connected option. No connector is required or privileged: each is classified using its own discovery/schema, connected-account/provider capabilities, and a least-invasive read-only check where supported.

The guardrails control observable tool calls and structured outputs; no hook can inspect private model reasoning. Unsupported connector claims made only in prose are therefore checked again at Stop. Harness failures fail closed for active-run phase/attachment integrity but fail open outside an active reconciliation run.

## Reset or restart a stuck run

If a session is interrupted or intentionally abandoned while work is pending, use:

```text
/qonto-reconciliation:qonto-reconciliation-reset
```

This hook-owned escape hatch deactivates and removes only the current run's `${CLAUDE_PLUGIN_DATA}/runtime/current/` state. It preserves `qonto-reconciliation.db`, learned supplier patterns, prior run history, and document memory. After resetting, invoke the normal reconciliation skill to begin a clean run.

Do not manually delete the database merely to escape the Stop hook. Database erasure is a separate destructive operation and is intentionally not performed by the reset skill.

## Dry mode

Run the full reconciliation workflow — capability probing, payment discovery, supplier grouping, researcher delegation, verifier confirmation, blocker/draft handling, and closure — **without ever uploading a document to Qonto**. Append a dry-run signal to the invocation:

```
/qonto-reconciliation:qonto-reconciliation dry
```

(`dry-run`, `dryrun`, and `--dry` also work.) In dry mode the harness lets every step through identically, but on a `confirmed` verdict it `deny`s the Qonto upload call, marks the authorization **simulated**, and advances the supplier to a terminal state — so the run closes cleanly with no network write. The final report should show a **Would attach** section (supplier, candidate, payment IDs, document location) instead of real attachment IDs. Live mode (the default) is unchanged.

## Persistent memory

State lives in `${CLAUDE_PLUGIN_DATA}/qonto-reconciliation.db` (SQLite), local to your machine, and survives plugin updates. It tracks reconciliation runs, per-transaction status, learned per-supplier retrieval patterns, and discovered tool/connector capabilities — all initialized automatically on first run.

## Requirements

The host needs Node.js (used by Claude Code and the hook harness), the `sqlite3` CLI for reconciliation memory, and a `pdftotext`-equivalent for document verification. The harness has no npm/pip dependencies.

After changing `hooks/`, `agents/`, `.mcp.json`, or the plugin manifest, run `/reload-plugins` or restart Claude Code. Skill markdown changes are immediate, but those cached plugin components are not. Validate a checkout with:

```bash
claude plugin validate ./skills/qonto-reconciliation --strict
node --test ./skills/qonto-reconciliation/hooks/tests/harness.test.js
```

Harness diagnostics are written to `${CLAUDE_PLUGIN_DATA}/runtime/current/harness.log`. Do not edit runtime state or the reconciliation database while a run is active; the main-thread tool guard blocks this by design.
