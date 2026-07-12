#!/usr/bin/env python3
"""submit_to_nexyzen.py — Send open ledger positions to the Nexyzen clearing engine.

Bridges Qonto data to the Nexyzen / Camera di Compensazione web service
(https://webapp.cameracompensazione.it), where the multilateral clearing
algorithm runs server-side over the whole network of participants.

Flow (see swagger: /webservices/index.php):
  1. POST /connect     (op "gjwt")        -> 1-hour JWT
  2. POST /send_manual (op "ins_manuale") -> one call per open invoice

Privacy by design: by default VAT numbers are pseudonymized with SHA-256
before leaving the machine (--no-pseudonymize sends them in clear, which the
counterparty matching in production requires — ask Nexyzen for guidance).
No payment is ever initiated: the engine only detects offset opportunities.

Credentials come from environment variables and are NEVER stored in the repo:
  NEXYZEN_AFFILIATE_CODE   affiliate code (from commerciale@cameracompensazione.it)
  NEXYZEN_TOKEN            API token
  NEXYZEN_BASE_URL         optional override of the API base URL

Without credentials the script runs in DRY-RUN mode and prints the payloads
it would send.

Usage:
  python submit_to_nexyzen.py --ledger ledger.json --org-vat IT03671960833 \
      [--email you@company.com] [--dry-run] [--no-pseudonymize]
"""

import argparse
import hashlib
import json
import os
import sys
import urllib.request

try:
    import local_secrets  # noqa: F401  (optional, gitignored — see scripts/local_secrets.example.py)
except ImportError:
    pass

DEFAULT_BASE_URL = "https://webapp.cameracompensazione.it/webservices/index.php"
PROVENANCE_CODE = "QONTO_MCP"  # native attribution for the Qonto integration


def pseudonymize(vat: str) -> str:
    """Deterministic pseudonym: same VAT -> same token, not reversible."""
    return "PS" + hashlib.sha256(vat.encode("utf-8")).hexdigest()[:20].upper()


def post_json(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def build_payloads(ledger: dict, org_vat: str, email: str | None,
                   do_pseudonymize: bool, default_country: str | None = None) -> list[dict]:
    """Map every open ledger invoice to a /send_manual 'dati' payload.

    Counterparties without a VAT number are skipped (with a warning): the
    clearing engine matches on VAT and cannot use name-only records.
    When sending clear VAT numbers, the country prefix seen in the source
    data is restored ('IT01...'), falling back to --default-country.
    """
    org_id = pseudonymize(org_vat) if do_pseudonymize else org_vat
    payloads = []
    for cp in ledger["counterparties"]:
        cp_vat = cp["vat"] or ""
        if not cp_vat:
            open_count = sum(1 for i in cp["invoices"] if float(i["open_amount"]) > 0)
            if open_count:
                print(f"SKIP {cp.get('canonical_name')}: no VAT number "
                      f"({open_count} open invoice(s) not submitted)", file=sys.stderr)
            continue
        if do_pseudonymize:
            cp_id = pseudonymize(cp_vat)
        else:
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
    ap.add_argument("--dry-run", action="store_true", help="print payloads, send nothing")
    ap.add_argument("--no-pseudonymize", action="store_true",
                    help="send clear VAT numbers instead of SHA-256 pseudonyms")
    ap.add_argument("--default-country", default=None,
                    help="country prefix for VAT numbers that lack one (e.g. IT); clear mode only")
    args = ap.parse_args()

    with open(args.ledger, encoding="utf-8") as f:
        ledger = json.load(f)

    payloads = build_payloads(ledger, args.org_vat, args.email,
                              do_pseudonymize=not args.no_pseudonymize,
                              default_country=args.default_country)
    print(f"{len(payloads)} open invoice(s) ready for the clearing engine "
          f"({'pseudonymized' if not args.no_pseudonymize else 'CLEAR'} VAT numbers).")

    affiliate = os.environ.get("NEXYZEN_AFFILIATE_CODE")
    token = os.environ.get("NEXYZEN_TOKEN")
    base_url = os.environ.get("NEXYZEN_BASE_URL", DEFAULT_BASE_URL)

    if args.dry_run or not (affiliate and token):
        if not (affiliate and token):
            print("NEXYZEN_AFFILIATE_CODE / NEXYZEN_TOKEN not set -> DRY RUN.")
        for p in payloads:
            print(json.dumps(p, ensure_ascii=False))
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
