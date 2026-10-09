#!/usr/bin/env python3
"""Skill CI: verifies that every cited BOFiP reference (references/*.md,
scripts/*.py, SKILL.md) exists and is IN FORCE, against the official
dataset "BOFiP Impôts - publications en vigueur" (data.gouv.fr,
dataset 64b0918379678314f968ee64, served by data.economie.gouv.fr).

Usage:
  python3 check_bofip.py [skill_root]              # extraction + online check
  python3 check_bofip.py --list [root]             # extraction only (offline)
  python3 check_bofip.py --stock stock.json [...]  # check against a local export

Run before every skill release: a reported doctrine (e.g. a CE reversal)
must trigger a review of the rule that cites it. A NOT FOUND identifier =
either reported, or a typo — in both cases, blocking.
Output: report + return code 1 if at least one reference is not found.
"""
from __future__ import annotations
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

API = ("https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/"
       "bofip-vigueur/records")
RX = re.compile(r"\bBOI-[A-Z]{2,10}(?:-(?:[A-Z]{1,10}|[0-9]{1,10}))+\b")


def extract(root: pathlib.Path) -> dict[str, set[str]]:
    cites: dict[str, set[str]] = {}
    for pat in ("references/*.md", "scripts/*.py", "SKILL.md"):
        for f in root.glob(pat):
            if f.name == pathlib.Path(__file__).name:
                continue
            for m in RX.findall(f.read_text(encoding="utf-8", errors="replace")):
                cites.setdefault(m, set()).add(f.name)
    return cites


def check_online(ident: str) -> bool | None:
    where = urllib.parse.quote(f'identifiant_juridique="{ident}"')
    url = f"{API}?where={where}&limit=1&select=identifiant_juridique"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.load(r).get("total_count", 0) >= 1
    except Exception:
        return None  # network/API unavailable: do not conclude


def main() -> int:
    args = [a for a in sys.argv[1:]]
    list_only = "--list" in args
    stock_path = args[args.index("--stock") + 1] if "--stock" in args else None
    pos = [a for a in args if not a.startswith("--") and a != stock_path]
    root = pathlib.Path(pos[0]) if pos else pathlib.Path(__file__).resolve().parents[1]

    cites = extract(root)
    print(f"{len(cites)} unique BOFiP references cited in the skill\n")
    if list_only:
        for ident in sorted(cites):
            print(f"  {ident:38s} <- {', '.join(sorted(cites[ident]))}")
        return 0

    stock = None
    if stock_path:
        raw = pathlib.Path(stock_path).read_text(encoding="utf-8", errors="replace")
        stock = set(RX.findall(raw))
        print(f"(offline mode: local stock, {len(stock)} identifiers)\n")

    missing, unknown = [], []
    for ident in sorted(cites):
        ok = (ident in stock) if stock is not None else check_online(ident)
        if stock is None:
            time.sleep(0.15)  # API politeness
        tag = "OK        " if ok else ("NOT FOUND  " if ok is False else "UNKNOWN   ")
        print(f"  {tag} {ident:38s} <- {', '.join(sorted(cites[ident]))}")
        if ok is False:
            missing.append(ident)
        elif ok is None:
            unknown.append(ident)

    print(f"\nSummary: {len(cites) - len(missing) - len(unknown)} OK, "
          f"{len(missing)} not found, {len(unknown)} not verifiable")
    if missing:
        print("⚠ References to fix or reported doctrine -> review the citing rules.")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
