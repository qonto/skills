#!/usr/bin/env python3
"""submit_to_nexyzen.py — Send open ledger positions to the Nexyzen clearing engine.

Bridges Qonto data to the Nexyzen / Camera di Compensazione web service
(https://webapp.cameracompensazione.it), where the multilateral clearing
algorithm runs server-side over the whole network of participants.

Flow (see swagger: /webservices/index.php):
  1. POST /connect     (op "gjwt")        -> 1-hour JWT
  2. POST /send_manual (op "ins_manuale") -> one call per open invoice

VAT numbers are sent IN CLEAR, together with invoice numbers, dates and amounts
of THIRD PARTIES (your counterparties), who have not agreed to any of it. That
is not optional polish: the clearing engine matches companies by VAT number, so
without clear VAT numbers it cannot find cycles across the network. There is no
hashed or "anonymous" mode on purpose: VAT numbers are public, a hash of them
is trivially reversible and would only suggest a protection that does not
exist. No payment is ever initiated: the engine only detects offset
opportunities.

Credentials come from plain environment variables and are NEVER stored in the repo:
  NEXYZEN_AFFILIATE_CODE   affiliate code (from commerciale@cameracompensazione.it)
  NEXYZEN_TOKEN            API token
The API destination is fixed to Nexyzen over HTTPS; redirects are refused.

THIRD-PARTY TRANSMISSION: this script sends, for each open invoice, the VAT
numbers of both parties (in clear), invoice number, date, total and open
amount, plus an optional notification email, to Nexyzen — a service operated
by Camera di Compensazione S.r.l., not by Qonto.

The default is DRY RUN: it only prints what would be sent. With --send the
script additionally asks for a typed confirmation on the user's own terminal
(not stdin, so a calling agent cannot answer it). With no terminal available it
refuses and tells the user to run the command themselves.

Usage:
  python submit_to_nexyzen.py --ledger ledger.json --org-vat IT03671960833 \
      [--email you@company.com] [--exclude-invoice 2026/012 ...] \
      [--default-country IT] [--send]
"""

import argparse
import json
import os
import sys
import threading

from nexyzen_http import BASE_URL, post_json

PROVENANCE_CODE = "QONTO_MCP"  # native attribution for the Qonto integration


def confirm_on_user_terminal(expected: str) -> bool | None:
    """Ask the user to type `expected` on their own terminal.

    Reads from the terminal device (CONIN$ on Windows, /dev/tty elsewhere), never
    from stdin, so an agent that launches this script cannot answer for the user.
    Returns True/False for the typed answer, or None when no terminal exists.
    """
    dev_in, dev_out = ("CONIN$", "CONOUT$") if os.name == "nt" else ("/dev/tty", "/dev/tty")
    result: list = []

    def ask() -> None:
        try:
            with open(dev_out, "w") as out, open(dev_in) as inp:
                out.write(f"\nTo send, type exactly:  {expected}\n> ")
                out.flush()
                result.append(inp.readline().strip() == expected)
        except OSError:
            result.append(None)

    t = threading.Thread(target=ask, daemon=True)
    t.start()
    t.join(timeout=120)  # nobody at the terminal: give up instead of hanging
    return result[0] if result else None


def build_payloads(ledger: dict, org_vat: str, email: str | None,
                   default_country: str | None = None) -> list[dict]:
    """Map every open ledger invoice to a /send_manual 'dati' payload.

    Counterparties without a VAT number are skipped (with a warning): the
    clearing engine matches on VAT and cannot use name-only records.
    The country prefix seen in the source data is restored ('IT01...'),
    falling back to --default-country.
    """
    org_id = org_vat
    payloads = []
    for cp in ledger["counterparties"]:
        cp_vat = cp["vat"] or ""
        if not cp_vat:
            open_count = sum(1 for i in cp["invoices"] if float(i["open_amount"]) > 0)
            if open_count:
                print(f"SKIP {cp.get('canonical_name')}: no VAT number "
                      f"({open_count} open invoice(s) not submitted)", file=sys.stderr)
            continue
        country = cp.get("vat_country") or default_country or ""
        cp_id = country + cp_vat
        for inv in cp["invoices"]:
            open_amount = float(inv["open_amount"])
            if open_amount <= 0:
                continue
            receivable = inv["kind"] == "receivable"
            dati = {
                # 'v' = sales invoice (we are the creditor), 'a' = purchase.
                "tipo_fattura": "v" if receivable else "a",
                "partita_iva_creditore": org_id if receivable else cp_id,
                "partita_iva_debitore": cp_id if receivable else org_id,
                "data_fattura": inv.get("issue_date"),
                "numero_fattura": inv.get("number"),
                "importo_totale": float(inv["total_amount"]),
                "importo_residuo": open_amount,
                "codProvenienza": PROVENANCE_CODE,
            }
            if email:
                dati["email_proponente"] = email
            payloads.append(dati)
    return payloads


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ledger", required=True, help="ledger.json from build_ledger.py")
    ap.add_argument("--org-vat", required=True, help="VAT number of the Qonto organization")
    ap.add_argument("--email", default=None, help="notification email for clearing proposals")
    ap.add_argument("--send", action="store_true",
                    help="actually transmit the invoices to Nexyzen. Without this flag the "
                         "script only prints what WOULD be sent (default). Use it only after "
                         "the user has seen that list and explicitly said yes")
    ap.add_argument("--exclude-invoice", action="append", default=[], metavar="NUMBER",
                    help="invoice number the user does not want to send (repeatable)")
    ap.add_argument("--default-country", default=None,
                    help="country prefix for VAT numbers that lack one (e.g. IT)")
    args = ap.parse_args()

    with open(args.ledger, encoding="utf-8") as f:
        ledger = json.load(f)

    payloads = build_payloads(ledger, args.org_vat, args.email,
                              default_country=args.default_country)
    excluded = set(args.exclude_invoice)
    payloads = [p for p in payloads if p.get("numero_fattura") not in excluded]
    print(f"{len(payloads)} open invoice(s) ready for the clearing engine "
          f"(VAT numbers in CLEAR).")

    affiliate = os.environ.get("NEXYZEN_AFFILIATE_CODE")
    token = os.environ.get("NEXYZEN_TOKEN")
    base_url = BASE_URL

    # Default is DRY RUN: nothing leaves the machine unless --send is given AND
    # credentials are configured.
    if not args.send or not (affiliate and token):
        print("DRY RUN — nothing has been sent. This is exactly what would be transmitted "
              "to the Nexyzen clearing service:")
        for p in payloads:
            print(json.dumps(p, ensure_ascii=False))
        if args.send:
            print("--send was given but NEXYZEN_AFFILIATE_CODE / NEXYZEN_TOKEN are not set.",
                  file=sys.stderr)
        else:
            print("To transmit, the user must first confirm this list; then re-run with --send.")
        return 0

    # --send: the user must confirm on their own terminal. An agent cannot do it.
    print("WARNING: VAT numbers, invoice numbers, dates and amounts of your "
          "counterparties (third parties who have not agreed to this) will be sent "
          "to Nexyzen IN CLEAR.", file=sys.stderr)
    phrase = f"SEND {len(payloads)} INVOICES IN CLEAR"
    answer = confirm_on_user_terminal(phrase)
    if answer is None:
        print("REFUSED: no interactive terminal available. Sending needs the user to type a "
              "confirmation, so the user must run this same command themselves in their own "
              "terminal.", file=sys.stderr)
        return 3
    if not answer:
        print("Confirmation not given. Nothing was sent.")
        return 0

    print(f"Connecting to {base_url} ...")
    conn = post_json(f"{base_url}/connect", {
        "op": "gjwt",
        "dati": {"cod_affiliato": affiliate, "token": token},
    })
    jwt = conn.get("jwt") or conn.get("token") or conn.get("JWT")
    if not jwt:
        print(f"ERROR: no JWT in /connect response: {conn}", file=sys.stderr)
        return 1
    print("JWT obtained (valid 1 hour). Sending invoices ...")

    failures = 0
    for p in payloads:
        try:
            resp = post_json(f"{base_url}/send_manual", {
                "op": "ins_manuale", "jwt": jwt, "dati": p,
            })
            print(f"  {p['numero_fattura']}: {resp}")
        except Exception as exc:  # keep going: one bad invoice must not stop the batch
            failures += 1
            print(f"  {p['numero_fattura']}: FAILED ({exc})", file=sys.stderr)
    print(f"Done: {len(payloads) - failures} sent, {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
