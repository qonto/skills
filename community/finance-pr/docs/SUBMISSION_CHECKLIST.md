# Submission checklist

## Definition of Done (from the brief)

- [x] One command starts the product (`npm install && npm run dev`).
- [x] Interactive **3-minute demo** works (guided auto-play + full controls).
- [x] Demo shows the real Finance PR solution (not generic invoice movement) —
      driven by the engine's own domain events via a pure reducer.
- [x] Viewer understands the product in ~10s (tagline, two zones, boundary gate).
- [x] Intent drift visibly blocked (Scenario C).
- [x] Changed-IBAN / document-injection visibly reviewed/blocked (B and C).
- [x] Clean case creates an immutable, hashed, fingerprinted Finance PR (A).
- [x] Exact proposal revalidated before crossing the boundary (Act; D1/D2/D3).
- [x] Qonto native approval clearly separate (boundary + captions + panel).
- [x] Synthetic mode fully functional with no credentials.
- [x] Sandbox reads use real discovered MCP contracts (mapper + verified round-trip).
- [x] Qonto writes disabled by default; **no write performed**.
- [x] Core tests (60), typecheck, and build pass.
- [x] No real sandbox values committed (`npm run scan:secrets` passes).
- [x] Attribution and limitations are honest (`ATTRIBUTION.md`, `KNOWN_LIMITATIONS.md`).
- [x] Skill usable from a fresh Claude Code session (`.claude/skills/finance-pr/`).
- [x] No unsupported fraud/safety/payment/Qonto-role claims.

## Files in the submission

- `README.md` — pitch, quickstart, safety chain, scenarios, architecture.
- `.claude/skills/finance-pr/` — the Claude Skill (SKILL.md + references).
- `src/` — engine, fixtures, UI, Node CLI.
- `tests/` — 60 deterministic tests.
- `docs/` — BUILD_DECISIONS, QONTO_TOOL_INVENTORY, ARCHITECTURE, DEMO_3_MINUTES,
  RECORDING_CHECKLIST, KNOWN_LIMITATIONS, THREAT_MODEL, RISK_SIGNAL_MAPPING, etc.
- `docs/screenshots/` — 6 captured stills.
- `ATTRIBUTION.md`, `SECURITY.md`.

## Verification commands

```bash
npm install
npm test              # 60 passed
npm run build         # typecheck + build OK
npm run scan:secrets  # privacy scan OK
npm run pr -- synth all
npm run dev           # demo at http://localhost:5173
```

## Remaining manual steps (require user action)

- [ ] Record the 3-minute video (see `docs/DEMO_3_MINUTES.md`).
- [ ] Commit / push / open PR to `qonto/skills` — **not done**; awaiting explicit
      user approval (per the working agreement, nothing was pushed or published).
- [ ] (Optional) If a suitable, explicitly-authorized controlled sandbox write is
      ever desired, implement a real write adapter and follow the per-object
      confirmation flow in `SECURITY.md`. Not implemented; no write performed.
