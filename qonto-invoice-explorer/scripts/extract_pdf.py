#!/usr/bin/env python3
"""Extract vendor / amount / currency / date / invoice_number from a receipt PDF.

Uses `pdftotext -layout` under the hood — requires `poppler` (`brew install poppler`).

Emits JSON on stdout:
    {"file": "...", "vendor": "...", "amount": 22.50, "currency": "USD",
     "date": "2026-02-20", "invoice_number": "0LDTB5YS-0002", "text_len": 1234}

If the PDF looks OCR-needed (very short extracted text), emits a hint on stderr.

Usage:
    scripts/extract_pdf.py path/to/invoice.pdf
    scripts/extract_pdf.py --dir path/to/folder/       # process every *.pdf, emit one JSON per line
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


FR_MONTHS = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "août": 8, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11,
    "décembre": 12, "decembre": 12,
}
EN_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}


def pdftotext(path: str) -> str:
    try:
        return subprocess.check_output(
            ["pdftotext", "-layout", path, "-"],
            stderr=subprocess.DEVNULL,
        ).decode("utf-8", errors="replace")
    except FileNotFoundError:
        raise SystemExit("pdftotext not found — install poppler: brew install poppler")
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"pdftotext failed on {path}: {e}")


def detect_amount(text: str) -> tuple[float | None, str | None]:
    """Return (amount, currency)."""
    patterns = [
        # "$22.50 USD due", "$99.00 USD paid"
        (r"\$\s*([\d,]+\.\d{2})\s+USD", "USD"),
        # "Amount due 22.50 USD"
        (r"Amount due\s+([\d,]+\.\d{2})\s+USD", "USD"),
        (r"Amount due\s+([\d,]+\.\d{2})\s+EUR", "EUR"),
        (r"Total\s+([\d,]+\.\d{2})\s+USD", "USD"),
        (r"Total\s+([\d,]+\.\d{2})\s+EUR", "EUR"),
        # "€ 12.00 due", "12,00 € payés le", "70,80 €"
        (r"(?:€|EUR)\s*([\d,]+[.,]\d{2})", "EUR"),
        (r"([\d,]+[.,]\d{2})\s*€", "EUR"),
        # "$XX.XX"
        (r"\$\s*([\d,]+\.\d{2})", "USD"),
        # "Total TTC 27,82"
        (r"Total\s+TTC\s+([\d,]+[.,]\d{2})", "EUR"),
        # Google Cloud "Solde de clôture en EUR: 27,82"
        (r"Solde de clôture en EUR[:\s]+([\d,]+[.,]?\d*)", "EUR"),
        (r"Closing balance in EUR[:\s]+([\d,]+[.,]?\d*)", "EUR"),
    ]
    best: tuple[float, str] | None = None
    for pat, cur in patterns:
        for m in re.finditer(pat, text):
            raw = m.group(1).replace(",", ".")
            # If comma is thousands separator ("1,234.56"), normalize
            # Heuristic: if raw contains 2 dots, it was thousands; keep as-is
            try:
                # Handle "1,234.56" (comma = thousands) → "1234.56"
                original = m.group(1)
                if original.count(",") == 1 and original.count(".") == 1 \
                   and original.index(",") < original.index("."):
                    val = float(original.replace(",", ""))
                else:
                    val = float(raw)
            except ValueError:
                continue
            # Prefer amounts >= 1 (avoid TVA rate lines like "20%")
            if val < 0.5:
                continue
            cand = (val, cur)
            # Prefer the largest match (usually the total)
            if best is None or val > best[0]:
                best = cand
    return best if best else (None, None)


def detect_date(text: str) -> str | None:
    """Return ISO date YYYY-MM-DD."""
    # English formats: "February 20, 2026", "Feb 20 2026"
    for m in re.finditer(
        r"\b(" + "|".join(EN_MONTHS.keys()) + r")\s+(\d{1,2}),?\s+(\d{4})\b",
        text, re.I,
    ):
        mm = EN_MONTHS[m.group(1).lower()]
        dd = int(m.group(2))
        yy = int(m.group(3))
        try:
            return datetime(yy, mm, dd).date().isoformat()
        except ValueError:
            continue
    # French format: "20 février 2026" / "15 avril 2026"
    for m in re.finditer(
        r"\b(\d{1,2})\s+(" + "|".join(FR_MONTHS.keys()) + r")\s+(\d{4})\b",
        text, re.I,
    ):
        dd = int(m.group(1))
        mm = FR_MONTHS[m.group(2).lower()]
        yy = int(m.group(3))
        try:
            return datetime(yy, mm, dd).date().isoformat()
        except ValueError:
            continue
    # ISO YYYY-MM-DD
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # French DD/MM/YYYY
    m = re.search(r"\b(\d{2})/(\d{2})/(\d{4})\b", text)
    if m:
        try:
            return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))).date().isoformat()
        except ValueError:
            pass
    return None


def detect_invoice_number(text: str) -> str | None:
    for pat in [
        r"Invoice number\s+([A-Z0-9\-]+)",
        r"Facture n[°º]\s*([A-Z0-9\-/]+)",
        r"N°\s*facture\s*[:\s]*([A-Z0-9\-/]+)",
        r"Receipt number\s+([A-Z0-9\-]+)",
        r"Reçu\s+#([A-Z0-9\-]+)",
    ]:
        m = re.search(pat, text, re.I)
        if m:
            return m.group(1).strip()
    return None


def _clean_vendor(s: str) -> str:
    # pdftotext -layout preserves spacing → the vendor line may look like
    # "Vercel Inc.                                Bill to"
    # Strip anything after 3+ whitespace (typical two-column artifact).
    s = re.split(r"\s{3,}", s, maxsplit=1)[0].strip()
    return s


def detect_vendor(text: str) -> str | None:
    lines = [l.rstrip() for l in text.splitlines() if l.strip()]
    if not lines:
        return None
    # Stripe hosted invoice: skip "Invoice" header then look for capitalized
    # vendor block a few lines below
    for i, l in enumerate(lines[:6]):
        low = l.strip().lower()
        if low.startswith(("invoice", "facture", "reçu", "receipt")):
            for k in range(i + 1, min(i + 8, len(lines))):
                cand = _clean_vendor(lines[k])
                if not cand:
                    continue
                if cand.lower().startswith(
                    ("date ", "invoice number", "facture ", "amount ", "solde ",
                     "statement", "period")
                ):
                    continue
                if 3 <= len(cand) <= 80:
                    return cand
    # Fallback: first meaningful line, cleaned
    for l in lines[:5]:
        cand = _clean_vendor(l)
        if 3 <= len(cand) <= 80 and not cand.lower().startswith(("page", "statement")):
            return cand
    return None


def process(path: str) -> dict:
    text = pdftotext(path)
    amt, cur = detect_amount(text)
    result = {
        "file": path,
        "vendor": detect_vendor(text),
        "amount": amt,
        "currency": cur,
        "date": detect_date(text),
        "invoice_number": detect_invoice_number(text),
        "text_len": len(text),
    }
    if len(text) < 100:
        print(f"[extract_pdf] WARN: only {len(text)} chars extracted from {path} "
              f"— may be a scanned/image PDF needing OCR", file=sys.stderr)
    return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("path", nargs="?", help="PDF file (omit if --dir used)")
    p.add_argument("--dir", help="Directory of PDFs — process each, emit JSONL")
    args = p.parse_args()

    if args.dir:
        for pdf in sorted(Path(args.dir).rglob("*.pdf")):
            print(json.dumps(process(str(pdf)), ensure_ascii=False))
    elif args.path:
        print(json.dumps(process(args.path), indent=2, ensure_ascii=False))
    else:
        p.error("Provide a file path or --dir")


if __name__ == "__main__":
    main()
