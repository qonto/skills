# Sales territoriality — rules for "out-of-scope" alerts

The skill qualifies **deductible** VAT. But a FEC also contains sales, and some
sales configurations create obligations (or errors) that the tool must **flag
without concluding**. This file gives the detection rules. Source: legal analyses
produced by Casus (wearecasus.co), 2026 — BOFiP cited.

## Services — skeleton and derogations (art. 259 et seq.)

General rules: **B2B = place of the customer** (259-1°, art. 44 of the directive)
→ net invoice, "Reverse charge" mention, DES; **B2C = place of the supplier**
(259-2°) → French VAT. "Taxable customer": a SIMPLE presumption with three
cumulative elements (valid VAT number communicated + mention on the invoice +
reference to art. 44) — VIES alone is not enough, the duty of vigilance remains
(Reg. 282/2011, art. 18; BOI-TVA-CHAMP-20-50-20 §230).

Main derogations (detail BOI-TVA-CHAMP-20-50-30):

| Service | B2B | B2C |
|---|---|---|
| Attached to a building (2°) | place of the building | same |
| Passenger transport (4°) | distances covered | same |
| **Access to an event** (5° bis) | place of the event | place of performance (5°-a) |
| Restaurant/catering (5°-b) | place of performance | same |
| Short-term vehicle rental (1°-a) | place of provision | same |
| **VIRTUAL event (streaming, since 2025)** | general rule (customer) | place of the customer (259 D, III) |
| B2C electronic services (259 D) | general rule | place of the customer (€10,000 threshold) |

**Boundary event vs generic service (training!)** — DGFiP practical rule
(BOI-TVA-CHAMP-20-50-30 §325; CJEU C-647/17 *Srf konsulterna*): training for
**several taxable persons** AND **≤ 7 business days** = event (VAT of the place);
training for ONE single client (in-house/bespoke) OR > 7 days = general rule
(place of the customer). Live remote sessions NEVER fall under 5° bis since 2025.

**Composite services**: a single operation if one element is principal and the
others ancillary with no independent purpose (CJEU *Card Protection Plan*,
*Levob*, *Stadion Amsterdam*); an organizer who resells transport + accommodation
bought from third parties in its own name shifts into the **travel-agency**
regime (259 A, 8° — VAT on the margin at the place of the supplier).

## Use and enjoyment (259 B / 259 C) and the extended scope of the taxable person

**259 B**: intangible services (consulting, advertising, IT, transfer of rights,
provision of staff…) invoiced to a customer OUTSIDE the EU leave the French scope
→ net invoice even in B2C outside the EU. **259 C** (repatriation B2C): supplier
outside the EU + non-taxable EU customer + effective use in France → French VAT.
Beware the extended scope of the "taxable customer" (259-0): partial taxable
persons, EXEMPT ones (doctor, micro under the basic exemption) and identified
legal entities count as taxable persons for territoriality; and a service
acquired for MIXED business/private use follows the B2B rules in full.

## Chains, triangular, call-off, margin

- **Chain sales** (1 transport, ≥ 3 operators): the intra-community-supply
  exemption is attributed to ONE single supply — the one toward the intermediary
  operator, unless it communicates its VAT number of the DEPARTURE state
  (262 ter-I, 1° bis).
- **Triangular simplification** (258 D / art. 141 of the directive): dispenses B
  from registering with C — STRICT interpretation, the number used by B must come
  from a third Member State (CJEU *Luxury Trust Automobil*).
- **Call-off stock** (256, III bis): NO registration in the Member State of the
  stock if prior agreement + known acquirer + register + transfer ≤ 12 months —
  otherwise a retroactive deemed transfer.
- **Margin scheme** (297 A, second-hand/art): no apparent VAT on the invoice
  (nothing to deduct at the buyer!), no intra-community-supply exemption; a
  "margin scheme" invoice from an EU seller of a used vehicle at an abnormally
  low price = a fraud signal (joint liability 283-4 ter).

## Exemptions: NOT portable (CJEU C-620/21 Momtrade)

It is **the state of taxation** that applies ITS exemption conditions. A French
exemption (training 261-4-4°, medical…) does not follow the service localized
elsewhere. Corollaries: (a) intra-EU B2B → the exemption is assessed at the
customer; if the service is exempt there, **no DES** for that operation
(BOI-TVA-DECLA-20-20-40 §140); (b) B2C → France = state of taxation, the French
exemption applies; (c) virtual B2C training post-2025 → state of the customer →
ITS exemption.

## Goods — quick verdicts

| Flow | Regime | Control point |
|---|---|---|
| Intra-community supply B2B (262 ter-I) | exempt if VIES number + proven transport + summary statement | quick-fixes proof (2 docs A or 1A+1B, art. 45 bis Reg. 282/2011) |
| Distance sale B2C EU | VAT of the destination country if > €10,000/year overall | switch ON THE DAY of crossing; OSS |
| Export (262 I) | exempt | DAU/ECS; EXW = proof risk |
| Moved stock (FBA…) | **deemed transfer** = intra-community supply + acquisition | registration in the Member State of the stock — OSS does NOT cover it |
| Marketplace, non-EU seller or shipment ≤ €150 | platform = deemed supplier (256, V-2°) | IOSS |

## FEC signals → "out-of-scope — consult" alerts

- 706/707 toward EU clients with no VAT nor trace of a DES → check VIES + DES
  (€750 penalty per missing declaration).
- "training" turnover exempted with no 261-4-4° certificate on file → alert.
- Cumulative B2C EU sales > €10,000 invoiced with French VAT → OSS required.
- Labels "Amazon FBA", foreign warehouses in the charges → likely deemed
  transfers → local registrations to check.
- Recurring warehouse rent/salaries abroad → risk of a VAT permanent
  establishment (permanence + human AND technical means, CJEU *Titanium*,
  *Berlin Chemie*, *Adient* — a building without staff is NOT a PE).
- Overall turnover from an "EX" account or EU basic exemption → 293 B bis/ter
  regime (EU ceiling €100,000).

The tool does NOT compute the VAT on sales: it alerts and refers out (blacklist,
see SKILL.md).
