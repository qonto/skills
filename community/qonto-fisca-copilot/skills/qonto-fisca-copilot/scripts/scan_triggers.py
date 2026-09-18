#!/usr/bin/env python3
"""Classify Qonto transactions into tax-nudge trigger buckets.

Deterministic first pass for the qonto-fisca-copilot skill: it tags each
transaction with the trigger categories it may hit, so Claude reasons over a
clean shortlist instead of eyeballing raw JSON. Claude still does the judgement
(business vs personal, city lookup, phrasing) — this only surfaces candidates.

Input: a `list_transactions` response, a bare array, or a list of pages.
Output: JSON on stdout, grouped by trigger, each rule keyed to the country rules
file (references/rules-<cc>-<regime>.md, e.g. rules-fr-is-tns.md). Trigger detection is country-
agnostic; the country-specific figures live in the rules file.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# Known foreign-service merchants (reverse-charge / autoliquidation candidates).
FOREIGN_SERVICE_RE = re.compile(
    r"anthropic|vercel|google|openai|github|amazon\s*web|aws|cloudflare|"
    r"notion|figma|slack|linear|stripe|apple|microsoft|netlify|supabase|youtube",
    re.IGNORECASE,
)
HOTEL_RE = re.compile(r"b&b|hotel|hôtel|booking|airbnb|ibis|mercure|novotel|campanile", re.IGNORECASE)
FUEL_RE = re.compile(r"total\s*energ|totalenergies|shell|esso|bp\b|station|carburant|essence|gazole", re.IGNORECASE)
RESTO_CAT_RE = re.compile(r"nourriture|boisson|restaurant|repas|accueil|réception|reception", re.IGNORECASE)
GIFT_RE = re.compile(r"cadeau|goodies|gift|fleuriste|interflora", re.IGNORECASE)
CCA_RE = re.compile(r"compte\s*courant|courant\s*associ|remboursement\s+.*associ", re.IGNORECASE)
EQUIP_RE = re.compile(r"mat[ée]riel|mobilier|[ée]quipement|informatique|outillage|hardware|fnac|ldlc|apple\s*store", re.IGNORECASE)


def load_transactions(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = [data]
    txns: list[dict] = []
    for chunk in data:
        if isinstance(chunk, dict) and "transactions" in chunk:
            txns.extend(chunk["transactions"])
        elif isinstance(chunk, dict):
            txns.append(chunk)
        elif isinstance(chunk, list):
            txns.extend(chunk)
    seen: dict = {}
    for t in txns:
        seen[t.get("id") or id(t)] = t
    return list(seen.values())


def name_of(t: dict) -> str:
    return t.get("clean_counterparty_name") or t.get("label") or ""


def category_of(t: dict) -> str:
    c = (t.get("cashflow_category") or {}).get("name") or ""
    s = (t.get("cashflow_subcategory") or {}).get("name") or ""
    return f"{c} {s}"


def is_foreign_currency(t: dict) -> bool:
    lc = t.get("local_currency")
    return bool(lc and lc != t.get("currency", "EUR"))


def triggers_for(t: dict) -> list[str]:
    tags: list[str] = []
    name = name_of(t)
    cat = category_of(t)
    debit = t.get("side") == "debit"

    # N1 — autoliquidation TVA (foreign service): foreign currency OR known SaaS
    if debit and (is_foreign_currency(t) or FOREIGN_SERVICE_RE.search(name)):
        tags.append("N1_autoliquidation_tva")
    # N4 — hotel VAT
    if debit and HOTEL_RE.search(name):
        tags.append("N4_tva_hotel")
    # N3 — meal (food category/subcategory incl. "accueil client / réception", or food-ish label)
    if debit and (RESTO_CAT_RE.search(cat) or RESTO_CAT_RE.search(name)):
        tags.append("N3_repas")
    # N2 — mileage candidate: ANY in-person card payment (has a physical location).
    # Exclude online SaaS (N1), fuel, and card-less operations. Claude then looks
    # up the merchant city and decides whether a trip happened.
    if (debit and t.get("operation_type") == "card" and name
            and "N1_autoliquidation_tva" not in tags
            and not FUEL_RE.search(name)):
        tags.append("N2_frais_km")  # needs city lookup / user confirm
    # N7 — fuel
    if debit and FUEL_RE.search(name):
        tags.append("N7_tva_carburant")
    # N6 — gift
    if debit and GIFT_RE.search(name):
        tags.append("N6_cadeaux_73e")
    # N5 — missing receipt
    if debit and t.get("attachment_required") is True and not t.get("attachment_ids"):
        tags.append("N5_facture_manquante")
    # N8 — compte courant associé movement
    if CCA_RE.search(name):
        tags.append("N8_compte_courant")
    # N9 — accountant / lawyer / bank fees
    if debit and (t.get("operation_type") == "qonto_fee"
                  or re.search(r"comptab|expertise|cabinet|avocat|greffe|huissier|notaire|honoraire", name, re.I)
                  or re.search(r"comptabilit|honoraire", cat, re.I)):
        tags.append("N9_honoraires_frais")
    # N10 — equipment/material purchase under 500 EUR HT -> immediate deduction.
    # 500 = the legal threshold (HT) below which small equipment is expensed at once
    # instead of being capitalized and amortized (BOFIP BOI-BIC-CHG-20-30-10).
    if debit:
        ht = float(t.get("amount", 0)) - float(t.get("vat_amount") or 0)
        if (EQUIP_RE.search(cat) or EQUIP_RE.search(name)) and 0 < ht < 500:
            tags.append("N10_deduction_immediate")
    return tags


RULE_LABELS = {
    "N1_autoliquidation_tva": "Reverse-charge VAT (foreign service) — CA3",
    "N2_frais_km": "Mileage / frais kilométriques (resolve the city, ask for CV)",
    "N3_repas": "Business meal / travel (note the guests)",
    "N4_tva_hotel": "Hotel VAT not recoverable",
    "N5_facture_manquante": "Ask for an invoice (card receipt is not enough)",
    "N6_cadeaux_73e": "Client gifts <= 73 EUR incl. VAT",
    "N7_tva_carburant": "Fuel VAT (petrol ~100% / diesel ~80%)",
    "N8_compte_courant": "Associate current account (presumption + interest)",
    "N9_honoraires_frais": "Accounting / bank fees deductible",
    "N10_deduction_immediate": "Purchase < 500 EUR HT -> immediate deduction (no amortization)",
}


def rule_order(tag: str) -> int:
    """Sort N1, N2 … N10 numerically (plain sort would put N10 before N2)."""
    m = re.match(r"N(\d+)", tag)
    return int(m.group(1)) if m else 99


def format_compact(out: dict) -> str:
    """Readable summary — the default, so the terminal stays legible."""
    triggers = out["triggers"]
    hits = sum(len(b["matches"]) for b in triggers.values())
    lines = [
        f"{out['transaction_count']} transactions scanned · "
        f"{len(triggers)} trigger types · {hits} candidate hits",
        "",
    ]
    for tag, block in triggers.items():
        code = tag.split("_")[0]
        rows = block["matches"]
        total = sum(r["amount"] for r in rows)
        lines.append(f"{code:<4}{block['rule']}")
        lines.append(f"    {len(rows)} hit(s) · {total:,.2f} EUR")
        for r in rows:
            fx = (f"  ({r['local_amount']:.2f} {r['local_currency']})"
                  if r.get("local_currency") else "")
            receipt = "  [receipt]" if r.get("receipt_available") else ""
            name = r["counterparty"][:30]
            lines.append(
                f"      {r['date']}  {name:<30} {r['amount']:>9,.2f} {r['currency']}{fx}{receipt}"
            )
        lines.append("")
    lines.append("[receipt] = a justificatif is attached -> can be read to resolve the city / cross-check VAT")
    lines.append("Run with --json for the full machine-readable output.")
    return "\n".join(lines)


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--json"]
    as_json = "--json" in sys.argv[1:]
    if not args:
        print("usage: scan_triggers.py <transactions.json> [--json]", file=sys.stderr)
        return 2
    txns = load_transactions(Path(args[0]))
    grouped: dict[str, list[dict]] = defaultdict(list)
    for t in txns:
        for tag in triggers_for(t):
            grouped[tag].append({
                "date": (t.get("emitted_at") or "")[:10],
                "counterparty": name_of(t),
                "amount": float(t.get("amount", 0)),
                "currency": t.get("currency", "EUR"),
                "local_amount": t.get("local_amount") if is_foreign_currency(t) else None,
                "local_currency": t.get("local_currency") if is_foreign_currency(t) else None,
                "receipt_available": bool(t.get("attachment_ids")),
                "id": t.get("id", ""),
            })
    out = {
        "transaction_count": len(txns),
        "triggers": {
            tag: {"rule": RULE_LABELS.get(tag, tag), "matches": grouped[tag]}
            for tag in sorted(grouped, key=rule_order)
        },
    }
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(format_compact(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
