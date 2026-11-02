# Operational table — expense category → VAT verdict

**Source of truth for categorical verdicts.** Each row is sourced (CGI / BOFiP
verified against the base in force). In case of doubt or an unlisted case, read
`exclusions.md` — never improvise.

Reminder: these verdicts assume an expense incurred for the needs of operations
giving a deduction right (CGI, art. 271; liability and taxation coefficients not
nil). A purely private expense is out of scope whatever the categorical verdict.

## Transport and travel

| Category (typical bank labels) | Verdict | Source |
|---|---|---|
| Taxi, private hire (Uber, Bolt, G7…) | ❌ NON-deductible, even on business travel | CGI ann. II, art. 206, IV-2-5°; BOI-TVA-DED-30-30-30, § 10 |
| Train (SNCF), plane (Air France, Vueling, Transavia…), boat, metro/bus | ❌ NON-deductible — "whatever the route and means used (road, rail, air, water)" | BOI-TVA-DED-30-30-30, § 10 |
| Operations ancillary to passenger transport (seat rental, booking fees, baggage, onboard wifi) | ❌ NON-deductible | BOI-TVA-DED-30-30-30, § 10 |
| Motorway tolls (Cofiroute, Vinci, APRR…) | ✅ Deductible (20%) — a toll is a road service, not passenger transport | Settled doctrine since 2001; invoice/receipt required |
| Parking | ✅/❌ Depending on assignment: client/visitor/employee parking at the workplace deductible; parking a passenger car excluded (service relating to an excluded good) | BOI-TVA-DED-30-30-70, § 10 |
| Passenger-car rental (Sixt, Hertz, Europcar — passenger vehicle) | ❌ NON-deductible (service relating to an excluded good) | CGI ann. II, art. 206, IV-2-10°; BOI-TVA-DED-30-30-70, § 20 |
| Utility-vehicle rental (category N) | ✅ Deductible | A contrario art. 206 IV-2-6° and 10° |
| Fines, tickets, surcharges (including those re-invoiced by a rental company) | ❌ NEVER — outside the VAT scope (not consideration for a service): DEAD ticket | General principles; no VAT appears on a fine |
| Transport exception: permanent contract to bring staff to the workplace; public-transport companies | ✅ Deductible | BOI-TVA-DED-30-30-30, § 30 |
| Nuance: transport costs re-invoiced to the client as an element of the price of a service | The CLIENT deducts under ordinary-law conditions (follows the regime of the principal service) | BOI-TVA-DED-30-30-30, § 20 |

## Accommodation and meals

| Category | Verdict | Source |
|---|---|---|
| Hotel / housing for the benefit of directors or employees (Booking, hotels while traveling) | ❌ NON-deductible | CGI ann. II, art. 206, IV-2-2°; BOI-TVA-DED-30-30-10, § 1 |
| Hotel / housing for the benefit of THIRD parties (clients, partners, external contributors) | ✅ Deductible — identity and capacity of the beneficiaries to be stated on the invoice; pro rata allowed if mixed | BOI-TVA-DED-30-30-10, § 1 (note) |
| Free housing of security/guarding staff on site or on the premises | ✅ Deductible (strict exception) | BOI-TVA-DED-30-30-10, § 10-40 |
| Restaurant, business meals, meals while traveling (VAT mainly at 10%) | ✅ Deductible — including for the benefit of directors/employees; compliant invoice required (in the company's name above €150 incl. VAT) | Ordinary law; BOI-TVA-DED-40-10-10 |
| Reception, catering | ✅ Deductible under the same conditions as meals | Ordinary law |

## Vehicles and fuels

| Category | Verdict | Source |
|---|---|---|
| Purchase / rental / maintenance / repair / parts of a passenger vehicle (category M, designed to transport people or mixed use) | ❌ NON-deductible — criterion = the vehicle's DESIGN, not its use | CGI ann. II, art. 206, IV-2-6° and 7°; BOI-TVA-DED-30-30-20, § 1 |
| Utility vehicle (category N), DERIV VP (2 seats) | ✅ Deductible | BOI-TVA-DED-30-30-20, § 35 |
| Vehicle exceptions: driving schools (exclusive assignment to instruction), taxis/private-hire in operation, ambulances, hearses, M2/M3 ≥ 9 seats for staff, vehicles assigned exclusively to rental, courtesy vehicles given on paid rental | ✅ Deductible | CGI, art. 273 septies A; BOI-TVA-DED-30-30-20, § 110-280 |
| Petrol, diesel, superethanol E85 — EXCLUDED vehicle (passenger car) | ⚠️ Deductible at 80% | CGI, art. 298, 4-1°-a/b; BOI-TVA-DED-30-30-40, § 110-130 (2022+ scale) |
| Petrol, diesel, E85 — NON-excluded vehicle (utility) | ✅ Deductible at 100% (since 2022) | BOI-TVA-DED-30-30-40, table § 110-130 |
| Fuel for the PRIVATE travel of directors/employees | ❌ NON-deductible (private use) | BOI-TVA-DED-30-30-40, § 70 |
| LPG, gas, charging electricity | ✅ Generally deductible (gaseous LPG 100%; charging electricity deductible including for passenger cars) | BOI-TVA-DED-30-30-40, § 50 et seq. |
| Lubricants for excluded vehicles | ❌ NON-deductible | CGI, art. 298, 4-1°-e |

## Gifts and goods transferred without remuneration

| Category | Verdict | Source |
|---|---|---|
| Gifts to clients/partners (goods transferred without remuneration) | ❌ NON-deductible in principle | CGI ann. II, art. 206, IV-2-3°; BOI-TVA-DED-30-30-50, § 20 |
| Very-low-value goods | ✅ Deductible if unit value incl. VAT ≤ the amount of art. 28-00 A ann. IV CGI, per item, per year and per beneficiary (€73 incl. VAT since 2021; five-yearly revaluation — check the 2026 value) | BOI-TVA-DED-30-30-50, § 90 |
| Samples, advertising material given free (conditions) | ✅ Deductible under conditions | BOI-TVA-DED-30-30-50 |

## Services, digital, general expenses

| Category | Verdict | Source |
|---|---|---|
| SaaS / services from FOREIGN suppliers (Anthropic Ireland, OpenAI, Vercel, Google Ireland, Microsoft Ireland…) invoiced net | 🔀 REVERSE CHARGE — no VAT to "recover" on the invoice; the regularization goes through A3/B2 + line 20 (neutral). See deadlines-and-regimes.md | CGI, art. 283-1 and 2; BOI-CF-INF-20-20, § 100 |
| Foreign supplier that charged foreign VAT (client's intra-community VAT number not filled in) | 🔀 Not deductible in France; ACTION: fill in the intra-community VAT number at the supplier (switch to net/reverse charge) + request a retroactive refund from the supplier | Art. 196 of directive 2006/112/EC |
| Software, subscriptions, French B2B services (with French VAT on the invoice) | ✅ Deductible (20%) | Ordinary law, art. 271 |
| Professional fees (accountant, lawyer, consultant) | ✅ Deductible | Ordinary law |
| Telephone, internet (Orange, Bouygues, Free…) | ✅ Deductible | Ordinary law |
| Insurance (Assurup, AXA…) | ⚫ NOTHING to recover — exempt operation, no VAT charged | CGI, art. 261 C |
| Banking and financial services, interest, factoring (exempt commissions) | ⚫ NOTHING to recover (unless the provider opts in — then VAT on the invoice) | CGI, art. 261 C |
| Professional training by an exempt body (certificate) | ⚫ NOTHING to recover — no VAT on the invoice | CGI, art. 261-4-4° |
| Prohibited advertising (alcohol outside the legal framework, etc.) | ❌ NON-deductible | CGI ann. II, art. 206, IV-2-4°; BOI-TVA-DED-30-30-60 |

## Cross-cutting reminders

- **Meal vs hotel on the same travel expense: opposite verdicts** (meal ✅, night
  ❌ if for the benefit of a director/employee). Break down the invoice.
- **The vehicle criterion is the design, not the use** — a salesperson who uses
  their sedan only for work deducts neither the vehicle nor its rental; they
  deduct 80% of the VAT on their fuel.
- **An expense without VAT (exempt, reverse-charged, out of scope) is never a
  line-21 ticket** — either there is nothing to recover (⚫), or it is the
  reverse-charge regime (🔀).
- Partial ⚠️ verdicts: apply the percentage to the VAT amount, not to the gross.


## Foreign VAT on the invoice (field lesson)

**The VAT country is read on the INVOICE, never on the brand.** The same supplier
invoices from different entities depending on the place of consumption: Tesla
France S.à r.l. (French VAT 20%, deductible) vs Tesla Spain S.L. (IVA 21% —
charging at La Jonquera). Parking, tolls, hotels, restaurants, fuel consumed
abroad carry the local VAT.

| Situation | CA3 verdict | Recovery route |
|---|---|---|
| VAT of another Member State (IVA, MwSt, BTW…) | ❌ Never line 21 (art. 271: only French VAT is deductible) | Directive 2008/9/EC: electronic claim via impots.gouv.fr before **30/09 N+1**; thresholds **€400 per quarter / €50 per calendar year** |
| VAT of a non-EU country | ❌ Never line 21 | 13th directive (86/560/EEC), per reciprocity |
| Foreign **net** invoice (B2B services) | 🔀 Reverse charge (art. 283) | Current CA3 return, no time-bar |

Category `foreign_expense` in `qualify_ticket.py`. In practice the unit amounts
(charging, parking) are far below the 2008/9 thresholds: the operational verdict
is "dead", said honestly.

## French supplier without VAT: basic exemption (art. 293 B)

Invoice from a micro-entrepreneur/exempt supplier **with no VAT line**: nothing
to recover (art. 271, II-1-a — only the tax that APPEARS on the invoice is
deductible). The missing mandatory mention "TVA non applicable, art. 293 B du
CGI" is a non-conformity of the SUPPLIER (to be flagged to them): it opens no
right at the client. Frequent pattern: networks of temporary
workers/subcontractors on assignment (labels M20xx). Category
`franchise_subcontractor`.


## Clarifications from the Casus analyses (wearecasus.co), 2026 — sourced BOFiP/CJEU

**Fuels 2026 confirmed**: petrol/diesel/E85 = 80% passenger car, 100% utility
(art. 298, 4-1°); **electricity = 100% even for a passenger car** (outside the
scope of 298, 4 — it is the only "fuel" fully deductible everywhere); liquefied
LPG, CNG, B100, ED95 = 100%; gaseous LPG = 50% passenger car; jet fuel and
lubricants of a passenger car = 0%.

**Parking ≠ toll**: parking is a service RELATING to the vehicle (206 IV-2-10°;
CAA Paris n° 89PA01433) → excluded if the vehicle is a passenger car; a toll is a
passage service → always deductible. Parking exceptions: utility vehicle,
standalone space (separate lease, visitors).

**Gifts**: threshold €73 incl. VAT per item, beneficiary and year (art. 23 N
ann. IV). **Housing**: excluded for directors/employees EXCEPT guarding/security
staff on site; housing of THIRD parties deductible; mixed accommodation pro rata
to the beneficiaries; broken-out breakfast = restaurant 10% deductible even if
the night is excluded.

**Restaurant**: multi-rate (10% on premises, 5.5% takeaway, **20% alcohol**);
< €150 net the receipt with separate VAT is enough; ≥ €150 net the complete
invoice IN THE COMPANY'S NAME is imperative — no tolerance.

## VAT charged in error — the rule that governs all edge cases

VAT that was not legally due is NEVER deductible, even if paid (art. 271, II-1-a;
CJEU *Genius Holding*), and NEVER refundable via 2008/9. The obligation to
reverse-charge REMAINS (double charge as long as the invoice is not corrected).
Way out: 1) supplier's corrective invoice (priority), 2) claim to the
administration only if impossibility/excessive difficulty — insolvency,
prescription (CE 15-11-2019 n° 420251 *Eye Shelter*; CJEU *PORR*, *HUMDA*,
*Schütte*). Mass case: an EU supplier charging its local VAT on a misconfigured
account; a construction subcontractor invoicing gross; a 293 B exempt supplier
charging VAT; a foreign supplier charging French VAT.
