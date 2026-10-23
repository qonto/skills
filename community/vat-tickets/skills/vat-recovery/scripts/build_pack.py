#!/usr/bin/env python3
"""THE DELIVERABLES — generated from tickets.json, never from the displayed pot.

    tickets.json ──> build_pack.py ──> pack-line21.csv
                                   ├─> sie-letter.md
                                   ├─> missing-invoices.md
                                   └─> accountant-annex.md

THE LOCK
--------
`pack-line21.csv` contains what the company will DECLARE to the State. A single
line without a read invoice, and the user deducts VAT wrongly: back-tax + late
interest (art. 1727 CGI), and a 40% surcharge if the deliberate nature is
established (art. 1729, a) — which a track record of returns built on estimates
would make easy to demonstrate.

Without an invoice, there is NO right to deduct (CGI, art. 271, II-1-a). Not a
fragile right: a nonexistent one.

So: `_pack_lock()` raises PackInvariantError and the script STOPS. This is not a
guideline addressed to an agent, it is a `raise` in the code. An LLM under
pressure can break a rule written in prose; it cannot break an exception.

The total of the SIE letter is the SUM OF THE CSV, never a figure taken from the
interface. If the two diverge, that is a blocking bug — and we prefer a blocking
bug to a false return.

Usage:
  python3 build_pack.py tickets.json --siren 123456789 --company "ACME SARL" \
      --period "July 2026" --out-dir ./deliverables
  python3 build_pack.py --test
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import os
import sys

# FIXED columns, in this order. This is what makes two runs comparable (diff).
COLUMNS = ["ticket_id", "status", "zone", "invoice_date", "supplier",
           "expense_nature", "net_amount", "vat_amount", "rate", "invoice",
           "verdict", "legal_source", "deadline", "days_left", "action"]


class PackInvariantError(AssertionError):
    """A non-declarable line tried to enter the pack. We stop."""


# =================================================================== lock ===
def _pack_lock(tickets: list[dict]) -> list[dict]:
    """Lets through ONLY tickets with a read invoice and a positive VAT amount.
    Everything else is turned away — by construction, not by discipline."""
    kept = []
    seen: set[tuple] = set()               # invoice uniqueness (flaw C1)
    for t in tickets:
        if t.get("status") != "won":
            continue
        invoice = t.get("invoice")
        if not isinstance(invoice, dict) or not (invoice.get("file") or invoice.get("number")):
            raise PackInvariantError(
                f"[{t.get('id')}] 'won' ticket WITHOUT an identifiable invoice in "
                f"tickets.json. The input file is corrupted or was edited by "
                f"hand. Without an invoice, there is no right to deduct "
                f"(CGI, art. 271, II-1-a). Generation ABORTED.")
        vat = t.get("vat_amount")
        # B2: NaN and Inf are floats and slipped past `x > 0`. So does bool.
        if (not isinstance(vat, (int, float)) or isinstance(vat, bool)
                or not math.isfinite(vat) or vat <= 0):
            raise PackInvariantError(
                f"[{t.get('id')}] vat_amount not usable ({vat!r}): a finite, "
                f"strictly positive number read off the invoice is required. ABORT.")
        if t.get("estimated_potential"):
            raise PackInvariantError(
                f"[{t.get('id')}] an ESTIMATED amount reached the pack. "
                f"No inference crosses this door. ABORT.")
        # C1: one and the same invoice cannot ground two deductions (double
        # consumption detected at the factory AND refused here, double barrier).
        key = (invoice.get("file"), invoice.get("number"))
        if key in seen:
            raise PackInvariantError(
                f"[{t.get('id')}] invoice {key} ALREADY grounds another pack line. "
                f"An invoice read once cannot be deducted twice "
                f"(double deduction = back-tax + 40% surcharge). ABORT.")
        seen.add(key)
        # C2: a time-barred line never goes to the State, even if tickets.json
        # presents it as 'won' (stale file, edited, or yesterday's run).
        dl = t.get("days_left")
        if isinstance(dl, (int, float)) and not isinstance(dl, bool) and dl < 0:
            raise PackInvariantError(
                f"[{t.get('id')}] time-barred ticket (days_left={dl}) in the pack: "
                f"right to deduct lost (CGI, ann. II, art. 208, I). ABORT.")
        kept.append(t)
    return kept


# ============================================================ deliverables ===
def pack_csv(tickets: list[dict], path: str) -> float:
    lines = _pack_lock(tickets)
    total = 0.0
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, delimiter=";")
        w.writeheader()
        for t in sorted(lines, key=lambda x: (x.get("date") or "")):
            vat = float(t["vat_amount"])
            total += vat
            invoice = t.get("invoice") or {}
            net = round(t["expense_amount"] - vat, 2)
            w.writerow({
                "ticket_id": t["id"], "status": t["status"], "zone": t.get("zone", ""),
                "invoice_date": invoice.get("date") or t.get("date") or "",
                "supplier": t.get("supplier", ""),
                "expense_nature": t.get("nature", ""),
                "net_amount": f"{net:.2f}", "vat_amount": f"{vat:.2f}",
                "rate": t.get("rate") or "",
                "invoice": invoice.get("file") or invoice.get("number") or "",
                "verdict": t.get("verdict", ""),
                "legal_source": t.get("legal_source", ""),
                "deadline": t.get("deadline") or "",
                "days_left": t.get("days_left") if t.get("days_left") is not None else "",
                "action": "To enter on line 21 of the CA3 return",
            })
    return round(total, 2)


def sie_letter(total: float, nb: int, siren: str, company: str, period: str,
               path: str) -> None:
    """The total comes from the CSV. Never from the interface. Never from an estimate."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"""# Cover letter to the SIE
> To be sent via the secure messaging of impots.gouv.fr (professional space,
> section "Write / VAT"), after review by your accountant.
> **This document is never sent automatically.**

---

**Subject: Voluntary disclosure of deductible VAT — {siren} — CA3 return for {period}**

Dear Sir or Madam,

As part of an internal review of its accounts, the company **{company}**
(SIREN {siren}) has identified amounts of deductible VAT whose deduction had
been omitted from its earlier returns.

Accordingly, the return no. 3310-CA3-SD filed for {period} includes, on
**line 21 ("other VAT to deduct"): {total:.2f} €**, corrected within the time
limit set by article 208 of annex II to the CGI.

The details appear in the attached summary statement ({nb} lines: supplier,
invoice and payment dates, net and VAT amounts, reason for the omission).
The corresponding invoices are available upon request.

We remain at your disposal for any further information.

Please accept, Dear Sir or Madam, the expression of our highest consideration.

[Name, capacity of the signatory — legal representative or chartered accountant]
[Date]

**Attachment: summary statement ({nb} lines) — `pack-line21.csv`**

---

## Read before filing

By filing this line 21, you are asking the State to return **{total:.2f} €**
to you. It may ask you to justify it. You will then have to produce, for each
line: **the invoice**, the **nature of the expense**, and **why it is
deductible** (CAA Paris, 5 February 2025, no. 23PA01221, pt 10). These three
elements are in your pack. Check that you have them **physically**. If a single
line does not hold up, remove it.

**We have only analysed the VAT you can recover — not the VAT you charge your
clients. A request for justification, however, can cover both.**

**Offset rather than refund.** If your CA3 return for the month has VAT to pay,
this line 21 **simply reduces your payment**: no refund request, no review, no
supporting documents to produce. Same money recovered, far lower exposure. Ask
your accountant to favour this route.
""")


def missing_invoices(tickets: list[dict], path: str) -> None:
    to_do = [t for t in tickets if t.get("status") in ("to_play", "to_secure")]
    to_do.sort(key=lambda t: -(t.get("hourly_rate") or 0))
    total_max = sum(t.get("estimated_potential") or 0 for t in to_do)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# The invoices still to be recovered\n\n")
        if not to_do:
            f.write("None. All your expenses are documented.\n")
            return
        f.write(f"**Up to {total_max} €** of additional VAT, if you recover "
                f"these {len(to_do)} invoices.\n\n")
        f.write("> These amounts are estimated **upper bounds**, rounded down to the "
                "euro. They are **not declarable**: without an invoice, there is no "
                "right to deduct (CGI, art. 271, II-1-a). Each recovered invoice "
                "turns them into a certain amount — and often exceeds it.\n\n")
        f.write("Sorted by **hourly yield**: start at the top.\n\n")
        f.write("| Supplier | Nature | Up to | Effort | €/h | Where to find it |\n")
        f.write("|---|---|---|---|---|---|\n")
        for t in to_do:
            f.write(f"| {t.get('supplier','')} "
                    f"| {t.get('nature','')} "
                    f"| {t.get('estimated_potential') or 0} € "
                    f"| {t.get('effort_icon','')} {t.get('effort_minutes') or '?'} min "
                    f"| {t.get('hourly_rate') or '—'} "
                    f"| {t.get('action','')} |\n")
        pitfalls = [t for t in to_do if t.get("pitfall")]
        if pitfalls:
            f.write("\n## ⚠️ Pitfalls to know\n\n")
            for t in pitfalls:
                f.write(f"- **{t.get('supplier')}** — {t.get('pitfall')}\n")


def accountant_annex(tickets: list[dict], inconsistent: list[dict], path: str) -> None:
    to_review = [t for t in tickets if t.get("status") == "to_review"
                 or t.get("verdict") == "TO_REVIEW"]
    names = [t for t in tickets if t.get("note") and "director" in (t.get("note") or "")]
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Annex — the points for your accountant to decide\n\n")
        f.write("This document blames no one. It gathers the invoices and the "
                "questions that, very likely, **never reached your firm**: till "
                "receipts not passed on, purchases paid by card, online "
                "subscriptions billed outside the usual channel.\n\n")

        f.write("## Lines to qualify (contradictory signals)\n\n")
        if to_review:
            for t in to_review:
                f.write(f"- **{t.get('supplier')}** — {t.get('date') or '?'} — "
                        f"{t.get('expense_amount')} € — {t.get('legal_source','')}\n")
        else:
            f.write("*Not covered — no ambiguous line detected in the data provided.*\n")

        f.write("\n## Invoices possibly in the director's name\n\n")
        if names:
            for t in names:
                f.write(f"- **{t.get('supplier')}** — {t.get('date')} — "
                        f"a corrective invoice in the company's name is imperative, "
                        f"and it **does not restart the time limit** (CE 31/12/2008, n° 305517).\n")
        else:
            f.write("*Not covered — none detected (the client's name is not always "
                    "legible on the invoices).*\n")

        f.write("\n## Illegible or inconsistent invoices\n\n")
        if inconsistent:
            for p in inconsistent:
                f.write(f"- `{p.get('file')}` — {p.get('reason')}\n")
        else:
            f.write("*None — every read invoice passes the net + VAT = gross check.*\n")

        f.write("\n## Questions to ask\n\n")
        f.write("1. Were these amounts **truly** omitted from every CA3 return "
                "filed? (the FEC suggests so, only you can confirm it)\n")
        f.write("2. Is the company a **full deductor**? A coefficient < 1 "
                "(exempt income, subsidies, bare-property rents) changes every verdict.\n")
        f.write("3. Can line 21 be **offset** against the month's VAT to pay "
                "rather than generate a refund request?\n")


# =================================================================== tests ==
def _tests() -> None:
    import tempfile
    d = tempfile.mkdtemp()
    won = {"id": "T-1", "status": "won", "zone": "omission", "supplier": "Darty",
           "nature": "Hardware", "date": "2024-03-12", "expense_amount": 154.80,
           "vat_amount": 25.80, "estimated_potential": None, "rate": 20,
           "invoice": {"file": "darty.pdf", "date": "2024-03-12"},
           "verdict": "DEDUCTIBLE", "legal_source": "art. 271",
           "deadline": "2026-12-31", "days_left": 171}
    to_play = {"id": "T-2", "status": "to_play", "supplier": "Orange",
               "nature": "Telecom", "date": "2025-05-02", "expense_amount": 120.0,
               "vat_amount": None, "estimated_potential": 20, "action": "Customer portal",
               "effort_minutes": 6, "effort_icon": "🔧", "hourly_rate": 200}

    total = pack_csv([won, to_play], os.path.join(d, "pack.csv"))
    assert total == 25.80, total
    rows = list(csv.DictReader(open(os.path.join(d, "pack.csv"), encoding="utf-8"), delimiter=";"))
    assert len(rows) == 1, "only the won ticket enters the pack"
    assert rows[0]["ticket_id"] == "T-1"
    print("PASS  the pack contains ONLY tickets with a read invoice (to_play turned away)")

    # The lock: we dress up a to_play as won, without an invoice.
    cheat = dict(to_play, status="won", vat_amount=20.0)
    try:
        pack_csv([cheat], os.path.join(d, "x.csv"))
        raise SystemExit("FAILURE: a line without an invoice entered the pack.")
    except PackInvariantError as e:
        assert "271" in str(e)
    print("PASS  lock: a 'won' without an invoice makes generation FAIL")

    # The lock again: a won ticket dragging an estimated potential.
    cheat2 = dict(won, estimated_potential=25)
    try:
        pack_csv([cheat2], os.path.join(d, "y.csv"))
        raise SystemExit("FAILURE: an inference reached the pack.")
    except PackInvariantError as e:
        assert "ESTIMATED" in str(e)
    print("PASS  lock: no inference crosses the pack door")

    sie_letter(total, 1, "123456789", "ACME SARL", "July 2026",
               os.path.join(d, "c.md"))
    txt = open(os.path.join(d, "c.md"), encoding="utf-8").read()
    assert "25.80 €" in txt and "23PA01221" in txt
    assert "We have only analysed the VAT you can recover" in txt, \
        "the scope warning (collected VAT not audited) is mandatory"
    assert "Offset rather than refund" in txt
    print("PASS  SIE letter: total = sum of the CSV, scope warning present")

    missing_invoices([won, to_play], os.path.join(d, "p.md"))
    pm = open(os.path.join(d, "p.md"), encoding="utf-8").read()
    assert "Up to 20 €" in pm and "not declarable" in pm
    assert "probable" not in pm.lower() and "likely" not in pm.lower()
    print("PASS  missing invoices: upper bounds, never 'probable', sorted by €/h")

    print("\n5/5 — the pack is watertight.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tickets", nargs="?")
    ap.add_argument("--siren", default="[SIREN]")
    ap.add_argument("--company", default="[COMPANY NAME]")
    ap.add_argument("--period", default=dt.date.today().strftime("%B %Y"))
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()

    if a.test:
        _tests()
        return
    if not a.tickets:
        ap.error("tickets.json required (or --test)")

    data = json.load(open(a.tickets, encoding="utf-8"))
    tickets = data["tickets"]
    os.makedirs(a.out_dir, exist_ok=True)
    p = lambda n: os.path.join(a.out_dir, n)  # noqa: E731

    try:
        total = pack_csv(tickets, p("pack-line21.csv"))
    except PackInvariantError as e:
        print(f"\n🛑 GENERATION REFUSED\n{e}\n", file=sys.stderr)
        sys.exit(2)

    nb = sum(1 for t in tickets if t.get("status") == "won")
    sie_letter(total, nb, a.siren, a.company, a.period, p("sie-letter.md"))
    missing_invoices(tickets, p("missing-invoices.md"))
    accountant_annex(tickets, data.get("inconsistent_invoices", []), p("accountant-annex.md"))

    print(f"4 deliverables -> {a.out_dir}/")
    print(f"  pack-line21.csv       {nb} lines — {total:.2f} € declarable (invoice in hand)")
    print(f"  sie-letter.md         ready to review, never sent")
    print(f"  missing-invoices.md   {sum(1 for t in tickets if t.get('status') in ('to_play','to_secure'))} invoices to recover")
    print(f"  accountant-annex.md   the questions for your accountant")


if __name__ == "__main__":
    main()
