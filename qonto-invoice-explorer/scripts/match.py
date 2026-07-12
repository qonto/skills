#!/usr/bin/env python3
"""Match extracted PDFs to Qonto transactions.

Inputs:
- `--pdfs` : JSONL from `extract_pdf.py --dir`  (one line per PDF)
- `--txs`  : JSON dump of Qonto transactions (list or {transactions:[]})
- `--vendor-keyword` (repeatable, optional): only consider tx whose label /
  clean_counterparty_name contains one of these substrings (case-insensitive).
  Use when scoping to one vendor group.

Matching rules (see references/matching-strategy.md):
- Prefer local_currency-based amount match for USD (or non-EUR)-billed vendors.
- Amount tolerance: ± 0.02 (rounding).
- Date window: default ± 5 days on `emitted_at`, widen with `--date-tolerance`.
- Never guess when ambiguous — dumps candidates and lets caller (agent/user) decide.

Output on stdout: JSON with two arrays:
    {"matches": [{"tx_id": ..., "pdf": ..., "confidence": "high"}],
     "ambiguous": [{"tx_id": ..., "candidates": [...]}],
     "unmatched_pdfs": [...],
     "unmatched_txs": [...]}
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import date, datetime, timedelta


def load_txs(path: str) -> list[dict]:
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict) and "transactions" in data:
        return data["transactions"]
    if isinstance(data, list) and data and "transactions" in data[0]:
        return [t for p in data for t in p.get("transactions", [])]
    return data


def load_pdfs(path: str) -> list[dict]:
    pdfs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                pdfs.append(json.loads(line))
    return pdfs


def parse_date(s: str | None) -> date | None:
    if not s:
        return None
    return datetime.fromisoformat(s[:10]).date()


def vendor_match(tx: dict, keywords: list[str] | None, pdf_vendor: str | None) -> bool:
    """Check whether the tx's label loosely matches the PDF vendor or vendor keywords."""
    tx_bag = " ".join(filter(None, [
        tx.get("clean_counterparty_name") or "",
        tx.get("label") or "",
    ])).lower()
    if keywords:
        if not any(k.lower() in tx_bag for k in keywords):
            return False
    if pdf_vendor:
        v = pdf_vendor.lower()
        # allow tokens overlap: at least one non-trivial word from vendor
        toks = [t for t in v.split() if len(t) >= 4]
        if toks and not any(t in tx_bag for t in toks):
            return False
    return True


def amount_matches(tx: dict, pdf_amt: float, pdf_cur: str | None,
                   amt_tol: float) -> str | None:
    """Return the axis on which they match: 'eur', 'local', or None."""
    # Try EUR (Qonto amount) first
    eur = tx.get("amount")
    if eur is not None and abs(float(eur) - pdf_amt) <= amt_tol:
        return "eur"
    # Try local currency
    loc = tx.get("local_amount")
    loc_cur = tx.get("local_currency")
    if (loc is not None and loc_cur == pdf_cur
            and abs(float(loc) - pdf_amt) <= amt_tol):
        return "local"
    return None


def match(pdfs: list[dict], txs: list[dict], keywords: list[str] | None,
          date_tol: int, amt_tol: float) -> dict:
    # Only tx that need attachment
    need = [t for t in txs
            if t.get("attachment_required")
            and not t.get("attachment_ids")
            and not t.get("attachment_lost")
            and t.get("side") == "debit"]

    matches = []
    ambiguous = []
    used_tx_ids: set[str] = set()
    used_pdfs: set[str] = set()

    for pdf in pdfs:
        pdf_amt = pdf.get("amount")
        pdf_cur = pdf.get("currency")
        pdf_date = parse_date(pdf.get("date"))
        pdf_vendor = pdf.get("vendor")

        if pdf_amt is None or pdf_date is None:
            continue  # extractor couldn't parse

        candidates: list[dict] = []
        for tx in need:
            if tx["id"] in used_tx_ids:
                continue
            if not vendor_match(tx, keywords, pdf_vendor):
                continue
            axis = amount_matches(tx, pdf_amt, pdf_cur, amt_tol)
            if not axis:
                continue
            tx_date = parse_date(tx.get("emitted_at") or tx.get("settled_at"))
            if tx_date is None:
                continue
            days = abs((tx_date - pdf_date).days)
            if days > date_tol:
                continue
            candidates.append({
                "tx_id": tx["id"],
                "tx_date": tx_date.isoformat(),
                "tx_label": tx.get("label"),
                "tx_amount": tx.get("amount"),
                "tx_local": tx.get("local_amount"),
                "tx_local_cur": tx.get("local_currency"),
                "axis": axis,
                "days_delta": days,
            })

        if len(candidates) == 1:
            c = candidates[0]
            conf = "high" if c["days_delta"] <= 2 else "medium"
            matches.append({
                "tx_id": c["tx_id"],
                "pdf": pdf["file"],
                "pdf_vendor": pdf_vendor,
                "pdf_amount": pdf_amt,
                "pdf_currency": pdf_cur,
                "pdf_date": pdf["date"],
                "match_axis": c["axis"],
                "days_delta": c["days_delta"],
                "confidence": conf,
            })
            used_tx_ids.add(c["tx_id"])
            used_pdfs.add(pdf["file"])
        elif len(candidates) > 1:
            ambiguous.append({"pdf": pdf["file"], "pdf_vendor": pdf_vendor,
                              "pdf_amount": pdf_amt, "pdf_date": pdf["date"],
                              "candidates": candidates})

    unmatched_pdfs = [p["file"] for p in pdfs
                      if p["file"] not in used_pdfs
                      and p.get("amount") is not None]
    unmatched_txs = [t["id"] for t in need if t["id"] not in used_tx_ids]

    return {"matches": matches, "ambiguous": ambiguous,
            "unmatched_pdfs": unmatched_pdfs, "unmatched_txs": unmatched_txs}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--pdfs", required=True, help="JSONL from extract_pdf.py --dir")
    p.add_argument("--txs", required=True, help="Qonto transactions JSON dump")
    p.add_argument("--vendor-keyword", action="append",
                   help="Filter to tx whose label contains this (repeatable)")
    p.add_argument("--date-tolerance", type=int, default=5,
                   help="Days window on emitted_at (default 5)")
    p.add_argument("--amount-tolerance", type=float, default=0.02,
                   help="Absolute amount tolerance (default 0.02)")
    args = p.parse_args()

    pdfs = load_pdfs(args.pdfs)
    txs = load_txs(args.txs)
    result = match(pdfs, txs, args.vendor_keyword,
                   args.date_tolerance, args.amount_tolerance)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"[match] matched={len(result['matches'])} "
          f"ambiguous={len(result['ambiguous'])} "
          f"unmatched_pdfs={len(result['unmatched_pdfs'])} "
          f"unmatched_txs={len(result['unmatched_txs'])}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
