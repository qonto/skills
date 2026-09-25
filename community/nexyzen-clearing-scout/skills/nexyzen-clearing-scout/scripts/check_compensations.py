#!/usr/bin/env python3
"""check_compensations.py — List and accept clearing proposals from the Nexyzen engine.

After submit_to_nexyzen.py has fed the ledger to the clearing network, the
server-side engine periodically searches for closed cycles of mutual debts.
This script lets the Qonto-side integration pull the results:

  list    show the compensation proposals waiting for the user's acceptance
  accept  accept one proposal by its one-time token (IRREVERSIBLE: it is the
          legal consent to the voluntary set-off — always require an explicit
          user confirmation first)

When every participant of a cycle has accepted, the cycle is finalized by the
clearing house (credit-assignment letters) and the matched amounts are
settled without any bank transfer. Invoices fully covered by a completed
cycle can then be marked as paid in Qonto (mark_client_invoice_as_paid /
change_supplier_invoice_status) — only with the user's explicit go-ahead.

Credentials via environment (same as submit_to_nexyzen.py):
  NEXYZEN_AFFILIATE_CODE, NEXYZEN_TOKEN, NEXYZEN_BASE_URL (optional override)

Usage:
  python check_compensations.py list --org-vat IT03671960833
  python check_compensations.py accept --token <one-time token>
"""

import argparse
import json
import os
import sys
import urllib.request

try:
    import local_secrets  # noqa: F401  (optional, gitignored — see scripts/local_secrets.example.py)
except ImportError:
    pass

DEFAULT_BASE_URL = "https://webapp.cameracompensazione.it/webservices/index.php"

# Warranties the assignor makes on the assigned receivable. The engine requires
# all of them (set to true) to accept, exactly as the public web form, and they
# are reproduced in the deed of assignment (art. 1266 c.c.). They must come from
# the user's explicit confirmation, never be forced by the integration.
DECLARATIONS = [
    ("riconoscimento_credito", "You hold the receivable you are assigning, towards your debtor."),
    ("riconoscimento_debito", "You acknowledge the payable being offset."),
    ("cessione_credito", "You assign the receivable to the assignee."),
    ("ricezione_credito", "You accept the receivable you get in exchange."),
    ("dich_esistenza", "The receivable exists, is certain, valid and due."),
    ("dich_titolarita", "The receivable is solely yours and is not encumbered in favour of third parties."),
    ("dich_non_pagato", "The receivable has not been paid, set off or otherwise extinguished."),
    ("dich_non_contestato", "The receivable is not disputed, nor in any proceedings."),
    ("dich_no_procedure", "You are not in insolvency proceedings and are not insolvent."),
    ("dich_no_incedibilita", "The assignment breaches no non-assignment clause or contractual/legal restriction."),
    ("dich_pro_soluto", "You acknowledge the terms of the operation (assignment without recourse, pro soluto)."),
]


def post_json(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
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
        print(json.dumps(items, indent=2, ensure_ascii=False))
        return 0
    if not items:
        print("No compensation proposal waiting for acceptance.")
        return 0
    print(f"{len(items)} compensation proposal(s) waiting for acceptance:")
    for c in items:
        print(f"\n#{c['id_compensazione']} — cycle {c['id_ciclo']} — EUR {c['importo']:.2f}")
        missing = c.get("anagrafica_mancante") or []
        if missing:
            print(f"  REGISTRY DATA REQUIRED before accepting ({len(missing)} field(s)): "
                  + ", ".join(missing))
            print("    collect them from the user and pass each as --set field=value on accept")
        print(f"  You assign a EUR {c['importo']:.2f} receivable towards "
              f"{c['credito_verso']['ragione_sociale']} (VAT {c['credito_verso']['partita_iva']})")
        print(f"    from invoices: {fmt_invoices(c['credito_verso']['fatture'])}")
        print(f"  In exchange your debt towards {c['debito_verso']['ragione_sociale']} "
              f"(VAT {c['debito_verso']['partita_iva']}) is settled for the same amount")
        print(f"    covering: {fmt_invoices(c['debito_verso']['fatture'])}")
        print(f"  Legal basis: {c['base_legale']}")
        print(f"  Acceptance token: {c['token']}")
    print("\nTo accept (after explicit user confirmation):")
    print("  python check_compensations.py accept --token <token>")
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


def cmd_accept(base_url: str, token: str, registry_fields: list, lang: str,
               confirm_declarations: bool) -> int:
    # Accepting attaches the assignor's warranties (art. 1266 c.c.): the engine
    # rejects the acceptance without them, and the integration must not attest
    # them on the user's behalf. Show them and refuse until the user has read and
    # confirmed them (re-run with --confirm-declarations).
    if not confirm_declarations:
        print("Before accepting, the assignor makes these declarations on the "
              "assigned receivable:\n")
        for _key, text in DECLARATIONS:
            print(f"  - {text}")
        print("\nPresent them to the user. Only after an explicit confirmation, "
              "re-run this command adding --confirm-declarations.", file=sys.stderr)
        return 2

    jwt = get_jwt(base_url)
    dati = {
        "token": token,
        "lingua": lang,
        "dichiarazioni": {key: True for key, _text in DECLARATIONS},
    }
    if registry_fields:
        anagrafica = {}
        for pair in registry_fields:
            if "=" not in pair:
                print(f"--set expects field=value, got: {pair}", file=sys.stderr)
                return 1
            k, v = pair.split("=", 1)
            anagrafica[k.strip()] = v.strip()
        dati["anagrafica"] = anagrafica
    resp = post_json(base_url, {
        "op": "accetta_compensazione",
        "jwt": jwt,
        "dati": dati,
    })
    print(json.dumps(resp, indent=2, ensure_ascii=False))
    if resp.get("ciclo_completo"):
        print("\nAll participants have accepted: the cycle is complete. "
              "The clearing house will issue the credit-assignment letters; "
              "invoices fully covered by the cycle can be marked as paid in Qonto.")
    elif resp.get("accepted"):
        print("\nAccepted. The cycle settles once the remaining participants accept too.")
    return 0 if resp.get("accepted") else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lang", choices=["en", "it"], default="en",
                    help="language of engine messages and legal-basis labels (default: en)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_list = sub.add_parser("list", help="list pending compensation proposals")
    p_list.add_argument("--org-vat", required=True, help="VAT of the organization (as submitted)")
    p_list.add_argument("--json", action="store_true", help="raw JSON output")
    p_accept = sub.add_parser("accept", help="accept a proposal by token (requires user confirmation)")
    p_accept.add_argument("--token", required=True, help="one-time acceptance token")
    p_accept.add_argument("--set", action="append", default=[], metavar="FIELD=VALUE",
                          help="registry (anagrafica) field to record with the acceptance; "
                               "repeatable — e.g. --set nome_legale_rappresentante=Mario")
    p_accept.add_argument("--confirm-declarations", action="store_true",
                          help="attest, on the user's behalf and only after their explicit "
                               "consent, the assignor's warranties on the assigned receivable "
                               "(art. 1266 c.c.); required to accept")
    p_letters = sub.add_parser("letters", help="fetch credit-assignment letters delivered to the Qonto channel")
    p_letters.add_argument("--org-vat", required=True, help="VAT of the organization (as submitted)")
    p_letters.add_argument("--all", action="store_true", help="include letters already delivered")
    p_letters.add_argument("--json", action="store_true", help="raw JSON output (full HTML bodies)")
    args = ap.parse_args()

    base_url = os.environ.get("NEXYZEN_BASE_URL", DEFAULT_BASE_URL)
    if args.cmd == "list":
        return cmd_list(base_url, args.org_vat, args.json, args.lang)
    if args.cmd == "letters":
        return cmd_letters(base_url, args.org_vat, args.all, args.json, args.lang)
    return cmd_accept(base_url, args.token, args.set, args.lang, args.confirm_declarations)


if __name__ == "__main__":
    sys.exit(main())
