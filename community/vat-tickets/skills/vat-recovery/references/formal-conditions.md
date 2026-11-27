# Formal conditions — compliant invoice, tolerances, verdict grid

## 1. The triple condition (BOI-TVA-DED-40-10-10, § 55 — verified text)

The tax on an expense can only be deducted on the **triple condition** that:
1. the expense be incurred **for the needs of operations giving a deduction
   right**;
2. the VAT amount appears **separately on an invoice** drawn up in accordance
   with art. 289 of the CGI and art. 242 nonies and 242 nonies A of annex II;
3. the tax **could legally appear** on that invoice (CGI, art. 271, II-1) — VAT
   charged in error (exempt operation, reverse charge due) is not deductible at
   the client.

Possession of the invoice conditions the exercise of the right (CGI, art. 271,
II-2-a): **no invoice = no deduction**, whatever the reality of the expense. This
is the foundation of the "ticket to play" status.

## 2. Key mandatory mentions (art. 242 nonies A, ann. II)

For automated control, check as a priority: identity and address of the supplier
AND of the client, **intra-community VAT number of the supplier** (as soon as the
invoice ≥ €150 net), date, invoice number, description of the goods/services,
unit net price, **VAT rate per line**, **VAT amount per rate**, total net and
gross. Invoices ≤ €150 net: lightened formalism (the supplier's VAT number and
certain mentions may be missing).

## 3. Tolerances and degraded cases

| Finding on the invoice | Treatment | Basis |
|---|---|---|
| Isolated missing mention (e.g. the provider's VAT number absent from a private-hire/card receipt) while the date, net/VAT/gross amounts and rate are legible | Tolerance: deduction allowed if the **reality of the operation** and its business character are justified otherwise — the company's bank transaction is the proof of payment. Verdict: "deductible with documented reservation" | Settled doctrine and case law on minor defects (formalism does not prevail over reality); keep the invoice + the proof of payment |
| Till receipt with no identification of the client (small amounts) | Allowed for low-amount invoices (lightened formalism < €150 net) | BOI-TVA-DED-40-10-10 (tempering) |
| **Invoice in the name of the director or an employee** (≠ legal name) | ❌ Deduction refusable: the recipient of the invoice is not the taxable person deducting. ACTION: **corrective invoice in the company's name**, imperative BEFORE entry in the pack. ⚠️ The corrective invoice **does not restart the deadline** (CE 31/12/2008, n° 305517) — deadline unchanged while waiting | Art. 271, II-1-a + 289 CGI |
| Invoice with no apparent VAT while the supplier owes it | Obtain a corrective invoice **within the deadline of art. 208 ann. II** (BOI-TVA-DED-40-20, § 40) | BOI-TVA-DED-40-20, § 40 |
| Invoice received after the period closes but before the return is filed | Deduction possible on that return (possession at filing is enough) | BOI-TVA-DED-40-20, § 25 |
| Duplicate / reissue from the supplier portal | Counts as the original (electronic invoice); trace the provenance | Art. 289 CGI (electronic invoicing) |

## 4. Verdict grid for the verification agent (vision)

To apply per invoice, in this order:

| # | Test | If failed → verdict |
|---|---|---|
| 1 | Is the document an invoice/receipt (not a quote, purchase order, statement)? | ⚫ non-probative document — ticket stays "to play" |
| 2 | Recipient = the company (legal name or SIREN)? | 🔴 corrective invoice imperative (deadline still runs) |
| 3 | Does French VAT appear separately (amount + rate)? | If net from a foreign supplier → 🔀 reverse-charge regime; if exempt (training, insurance…) → ⚫ dead "nothing to recover"; if foreign VAT → 🔀 intra-community VAT-number action |
| 4 | Is the expense category admitted? (table vat-heuristics.md) | ⚫ dead, reason = exclusion article cited |
| 5 | Invoice gross ≈ transaction amount (± tip/rounding)? | 🟡 check the reconciliation (partial invoice, multi-transactions) |
| 6 | Mentions complete? | Isolated gap → 🟡 deductible with reservation; multiple gaps or illegible amounts → ⚫ insufficient document |
| 7 | Deadline (31/12 N+2 from min(invoice date, payment date)) met? | ⚫ time-barred (except reverse-charge rerouting, no deadline if voluntary) |
| — | All pass | 🟢 WON: exact VAT read on the invoice → pack |

**Final proof standard** (CAA Paris 23PA01221, pt 10): for each line of the pack,
be able to establish (a) the **nature of the expense**, (b) its **deductible
character**, (c) the **invoice**. The judge rejects when one of the three is
missing.

## 5. Supporting documents — accounting side (PCG)

Every accounting entry states the references of the supporting document that
backs it (PCG, art. 1032-1); each entry rests on a dated document, on a reliable
medium, kept for the required periods (art. 1032-2). Operations of the same
nature, same place, same day may be summarized on a single document. Retention:
6 years minimum (LPF, art. L. 102 B), 10 years for accounting purposes (C. com.,
art. L. 123-22).


## False friends of the invoice (non-probative for VAT)

The following are NOT invoices within the meaning of art. 271, II-2-a (deduction
requires **possession of the invoice**): affidavit, lost-receipt attestation,
bank statement, order confirmation, quote, proforma, payment receipt without
separate VAT. Useful to the expense file (corporate tax), inoperative for VAT.
**Systematic action: ask the supplier for a duplicate** (gas stations, retailers
and platforms reissue on request); failing that, the ticket is dead for lack of
an invoice.

## Defect n° 1 in frequency: invoice in the director's name

On card purchases and SaaS, the invoice is very often issued in the person's name
("Mr. Dupont", personal email, account handle) and not the company's — 3 invoices
out of 5 in a real sample. Two-step remedy:
1. **For the future**: fix the supplier account (legal name, registered-office
   address, intra-community VAT number — a field often available in the SaaS
   billing settings).
2. **For the past**: request a corrective invoice; the corrective invoice starts
   a new deduction deadline (BOI-TVA-DED-40-20, § 80).
PRECISE tolerance (Casus analysis — wearecasus.co, 2026): < €150 net, the
simplified receipt without the client's identity is allowed (art. 242 nonies A,
II ann. II); ≥ €150 net, NO tolerance — a complete invoice in the company's name
is mandatory, the added handwritten mention is fragile under audit. For reverse
charge, the taxable customer must be identifiable: correct it.

## Preliminary test: was the VAT LEGALLY DUE?

Above all: VAT charged in error (reverse charge applicable, 293 B basic
exemption, exempt operation, excessive rate) is NON-deductible even if paid
(art. 271, II-1-a) and NON-refundable under 2008/9 — only the corrective invoice
opens a route (detail: vat-heuristics.md). For reverse charge, the FORMAL
condition of deduction is not an invoice: it is the MENTION of the operation on
the CA3 return itself (BOI-TVA-DED-40-10-40 §70-80) — a reverse charge never
declared = deduction not secured under audit.

## "Separate VAT" test: check it is FRENCH

VAT at 21%, 19%, "IVA", "MwSt", "VAT" with a country prefix ≠ FR, or a foreign
issuing address = foreign VAT -> see `vat-heuristics.md` (2008/9 route), never
line 21. The rate is a quick clue: 21% does not exist in France.


## Automating the recipient/supplier test (open data)

The French intra-community VAT number is COMPUTED: FR + key + SIREN, with key =
(12 + 3 × (SIREN mod 97)) mod 97. The vision agent can therefore, for any French
party identified by its SIREN/SIRET: reconstruct the expected VAT number and
compare it to the one on the invoice — an inconsistent "VAT-Code" (e.g.
"FRSL000D") is detected mechanically. In addition, the Recherche d'Entreprises
API (recherche-entreprises.api.gouv.fr, no key) gives the supplier's
administrative status: an invoice issued by an entity CEASED at the invoice date
is a major defect to escalate. For EU suppliers, validation goes through VIES
(duty of vigilance, simple presumption).
