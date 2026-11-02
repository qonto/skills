# Reconciliation invoice ↔ transaction ↔ FEC — deterministic state table

The engine that reads invoices is the agent's native vision (no OCR embedded in
this skill, and that is deliberate: the skill provides the grid, not the engine).
On the other hand, **once the invoice is read, everything else is
deterministic**: each invoice becomes a structured tuple, and the state of each
tuple is deduced from the table below — never from intuition.

## 1. Tuple extracted from each invoice (vision → structure)

| Field | Use |
|---|---|
| `supplier` (legal name + VAT/SIREN number if present) | matching key + liability |
| `invoice_number`, `invoice_date` | invoice identity, start of the deadline |
| `net_amount`, `vat_amount`, `rate`, `gross_amount` | self-check: net + VAT = gross (to the cent) |
| `vat_country` (read on the invoice, NOT on the brand) | CA3 vs 2008/9 vs 13th directive |
| `mentions`: "293 B", "Reverse charge", "credit note", "cancels and replaces" | verdict + handling of corrective invoices |
| `client_name` invoiced | 🔴 if director ≠ company (formal-conditions.md) |

**Mandatory self-checks before any matching**: net + VAT = gross; if a candidate
payment exists, gross = amount of the bank movement. A tuple that fails the
self-check → re-read the invoice, never force it.

## 2. Matching keys, in order of reliability

1. **Exact join**: `PieceRef` of the FEC = external reference of the pre-
   accounting tool (or invoice number). Maximum reliability, no tolerance.
2. **Triplet**: exact gross amount + date ± k days (default k = 7 for a payment,
   k = 45 between invoice date and payment date) + normalized supplier
   (lowercase, no accents or punctuation, first 2 words).
3. **Bank label** alone: weak signal → never conclusive without 1 or 2.

One payment may settle SEVERAL invoices (batch) and one invoice may be paid in
SEVERAL installments (deposits): if the exact amount does not match, test the
sums of open invoices from the same supplier before concluding an inconsistency.

## 3. State table (invoice × transaction × FEC)

| Invoice | Bank transaction | FEC entry (charge/VAT) | STATE | Action |
|---|---|---|---|---|
| read, VAT > 0 | matched | charge with 4456x, filed | `already_deducted` | nothing (anti-double-deduction) |
| read, VAT > 0 | matched | charge **without** VAT (account "No VAT") | **`won`** | line 21 within the deadline, invoice to the pack |
| read, VAT > 0 | matched | 4456x never filed (QMG) | **`won`** | line 21 — this is the QMG pocket |
| read, VAT > 0 | matched | no charge (payment only, 401/4716 in debit) | `paid_not_booked` | send the invoice to the accountant, then re-qualify |
| read, VAT = 0 (293 B, reverse charge, out of scope) | — | — | `nothing_to_recover` | reason cited, ticket closed |
| read | **no** transaction, past date | — | `unpaid_or_paid_elsewhere` | question: another account? personal? credit note? |
| read | amount ≠ gross (outside batch/deposits §2) | — | `inconsistency` | TO_REVIEW: credit note, discount, error — never guess |
| read, future date / due date upcoming | — | — | `upcoming` | out of the pocket (no chargeability) |
| read, mention "cancels and replaces" or credit note | — | — | see §4 | the CHAIN of invoices, not the isolated invoice |
| **absent** | orphan (empty attachment, no invoice found) | charge without VAT | `to_play` | estimate (upper bound) + hunt for the invoice |
| absent | payment with no invoice AND no charge | 401/4716 in debit | `accounting_orphan` | `payments_without_invoice` output of extract_fec — claim it |

Cross-cutting reminders: the `won` state ALSO requires the deadline to be open
(temporal window) and formal conformity (🟢/🟡); any charge later than the last
detected filing is **current flow**: state `to_secure` — counted in the pot
(estimated VAT), action "provide the invoice before the next CA3", never "won"
nor line 21 (nothing has been omitted yet: the omission arises at the close of
the return without the invoice).

## 4. Corrective invoices, credit notes, duplicates

- **VAT charged in error** (e.g. a 293 B exempt supplier that invoices with VAT):
  never deductible even if paid (art. 271, II-1-a; CJEU *Genius Holding*). Only
  the corrective invoice in force opens a right — and it **does not restart** the
  deadline (CE 31/12/2008, n° 305517).
- "cancels and replaces" chain: keep only the last invoice in force; the
  cancelled invoices are excluded from matching (otherwise triple counting).
  Detection: same supplier + same assignment/period + mentions, or identical
  amounts with different numbers → ask which one is authoritative.
- A credit note (negative amount or "credit note" mention) is offset against the
  original invoice before any VAT verdict.
