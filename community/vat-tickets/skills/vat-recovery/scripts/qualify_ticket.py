#!/usr/bin/env python3
"""Deterministic qualification of a VAT ticket: category verdict, regime,
legal deadline.

Usage:
  python3 qualify_ticket.py --category taxi --payment-date 2026-03-14
  python3 qualify_ticket.py --category saas --payment-date 2025-06-01 --foreign-supplier
  python3 qualify_ticket.py --test   # runs the fixtures

The category verdict comes from the table (source: references/vat-heuristics.md,
sourced from CGI/BOFiP). The deadline follows the prudent rule: 31/12 of N+2 with
N = min(invoice year, payment year) — chargeability at the supplier
(CE 31/12/2008 n° 305517 ; BOI-TVA-DED-40-20 § 50).
"""
import argparse
import datetime as dt
import json
import sys

# Verdicts: DEDUCTIBLE / PARTIAL_80 / NON_DEDUCTIBLE / DEAD (never any VAT) /
#           REVERSE_CHARGE / EXEMPT / FOREIGN_VAT (2008/9 route, off the CA3 return) /
#           NOTHING_TO_RECOVER (293 B franchise) / TO_REVIEW
CATEGORIES = {
    # --- Passenger transport: art. 206 IV-2-5° ann. II ---
    "taxi":            ("NON_DEDUCTIBLE", "Passenger transport — CGI ann. II art. 206 IV-2-5° ; BOI-TVA-DED-30-30-30 §10"),
    "vtc":             ("NON_DEDUCTIBLE", "Passenger transport — art. 206 IV-2-5°"),
    "train":           ("NON_DEDUCTIBLE", "Passenger transport (rail) — art. 206 IV-2-5°"),
    "plane":           ("NON_DEDUCTIBLE", "Passenger transport (air) — art. 206 IV-2-5°"),
    "public_transport":("NON_DEDUCTIBLE", "Passenger transport — art. 206 IV-2-5°"),
    "toll":            ("DEDUCTIBLE", "Toll = charge for passage on infrastructure, not a service related to the vehicle — deductible whatever the vehicle (BOI-TVA-DED-30-30-70 a contrario)"),
    "parking":         ("NON_DEDUCTIBLE", "Parking = service related to an excluded passenger car (art. 206 IV-2-10° ann. II ; CAA Paris 9-10-1990 n° 89PA01433) — EXCEPT for a utility vehicle, or a standalone space (separate commercial lease, visitor parking): to be re-qualified from the invoice"),
    "ev_charging":     ("DEDUCTIBLE", "Charging electricity: 100% deductible EVEN for a passenger car — not a petroleum product, outside the scope of art. 298, 4 (BOI-TVA-DED-30-30-40)"),
    # --- Vehicles: art. 206 IV-2-6°/7°/10° ---
    "passenger_car_rental": ("NON_DEDUCTIBLE", "Service related to an excluded asset — art. 206 IV-2-10° ; BOI-TVA-DED-30-30-70 §20"),
    "utility_vehicle_rental":     ("DEDUCTIBLE", "Category N vehicle, not excluded"),
    "passenger_car_maintenance":  ("NON_DEDUCTIBLE", "Parts/services on an excluded asset — art. 206 IV-2-7° and 10°"),
    # --- Fuels: art. 298, 4 CGI ---
    "passenger_car_fuel":  ("PARTIAL_80", "Petrol/diesel for an excluded vehicle: 80% — art. 298, 4-1° ; BOI-TVA-DED-30-30-40"),
    "utility_vehicle_fuel":        ("DEDUCTIBLE", "Fuel for a non-excluded vehicle: 100% since 2022"),
    # --- Fines and similar ---
    "fine":            ("DEAD", "Fine/ticket: outside the scope of VAT (not consideration for a service, CGI art. 256/271) — no tax shown, never recoverable"),
    # --- Accommodation / catering ---
    "director_hotel":  ("NON_DEDUCTIBLE", "Accommodation for directors/staff — art. 206 IV-2-2° ; BOI-TVA-DED-30-30-10"),
    "employee_hotel":  ("NON_DEDUCTIBLE", "Accommodation for directors/staff — art. 206 IV-2-2° ; EXCEPTIONS: on-site security/guard staff (deductible), and breakfast itemised separately (catering 10%, deductible)"),
    "third_party_hotel": ("DEDUCTIBLE", "Accommodation for the benefit of third parties — BOI-TVA-DED-30-30-10 §1 (beneficiary's identity on the invoice)"),
    "restaurant":      ("DEDUCTIBLE", "Catering deductible (10%) including directors/employees — ordinary rules"),
    # --- Leasing / long-term rental ---
    "bike":            ("DEDUCTIBLE", "Bike/e-bike: not a vehicle 'designed for the transport of persons' within the meaning of 206 IV-2-6° — VAT 100% deductible (purchase, rental, maintenance)"),
    "passenger_car_purchase": ("NON_DEDUCTIBLE", "Category M vehicle (passenger car): nil admission coefficient (206 IV-2-6°) — the CATEGORY takes precedence over the number of seats (a 2-seat passenger car stays excluded; double-cab pick-up excluded §36). Exceptions: N1/DERIV VP, driving school (273 septies A), exclusive taxi/VTC use, rental, resale as new"),
    "utility_vehicle_purchase": ("DEDUCTIBLE", "Category N vehicle (utility, van, DERIV VP, single-cab pick-up): VAT 100% deductible — check the category on the registration document (field J)"),
    "leasing":         ("TO_REVIEW", "Leasing/hire-purchase: EXCLUDED if the asset is a passenger car (art. 206 IV-2-10°), deductible otherwise — read the CONTRACT (nature of the asset); often high stakes (recurring lease payments)"),
    # --- Gifts ---
    "gift":            ("TO_REVIEW", "Deductible only if ≤ the €73 gross threshold per item, beneficiary and year (art. 23 N ann. IV, confirmed 2026) — otherwise excluded art. 206 IV-2-3°"),
    # --- Exempt (nothing to recover) ---
    "insurance":       ("TO_REVIEW", "Premium exempt by nature (art. 261 C: insurance premium tax instead) — BUT brokers (especially online ones) often charge fees/management costs SUBJECT to VAT on the same invoice: read the invoice before closing; pure premium -> exempt, fee line -> deductible"),
    "bank_fees":       ("EXEMPT", "Banking services exempt art. 261 C (unless the provider opts in: check the invoice)"),
    "exempt_training": ("EXEMPT", "Professional training exempt art. 261-4-4° (certificate)"),
    # --- Foreign ---
    "saas":            ("TO_REVIEW", "If the supplier is foreign: reverse charge (art. 283); if French with VAT: deductible"),
    # --- Foreign VAT & franchise (field lessons: Tesla Spain, IA & Co) ---
    "foreign_expense": ("FOREIGN_VAT", "VAT of another State on the invoice (the country is read from the INVOICE, not the brand): never deductible on the CA3 return (art. 271) — refund via directive 2008/9/CE, impots.gouv portal before 30/09 of year N+1, thresholds €400 (quarter) / €50 (year); 13th directive outside the EU"),
    "construction_subcontracting": ("TO_REVIEW", "Subcontracted construction work = REVERSE CHARGE by the principal (art. 283, 2 nonies). Subcontractor invoice received WITH VAT = wrongly charged VAT NOT deductible (double charge: the reverse charge is still owed) -> demand a corrected net invoice marked 'Autoliquidation'. Outside the scope of the nonies rule: routine cleaning, security guarding, intellectual services, bare equipment rental, supply without installation (BOI-TVA-DECLA-10-10-20)"),
    "intra_eu_goods_acquisition": ("REVERSE_CHARGE", "Goods shipped from the EU with a FR VAT number provided: intra-EU acquisition — VAT reverse-charged on line 3B + deducted on line 20 (19 for a fixed asset), due on the 15th of the following month or at invoicing. If the seller charged French VAT (a FR subsidiary like Amazon EU): normal regime, the invoice decides"),
    "import":          ("REVERSE_CHARGE", "Import from outside the EU: ATVAI mandatory (art. 293 A) — base pre-filled on line A4 from customs data, but the DEDUCTIBLE part (lines 19/20 + breakdown on line 24) is NEVER pre-filled: omitting it = a cash advance. Absent from the pre-fill (DDP, IOSS, baggage): declare manually, supporting document = DAU in the company's name"),
    "wrongly_charged_vat": ("NON_DEDUCTIBLE", "VAT not legally due = never deductible even if paid (art. 271, II-1-a ; CJUE Genius Holding) and never refundable via 2008/9 — route: corrected invoice from the supplier, then the tax authority as a subsidiary remedy if impossible (CE 15-11-2019 Eye Shelter ; CJUE PORR)"),
    "franchise_subcontractor": ("NOTHING_TO_RECOVER", "French supplier under the VAT franchise scheme (art. 293 B): no VAT charged -> no deduction (art. 271, II-1-a). Missing '293 B' mention = a SUPPLIER non-compliance to flag, without opening any deduction right. Corroborate via the Recherche d'Entreprises API (recherche-entreprises.api.gouv.fr, open): legal category sole trader + 0 headcount = franchise very likely; status 'cessée' = red flag on the invoice"),
    # --- French overheads ---
    "french_software": ("DEDUCTIBLE", "French B2B service with VAT — art. 271"),
    "professional_fees": ("DEDUCTIBLE", "Professional fees with French VAT — art. 271"),
    "telecom":         ("DEDUCTIBLE", "Telecoms with French VAT — art. 271"),
    "supplies":        ("DEDUCTIBLE", "Purchases with French VAT — art. 271"),
}


def line21_deadline(payment_date: str, invoice_date: str | None = None) -> str:
    """31/12 of N+2, N = min(invoice year, payment year) — prudent rule."""
    years = [dt.date.fromisoformat(payment_date).year]
    if invoice_date:
        years.append(dt.date.fromisoformat(invoice_date).year)
    return f"{min(years) + 2}-12-31"


def qualify(category: str, payment_date: str, invoice_date: str | None = None,
            foreign_supplier: bool = False, vat_on_invoice: bool | None = None,
            today: str | None = None) -> dict:
    today_d = dt.date.fromisoformat(today) if today else dt.date.today()
    cat = category.lower().strip()
    verdict, reason = CATEGORIES.get(cat, ("TO_REVIEW", "Category not in table — read references/vat-heuristics.md then exclusions.md"))

    regime = "line21"
    # Reverse-charge routing: foreign supplier (services)
    if foreign_supplier and verdict not in ("DEAD", "FOREIGN_VAT", "NOTHING_TO_RECOVER", "NON_DEDUCTIBLE", "REVERSE_CHARGE"):
        regime = "reverse_charge"
        if verdict == "TO_REVIEW" and cat == "saas":
            verdict, reason = "REVERSE_CHARGE", ("Service from a foreign supplier: VAT reverse-charged A3/B2 + L20, "
                                                  "neutral — voluntary disclosure with NO time bar (BOI-CF-INF-20-20 §100), "
                                                  "5% penalty (art. 1788 A, 4) avoided if before any tax audit notice")
    ddl = line21_deadline(payment_date, invoice_date)
    time_barred = regime == "line21" and dt.date.fromisoformat(ddl) < today_d

    if verdict in ("NON_DEDUCTIBLE", "DEAD", "EXEMPT", "FOREIGN_VAT", "NOTHING_TO_RECOVER"):
        status = "dead"
    elif time_barred:
        status, reason = "dead", reason + f" | TIME-BARRED: deadline {ddl} passed (art. 208 ann. II)"
    else:
        status = "qualifiable"  # won/to_play depending on whether the invoice is present (outside this script's scope)

    return {
        "category": cat,
        "verdict": verdict,
        "reason": reason,
        "regime": regime,
        "legal_deadline": None if regime == "reverse_charge" else ddl,
        "urgency": ("regularise before any tax audit notice" if regime == "reverse_charge"
                     else f"declarable until {ddl}"),
        "status_pre_invoice": status,
    }


FIXTURES = [
    # (kwargs, expected_verdict, expected_status)
    (dict(category="taxi", payment_date="2026-03-14"), "NON_DEDUCTIBLE", "dead"),
    (dict(category="fine", payment_date="2026-02-01"), "DEAD", "dead"),           # Sixt = dead fine
    (dict(category="foreign_expense", payment_date="2026-04-02"), "FOREIGN_VAT", "dead"),   # Tesla Spain, IVA 21%
    (dict(category="foreign_expense", payment_date="2026-04-02", foreign_supplier=True), "FOREIGN_VAT", "dead"),  # no reverse-charge rerouting
    (dict(category="franchise_subcontractor", payment_date="2026-03-05"), "NOTHING_TO_RECOVER", "dead"),  # IA & Co without 293 B
    (dict(category="restaurant", payment_date="2026-04-02"), "DEDUCTIBLE", "qualifiable"),
    (dict(category="saas", payment_date="2025-06-01", foreign_supplier=True), "REVERSE_CHARGE", "qualifiable"),
    (dict(category="director_hotel", payment_date="2026-01-10"), "NON_DEDUCTIBLE", "dead"),
    (dict(category="passenger_car_fuel", payment_date="2026-05-05"), "PARTIAL_80", "qualifiable"),
    (dict(category="french_software", payment_date="2023-11-15", today="2026-07-11"), "DEDUCTIBLE", "dead"),  # time-barred (ddl 2025-12-31)
    (dict(category="french_software", payment_date="2024-01-15", today="2026-07-11"), "DEDUCTIBLE", "qualifiable"),  # ddl 2026-12-31: URGENT
    (dict(category="toll", payment_date="2026-03-01"), "DEDUCTIBLE", "qualifiable"),
    (dict(category="parking", payment_date="2026-03-01"), "NON_DEDUCTIBLE", "dead"),          # accessory to an excluded passenger car
    (dict(category="bike", payment_date="2026-03-01"), "DEDUCTIBLE", "qualifiable"),
    (dict(category="passenger_car_purchase", payment_date="2026-03-01"), "NON_DEDUCTIBLE", "dead"),
    (dict(category="utility_vehicle_purchase", payment_date="2026-03-01"), "DEDUCTIBLE", "qualifiable"),
    (dict(category="ev_charging", payment_date="2026-03-01"), "DEDUCTIBLE", "qualifiable"),  # 100% even for a passenger car
    (dict(category="construction_subcontracting", payment_date="2026-03-01"), "TO_REVIEW", "qualifiable"),   # nonies: the invoice decides
    (dict(category="intra_eu_goods_acquisition", payment_date="2026-03-01"), "REVERSE_CHARGE", "qualifiable"),
    (dict(category="import", payment_date="2026-03-01"), "REVERSE_CHARGE", "qualifiable"),
    (dict(category="wrongly_charged_vat", payment_date="2026-03-01"), "NON_DEDUCTIBLE", "dead"),
    (dict(category="wrongly_charged_vat", payment_date="2026-03-01", foreign_supplier=True), "NON_DEDUCTIBLE", "dead"),  # no rerouting
    (dict(category="passenger_car_rental", payment_date="2026-02-20"), "NON_DEDUCTIBLE", "dead"),
]


def run_tests() -> int:
    failed = 0
    for kwargs, exp_verdict, exp_status in FIXTURES:
        r = qualify(**kwargs)
        ok = r["verdict"] == exp_verdict and r["status_pre_invoice"] == exp_status
        print(f"{'PASS' if ok else 'FAIL'}  {kwargs.get('category'):32s} -> {r['verdict']:16s} {r['status_pre_invoice']:12s} ddl={r['legal_deadline']}")
        if not ok:
            failed += 1
            print(f"      expected: {exp_verdict} / {exp_status}")
    print(f"\n{len(FIXTURES) - failed}/{len(FIXTURES)} fixtures OK")
    return failed


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--category")
    p.add_argument("--payment-date")
    p.add_argument("--invoice-date")
    p.add_argument("--foreign-supplier", action="store_true")
    p.add_argument("--vat-on-invoice", type=int, choices=[0, 1])
    p.add_argument("--today")
    p.add_argument("--test", action="store_true")
    a = p.parse_args()
    if a.test:
        sys.exit(1 if run_tests() else 0)
    if not (a.category and a.payment_date):
        p.error("--category and --payment-date required (or --test)")
    print(json.dumps(qualify(a.category, a.payment_date, a.invoice_date,
                             a.foreign_supplier,
                             None if a.vat_on_invoice is None else bool(a.vat_on_invoice),
                             a.today), ensure_ascii=False, indent=2))
