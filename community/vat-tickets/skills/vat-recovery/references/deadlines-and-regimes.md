# Deadlines and voluntary-disclosure regimes

## 1. The principle: "operating a deduction" = reporting it on a CA3 return

"The expression 'operating a deduction' must be understood as the operation
consisting of reporting the amount of deductible tax on the return referred to
in article 287 of the CGI" (BOI-TVA-DED-40-20, § 10) — even in a credit position.

**Consequence: booked ≠ declared.** VAT recorded in account 44566 but never
picked up in a CA3 filing was never "deducted" in the tax sense and lapses.
Confirmed in litigation: CAA Paris, 5 February 2025, n° 23PA01221 (SARL QMG,
business advisory; full text:
https://www.legifrance.gouv.fr/ceta/id/CETATEXT000051141323 — fetch as needed,
store only this canonical URL) — €107,552 of VAT definitively lost "even though
the value-added tax in question had been entered in the accounts" (pt 9).

## 2. Regime A — line 21 of the CA3 return (French VAT on invoice)

### Mechanism
Tax whose deduction was omitted may appear on later returns **provided it is
reported separately**, on **line 21** of form n° 3310-CA3-SD ("other VAT to
deduct") (CGI, ann. II, art. 208, I; BOI-TVA-DED-40-20, § 40 and 60).
- **Aggregation allowed**: no breakdown by original period, no ceiling, no
  threshold triggering a corrective CA3. A single aggregated filing is enough.
- The amount is computed **according to the rules in force at the date the right
  arose** (rate, exclusions of that time) — BOI-TVA-DED-40-20, § 90.

### Deadline: 31 December of N+2
N = year the **tax became chargeable at the supplier**
(CE, 31 December 2008, n° 305517 and n° 307142; BOI-TVA-DED-40-20, § 50):
- Supply of services: chargeable on **collection** (default) — i.e. on the
  **payment** date (the bank transaction is authoritative) — or on **invoicing**
  if the supplier opted for the accrual basis (BOI-TVA-BASE-20-20;
  BOI-TVA-BASE-20-50-10).
- Supply of goods: chargeable on **delivery** (≈ invoice date).
- ⚠️ The mention "VAT paid on the accrual basis" on the invoice is **advised but
  NOT mandatory** (BOI-TVA-BASE-20-50-10, § 70) — so the supplier's regime
  cannot be inferred from the absence of the mention.
- **Prudent encoding: N = min(invoice year, payment year).** Never wrong, at
  worst conservative by a few weeks.

### What does NOT save a time-barred line
- **A corrective invoice does not restart the deadline**: it "does not create a
  deduction right" and "does not alter the starting point of the lapse period"
  (CE 31/12/2008 above; BOI-TVA-DED-40-20, § 50). The countdown runs while you
  wait for the correction.
- The national time-bar (foreclosure of the deduction right) is compatible with
  EU law (CJEU, 8 May 2008, C-95/07 and C-96/07, Ecotrade).

### The one exception that reopens a deadline
**Tax reassessment at the supplier**: if the supplier is reassessed and issues a
corrective invoice carrying a VAT regularization, the customer may deduct the
top-up **until 31/12 of the second year following that of the corrective
invoicing** (BOI-TVA-DED-40-20, § 80). This is the only case where a corrective
invoice creates a new deadline.

### Favorable nuance on late receipt
An invoice received **after** the period closes but **before the return is
filed** allows deduction on that return (BOI-TVA-DED-40-20, § 25). Possession at
the time of filing is enough.

## 3. Regime B — omitted reverse charge (foreign suppliers)

Concerns services acquired from taxable persons not established in France
(CGI, art. 283-1 al. 2 and 283-2): SaaS, platforms, EU/non-EU providers. The VAT
should have been reverse-charged (collected A3/B2 **and** deducted on line 20, a
cash-neutral operation for a full deductor).

### Administrative tolerance (BOI-CF-INF-20-20, § 100) — verified against the text
- If the omitted reverse-charged VAT meets the substantive conditions of the
  deduction right: **no tax reassessment**, but a 5% penalty on the deductible
  tax (CGI, art. 1788 A, 4).
- **The penalty is NOT applied** to a taxpayer who, "before any action by the
  administration," notices the omission and **voluntarily files** a corrective
  return — in practice, the regularization "may be carried out on a later return,
  filed in the usual format, which separately indicates the elements relating to
  the reverse-charged operation."
- **"A taxpayer may voluntarily regularize a failure to declare reverse-charged
  operations without being opposed the time-bar of the deduction right provided
  by I of article 208 of annex II to the CGI."** (exact wording of § 100) — no
  31/12 N+2 deadline for this regime.
- The tolerance also applies to partial taxpayers (the non-deductible fraction is
  then reassessed, with late-payment interest).

### Urgency of this regime
No time-bar, but the tolerance falls away at the **first tax audit notice**.
"Voluntary" is a substantive condition: regularize BEFORE any audit. In
litigation, the 5% penalty applied after an audit is nearly unassailable
(proportionality upheld: CAA Paris 23PA01221, pt 12; Cons. const., QPC 2021-908
of 26/01/2022 on the 1788 A scale).

## 4. Routing table

| | Line 21 | Reverse charge |
|---|---|---|
| Trigger | French VAT on a supplier invoice, never reported on a CA3 return | Foreign supplier service, reverse charge never applied |
| Support | Line 21 of the current CA3 return, separate entry, aggregatable | A3/B2 (collected) + line 20 (deductible) on the current CA3 return |
| Cash effect | Refund / offset of the amount | Neutral (full deductor) |
| Deadline | 31/12 of N+2 (strict) | None if voluntary |
| Risk | Definitive time-bar | 5% penalty if the administration acts first |
| What kills the ticket | Deadline passed | Tax audit notice received |

## 5. Filing procedure (pack)

1. Line 21 filled in on the current CA3 return, aggregated amount, **separate
   entry** (requirement of art. 208 ann. II).
2. **Summary statement** attached or kept available: supplier, invoice date,
   payment date, net (excl. VAT), VAT, reason for the omission, invoice
   reference — this is the judge's proof standard: the taxpayer must establish
   the **nature of the expenses** AND their **deductible character**, with
   supporting documents (CAA Paris 23PA01221, pt 10: rejected for lack of both —
   the court requires, invoice by invoice, proof of the nature of the expense,
   of its deductible character AND the supporting document; accounting entries
   and bank statements alone are not enough).
3. **Cover letter to the SIE** (French business tax office) via the
   impots.gouv.fr secure messaging (template: `assets/sie-letter-template.md`) —
   not mandatory, but it materializes the voluntary nature and forestalls a
   request for justification on an unusual line 21.
4. Filing is done by the accountant or the legal representative — never by the
   tool.

## 6. Reference texts
- CGI, art. 271 (birth and conditions of the right); art. 283 (taxpayers /
  reverse charge); art. 1788 A, 4 (5% penalty).
- CGI, annex II: art. 205-206 (coefficients), art. 207 (regularizations),
  art. 208 (deadline + line 21 + credit carry-forward).
- BOFiP: BOI-TVA-DED-40-20 (conditions of time — THE central text),
  BOI-TVA-DED-10-30 (birth), BOI-CF-INF-20-20 § 100 (reverse-charge tolerance),
  BOI-TVA-BASE-20-20 and 20-50-10 (chargeability, accrual basis).
- Case law: CE 31/12/2008 n° 305517 and 307142 (corrective invoice without
  effect on the deadline); CJEU 8/05/2008 C-95/07 Ecotrade (time-bar compatible
  with EU law); CAA Paris 5/02/2025 n° 23PA01221 (booked ≠ declared; proof
  standard; penalty).


## Unified temporal table (Casus analysis — wearecasus.co, 2026)

| Object | Deadline | Text |
|---|---|---|
| Reassessment by the administration | 31/12 **N+3** | L. 176 LPF |
| Exercise of the deduction right | 31/12 **N+2** | 208, I ann. II |
| Litigation claim | 31/12 N+2 (after collection/payment) | R*196-1 LPF |
| Rejection of credit refund | **1 year** after express rejection | CE 14-11-2025 *Penn Ar Bed* |
| Irrecoverable debt (272) | 31/12 N+2 after the finding | RES N2005/70 |
| EU refund 2008/9 | **30/09 N+1**, absolute time-bar | 242-0 R ann. II |
| 13th-directive refund | **30/06 N+1** | 242-0 Z septies |
| Fixed-asset regularizations | 5 years (movables) / 20 years (buildings) | 207 ann. II |

**The N+3/N+2 mismatch trap**: the administration can reassess an omitted
reverse charge until end of N+3, but the mirror deduction right expires at end
of N+2 — so a late reassessment can cost the full VAT. This is the knock-out
argument for regularizing VOLUNTARILY (§100 of BOI-CF-INF-20-20 then opposes
neither the 5% penalty nor the time-bar).

## CA3 2026 lines by type of reverse charge

| Operation | Collected | Deductible |
|---|---|---|
| B2B services from an EU supplier (283-2) | **2A** | 20 (19 for fixed assets) |
| Services/goods from a non-established supplier (283, 1-al. 2) | **3B** | 20/19 |
| Intra-community acquisition of goods (283, 2 bis) | **3B** | 20/19 |
| Import ATVAI (293 A) | **A4** (pre-filled on the 14th of the month) | 19/20 **+ breakdown on line 24 — NEVER pre-filled** |
| Domestic reverse charges (construction, waste, energy, quotas, telecom) | "Other taxable operations" | 20/19 |

Import missing from the pre-fill (DDP parcel in the forwarder's name, IOSS
exempt art. 291 II-11°, purchase in luggage): declare manually, support = the
customs declaration (DAU) where the company appears as the real consignee.

## Domestic reverse charges (same reflexes as for foreign ones)

**Construction subcontracting** (283, 2 nonies): construction, repair, SITE
cleaning, maintenance, transformation, demolition of a building, supply WITH
installation. Out of scope: routine cleaning, security, intellectual services
(engineering firms, project management), rental of bare equipment, supply
without installation. Also: new waste/recovered materials (2 sexies),
gas/electricity between traders — EVEN between two French parties (2 quinquies),
carbon quotas and guarantees of origin (2 septies), wholesale telecom
(2 octies).

## Basic exemption (franchise en base) 2026 & effects at the customer

Thresholds maintained: **€85,000** sales / **€37,500** services (uplifted to
93,500/41,250) — the single-threshold reform of €25,000 is REPEALED (law
2025-1044 of 3-11-2025). Exit **on the day the uplifted threshold is exceeded**
(no longer on the 1st of the month). EU "EX" regime: cross-border exemption if
total EU turnover ≤ €100,000 (293 B bis/ter). On the CUSTOMER side: VAT charged
by an exempt supplier is owed by them (283-3) but NOT deductible at the customer
(271, II-1-a); after a legitimate exit, the corrective invoice with VAT normally
opens the deduction.


## Credit notes, cancellations, unpaid debts (art. 272) — the mirror effect on the PURCHASE side

Sale terminated/cancelled/rebated, or a debt that is DEFINITIVELY irrecoverable
(liquidation closed, bailiff's certificate — mere non-payment is not enough):
the supplier recovers its VAT via a duplicate stamped with the legal mention,
until 31/12 N+2. **On the buyer side — what the tool must detect**: on receipt
of a credit note or the duplicate, the VAT initially deducted must be REPAID
(line 15). A supplier credit note in the FEC (609/765 or 401 in debit) without a
44566 repayment = a reverse anomaly.

## Regime 42 and start-up credit

**Customs regime 42**: import followed by an immediate intra-community supply →
import VAT EXEMPT in France (291-III), the intra-community acquisition is
declared in the destination Member State — so an import "without VAT" in the
pre-fill may be normal. **Start-up credit** (exit from the basic exemption,
art. 207, III-4° ann. II): the new taxable person recovers the VAT on stock at
the first day of liability and on fixed assets still in use — a line-21 pocket
often forgotten among former exempt businesses.

## Electronic invoicing 2026-2027 (context for the invoices to come)

Mandatory reception for EVERYONE on **1 September 2026**; issuance: large
enterprises/mid-caps 09/2026, SME/micro **09/2027**. E-invoicing covers domestic
B2B; INTERNATIONAL and B2C flows move to **e-reporting** (transaction data
within 10 business days). The DES (European services declaration) and the
summary statement REMAIN — the reform does not replace them. Tool impact:
domestic French B2B invoices will become structured (reverse-charge mention in a
dedicated field); foreign invoices will remain the weak link. **CIBS
recodification** (ord. 2025-1247): the VAT articles migrate from the CGI to the
CIBS on 01/09/2026, but the CGI references stay valid until 31/12/2027 — the
skill's citations remain enforceable.


## Base in foreign currency: DGFiP chancellery exchange rate

To ground in euros the base of a reverse charge on an invoice in foreign
currency (USD, AED, CHF…), use the last published rate — dataset "DGFIP - Taux
de change (chancellerie)" on data.gouv.fr — on the day of chargeability, and cite
the rate used in the pack. The amount DEBITED at the bank includes the exchange
spread: this is a consistency check, not the legal base.
