# Implementation plan for Claude Code

## 1. Delivery strategy

Build the safety-critical path before the visual polish. The order below is a gate sequence: do not start a later phase until the phase exit criteria are met.

Target: one supplier invoice, one Finance PR, one approval, one revalidation, and at most one allowlisted Qonto sandbox mutation.

## 2. Proposed implementation shape

Claude Code should confirm this after Qonto tool discovery:

```text
mcp_skills/
  CLAUDE.md
  README_en.md
  README_ru.md
  docs/
  finance_pr/                  # small Python package, deterministic core
    models.py
    intent.py
    evidence.py
    signals.py
    policy.py
    integrity.py
    store.py
    events.py
    report.py
    cli.py
  skills/
    finance-pr/
      SKILL.md
      references/
  policies/
    default.yaml               # or JSON if no YAML dependency is justified
  scenarios/
    synthetic/
  visual/
    src/
  tests/
  submission/
  ATTRIBUTION.md
```

The exact Claude Skill location must follow the installed Claude Code version's documented convention. Do not create two competing copies.

## 3. Phase 0 — Qonto MCP discovery

**Label: MVP / Qonto requirement.**  
**Why:** every adapter and Act claim depends on the real authenticated tool contract.  
**Hackathon fit:** one focused inspection pass.

Tasks:

1. List the available Qonto MCP tools and classify read/write.
2. Record exact input schemas, output fields, pagination, statuses, and errors.
3. Run read-only sandbox calls for authenticated membership, organization, supplier invoices, requests, and transactions.
4. Identify whether supplier invoice detail/history, attachment metadata, matched transactions, IBAN, available actions, native approval state, and `updated_at` are present.
5. Identify the narrowest safe write that routes a supplier invoice into a Qonto request/approval flow; record idempotency and SCA semantics.
6. If no appropriate write exists, explicitly set MVP Act outcome to `ready_for_qonto` and do not invent one.
7. Save a redacted tool-surface inventory in implementation docs; never commit live IDs/data.

Exit criteria:

- Read inventory is confirmed from actual tool calls.
- Exact MVP write action is selected or formally marked unavailable.
- No write has been called.

## 4. Phase 1 — Freeze contracts and policy

**Label: REIMPLEMENT / MVP.**  
**Origin:** new Finance PR design.

Tasks:

1. Define typed schemas for evidence, signals, gates, immutable PR body, integrity envelope, approval, execution, and events.
2. Define state transition tables and reject illegal transitions.
3. Define critical Qonto fields from Phase 0.
4. Define the exact default policy: thresholds, required evidence, minimum score coverage, high-value route, expiry, and allowlisted action.
5. Define canonical JSON rules and fingerprint format.
6. Create synthetic Green, changed-IBAN, prompt-authority, tampered, stale, and replay fixtures.
7. Add a data-mode and redaction contract.

Exit criteria:

- Schemas can represent all acceptance scenarios without free-form business fields.
- Weighted signals and hard gates are disjoint.
- No unknown state is encoded as zero risk/pass.

## 5. Phase 2 — Deterministic Finance PR core

**Label: MVP.**  

Implementation order:

1. Schema validation and decimal/IBAN/date normalization.
2. Authority-aware intent gate.
3. Evidence availability and conflict evaluation.
4. Hard gates.
5. Weighted signals and coverage.
6. Policy decision.
7. Deterministic human report.
8. Canonical hash/fingerprint.
9. SQLite immutable store and append-only events.
10. CLI commands for synthetic `observe`, `prepare`, `show`, `approve`, and dry-run `act`.

Port concepts, not source code. Do not implement vendor reputation, budgets, timing/geo, dashboards, PostgreSQL, or WebSockets.

Exit criteria:

- All synthetic core tests pass.
- Re-preparing identical frozen input yields the documented canonical body/hash behavior.
- Attempted body update is rejected.
- Reports are redacted and deterministic.

## 6. Phase 3 — Approval and Act gate

**Label: REIMPLEMENT / MVP; safety critical.**

Tasks:

1. Parse or record explicit approval with PR ID and fingerprint.
2. Validate reviewer route without inventing Qonto roles.
3. Implement expiry and policy-version checks.
4. Recompute full hash.
5. Accept no caller-supplied action payload.
6. Inject a Qonto reread adapter and compare critical state.
7. Implement atomic one-shot reservation in SQLite.
8. Implement dry-run write adapter first.
9. Define definite failure versus ambiguous result; forbid hidden retry.
10. Keep real writes behind two controls: configuration flag and explicit current-turn user confirmation.

Exit criteria:

- Missing approval, wrong fingerprint, tamper, expiry, stale amount/IBAN/status, action mismatch, and replay all block before adapter invocation.
- Concurrent Act attempts invoke the adapter at most once.
- Dry-run event log is complete.

## 7. Phase 4 — Claude Skill and sandbox reads

**Label: MVP / Qonto requirement.**

Tasks:

1. Write a concise Skill that enforces Observe -> Prepare -> Act.
2. Include exact tool-use rules discovered in Phase 0.
3. Separate the literal user message from tool/document evidence.
4. Map sandbox reads to engine evidence.
5. Default to synthetic mode when sandbox evidence is missing or when the user asks for a demo.
6. Render the PR and approval syntax in chat.
7. Refuse direct Qonto writes outside the Act gate.
8. Add an honest limitation that the Skill is not a global MCP proxy.

Exit criteria:

- A new Claude Code session can follow the Skill without hidden context.
- Observe and Prepare tool transcripts contain only read calls.
- The same core tests run without Qonto access.

## 8. Phase 5 — Optional independent model

**Label: ROADMAP / optional MVP.**  
Implement only if Phases 0–4 and their tests are complete.

Tasks:

1. Provider-neutral reviewer interface and disabled-by-default flag.
2. Strict sanitized input builder and output schema.
3. Trigger rules for ambiguity, high value, or language/action disagreement.
4. Merge logic that only preserves/increases review.
5. Timeout/unavailable/malformed tests.

Exit criteria:

- Model sees no Qonto tools or secrets.
- Agree cannot lower deterministic output or satisfy a gate.
- Unavailability fails safely.

## 9. Phase 6 — Dynamic visual demo

**Label: SIMPLIFY / MVP.**  
**Origin:** clean reimplementation of FlowTwin patterns.

Tasks:

1. Create React/Vite shell with a small dependency set.
2. Import the shared event schema or generated type contract.
3. Implement pure reducer and deterministic playback cursor.
4. Build ten state cards and Qonto boundary.
5. Add invoice tokens, stable transitions, dwell, selection panel, controls, scenario shortcuts, and summary.
6. Generate scenario event fixtures by running the Finance PR core; do not hand-author contradictory status data.
7. Add accessibility, responsive layout, and reduced motion.
8. Add visible synthetic/sandbox provenance.

Exit criteria:

- Event replay exactly matches engine terminal results and summary.
- Reset/replay makes zero Qonto calls.
- The boundary and Green language pass acceptance tests.

## 10. Phase 7 — Controlled sandbox write

**Label: optional MVP validation.**  
Run only after explicit user authorization for the exact test Finance PR and only if Phase 0 found an appropriate safe sandbox write.

Preflight:

- dedicated synthetic/sandbox test object;
- exact PR/fingerprint displayed;
- writes flag off until the final step;
- expected Qonto native status documented;
- no retry plan;
- read-based reconciliation plan;
- cleanup/decline path documented if Qonto supports it.

Record one result honestly as successful, failed, native-approval-pending, or unknown. Do not broaden from one controlled test into batch execution.

## 11. Phase 8 — Tests and submission

Tasks:

1. Run unit, integration, security, visual reducer, accessibility, and build tests.
2. Scan committed artifacts for IBANs, emails, opaque live IDs, tokens, and temporary URLs.
3. Produce architecture and threat diagrams, demo script, screenshots, short video plan, and pitch.
4. Add `ATTRIBUTION.md`, dependency licence report, and known limitations.
5. Ensure all sandbox/synthetic claims are labelled.
6. Prepare submission materials without publishing until authorized.

## 12. Time-box and cuts

Cut in this order if time is short:

1. Optional second model.
2. Real sandbox write (keep dry-run Act and sandbox reads).
3. Multiple invoice tokens (retain one hero invoice plus recorded adversarial scenarios).
4. Advanced animation and analytics.

Never cut:

- intent authority gate;
- immutable hash/fingerprint;
- explicit bound approval;
- fresh-state comparison;
- expiry/replay protection;
- unknown-data semantics;
- Qonto boundary language;
- redaction and synthetic labels;
- tests for all hard gates.

## 13. Exact implementation order summary

1. Qonto tool inventory.
2. MVP action freeze.
3. Schemas/state machine/policy/event vocabulary.
4. Synthetic fixtures.
5. Deterministic gates and signals.
6. Hash, fingerprint, immutable SQLite store, report.
7. Approval binding and Act dry run.
8. Fresh Qonto reread and replay protection.
9. Claude Skill and sandbox read adapter.
10. Optional second model only if core is green.
11. Event-driven visual demo.
12. Optional explicitly approved sandbox write.
13. Full acceptance/security suite.
14. Attribution and submission materials.

