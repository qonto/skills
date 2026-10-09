# Methodology — how the numbers are computed

**Deterministic by design: there is no AI in the matching.** The language
model narrates; every figure comes from plain Python over the raw Qonto data.
Same input, same output, fully auditable — run the scripts yourself and diff.

## Definitions

| Term | Meaning |
|---|---|
| Open receivable | Client invoice with status `unpaid`, for the residual amount |
| Open payable | Supplier invoice not `paid`/`rejected`/`archived`, for its payable amount |
| Frozen working capital | Open receivables + open payables: cash that moves only if everyone pays everyone |
| Net position (per counterparty) | Open credit − open debit toward that counterparty |
| Bilateral offset | `min(open credit, open debit)` toward one counterparty |
| Clearing cycle | Closed chain A→B→C→A of debts; settleable up to the minimum edge |

## Normalization rules (build_ledger.py)

1. **Counterparty identity = normalized VAT number.** Uppercased, separators
   stripped, EU country prefix removed (`IT01982340992` ≡ `01982340992`).
   Name spelling variants and OCR typos (e.g. `CLOUDTALIA` vs `CLOUDITALIA`)
   collapse into one counterparty when the VAT matches; all variants are kept
   in `name_variants` for transparency. Italian VAT check digits are
   validated and reported (`vat_check_digit_valid`).
2. **Only open positions count.** `paid` / `canceled` client invoices and
   `paid` / `rejected` / `archived` supplier invoices are excluded; `draft`
   client invoices are excluded too (not yet legally issued).
3. **Partial payments.** Supplier side: Qonto's `payable_amount` is used
   directly. Client side: Qonto has no residual field, so an explicit note
   `residuo EUR <x>` (any case, `€` accepted) in the invoice items, header,
   footer or terms overrides the open amount; a `paid_amount` field, when
   present, is subtracted. Everything else counts at face value.
4. **Aging buckets** are computed on the due date against the `--as-of` date
   (default: today): `current`, `1-30`, `31-60`, `61-90`, `>90` days overdue.
5. **Money is exact.** All arithmetic uses decimal types, two places,
   half-up rounding. Output amounts are strings to avoid float drift.
6. **Deterministic ordering.** Counterparties sort by absolute net position
   (descending), then VAT. Matches and cycles sort by amount (descending).

## Bilateral detection (detect_offsets.py)

A counterparty with `open_credit > 0` **and** `open_debit > 0` yields an
offset of `min(credit, debit)`. Nothing subtler than that — by design. The
result is immediately actionable: statutory set-off between reciprocal,
liquid, collectable money debts (see `legal_basis.md`) or a voluntary
set-off agreement for everything else.

## Multilateral preview (simulate_network.py)

Plain depth-first search enumerates the simple cycles of the provided debt
graph; a cycle settles up to `min(edge amounts)`, and the script reports each
edge's post-clearing balance. Edges marked `"simulated": true` represent
debts between third parties that the organization **cannot see in its own
Qonto data**; any cycle containing one is flagged `contains_simulated_edges`
and must be presented as a what-if. Production multilateral clearing over
real, verified network data runs server-side in the Nexyzen clearing engine —
the algorithm is not part of this public skill.

## Privacy (submit_to_nexyzen.py)

Ledger rows leave the machine only on explicit request, and a typed
confirmation by the user on their own terminal. They go to Nexyzen, a service
operated by Camera di Compensazione S.r.l., not by Qonto, with VAT numbers in
clear: the engine matches companies by VAT number, so without them it cannot
find cycles. That includes the VAT numbers, invoice numbers and amounts of
the user's counterparties. There is no hashed or anonymous mode on purpose:
VAT numbers are public, so a hash is trivially reversible and would only
suggest a protection that does not exist. Credentials live in environment
variables, never in files. Network requests use only the fixed Nexyzen HTTPS
API; redirects and destination overrides are not supported. The engine only
*detects* offsets — no payment is ever initiated, on Qonto or anywhere else.

## Timing: submission is on-demand, matching is not

There is no scheduler in this skill: `submit_to_nexyzen.py` only runs when
the user asks for it (or agrees when it's proposed). But sending is not the
same as matching — the clearing engine's own cycle-search runs on its own
weekly cadence over the weekend, so a submission made any day of the week
only shows up in the following Monday's results. `check_compensations.py
list` can be called anytime; before then it will simply show nothing new.

## Known limits

- Client-invoice residuals rely on the `residuo EUR x` convention or a
  `paid_amount` field; partial payments recorded only in bank transactions
  are not yet reconciled automatically.
- Multi-currency positions are not netted: everything is assumed EUR.
- Multilateral figures are potentials, not claims: **the counterparties must
  join the clearing network for a cycle to settle.**
