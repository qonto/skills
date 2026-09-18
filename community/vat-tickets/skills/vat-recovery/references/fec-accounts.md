# VAT accounts in the FEC — corrected mapping and the "declared?" test

The PCG (French chart of accounts) contains no deductibility rule (accounting
law ≠ tax law). Here it serves ONE purpose: reading the FEC. Chart of accounts:
PCG, art. 1121-1; operation of account 445: PCG, art. 1214-44.

## 1. The 445x accounts (PCG, art. 1121-1)

| Account | Title | Usual direction |
|---|---|---|
| 44551 | VAT payable | Credit at filing, debit at payment |
| 4452 | Intra-community VAT due | Reverse-charge collected VAT (intra-community) |
| 44562 | Deductible VAT on fixed assets | Debit at purchase |
| 44566 | Deductible VAT on other goods and services | Debit at purchase |
| 44567 | **VAT credit to carry forward** | See §2 — the convention is often inverted in the docs |
| 44571 | Collected VAT | Credit at sale |
| 4458x | VAT to regularize or pending | 44583 refund requested, 44586/44587 invoices not received / to issue |
| 44564x / 44574x (free subdivisions) | VAT "on collections" awaiting chargeability | Frequent intermediate accounts for cash-basis taxpayers; transferred to 44566/4457x on collection |

Reverse charge (PCG, art. 1214-44): two distinct VAT amounts of equal value —
one payable in a 4457 sub-account, one recoverable in a 4456 sub-account.

## 2. Convention 44567 "VAT credit to carry forward"

Verified against real entries (full chain: credit recognized → offset):
- **DEBIT 44567 = RECOGNITION of the VAT credit** (the filing entry of the
  surplus month debits 44567 — the credit appears, line 27 of the CA3).
- **CREDIT 44567 = OFFSET of the credit** against a following month (line 22 of
  the CA3).

Before concluding an anomaly on the VAT-credit chain, reproduce the full cycle
(recognition → carry-forward → offset) by hand on the raw entries: a credit that
"appears" in a given month is normally the balance of the previous month, not a
data-entry error.

## 3. The filing entry = the CA3 in the FEC

Each return materializes as an entry (often in a journal entry, labeled "TVA",
last day of the month):
```
Debit  44571  (collected for the month)     ← line 08/16 CA3
Debit  44567  (if a credit is recognized)   ← line 27
    Credit 44562/44566 (deductible)         ← lines 19/20
    Credit 44567 (if a prior credit is offset) ← line 22
    Credit 44551 (VAT payable)              ← line 28 (VAT to pay)
```

**Test "has this VAT been declared?"** — the QMG test:
deductible VAT is *declared* if and only if the initial debit to 4456x was
**cleared by a filing entry** (credit 4456x in an entry containing the schema
above). A 4456x balance lingering with no filing = VAT booked but NEVER declared
= it lapses (CAA Paris 23PA01221). That is the definition of the recoverable
pocket.

⚠ **FEC nuance during the fiscal year**: on a FEC cut off mid-year, the 4456x
balance normally holds the VAT of the most recent periods **whose CA3 is not yet
due** (June's VAT is filed in July). The QMG pocket is only concluded on periods
whose filing deadline has passed; the recent remainder is a normal work in
progress, not an omission.

## 4. Known reconstruction traps

- **Unmapped 44564x/44574x accounts**: a recomputation that ignores these
  intermediate sub-accounts produces false "deductible discrepancies"
  (experienced error: ~€13.7K of artefactual discrepancy). Include them in the
  mapping or explicitly neutralize them.
- **Rounding**: CA3 returns are to the euro; the FEC to the cent. Discrepancies
  < €2 per line = rounding.
- **Intra-community reverse charge**: the collected VAT goes through 4452/44520,
  its mirror deductible through 445662 or similar — do not count it as "French
  supplier" deductible.
- **Never compare a bank month to a CA3 month**: cash-basis chargeability, credit
  carry-forwards and multiple collection channels make a single-month comparison
  meaningless.


## Structured candidate alerts (`alert_level`)

`extract_fec.py` emits for each candidate an `alert_level` field: `"exclusion"`
(excluded nature, e.g. 6251 transport), `"breakdown"` (mixed account to sort line
by line: 625 travel, 6234 gifts, 6135 rentals, **612 leasing** — often high
stakes, the nature of the asset is read from the contract), or `null`. **Route on
this field, never on the alert text**: the breakdown prose contains both
"EXCLUDED" and "DEDUCTIBLE", a substring filter destroys valid tickets.


## "Coefficient ≠ 1" signals (partial taxpayer) — to scan BEFORE any verdict

The skill's reasoning assumes a deduction coefficient = 1. Suspend that
assumption and downgrade all DEDUCTIBLE verdicts to "conditional" if the FEC
shows: **706/708 without collected VAT** (exempt services: training 261-4-4°,
health…), **741/744** (subsidies — linked to the price of exempt operations =
denominator of the pro rata, CE n° 364715), **752/753 without 44571** (bare
rentals not opted-in — destructive for the pro rata), **761/762/764** (dividends
out of scope, exempt interest except ancillary < 10% of resources or < 5% of
gross turnover). § 100 (BOI-CF-INF-20-20) expressly RESERVES the case of partial
taxpayers: a partial taxpayer's line-21 regularization must go through a tax
specialist.

## Fixed assets: 5/20-year tracking (2xx accounts + 44562)

Debit 44562 = starting point of a regularization tracking (1/5th movables, 1/20th
buildings, art. 207 ann. II). Alerts: disposal of a fixed asset (credit 2xx)
without a facing 44551/44562 → disposal without regularization; coefficient
variation > 1/10th without a 44562 entry → annual regularization omitted.

## Special-regime signals

- Mention "293 B" or 70x with no 44571 at all → basic exemption (nothing to
  recover from the supplier; its charged VAT would be charged in error).
- 70x > €85,000/37,500 without 44571 → likely exemption threshold exceeded.
- 761 (dividends) + significant 44566 without any 706 management fees → passive
  holding deducting in error (full reassessment, CE *AXA* type).
- Disappearance of VAT on intra-group invoices → single taxable person (256 C):
  internal operations out of scope, check the global regularizations at setup.
- 708 "Airbnb/stays" without VAT with 3 of the 4 para-hotel services
  (261 D, 4°-b bis) → likely undeclared taxable activity.
- Supplier invoices at 5.59%/4.43% → agricultural flat-rate reimbursement
  (deduction at the buyer on a certificate).


## Coefficient mechanics (to qualify the "partial taxpayer" alert)

Deduction coefficient = **liability × taxation × admission** (art. 205-206
ann. II). Options: SINGLE taxation coefficient (simple but degrades 100%-taxed
expenses); **distinct sectors** (art. 209, as of right if activities have
different regimes — often the best answer: taxed sector at 1, exempt sector at 0,
pro rata only on shared costs). ANCILLARY financial/real-estate operations
excluded from the pro rata if < 10% of the burdened resources or < 5% of gross
turnover. Annual regularization: provisional coefficient (N-1) → final before
**25 April N+1**, discrepancy on line 15 (repayment) or 21 (top-up); waived if
the discrepancy ≤ 1/10th.

## Additional signals

- **Associations**: 756/758 "events" without VAT → normal up to 6/year
  (261, 7-1°-c), anomaly beyond; commercial receipts > **€80,011** (2025-2026) →
  the commercial-tax exemption is exceeded, VAT due.
- **Para-hotel activity** (261 D, 4°-b bis): taxable if 3 of the 4 services —
  breakfast, **REGULAR cleaning during the stay** (the exit cleaning does not
  count, CE 12-11-2025 n° 498267), household linen, reception of the clientele.
  708 "Airbnb" without VAT + 3/4 provided = alert.
- **Supplier credit notes** (credit 609/debit 401) without repayment of the
  deducted VAT → line-15 regularization omitted (art. 272, mirror effect).
