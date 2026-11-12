# Build decisions (Claude Code, execution owner)

Short synthesis of the Codex research into the smallest strong product we can ship
today. Codex docs are treated as research, not a contract.

## What we are building

**Finance PR for Qonto MCP** — turns every AI-proposed financial action into a
reviewable, evidence-bound change request before it reaches Qonto approval. One
vertical slice: **one supplier invoice → Observe → immutable Finance PR →
fingerprint approval → Act revalidation → Qonto boundary.**

## Biggest change from Codex: one TypeScript codebase

Codex implied Python backend + React frontend + SQLite. We ship **a single
TypeScript project (Vite + React + Vitest)** instead.

Why this is stronger today:

- **The engine is pure, I/O-free TypeScript** that runs *identically* in Node
  (CLI / Claude Skill) and in the browser (visual demo). This makes the
  invariant "the visual is driven by the same domain events the engine produces"
  literally true — the browser runs the real engine, not a replayed mock.
- **One command each**: `npm run dev` (demo), `npm test`, `npm run build`. A
  judge can run it in under a minute. No Python env, no two servers.
- Determinism is trivial to guarantee because the engine takes an injected
  `clock`; synthetic scenarios use a fixed clock so hashes/fingerprints/event
  times are stable and testable.

## Frozen MVP write: `ready_for_qonto` handoff (writes disabled)

We inspected the live sandbox (see `QONTO_TOOL_INVENTORY.md`). Findings that
freeze the decision:

- The two supplier invoices have `iban: null` and `available_actions.pay: false`
  with reason `missing_iban`. There is **no MCP tool that turns a supplier
  invoice into a payment request / native approval workflow.**
- `list_requests` returns **403** on this org (plan-gated), so the
  transfer-request workflow is not even readable here.
- The only supplier-invoice lifecycle write is `change_supplier_invoice_status`
  (reject / mark_as_paid), which merely records an out-of-band settlement — it is
  not "send to native approval," and mutating sandbox state contradicts the
  product framing.

Therefore **Act terminates at a verified `ready_for_qonto` handoff and all Qonto
writes remain disabled by default.** This is exactly the honest fallback the
constitution requires. The write adapter is a clean seam (`DisabledWriteAdapter`
default); the nearest real write (`create_multi_transfer_request`, which only
ever creates a *pending* request that still needs the user's own SCA) is
documented but never called. We do not invent an endpoint or fake a result.

## Kept from Codex

- The 5 MVP weighted signals and weights (possible_duplicate .30,
  supplier_iban_drift .30, unusual_amount .20, evidence_gap_risk .10,
  untrusted_instruction_indicator .10) + observed-only aggregate and separate
  coverage.
- The hard-gate list, split cleanly from risk (integrity/replay/state are gates,
  never score inputs).
- The event vocabulary and 10 lifecycle states from `VISUAL_DEMO_SPEC.md`.
- The four scenarios (A clean, B IBAN-drift, C document-injection/intent-drift,
  D tamper/stale/replay).
- `data_mode: synthetic | qonto_sandbox` stamped on every record; masking rules.
- `designated_approver` (never claim CFO/CEO are Qonto roles).

## Changed / simplified from Codex

- **Single codebase** (above).
- **Persistence**: no SQLite. Engine defines a small `PrStore` interface with a
  `MemoryStore` (browser/tests) and a Node `FileStore` whose one-shot reservation
  uses an atomic exclusive-create (`open ... "wx"`) marker — the same
  compare-and-set guarantee SQLite would give, with zero dependency.
- **Hashing**: `js-sha256` (MIT, sync, browser+Node) so canonicalize→hash is a
  pure sync function everywhere and verifiable against known vectors in tests.
- **Second model**: implemented as a deterministic, offline, escalate-only
  `HeuristicReviewer` behind a flag (no network, no Qonto tools). A networked
  OpenAI reviewer is left as a documented interface only.
- **Visual**: not ten flat cards in a row. A **spatial "Finance PR review floor"
  with a hard, lockable Qonto boundary gate** — a single invoice "PR packet"
  travels stations, dwells, and either gets stamped BLOCKED (gate stays locked)
  or clears Act revalidation (gate opens). Same events, stronger stage.

## Deliberately cut (per constitution cut-order)

- Real Qonto write execution (documented seam only).
- Networked OpenAI reviewer (offline heuristic stub instead).
- Extra signals (vendor reputation, budget, timing, geo, actor) —
  correlated / not Qonto-sourced / bias risk.
- Multi-invoice queue simulation and analytics.

## Three invariants — how we hold them

1. **Working product today**: `npm i && npm run dev` runs the full synthetic demo
   with no Qonto/model creds; `npm test` and `npm run build` pass.
2. **Interactive 3-minute demo**: "Run 3-minute demo" button auto-plays A→B→C→D
   with narrated beats, full transport controls, deterministic reducer.
3. **Safety chain**: intent authority ≠ document/tool text; Act reloads the
   stored PR and rejects chat-supplied parameters; hash/fingerprint/expiry/
   replay/stale/changed-field are gates a risk score can never override.
