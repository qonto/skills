#!/usr/bin/env python3
"""detect_offsets.py — Find bilateral netting opportunities in a clearing ledger.

Reads the ledger produced by build_ledger.py and reports every counterparty
that is simultaneously a client and a supplier: the two positions can be
offset immediately, with no bank transfer, under statutory set-off rules
(Italy: art. 1241-1252 Codice Civile; see references/legal_basis.md for
other EU jurisdictions).

The offsettable amount is simply min(open_credit, open_debit) — deterministic
and auditable. Multilateral opportunities (closed cycles across 3+ companies)
are out of scope here: they require a clearing network — see
simulate_network.py for a what-if preview.

Usage:
  python detect_offsets.py --ledger ledger.json [--out offsets.json]
"""

import argparse
import json
import sys
from decimal import Decimal

TWO_PLACES = Decimal("0.01")


def detect(ledger: dict) -> dict:
    matches = []
    for cp in ledger["counterparties"]:
        credit = Decimal(cp["open_credit"])
        debit = Decimal(cp["open_debit"])
        if credit <= 0 or debit <= 0:
            continue
        offset = min(credit, debit)
        matches.append({
            "counterparty": cp["canonical_name"],
            "vat": cp["vat"],
            "open_credit": str(credit),
            "open_debit": str(debit),
            "offsettable": str(offset.quantize(TWO_PLACES)),
            "residual_credit": str((credit - offset).quantize(TWO_PLACES)),
            "residual_debit": str((debit - offset).quantize(TWO_PLACES)),
            "credit_invoices": [i["number"] for i in cp["invoices"]
                                if i["kind"] == "receivable" and Decimal(i["open_amount"]) > 0],
            "debit_invoices": [i["number"] for i in cp["invoices"]
                               if i["kind"] == "payable" and Decimal(i["open_amount"]) > 0],
            "legal_basis": "art. 1241-1252 c.c. (set-off); voluntary set-off agreement ex art. 1252 c.c.",
        })
    matches.sort(key=lambda m: (-Decimal(m["offsettable"]), m["vat"] or ""))
    total = sum((Decimal(m["offsettable"]) for m in matches), Decimal("0"))
    return {
        "generated_by": "nexyzen-clearing-scout/detect_offsets.py",
        "as_of": ledger.get("as_of"),
        "bilateral_matches": matches,
        "total_offsettable": str(total.quantize(TWO_PLACES)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ledger", required=True, help="ledger.json from build_ledger.py")
    ap.add_argument("--out", default="offsets.json", help="output path")
    args = ap.parse_args()

    with open(args.ledger, encoding="utf-8") as f:
        ledger = json.load(f)

    result = detect(ledger)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Offsets written to {args.out}")
    if not result["bilateral_matches"]:
        print("  No bilateral netting opportunity found.")
    for m in result["bilateral_matches"]:
        print(f"  {m['counterparty']} (VAT {m['vat']}): offset EUR {m['offsettable']} "
              f"(credit {m['open_credit']} vs debit {m['open_debit']}) -> "
              f"residual credit EUR {m['residual_credit']}, residual debit EUR {m['residual_debit']}")
    print(f"  TOTAL offsettable without a single transfer: EUR {result['total_offsettable']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
