#!/usr/bin/env python3
"""Inject tickets.json into the board and produce the artifact-ready HTML.

    tickets.json  +  assets/board.html   ──>   board-ready.html
                                                (→ mcp__cowork__create_artifact)

WHY THIS SCRIPT EXISTS
----------------------
The "replace the DATA constant by hand" step was the weak link in the run:
an agent copying a JSON blob into a 900-line HTML file eventually damages a
piece of it — or, worse, "tidies up" an amount.

Here nothing is copied: we replace a delimited block, and we VERIFY the
result. Three guardrails:

1. `_demo_vat` is ALWAYS stripped. This field only exists to replay the
   ceremony offline; in production, no amount is simulated. If it survived,
   the board would unlock a card with no invoice — that is, it would lie.
2. No `won` ticket gets through without an invoice and a read amount (double
   barrier with build_tickets.py: if a tickets.json was hand-edited, we refuse).
3. The produced HTML is re-read: the DATA constant must be valid JSON.

Usage:
  python3 make_board.py tickets.json --out board-ready.html
  python3 make_board.py --test
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "board.html")

# The block to replace, delimited by the declaration and the `};` that closes it.
START = "const DATA="
END = "\n};\n"


class BoardError(RuntimeError):
    """The HTML could not be produced. We do not ship a dubious board."""


def _clean(tickets: list[dict]) -> list[dict]:
    """Strip every demo field and refuse an unproven win."""
    clean = []
    for t in tickets:
        t = {k: v for k, v in t.items() if not k.startswith("_")}   # exit _demo_vat
        if t.get("status") == "won":
            if not t.get("invoice"):
                raise BoardError(
                    f"[{t.get('id')}] 'won' ticket with no invoice in tickets.json. "
                    f"The board would show an amount that nothing proves. ABORT.")
            m = t.get("vat_amount")
            if not isinstance(m, (int, float)) or isinstance(m, bool) or m <= 0:
                raise BoardError(
                    f"[{t.get('id')}] 'won' ticket with no amount read from the invoice. ABORT.")
            if t.get("estimated_potential"):
                raise BoardError(
                    f"[{t.get('id')}] a win carries an estimated amount: the two fields "
                    f"never coexist. ABORT.")
        clean.append(t)
    return clean


def build(tickets_path: str, out_path: str, template: str = TEMPLATE) -> dict:
    data = json.load(open(tickets_path, encoding="utf-8"))
    tickets = _clean(data.get("tickets", []))
    pot = data.get("pot", {})

    payload = {
        "pot": {"expiry": pot.get("expiry", {})},
        "tickets": tickets,
    }

    html = open(template, encoding="utf-8").read()
    i = html.index(START)
    j = html.index(END, i) + len(END)
    block = "const DATA=" + json.dumps(payload, ensure_ascii=False, indent=1) + ";\n"
    html = html[:i] + block + html[j:]

    # Check: the re-injected constant must be re-readable...
    i2 = html.index(START) + len(START)
    j2 = html.index(";\n", i2)
    block_data = html[i2:j2]
    json.loads(block_data)                        # raises if the JSON is broken

    # ...and contain NO demo field. (The JS code itself keeps its `_demo_vat`
    # support: that's the offline demo mode. What is forbidden is a PRODUCTION
    # DATUM carrying one.)
    if "_demo" in block_data:
        raise BoardError("a demo field survived injection — "
                         "the board would show a simulated amount. ABORT.")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    sec = sum(t["vat_amount"] for t in tickets if t.get("status") == "won")
    lock = sum(t.get("estimated_potential") or 0 for t in tickets
               if t.get("status") in ("to_play", "to_secure"))
    return {"file": out_path, "tickets": len(tickets),
            "secured": round(sec, 2), "locked": lock,
            "openable": sum(1 for t in tickets if t.get("status") in
                            ("won", "to_play", "to_secure", "fix"))}


def _tests() -> None:
    import tempfile
    d = tempfile.mkdtemp()
    tj = os.path.join(d, "t.json")
    json.dump({"pot": {"expiry": {"2026-12-31": 25.8}}, "tickets": [
        {"id": "T1", "status": "won", "supplier": "Darty", "nature": "Hardware",
         "vat_amount": 25.8, "estimated_potential": None, "deadline": "2026-12-31",
         "invoice": {"file": "d.pdf"}, "_demo_vat": 999.0},
        {"id": "T2", "status": "to_play", "supplier": "LDLC", "nature": "Hardware",
         "estimated_potential": 149, "effort_minutes": 3, "hourly_rate": 2980,
         "action": "ldlc.com > My orders", "url": "https://secure.ldlc.com/fr-fr/Account/Orders",
         "amount_label": "Up to 149 € — if your LDLC invoice carries French VAT."},
    ]}, open(tj, "w"), ensure_ascii=False)

    out = os.path.join(d, "p.html")
    r = build(tj, out)
    html = open(out, encoding="utf-8").read()
    block = html.split(START, 1)[1].split(";\n", 1)[0]    # the DATA only
    assert "_demo" not in block, "a demo field survived in the data"
    assert "999" not in block, "a simulated amount survived"
    assert '"url": "https://secure.ldlc.com' in block, "the url must reach the board"
    assert r["secured"] == 25.8 and r["locked"] == 149
    print("PASS  injection: demo fields stripped, url kept, counters correct")

    # A win with no invoice, slipped in by hand into tickets.json -> refused.
    json.dump({"tickets": [{"id": "X", "status": "won", "supplier": "F",
                            "vat_amount": 50.0}]}, open(tj, "w"))
    try:
        build(tj, out)
        raise SystemExit("FAIL: a win with no invoice reached the board.")
    except BoardError as e:
        assert "no invoice" in str(e)
    print("PASS  guardrail: a win with no invoice never reaches the screen")
    print("\n2/2 — the board cannot show an amount that nothing proves.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tickets", nargs="?", default="tickets.json")
    ap.add_argument("--out", default="board-ready.html")
    ap.add_argument("--template", default=TEMPLATE)
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        _tests()
        return
    try:
        r = build(a.tickets, a.out, a.template)
    except BoardError as e:
        print(f"\n🛑 BOARD REFUSED\n{e}\n", file=sys.stderr)
        sys.exit(2)
    print(f"Board ready: {r['file']}")
    print(f"  {r['openable']} openable cards out of {r['tickets']} tickets")
    print(f"  ✅ SECURED : {r['secured']:.2f} €")
    print(f"  🔒 LOCKED  : up to {r['locked']} €")
    print(f"\n→ mcp__cowork__create_artifact(id='vat-tickets-board', html_path='{r['file']}')")


if __name__ == "__main__":
    main()
