#!/usr/bin/env python3
"""simulate_network.py — What-if preview of multilateral clearing cycles.

Takes a small debt graph (edges "A owes B amount X") and finds closed cycles:
chains like A -> B -> C -> A where every company owes the next one. Each cycle
can be settled up to the minimum edge amount with zero bank transfers, once
all participants agree (voluntary multilateral set-off).

Edges may be marked "simulated": true — debts between third parties that the
organization cannot see in its own Qonto data. They are clearly flagged in the
output: this script is a NETWORK PREVIEW, not a statement of existing claims.
Production-grade multilateral clearing over real network data is performed
server-side by the Nexyzen clearing engine (see submit_to_nexyzen.py).

Deterministic: plain DFS over the graph, no heuristics, no AI.

Usage:
  python simulate_network.py --edges network_edges.json [--out cycles.json]

Edges file format:
  {"visible_edges": [{"from": ..., "from_vat": ..., "to": ..., "to_vat": ...,
                      "amount": "9800.00", "simulated": false}, ...],
   "simulated_edges": [...]}
(or a bare array of edge objects).
"""

import argparse
import json
import sys
from decimal import Decimal

TWO_PLACES = Decimal("0.01")


def load_edges(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        edges = data
    else:
        edges = list(data.get("visible_edges", [])) + list(data.get("simulated_edges", []))
    for e in edges:
        e["amount"] = Decimal(str(e["amount"])).quantize(TWO_PLACES)
        e.setdefault("simulated", False)
    return edges


def find_cycles(edges: list[dict]) -> list[list[dict]]:
    """Return all simple cycles as edge lists, canonicalized and deduplicated."""
    by_source: dict[str, list[dict]] = {}
    for e in edges:
        by_source.setdefault(e["from_vat"], []).append(e)

    cycles: list[list[dict]] = []
    seen: set[tuple] = set()

    def dfs(start: str, node: str, path: list[dict], visited: set[str]):
        for edge in by_source.get(node, []):
            nxt = edge["to_vat"]
            if nxt == start and len(path) >= 1:
                cycle = path + [edge]
                # Canonical key: rotate so the smallest VAT comes first.
                vats = [c["from_vat"] for c in cycle]
                i = vats.index(min(vats))
                key = tuple(vats[i:] + vats[:i])
                if key not in seen:
                    seen.add(key)
                    cycles.append(cycle)
            elif nxt not in visited and nxt != start:
                dfs(start, nxt, path + [edge], visited | {nxt})

    for start in sorted(by_source):
        dfs(start, start, [], {start})
    return cycles


def rotate_to_focus(cycle: list[dict], focus_vat: str | None) -> list[dict]:
    """Rotate the cycle so it starts at the focus company, when present."""
    if not focus_vat:
        return cycle
    for i, e in enumerate(cycle):
        if e["from_vat"] == focus_vat:
            return cycle[i:] + cycle[:i]
    return cycle


def summarize(cycles: list[list[dict]], focus_vat: str | None = None) -> list[dict]:
    out = []
    for cycle in cycles:
        cycle = rotate_to_focus(cycle, focus_vat)
        clearing = min(e["amount"] for e in cycle)
        out.append({
            "chain": [e["from"] for e in cycle] + [cycle[0]["from"]],
            "chain_vat": [e["from_vat"] for e in cycle] + [cycle[0]["from_vat"]],
            "length": len(cycle),
            "clearing_amount": str(clearing),
            "contains_simulated_edges": any(e["simulated"] for e in cycle),
            "edges": [{
                "from": e["from"], "to": e["to"],
                "amount": str(e["amount"]),
                "post_clearing_amount": str((e["amount"] - clearing).quantize(TWO_PLACES)),
                "simulated": e["simulated"],
                "source": e.get("source"),
            } for e in cycle],
        })
    out.sort(key=lambda c: (-Decimal(c["clearing_amount"]), c["length"]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--edges", required=True, help="debt graph JSON")
    ap.add_argument("--out", default="cycles.json", help="output path")
    ap.add_argument("--focus", default=None,
                    help="VAT of the organization: cycles are presented starting from it")
    args = ap.parse_args()

    edges = load_edges(args.edges)
    cycles = summarize(find_cycles(edges), focus_vat=args.focus)

    result = {
        "generated_by": "nexyzen-clearing-scout/simulate_network.py",
        "edge_count": len(edges),
        "simulated_edge_count": sum(1 for e in edges if e["simulated"]),
        "cycles": cycles,
        "disclaimer": (
            "Cycles that contain simulated edges are what-if previews: they "
            "assume debts the organization cannot verify from its own data. "
            "Actual multilateral clearing requires every counterparty to join "
            "the clearing network and consent to the set-off."
        ),
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    print(f"Cycles written to {args.out}")
    if not cycles:
        print("  No closed cycle found in the provided graph.")
    for c in cycles:
        flag = " [includes SIMULATED edges]" if c["contains_simulated_edges"] else ""
        print(f"  {' -> '.join(c['chain'])}: clearing EUR {c['clearing_amount']}{flag}")
        for e in c["edges"]:
            sim = " (simulated)" if e["simulated"] else ""
            print(f"    {e['from']} owes {e['to']}: EUR {e['amount']} "
                  f"-> EUR {e['post_clearing_amount']} after clearing{sim}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
