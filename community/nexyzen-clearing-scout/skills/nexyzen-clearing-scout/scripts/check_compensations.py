#!/usr/bin/env python3
"""check_compensations.py — Read-only: list clearing proposals and fetch letters from Nexyzen.

After submit_to_nexyzen.py has fed the ledger to the clearing network, the
server-side engine periodically searches for closed cycles of mutual debts.
This script lets the Qonto-side integration READ the results:

  list     show the compensation proposals waiting for the user's decision
  letters  fetch the credit-assignment letters of cycles that were completed

It deliberately has NO way to accept a proposal. Accepting a compensation is a
binding legal act (credit assignment with the assignor's warranties, art. 1266
c.c.): only the user can do it, themselves, on the Nexyzen acceptance page
that `list` points to. An agent must never accept, confirm declarations or
attest warranties on the user's behalf.

Both commands are network calls to Nexyzen (not Qonto) and send the
organization's VAT number IN CLEAR to look up its proposals and letters.

When every participant of a cycle has accepted, the cycle is finalized by the
clearing house and the matched amounts are settled without any bank transfer.

Credentials via environment (same as submit_to_nexyzen.py):
  NEXYZEN_AFFILIATE_CODE, NEXYZEN_TOKEN
The API destination is fixed to Nexyzen over HTTPS; redirects are refused.

Usage:
  python check_compensations.py list --org-vat IT03671960833
  python check_compensations.py letters --org-vat IT03671960833
"""

import argparse
import json
import os
import sys
import urllib.error

from nexyzen_http import BASE_URL, post_json as nexyzen_post_json

ACCEPTANCE_PAGE = "https://webapp.cameracompensazione.it/attiva_compensazione.php?token="


def post_json(url: str, payload: dict) -> dict:
    try:
        return nexyzen_post_json(url, payload)
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
            detail = body.get("message") or body.get("error") or body.get("result") or body
        except Exception:
            detail = e.reason
        print(f"REFUSED (HTTP {e.code}): {detail}", file=sys.stderr)
        sys.exit(1)


def get_jwt(base_url: str) -> str:
    affiliate = os.environ.get("NEXYZEN_AFFILIATE_CODE")
    token = os.environ.get("NEXYZEN_TOKEN")
    if not (affiliate and token):
        print("NEXYZEN_AFFILIATE_CODE / NEXYZEN_TOKEN not set", file=sys.stderr)
        sys.exit(1)
    conn = post_json(f"{base_url}/connect", {
        "op": "gjwt",
        "dati": {"cod_affiliato": affiliate, "token": token},
    })
    jwt = conn.get("jwt")
    if not jwt:
        print(f"ERROR: no JWT in /connect response: {conn}", file=sys.stderr)
        sys.exit(1)
    return jwt


def fmt_invoices(invoices: list) -> str:
    return ", ".join(
        f"{i['numero']} ({i['data']}, EUR {i['importo_residuo']:.2f} open)"
        for i in invoices
    ) or "-"


def cmd_list(base_url: str, org_vat: str, as_json: bool, lang: str) -> int:
    jwt = get_jwt(base_url)
    resp = post_json(base_url, {
        "op": "get_compensazioni",
        "jwt": jwt,
        "dati": {"partita_iva": org_vat, "lingua": lang},
    })
    items = resp.get("compensazioni", [])
    if as_json:
        # The one-time acceptance token is never handed to the agent.
        for c in items:
            c.pop("token", None)
        print(json.dumps(items, indent=2, ensure_ascii=False))
        return 0
    if not items:
        print("No compensation proposal waiting for a decision.")
        return 0
    print(f"{len(items)} compensation proposal(s) waiting for the user's decision:")
    for c in items:
        print(f"\n#{c['id_compensazione']} — cycle {c['id_ciclo']} — EUR {c['importo']:.2f}")
        print(f"  The user would assign a EUR {c['importo']:.2f} receivable towards "
              f"{c['credito_verso']['ragione_sociale']} (VAT {c['credito_verso']['partita_iva']})")
        print(f"    from invoices: {fmt_invoices(c['credito_verso']['fatture'])}")
        print(f"  In exchange their debt towards {c['debito_verso']['ragione_sociale']} "
              f"(VAT {c['debito_verso']['partita_iva']}) is settled for the same amount")
        print(f"    covering: {fmt_invoices(c['debito_verso']['fatture'])}")
        print(f"  Legal basis: {c['base_legale']}")
    print("\nThe agent cannot accept. Accepting is a binding legal act that only the user "
          "can perform, on the Nexyzen acceptance page linked in the notification they "
          f"received (format: {ACCEPTANCE_PAGE}<token>).")
    return 0


def cmd_letters(base_url: str, org_vat: str, include_delivered: bool, as_json: bool, lang: str) -> int:
    jwt = get_jwt(base_url)
    resp = post_json(base_url, {
        "op": "get_lettere_cessione",
        "jwt": jwt,
        "dati": {"partita_iva": org_vat, "tutte": include_delivered, "lingua": lang},
    })
    letters = resp.get("lettere", [])
    if as_json:
        print(json.dumps(letters, indent=2, ensure_ascii=False))
        return 0
    if not letters:
        print("No credit-assignment letter waiting.")
        return 0
    print(f"{len(letters)} credit-assignment letter(s):")
    for l in letters:
        status = f"delivered {l['consegnata']}" if l.get("consegnata") else "NEW"
        print(f"\n[{status}] #{l['id']} — compensation n.{l['id_compensazione']} — created {l['creata']}")
        print(f"  Subject: {l['oggetto']}")
        print(f"  Body: {len(l['corpo_html'])} chars of HTML (present it to the user, "
              f"or save it as the legal record of the settled set-off)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lang", choices=["en", "it"], default="en",
                    help="language of engine messages and legal-basis labels (default: en)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_list = sub.add_parser("list", help="list pending compensation proposals (read-only)")
    p_list.add_argument("--org-vat", required=True, help="VAT of the organization (as submitted)")
    p_list.add_argument("--json", action="store_true", help="raw JSON output")
    p_letters = sub.add_parser("letters", help="fetch credit-assignment letters delivered to the Qonto channel")
    p_letters.add_argument("--org-vat", required=True, help="VAT of the organization (as submitted)")
    p_letters.add_argument("--all", action="store_true", help="include letters already delivered")
    p_letters.add_argument("--json", action="store_true", help="raw JSON output (full HTML bodies)")
    args = ap.parse_args()

    base_url = BASE_URL
    if args.cmd == "list":
        return cmd_list(base_url, args.org_vat, args.json, args.lang)
    return cmd_letters(base_url, args.org_vat, args.all, args.json, args.lang)


if __name__ == "__main__":
    sys.exit(main())
