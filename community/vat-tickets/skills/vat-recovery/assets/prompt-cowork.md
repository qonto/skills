# ⛔ OBSOLETE — DO NOT USE, DO NOT READ FOR GUIDANCE

This file taught the **doctrine rejected in the meeting on 13/07/2026**. It was
emptied because it was the single worst risk in the project: a file that
proclaimed itself the "source of truth" while contradicting `SKILL.md` on three
points, two of which are now **hard prohibitions**.

## What it said, and why it was wrong

| Old version (wrong) | Doctrine in force |
|---|---|
| "~25,80 € **probable**" | The words "**probable**"/"**likely**" are **FORBIDDEN** — an indefensible statistical claim. `build_tickets.py` raises an exception on them. Required format: "**Up to X € — if your invoice carries French VAT.**" |
| "scratch = **launch the vision agent**, load time accepted" | **REJECTED.** All vision is done **at collection time**. Opening a card = **instant** reveal of an already-established verdict. A wait on click kills the dopamine — and didn't tackle the real problem. |
| "`SCRATCH <id>` → the interface sends an orchestration message" | **IMPOSSIBLE.** A Cowork artifact **cannot write into the conversation** (verified by test). |
| "copy `scratch-interface.jsx` into an artifact" | Artifacts are **not JSX**. The interface is **`assets/board.html`**. |
| "FIRM / POTENTIAL" counters | **SECURED / LOCKED**. |

It also ignored the `fix` status, the "dead cards don't open" rule, and the ban
on a countdown over a potential.

## Where the truth is, now

- **`CLAUDE.md`** (project root) — the orchestration prompt to paste into the
  Cowork project. **Single source of truth.**
- **`SKILL.md`** — the tax doctrine and the game layer.
- **`assets/board.html`** — the interface.
- **`scripts/build_tickets.py`** — the factory: it is the CODE, not a prompt,
  that guarantees the invariants.
