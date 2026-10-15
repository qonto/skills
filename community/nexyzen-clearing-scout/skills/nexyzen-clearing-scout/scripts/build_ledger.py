#!/usr/bin/env python3
"""build_ledger.py — Normalize Qonto invoice data into a clearing ledger.

Reads client invoices (receivables) and supplier invoices (payables) as
returned by the Qonto MCP tools `list_client_invoices` / `list_supplier_invoices`
(or equivalent Business API payloads) and produces a deterministic JSON ledger:

  - counterparties deduplicated by normalized VAT / tax identification number
    (handles country prefixes, spelling variants and OCR typos in names);
  - open positions per counterparty (credit = they owe us, debit = we owe them);
  - explicit partial-payment notes ("residuo EUR 1.234,56") are honored;
  - settled invoices (paid) are excluded from open positions;
  - receivables aging buckets and total frozen working capital.

No AI in the math: same input, same output, fully auditable.

Usage:
  python build_ledger.py --clients client_invoices.json \
                         --suppliers supplier_invoices.json \
                         [--as-of YYYY-MM-DD] [--out ledger.json]

Input files may be either the raw MCP tool output (with "client_invoices" /
"supplier_invoices" arrays) or a bare JSON array of invoices.
"""

import argparse
import datetime as dt
import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP

TWO_PLACES = Decimal("0.01")

# Invoice states that mean "no longer an open position".
CLIENT_CLOSED_STATUSES = {"paid", "canceled", "cancelled"}
SUPPLIER_CLOSED_STATUSES = {"paid", "rejected", "archived"}

# Matches explicit residual-amount notes left on invoices, e.g.
# "ACCONTO 50% GIA' INCASSATO (residuo EUR 4.617,50)" or "residuo € 1.200,00".
RESIDUAL_NOTE_RE = re.compile(
    r"resid[uo]\w*\s*[:\s]\s*(?:EUR|€)?\s*([0-9][0-9.,]*)", re.IGNORECASE
)

EU_VAT_PREFIXES = (
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR",
    "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO",
    "SE", "SI", "SK", "XI", "CH", "GB",
)


def parse_amount(raw) -> Decimal:
    """Parse '1234.56', '1.234,56', 1234.56 or {'value': '1234.56'} into Decimal."""
    if raw is None:
        return Decimal("0")
    if isinstance(raw, dict):
        raw = raw.get("value", "0")
    s = str(raw).strip().replace("€", "").replace("EUR", "").strip()
    if not s:
        return Decimal("0")
    if "," in s and "." in s:
        # 1.234,56 (EU) vs 1,234.56 (US): the last separator is the decimal mark.
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    return Decimal(s).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def normalize_vat(raw: str) -> str:
    """Normalize a VAT / tax identification number for matching.

    Uppercases, strips spaces/dots/dashes and removes a leading country
    prefix so that 'IT01982340992' and '01982340992' match.
    """
    if not raw:
        return ""
    v = re.sub(r"[\s.\-]", "", str(raw)).upper()
    for prefix in EU_VAT_PREFIXES:
        if v.startswith(prefix) and len(v) > len(prefix) and v[len(prefix)].isdigit():
            return v[len(prefix):]
    return v


def vat_country(raw: str) -> str | None:
    """Country prefix of a raw VAT number, when present ('IT01...' -> 'IT')."""
    if not raw:
        return None
    v = re.sub(r"[\s.\-]", "", str(raw)).upper()
    for prefix in EU_VAT_PREFIXES:
        if v.startswith(prefix) and len(v) > len(prefix) and v[len(prefix)].isdigit():
            return prefix
    return None


def italian_vat_check_digit_ok(vat: str) -> bool:
    """Validate the check digit of an 11-digit Italian partita IVA."""
    if not re.fullmatch(r"\d{11}", vat):
        return False
    total = 0
    for i, ch in enumerate(vat[:10]):
        n = int(ch)
        if i % 2 == 0:
            total += n
        else:
            n *= 2
            total += n if n < 10 else n - 9
    return (10 - total % 10) % 10 == int(vat[10])


def extract_residual_note(*texts) -> Decimal | None:
    """Look for an explicit 'residuo EUR x' note in free-text fields."""
    for text in texts:
        if not text:
            continue
        m = RESIDUAL_NOTE_RE.search(str(text))
        if m:
            return parse_amount(m.group(1))
    return None


def load_invoices(path: str, key: str) -> list:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get(key, [])


def client_invoice_texts(inv: dict):
    yield inv.get("terms_and_conditions")
    yield inv.get("header")
    yield inv.get("footer")
    for item in inv.get("items") or []:
        yield item.get("title")
        yield item.get("description")
    yield inv.get("item_title")  # fixtures format


def extract_client_invoice(inv: dict) -> dict | None:
    """Map one Qonto client invoice to a ledger row (or None if not open)."""
    status = (inv.get("status") or "").lower()
    client = inv.get("client") or {}
    vat_raw = (
        client.get("vat_number")
        or client.get("tax_identification_number")
        or ""
    )
    total = parse_amount(inv.get("total_amount"))
    if status in CLIENT_CLOSED_STATUSES or status == "draft":
        open_amount = Decimal("0")
    else:
        open_amount = total
        # Partial payments: Qonto client invoices carry no residual field, but
        # real ledgers do — honor explicit notes and paid_amount when present.
        residual = extract_residual_note(*client_invoice_texts(inv))
        if residual is not None:
            open_amount = residual
        elif inv.get("paid_amount") is not None:
            open_amount = total - parse_amount(inv.get("paid_amount"))
    return {
        "kind": "receivable",
        "number": inv.get("number") or inv.get("invoice_number") or "?",
        "counterparty_name": (client.get("name") or "").strip(),
        "counterparty_vat_raw": vat_raw,
        "issue_date": inv.get("issue_date"),
        "due_date": inv.get("due_date"),
        "status": status,
        "total_amount": str(total),
        "open_amount": str(open_amount.quantize(TWO_PLACES)),
    }


def extract_supplier_invoice(inv: dict) -> dict:
    status = (inv.get("status") or "").lower()
    vat_raw = inv.get("vat_number") or inv.get("tin_number") or ""
    total = parse_amount(inv.get("total_amount"))
    if status in SUPPLIER_CLOSED_STATUSES:
        open_amount = Decimal("0")
    else:
        payable = parse_amount(inv.get("payable_amount"))
        open_amount = payable if payable > 0 else total
    name = (inv.get("supplier_name") or inv.get("issuer_name") or "").strip()
    return {
        "kind": "payable",
        "number": inv.get("invoice_number") or inv.get("number") or "?",
        "counterparty_name": name,
        "counterparty_vat_raw": vat_raw,
        "issue_date": inv.get("issue_date"),
        "due_date": inv.get("due_date"),
        "status": status,
        "total_amount": str(total),
        "open_amount": str(open_amount.quantize(TWO_PLACES)),
    }


def aging_bucket(due_date: str, as_of: dt.date) -> str:
    if not due_date:
        return "unknown"
    due = dt.date.fromisoformat(due_date)
    overdue = (as_of - due).days
    if overdue <= 0:
        return "current"
    if overdue <= 30:
        return "1-30"
    if overdue <= 60:
        return "31-60"
    if overdue <= 90:
        return "61-90"
    return ">90"


def build_ledger(client_rows, supplier_rows, as_of: dt.date) -> dict:
    counterparties: dict[str, dict] = {}
    for row in client_rows + supplier_rows:
        vat = normalize_vat(row["counterparty_vat_raw"])
        key = vat or "NAME:" + row["counterparty_name"].upper()
        cp = counterparties.setdefault(key, {
            "vat": vat or None,
            "vat_country": None,
            "vat_check_digit_valid": italian_vat_check_digit_ok(vat) if vat else None,
            "names": [],
            "open_credit": Decimal("0"),
            "open_debit": Decimal("0"),
            "invoices": [],
        })
        if cp["vat_country"] is None:
            cp["vat_country"] = vat_country(row["counterparty_vat_raw"])
        if row["counterparty_name"] and row["counterparty_name"] not in cp["names"]:
            cp["names"].append(row["counterparty_name"])
        open_amount = Decimal(row["open_amount"])
        if row["kind"] == "receivable":
            cp["open_credit"] += open_amount
        else:
            cp["open_debit"] += open_amount
        row = dict(row)
        row["aging"] = aging_bucket(row["due_date"], as_of) if open_amount > 0 else None
        cp["invoices"].append(row)

    total_credit = sum((cp["open_credit"] for cp in counterparties.values()), Decimal("0"))
    total_debit = sum((cp["open_debit"] for cp in counterparties.values()), Decimal("0"))

    aging_totals: dict[str, Decimal] = {}
    for cp in counterparties.values():
        for inv in cp["invoices"]:
            if inv["kind"] == "receivable" and inv["aging"] and Decimal(inv["open_amount"]) > 0:
                aging_totals[inv["aging"]] = aging_totals.get(inv["aging"], Decimal("0")) + Decimal(inv["open_amount"])

    out_counterparties = []
    for cp in counterparties.values():
        role = "both" if cp["open_credit"] > 0 and cp["open_debit"] > 0 else (
            "client" if cp["open_credit"] > 0 else (
                "supplier" if cp["open_debit"] > 0 else "settled"))
        out_counterparties.append({
            "vat": cp["vat"],
            "vat_country": cp["vat_country"],
            "vat_check_digit_valid": cp["vat_check_digit_valid"],
            "canonical_name": max(cp["names"], key=len) if cp["names"] else None,
            "name_variants": cp["names"],
            "role": role,
            "open_credit": str(cp["open_credit"].quantize(TWO_PLACES)),
            "open_debit": str(cp["open_debit"].quantize(TWO_PLACES)),
            "net_position": str((cp["open_credit"] - cp["open_debit"]).quantize(TWO_PLACES)),
            "invoices": cp["invoices"],
        })
    # Deterministic ordering: largest absolute net position first, VAT as tiebreak.
    out_counterparties.sort(key=lambda c: (-abs(Decimal(c["net_position"])), c["vat"] or ""))

    overdue_credit = sum(
        (v for k, v in aging_totals.items() if k not in ("current", "unknown")),
        Decimal("0"),
    )
    return {
        "generated_by": "nexyzen-clearing-scout/build_ledger.py",
        "as_of": as_of.isoformat(),
        "totals": {
            "open_receivables": str(total_credit.quantize(TWO_PLACES)),
            "open_payables": str(total_debit.quantize(TWO_PLACES)),
            "net_position": str((total_credit - total_debit).quantize(TWO_PLACES)),
            "frozen_working_capital": str((total_credit + total_debit).quantize(TWO_PLACES)),
            "overdue_receivables": str(overdue_credit.quantize(TWO_PLACES)),
        },
        "receivables_aging": {k: str(v.quantize(TWO_PLACES)) for k, v in sorted(aging_totals.items())},
        "counterparties": out_counterparties,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--clients", required=True, help="client invoices JSON (Qonto MCP output)")
    ap.add_argument("--suppliers", required=True, help="supplier invoices JSON (Qonto MCP output)")
    ap.add_argument("--as-of", default=None, help="reference date YYYY-MM-DD (default: today)")
    ap.add_argument("--out", default="ledger.json", help="output ledger path")
    args = ap.parse_args()

    as_of = dt.date.fromisoformat(args.as_of) if args.as_of else dt.date.today()

    client_rows = [r for r in (extract_client_invoice(i) for i in load_invoices(args.clients, "client_invoices")) if r]
    supplier_rows = [extract_supplier_invoice(i) for i in load_invoices(args.suppliers, "supplier_invoices")]

    ledger = build_ledger(client_rows, supplier_rows, as_of)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)

    t = ledger["totals"]
    print(f"Ledger written to {args.out} (as of {ledger['as_of']})")
    print(f"  Open receivables : EUR {t['open_receivables']}")
    print(f"  Open payables    : EUR {t['open_payables']}")
    print(f"  Net position     : EUR {t['net_position']}")
    print(f"  Overdue (recv.)  : EUR {t['overdue_receivables']}")
    both = [c for c in ledger["counterparties"] if c["role"] == "both"]
    print(f"  Counterparties   : {len(ledger['counterparties'])} "
          f"({len(both)} both client and supplier)")
    for c in both:
        print(f"    -> {c['canonical_name']} (VAT {c['vat']}): "
              f"credit EUR {c['open_credit']} vs debit EUR {c['open_debit']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
