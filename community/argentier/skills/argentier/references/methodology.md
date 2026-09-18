# Argentier — methodology & architecture

Two diagrams (open in a browser; no real data, safe to share):

- [`schema-macro.html`](schema-macro.html) — the macro architecture: sources,
  the loop, the guardrails, the human gate.
- [`schema-workflow.html`](schema-workflow.html) — the runtime workflow:
  Qonto → Claude (labels) → `engine.py` (€) → dashboard → deliverables → gate.

## The four non-negotiable rules

1. **Read-only Qonto** — only read tools; every write tool hard-blocked (`deny > allow`).
2. **`engine.py` computes, never the model** — every euro is deterministic and auditable.
3. **Zero PII to the web** — benchmarks send only a merchant name + category.
4. **Every price = source + date** — or it's labelled "not verified". Never invented.

## The two brains

- **Claude labels.** For each merchant it returns a *label set*: nature
  (pilotable / structurel / ponctuel / perso), area, action, and a saving
  *ratio* — never an amount.
- **`engine.py` computes.** Deterministic maths: recurrence detection,
  annualization (monthly × 12; a one-off is **never** annualized), duplicate
  detection (same merchant, same day → one-off recovery), FX-fee aggregation,
  run-rate, and each euro of saving (`monthly × ratio`).

## The engine's rules (see `../engine.py`, tested in `../tests/`)

- **Recurrence** = a merchant seen ≥ 2× over 90 days at a similar amount.
- **Annualization** = monthly × 12, applied *only* to real recurring subscriptions.
- **Duplicate** = 2 charges from the same merchant on the same day → one-off
  recovery, never annualized.
- **FX** = Qonto FX fees (`qonto_fee` + `fx_card`) aggregated into one lever.
- **EI accounts** (personal + business mixed) → every spend classified
  **PRO / PERSO / A-CLARIFIER**; when in doubt, A-CLARIFIER.

## Why this wins trust

A bank cannot ship an agent that hallucinates numbers or moves money. Argentier
answers both: the numbers are deterministic and reproducible, and the agent is
read-only and never sends. It prepares; you decide; `/verify` proves the result.
