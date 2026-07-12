#!/usr/bin/env python3
"""Group Qonto transactions by vendor to plan justificatif retrieval.

Input: a JSON dump of transactions fetched by the agent from
`mcp__qonto__list_transactions` (paginated + concatenated). Either a file path
or stdin.

Output: a grouped-by-vendor JSON list on stdout, and a summary table on stderr.

Reads transactions in "raw MCP list_transactions" format:
    {"transactions": [{id, amount, currency, local_amount, local_currency,
                       label, clean_counterparty_name, emitted_at, side,
                       attachment_ids, attachment_required, attachment_lost,
                       operation_type, ...}, ...]}

Or a plain array of transaction dicts.

Usage:
    scripts/list_missing.py --from FILE.json > missing_by_vendor.json
    cat FILE.json | scripts/list_missing.py > missing_by_vendor.json
    scripts/list_missing.py --from FILE.json --include-refunds  # also list credits
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import defaultdict
from typing import Any


def load_transactions(source: str | None) -> list[dict]:
    if source and source != "-":
        with open(source) as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)
    if isinstance(data, dict) and "transactions" in data:
        return data["transactions"]
    if isinstance(data, list):
        # could be list of pages, each with .transactions
        if data and isinstance(data[0], dict) and "transactions" in data[0]:
            return [t for page in data for t in page.get("transactions", [])]
        return data
    raise SystemExit("Unrecognized input shape — expected list or {transactions:[]}")


def is_missing_receipt(tx: dict, include_refunds: bool) -> bool:
    if not tx.get("attachment_required"):
        return False
    if tx.get("attachment_ids"):
        return False
    if tx.get("attachment_lost"):
        return False
    if tx.get("side") == "credit" and not include_refunds:
        return False
    return True


def vendor_of(tx: dict) -> str:
    for key in ("clean_counterparty_name", "counterparty_name", "label"):
        v = tx.get(key)
        if v:
            return str(v).strip()
    return "?"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--from", dest="src", default="-",
                   help="JSON file with tx (or '-' for stdin, default)")
    p.add_argument("--include-refunds", action="store_true",
                   help="Also list credit-side tx (default: debits only)")
    p.add_argument("--min-eur", type=float, default=0.0,
                   help="Skip groups whose |total_eur| is below this (default: 0)")
    args = p.parse_args()

    txs = load_transactions(args.src)
    missing = [t for t in txs if is_missing_receipt(t, args.include_refunds)]

    groups: dict[str, dict] = defaultdict(lambda: {
        "vendor": None, "n": 0,
        "total_eur": 0.0, "total_local": 0.0, "local_currency": None,
        "labels": set(), "op_types": set(),
        "min_date": None, "max_date": None,
        "tx_ids": [],
    })

    for tx in missing:
        v = vendor_of(tx)
        g = groups[v]
        g["vendor"] = v
        g["n"] += 1
        amt = float(tx.get("amount") or 0)
        # side=debit is a positive outflow; we sum as positive €
        g["total_eur"] += amt
        loc_amt = tx.get("local_amount")
        loc_cur = tx.get("local_currency")
        if loc_amt and loc_cur:
            g["total_local"] += float(loc_amt)
            g["local_currency"] = loc_cur
        if tx.get("label"):
            g["labels"].add(tx["label"])
        if tx.get("operation_type"):
            g["op_types"].add(tx["operation_type"])
        date = (tx.get("emitted_at") or tx.get("settled_at") or "")[:10]
        if date:
            g["min_date"] = min(g["min_date"], date) if g["min_date"] else date
            g["max_date"] = max(g["max_date"], date) if g["max_date"] else date
        g["tx_ids"].append(tx["id"])

    out = []
    for v, g in groups.items():
        if abs(g["total_eur"]) < args.min_eur:
            continue
        g["labels"] = sorted(g["labels"])
        g["op_types"] = sorted(g["op_types"])
        g["total_eur"] = round(g["total_eur"], 2)
        g["total_local"] = round(g["total_local"], 2) if g["local_currency"] else None
        out.append(g)

    out.sort(key=lambda x: -x["total_eur"])
    json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")

    # Summary on stderr
    total_n = sum(g["n"] for g in out)
    total_eur = sum(g["total_eur"] for g in out)
    print(f"[list_missing] {total_n} tx across {len(out)} vendors, {total_eur:.2f} EUR total",
          file=sys.stderr)
    print(f"[list_missing] Top 10 vendors by €:", file=sys.stderr)
    for g in out[:10]:
        loc = f" ({g['total_local']:.2f} {g['local_currency']})" if g["local_currency"] else ""
        print(f"  - {g['vendor']:<40} n={g['n']:>3}  €{g['total_eur']:>10.2f}{loc}",
              file=sys.stderr)


if __name__ == "__main__":
    main()
