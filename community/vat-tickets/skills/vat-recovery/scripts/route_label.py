#!/usr/bin/env python3
"""Route a bank/FEC label -> a category for qualify_ticket.py.

Signal hierarchy (most reliable to least):
  1. the accounting account (6251 vs 6257...) and extract_fec's `alert_level`;
  2. the label — via this module, WORD-BOUNDARY patterns, ordered;
  3. as a last resort: TO_REVIEW (never guess).
The INVOICE always decides in the end: same supplier, different VAT country
depending on location (Tesla France = French VAT; Tesla Spain = Spanish IVA 21%).

Real pitfalls encountered (encoded as fixtures below):
  - "Facture pre*station*" matched `station` -> \\b mandatory;
  - "Corbeil-*Esso*nnes" matched `esso` -> \\b mandatory;
  - leasing and subcontracting must come BEFORE fuel/supplies;
  - a generic pattern (google, apple) says nothing about the VAT country;
  - dossier-specific patterns (mission refs, names) live in
    client-config.json, NEVER here.

Usage:  python3 route_label.py "TAXI LLIC 7716"     |  --test
"""
from __future__ import annotations
import re
import sys

# (pattern, qualify_ticket category, foreign_supplier_likely)

import json, os

def _load_client_rules() -> list[tuple[str, str, bool]]:
    """Dossier-specific rules (mission refs, known subcontractors,
    clients...), generated on the first interaction — see SKILL.md
    §"First launch". They run BEFORE the generic rules.
    client-config.json format: {"client_rules": [
        {"pattern": "supplier.?name\\b", "category": "franchise_subcontractor",
         "foreign_supplier": false}, ...]}
    Absent, malformed, or containing an invalid regex pattern: NEVER a
    crash — client-config.json is hand-edited by the user (SKILL.md,
    validation); a broken client rule is dropped on its own (with a
    warning), the other client rules and ALL generic rules keep working."""
    path = os.environ.get("VAT_RECOVERY_CLIENT_CONFIG",
                          os.path.join(os.path.dirname(__file__), "..", "client-config.json"))
    if not os.path.exists(path):
        return []
    try:
        cfg = json.load(open(path, encoding="utf-8"))
        raw = cfg.get("client_rules", [])
        if not isinstance(raw, list):
            raise TypeError("client_rules must be a list")
    except Exception as e:
        print(f"⚠ client-config.json ignored (client_rules): {e}", file=sys.stderr)
        return []
    rules = []
    for i, r in enumerate(raw):
        try:
            pat = r["pattern"]
            re.compile(pat)  # validate the pattern NOW, never at the first routing
            rules.append((pat, r["category"], bool(r.get("foreign_supplier", False))))
        except Exception as e:
            print(f"⚠ client_rule #{i} ignored (invalid pattern): {e}", file=sys.stderr)
    return rules

CLIENT_RULES = _load_client_rules()

RULES: list[tuple[str, str, bool]] = [
    (r"cr[ée]dit.?bail|leasing|\bloyer\b.*\bbail\b", "leasing", False),
    (r"\bvacataire\b|\bfreelance\b|\bsous.?traitan", "franchise_subcontractor", False),
    (r"\btaxi\b|\buber\b(?!.?eats)|\bvtc\b", "taxi", False),
    (r"vueling|transavia|ryanair|easyjet|air france|\bavion\b", "plane", False),
    (r"\bsncf\b|trainline|\bter\b|\btgv\b|eurostar", "train", False),
    (r"\bratp\b|\bmetro\b|flixbus|blablacar|\bbolt\b|navigo", "public_transport", False),
    (r"h[oô]tel|booking|airbnb|\bibis\b|mercure|novotel|campanile|motel", "director_hotel", False),
    (r"\bsixt\b|rentalcars|hertz|europcar|getaround", "passenger_car_rental", False),
    (r"\bamende\b|\bantai\b|forfait de post", "fine", False),
    (r"parking|\bindigo\b|\beffia\b|\bq-park\b|\bzenpark\b", "parking", False),
    (r"p[ée]age|\bsapn\b|\baprr\b|\bsanef\b|cofiroute|\bvinci autoroutes?\b|\bescota\b|\barea\b|ulys|bip.?go", "toll", False),
    (r"\bchantier\b|ma[çc]onnerie|plaquiste|couverture|charpente|terrassement|\bbtp\b|plomberie|d[ée]molition|gros [oœ]uvre", "construction_subcontracting", False),
    (r"anthropic|openai|chatgpt|webflow|vercel|tailscale|typeform|tella|figma|notion|canva|midjourney|deepl|elevenlabs|github|\baws\b|heroku|\bzoom\b|slack|\bmiro\b|airtable|hubspot|calendly|fiverr|google|microsoft|apple\.com|adobe|linkedin|\bmeta\b", "saas", True),
    (r"scaleway|\bovh\b|pennylane|qonto|payfit|gocardless", "french_software", False),
    (r"\borange\b|bouygues|\bsfr\b|free mobile", "telecom", False),
    (r"assur|\baxa\b|allianz|\bmaif\b|generali", "insurance", False),
    (r"agios|inter[êe]ts|frais bancaires|affacturage|karmen", "bank_fees", False),
    (r"avocat|notaire|expert.?comptable|cabinet|honoraire|\bconseil\b|comptab", "professional_fees", False),
    (r"amazon|\bfnac\b|darty|boulanger|\bldlc\b|apple store|\bikea\b|bureau vall", "supplies", False),
    (r"tesla|electra|ionity|chargemap|\brecharge\b|supercharg", "ev_charging", False),
    (r"\bavia\b|stat avio|total ?energies|\besso\b|\bshell\b|\bbp\b|carburant|\bessence\b|station.service", "passenger_car_fuel", False),
    (r"restaurant|\bresto\b|\bmcdo\b|burger|pizza|brasserie|traiteur|deliveroo|uber.?eats|sushi|boulangerie|caf[ée]t?\b", "restaurant", False),
    (r"\bv[ée]lo\b|\bvae\b|swapfiets|cyclofix|\bcargo.?bike\b", "bicycle", False),
    (r"cadeau|\bfleurs?\b|champagne|coffret", "gift", False),
]


def route(libelle: str) -> tuple[str | None, bool]:
    """-> (category, foreign_supplier_likely). None = TO_REVIEW."""
    for pat, cat, foreign in CLIENT_RULES + RULES:
        if re.search(pat, libelle, re.I):
            return cat, foreign
    return None, False


FIXTURES = [
    ("Premier loyer crédit bail - GUIGUICHARD - Facture prestation mars", "leasing"),
    ("Virement freelance mission x5: Corbeil Essonnes", "franchise_subcontractor"),  # esso\b pitfall
    ("Facture RESTAURANTS - 027", "restaurant"),
    ("STAT AVIO 02507", "passenger_car_fuel"),
    ("TAXI LLIC 7716", "taxi"),
    ("UBER *TRIP", "taxi"),
    ("UBER EATS PARIS", "restaurant"),
    ("BKG*HOTEL AT BOOKING.C", "director_hotel"),
    ("ANTHROPIC* CLAUDE SUB", "saas"),
    ("SAPN", "toll"),
    ("PARKING GRAN VIA", "parking"),  # ⚠ and invoice = Spain -> exclusions-by-country.md at vision time
    ("Facture Dupont Formation - 17 REFINT_204", None),  # client-specific patterns -> client-config.json
    ("Tesla Spain, S.L.", "ev_charging"),  # ⚠ invoice -> foreign_expense (IVA 21%)
    ("INDIGO PARK LYON", "parking"),
    ("Facture maçonnerie chantier Lot 3", "construction_subcontracting"),
    ("Mission conseil stratégie", "professional_fees"),
    ("VIREMENT SEPA DUPONT", None),
]


def _test() -> int:
    bad = 0
    for lib, expected in FIXTURES:
        got, _ = route(lib)
        ok = got == expected
        bad += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {lib[:52]:54s} -> {got}")
    print(f"\n{len(FIXTURES) - bad}/{len(FIXTURES)} fixtures OK")
    return 1 if bad else 0


if __name__ == "__main__":
    if "--test" in sys.argv:
        sys.exit(_test())
    lib = " ".join(a for a in sys.argv[1:] if not a.startswith("--"))
    cat, foreign = route(lib)
    print(f"category={cat or 'TO_REVIEW'} foreign_supplier_likely={foreign}")
