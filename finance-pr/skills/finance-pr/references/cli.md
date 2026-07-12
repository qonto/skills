# Finance PR CLI reference

Run from the repo root. All commands are local and offline (except the Qonto
reads you do yourself via MCP). Qonto writes are disabled in every path.

```
npm run pr -- synth [A|B|C|D1|D2|D3|all]
    Run a synthetic scenario through the real engine and print the report.
    A  = clean invoice → ready_for_finance_review → (synthetic) reaches Qonto
    B  = changed IBAN + elevated amount → manual_review_required
    C  = question + document injection → blocked before Finance review
    D1 = tampered stored PR → integrity_failed
    D2 = stale Qonto state → stale
    D3 = replay → replay_blocked

npm run pr -- map --bundle bundle.json [--out evidence.json]
    Map raw Qonto MCP JSON (read-only) into typed evidence. data_mode=qonto_sandbox.

npm run pr -- prepare --evidence evidence.json [--request "..."]
    [--source user_chat|document] [--pr FPR-1] [--store DIR]
    [--policy trusted-policy.txt|.json]
    Build the immutable Finance PR. Prints the report + fingerprint + approval line.
    Persists to DIR (default .finance-pr).
    --policy loads an EXPLICITLY TRUSTED operator policy file (never invoice text).
      Typed keys only (any other line throws; compile NL to these first, then ratify):
        currency, hard_block, role.<name>, block_supplier, block_supplier_id,
        fx.<FROM>.<TO> (operator-FROZEN rate, bound into the PR hash — never live).
      Over a role limit → "policy breach" signal → manual review.
      Over the hard block → within_trusted_policy_hard_limit gate fails → blocked.
      Blocked supplier (structured supplier_name/id) → supplier_not_blocked gate → blocked.
      Foreign currency converts ONLY via a frozen fx rate; otherwise not_applicable.

npm run pr -- act --pr FPR-1 --approval "Approve Finance PR FPR-1, fingerprint XXXX-YYYY"
    [--fresh fresh_supplier_invoice.json] [--store DIR]
    Reload → re-hash → re-read → expiry/replay → one-shot. Terminal: ready_for_qonto.

npm run pr -- show --pr FPR-1 [--store DIR]
    Print the stored PR (JSON).
```

## Decisions

- `ready_for_finance_review` — all Prepare gates pass, coverage ≥ 80%, no material
  signal. Still needs an explicit fingerprint approval, then Qonto approval + SCA.
- `manual_review_required` — gates pass but coverage is low, or IBAN drift /
  high value / a material signal routes to a reviewer.
- `blocked` — a hard gate failed (e.g. advice-not-action, document tried to
  authorize, already paid, completed duplicate).

## Act outcomes

`ready_for_qonto` (cleared to reach Qonto) · `integrity_failed` · `stale` ·
`expired` · `replay_blocked` · `blocked` · `execution_unknown` (ambiguous write,
never retried).
