---
name: qonto-reconciliation-reset
description: Force-reset an abandoned or stuck Qonto reconciliation harness run while preserving the persistent reconciliation database. Use when a reconciliation Stop hook keeps reporting incomplete assignments, the operator asks to abort/restart/clean the current run, or before deliberately starting over.
---

# Reset Qonto reconciliation runtime

This is the supported escape hatch for an abandoned, interrupted, or stale reconciliation run.

Run exactly:

```bash
node "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/control.js" reset-run
```

The command removes only the active session's hook runtime directory under `${CLAUDE_PLUGIN_DATA}/runtime/`. It does **not** delete `${CLAUDE_PLUGIN_DATA}/qonto-reconciliation.db`, learned supplier patterns, document history, or prior reconciliation records.

After it succeeds:

- State clearly that the active harness run was aborted/reset.
- State clearly that persistent reconciliation memory was preserved.
- Do not automatically start a new reconciliation unless the operator asked you to restart it.
- If the operator requested a fresh run, invoke `/qonto-reconciliation:qonto-reconciliation` normally after the reset.

Never advise the operator to manually delete hook-owned runtime files or the reconciliation database merely to escape a Stop hook. Database deletion is a separate destructive operation and is not part of this reset skill.
