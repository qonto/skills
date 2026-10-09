#!/usr/bin/env python3
"""In-depth tests for extract_fec.py.

Part A — cross-validations on real FEC files (if provided as arguments):
  A1  independent counter-computation of the reserve (raw sum per account)
  A2  internal invariant of each filing (sum of 445x ≈ rounding gaps)
  A3  inter-year consistency: closing N == opening balances N+1 per 445x account
  A4  detected 'to pay' == actual 44551 credits of the file
  A5  no candidate comes from an entry containing 4456x, from the AN journal,
      or from a structurally VAT-less account
  A6  determinism: two analyses -> identical results
  A7  each month covered by the sales journals has a filing

Part B — synthetic cases (always run):
  B1  pipe separator + dot decimal + cp1252 encoding
  B2  unbalanced entry detected
  B3  strict duplicate detected
  B4  out-of-period date counted
  B5  unreadable amount -> line rejected, counted in the diagnostics
  B6  missing column reported
  B7  candidate filtering (insurance/payroll excluded, 6251 alerted, ≤1 € ignored,
      entry with 4456x ignored, AN ignored, correct deadline)
  B8  synthetic filing (44551 credit) detected; per-transaction reverse-charge
      entry NOT detected
  B9  44567 cycle: L27 on recording, L22 on application
  B10 non-compliant filename -> siren None
  B11 header-only file -> zero lines, zero crash
  B12 supplier credit note (6xx credit) -> no negative candidate
  B13 load test: 120,000 lines < 10s
  B14 arbitrary file -> diagnostic, no crash
  B15 time_window: old year TIME_BARRED, recent OPEN, deadline 31/12 N+2 exact
  B16 supplier_profiles: registered_history / presumed_franchise /
      mixed_to_verify correct on synthetic history
  B17 payments_without_invoice: payment without a matching invoice detected
      as an orphan; payment with a matching invoice NOT an orphan
  B18 payments_without_invoice: DOCUMENTED FALSE NEGATIVE — a truly orphan
      payment is hidden by an old unpaid invoice from the same supplier at
      the same amount (known limit, not a regression)

Part C — client-config.json robustness (subprocess, isolated):
  C1  extract_fec.py: malformed JSON -> no crash, empty aliases
  C2  extract_fec.py: mistyped supplier_aliases -> no crash, warning
  C3  route_label.py: malformed JSON -> no crash, empty rules
  C4  route_label.py: invalid regex pattern -> that rule dropped alone, the
      other rules (client + generic) stay active

Usage: python3 test_extract_fec.py [FEC_N.txt FEC_N+1.txt]
"""
from __future__ import annotations
import csv
import json
import os
import sys
import subprocess
import tempfile
from decimal import Decimal
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_fec import analyze, detect_and_read, FEC_COLUMNS  # noqa: E402

PASS, FAIL = 0, 0


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not cond else ""))
    PASS += cond
    FAIL += not cond


# ------------------------------------------------------------------ helpers
def write_fec(rows: list[list[str]], sep="\t", encoding="utf-8",
              name="123456789FEC20251231.txt") -> str:
    d = tempfile.mkdtemp()
    p = os.path.join(d, name)
    with open(p, "w", encoding=encoding, newline="") as f:
        f.write(sep.join(FEC_COLUMNS) + "\n")
        for r in rows:
            f.write(sep.join(r) + "\n")
    return p


def L(journal, num, date, compte, lib, debit, credit, elib, piece="P1", jlib=None):
    return [journal, jlib or f"Journal {journal}", str(num), date, compte, lib,
            "", "", piece, date, elib, debit, credit, "", "", date, debit or credit, "EUR"]


# ============================================================ B synthetic ==
def synthetic_tests():
    # B1 pipe + decimal dot + cp1252
    rows = [L("BQ", 1, "20250110", "606", "Fournitures", "100.00", "0", "Achat papeterie é"),
            L("BQ", 1, "20250110", "44566", "TVA déductible", "20.00", "0", "Achat papeterie é"),
            L("BQ", 1, "20250110", "512", "Banque", "0", "120.00", "Achat papeterie é")]
    p = write_fec(rows, sep="|", encoding="cp1252")
    res = analyze(p)
    check("B1 pipe separator detected", res["parsing"]["separator"] == "pipe")
    check("B1 cp1252 encoding read", res["parsing"]["encoding"] in ("cp1252", "latin-1", "utf-8", "utf-8-sig"))
    check("B1 dot decimal accepted", res["checks"]["total_debit"] == "120.00")
    check("B1 balance balanced", res["checks"]["balanced"])

    # B2 unbalanced entry
    rows = [L("OD", 1, "20250201", "606", "Fournitures", "100,00", "0,0", "e1"),
            L("OD", 1, "20250201", "512", "Banque", "0,0", "90,00", "e1")]
    res = analyze(write_fec(rows))
    check("B2 unbalanced entry detected", res["checks"]["unbalanced_entry_count"] == 1)
    check("B2 global balance flagged unbalanced", not res["checks"]["balanced"])

    # B3 strict duplicate
    l1 = L("BQ", 1, "20250301", "606", "F", "50,0", "0,0", "dup")
    rows = [l1, list(l1), L("BQ", 1, "20250301", "512", "B", "0,0", "100,0", "dup")]
    res = analyze(write_fec(rows))
    check("B3 strict duplicate detected", res["checks"]["strict_duplicates"] == 1)

    # B4 out-of-period date (closing 20251231 -> year 2025)
    rows = [L("BQ", 1, "20240515", "606", "F", "10,0", "0,0", "vieux"),
            L("BQ", 1, "20240515", "512", "B", "0,0", "10,0", "vieux")]
    res = analyze(write_fec(rows))
    check("B4 out-of-period lines counted", res["checks"]["out_of_period_lines"] == 2)

    # B5 malformed amount rejected
    rows = [L("BQ", 1, "20250401", "606", "F", "abc", "0,0", "cassé"),
            L("BQ", 2, "20250401", "606", "F", "10,0", "0,0", "ok"),
            L("BQ", 2, "20250401", "512", "B", "0,0", "10,0", "ok")]
    res = analyze(write_fec(rows))
    check("B5 unreadable line rejected and traced",
          len(res["parsing"]["rejected_lines"]) == 1 and res["checks"]["line_count"] == 2)

    # B6 missing column
    p = write_fec([])
    txt = open(p).read().replace("\tIdevise", "")
    open(p, "w").write(txt)
    res = analyze(p)
    check("B6 missing column reported",
          not res["parsing"]["columns_compliant"] and res["parsing"]["missing_columns"] == ["Idevise"])

    # B7 candidate filtering
    rows = [
        # legitimate candidate: fees with no VAT in the entry
        L("BQ", 1, "20250510", "6226", "Honoraires", "1000,0", "0,0", "avocat"),
        L("BQ", 1, "20250510", "512", "Banque", "0,0", "1000,0", "avocat"),
        # NOT a candidate: VAT deducted in the same entry
        L("BQ", 2, "20250511", "606", "Fournitures", "100,0", "0,0", "avec tva"),
        L("BQ", 2, "20250511", "44566", "TVA déd", "20,0", "0,0", "avec tva"),
        L("BQ", 2, "20250511", "512", "Banque", "0,0", "120,0", "avec tva"),
        # NOT a candidate: insurance (exempt)
        L("BQ", 3, "20250512", "616", "Assurances", "500,0", "0,0", "axa"),
        L("BQ", 3, "20250512", "512", "Banque", "0,0", "500,0", "axa"),
        # NOT a candidate: payroll
        L("OD", 4, "20250531", "6411", "Salaires", "3000,0", "0,0", "paie mai"),
        L("OD", 4, "20250531", "421", "Personnel", "0,0", "3000,0", "paie mai"),
        # candidate ALERTED, excluded by nature: 6251 transport
        L("BQ", 5, "20250513", "6251", "Voyages", "200,0", "0,0", "sncf"),
        L("BQ", 5, "20250513", "512", "Banque", "0,0", "200,0", "sncf"),
        # NOT a candidate: ≤ 1 €
        L("BQ", 6, "20250514", "606", "F", "0,80", "0,0", "mini"),
        L("BQ", 6, "20250514", "512", "B", "0,0", "0,80", "mini"),
        # NOT a candidate: AN journal
        L("AN", 7, "20250101", "606", "F", "999,0", "0,0", "à nouveau", jlib="Journal des à-nouveaux"),
        L("AN", 7, "20250101", "512", "B", "0,0", "999,0", "à nouveau", jlib="Journal des à-nouveaux"),
    ]
    res = analyze(write_fec(rows))
    cand = res["ticket_candidates"]
    comptes = {l["account"] for l in cand["lines"]}
    check("B7 fees candidate present", "6226" in comptes)
    check("B7 entry with 4456x excluded", "606" not in comptes or all(
        l["account"] != "606" or l["label"] != "avec tva" for l in cand["lines"]))
    check("B7 insurance (616) excluded", "616" not in comptes)
    check("B7 payroll (6411) excluded", "6411" not in comptes)
    c6251 = [l for l in cand["lines"] if l["account"] == "6251"]
    check("B7 6251 present with exclusion alert",
          len(c6251) == 1 and "206 IV-2-5" in (c6251[0]["alert_nature"] or ""))
    check("B7 6251 out of potential base", cand["expense_base_excl_exclusions"] == "1000.00")
    check("B7 amount ≤ 1 € ignored", all(l["label"] != "mini" for l in cand["lines"]))
    check("B7 AN journal ignored", all(l["journal"] != "AN" for l in cand["lines"]))
    check("B7 deadline 31/12 N+2 correct",
          c6251[0]["line21_deadline"] == "2027-12-31")
    check("B7 structured alert_level: 6251 -> exclusion",
          c6251[0].get("alert_level") == "exclusion")
    ch = [l for l in cand["lines"] if l["account"] == "6226"]
    check("B7 structured alert_level: clean candidate -> None",
          ch and ch[0].get("alert_level") is None)

    # B8 filing vs per-transaction reverse charge
    rows = [
        # real filing (44551 credit)
        L("TVA", 1, "20250630", "44571", "TVA collectée", "1000,0", "0,0", "TVA juin 2025"),
        L("TVA", 1, "20250630", "44566", "TVA déd", "0,0", "400,0", "TVA juin 2025"),
        L("TVA", 1, "20250630", "44551", "TVA à décaisser", "0,0", "600,0", "TVA juin 2025"),
        # per-transaction reverse charge: same debit-ded/credit-coll profile -> NOT a filing
        L("RT", 2, "20250615", "445662", "TVA déd intracom", "3,60", "0,0", "CLAUDE SUBSCRIPTION"),
        L("RT", 2, "20250615", "4452", "TVA due intracom", "0,0", "3,60", "CLAUDE SUBSCRIPTION"),
    ]
    res = analyze(write_fec(rows))
    liqs = res["vat"]["detected_ca3_filings"]
    check("B8 44551 filing detected (only one)", len(liqs) == 1 and liqs[0]["entry"] == "1")
    check("B8 filing amounts exact",
          liqs[0]["collected_filed"] == "1000.00" and liqs[0]["deductible_filed"] == "400.00"
          and liqs[0]["vat_to_pay"] == "600.00")
    check("B8 net reverse charge balanced",
          res["vat"]["reverse_charge"]["gap_due_vs_mirror"] == "0.00")

    # B9 44567 cycle
    rows = [
        # month 1: credit recorded (deductible > collected)
        L("TVA", 1, "20250131", "44571", "Coll", "100,0", "0,0", "TVA janvier 2025"),
        L("TVA", 1, "20250131", "44566", "Déd", "0,0", "300,0", "TVA janvier 2025"),
        L("TVA", 1, "20250131", "44567", "Crédit à reporter", "200,0", "0,0", "TVA janvier 2025"),
        # month 2: credit applied
        L("TVA", 2, "20250228", "44571", "Coll", "500,0", "0,0", "TVA février 2025"),
        L("TVA", 2, "20250228", "44566", "Déd", "0,0", "100,0", "TVA février 2025"),
        L("TVA", 2, "20250228", "44567", "Crédit à reporter", "0,0", "200,0", "TVA février 2025"),
        L("TVA", 2, "20250228", "44551", "À décaisser", "0,0", "200,0", "TVA février 2025"),
    ]
    res = analyze(write_fec(rows))
    liqs = {l["period"]: l for l in res["vat"]["detected_ca3_filings"]}
    check("B9 credit recorded on 44567 debit (L27)",
          liqs["2025-01"]["credit_recorded_L27"] == "200.00" and liqs["2025-01"]["credit_applied_L22"] == "0.00")
    check("B9 credit applied on 44567 credit (L22)",
          liqs["2025-02"]["credit_applied_L22"] == "200.00" and liqs["2025-02"]["credit_recorded_L27"] == "0.00")

    # B10 non-compliant filename
    p = write_fec([], name="export_compta.txt")
    res = analyze(p)
    check("B10 non-compliant name -> siren None",
          res["meta"]["siren"] is None and not res["meta"]["name_compliant"])

    # B11 header only
    p = write_fec([])
    res = analyze(p)
    check("B11 empty file: zero lines, zero crash",
          res["checks"]["line_count"] == 0 and res["ticket_candidates"]["candidate_count"] == 0)

    # B12 supplier credit note: 6xx credit, net negative -> no candidate
    rows = [L("BQ", 1, "20250601", "606", "F", "0,0", "50,0", "avoir"),
            L("BQ", 1, "20250601", "512", "B", "50,0", "0,0", "avoir")]
    res = analyze(write_fec(rows))
    check("B12 credit note (net negative expense) without candidate",
          res["ticket_candidates"]["candidate_count"] == 0)

    # B13 load test: 120,000 lines -> < 10 s, exact results
    import time
    big = []
    for i in range(20000):
        d = f"2025{(i % 12) + 1:02d}{(i % 28) + 1:02d}"
        big.append(L("BQ", 1000 + i, d, "606", "F", "100,0", "0,0", f"achat {i}"))
        big.append(L("BQ", 1000 + i, d, "44566", "TVA", "20,0", "0,0", f"achat {i}"))
        big.append(L("BQ", 1000 + i, d, "512", "B", "0,0", "120,0", f"achat {i}"))
        big.append(L("VT", 5000 + i, d, "706", "Prestations", "0,0", "200,0", f"vente {i}"))
        big.append(L("VT", 5000 + i, d, "44571", "TVA coll", "0,0", "40,0", f"vente {i}"))
        big.append(L("VT", 5000 + i, d, "411", "Clients", "240,0", "0,0", f"vente {i}"))
    t0 = time.perf_counter()
    res = analyze(write_fec(big))
    dt_big = time.perf_counter() - t0
    check("B13 120,000 lines < 10 s", dt_big < 10, f"{dt_big:.1f}s")
    check("B13 exact balance at scale",
          res["checks"]["balanced"] and res["checks"]["line_count"] == 120000)
    check("B13 exact reserve at scale (20000 × 20 €)",
          res["vat"]["unfiled_deductible_reserve"].get("44566", {}).get("unfiled_balance") == "400000.00")

    # B15 time window: old year time-barred, recent open
    import datetime as _dt
    today = _dt.date.today()
    annee_forclose = today.year - 3   # deadline 31/12/(year+2) < today
    annee_ouverte = today.year
    rows = [L("HA", 1, f"{annee_forclose}0115", "606", "F", "100,0", "0,0", "vieux"),
            L("HA", 1, f"{annee_forclose}0115", "44566", "TVA", "20,0", "0,0", "vieux"),
            L("HA", 1, f"{annee_forclose}0115", "401", "F", "0,0", "120,0", "vieux"),
            L("HA", 2, f"{annee_ouverte}0115", "606", "F", "100,0", "0,0", "recent"),
            L("HA", 2, f"{annee_ouverte}0115", "44566", "TVA", "20,0", "0,0", "recent"),
            L("HA", 2, f"{annee_ouverte}0115", "401", "F", "0,0", "120,0", "recent")]
    res = analyze(write_fec(rows))
    fen = res["time_window"]
    check("B15 old year TIME_BARRED", fen["years"][str(annee_forclose)]["status"] == "TIME_BARRED")
    check("B15 recent year OPEN", fen["years"][str(annee_ouverte)]["status"] == "OPEN")
    check("B15 deadline 31/12 N+2 exact",
          fen["years"][str(annee_ouverte)]["line21_deadline"] == f"{annee_ouverte + 2}-12-31")

    # B16 supplier_profiles: history decides the probable regime
    rows = [  # REGISTERED (always with VAT)
            L("HA", 1, "20250110", "606", "F", "100,0", "0,0", "Facture Assujetti SA n1"),
            L("HA", 1, "20250110", "44566", "TVA", "20,0", "0,0", "Facture Assujetti SA n1"),
            L("HA", 1, "20250110", "401", "F", "0,0", "120,0", "Facture Assujetti SA n1"),
            L("HA", 2, "20250210", "606", "F", "50,0", "0,0", "Facture Assujetti SA n2"),
            L("HA", 2, "20250210", "44566", "TVA", "10,0", "0,0", "Facture Assujetti SA n2"),
            L("HA", 2, "20250210", "401", "F", "0,0", "60,0", "Facture Assujetti SA n2"),
              # FRANCHISE (never any VAT)
            L("HA", 3, "20250310", "606", "F", "80,0", "0,0", "Facture Microentreprise n1"),
            L("HA", 3, "20250310", "401", "F", "0,0", "80,0", "Facture Microentreprise n1"),
              # MIXED (once with, once without -> to verify)
            L("HA", 4, "20250410", "606", "F", "40,0", "0,0", "Facture Mixte SARL n1"),
            L("HA", 4, "20250410", "44566", "TVA", "8,0", "0,0", "Facture Mixte SARL n1"),
            L("HA", 4, "20250410", "401", "F", "0,0", "48,0", "Facture Mixte SARL n1"),
            L("HA", 5, "20250510", "606", "F", "30,0", "0,0", "Facture Mixte SARL n2"),
            L("HA", 5, "20250510", "401", "F", "0,0", "30,0", "Facture Mixte SARL n2")]
    res = analyze(write_fec(rows))
    profils = {l["label"]: l["supplier_profile"] for l in res["ticket_candidates"]["lines"]}
    check("B16 presumed_franchise detected (Microentreprise, never any VAT)",
          any(v == "presumed_franchise" for k, v in profils.items() if "Microentreprise" in k))
    check("B16 mixed_to_verify detected (Mixte SARL n2, without VAT this time -> candidate)",
          any(v == "mixed_to_verify" for k, v in profils.items() if "Mixte" in k))

    # B17 payments_without_invoice: real orphan detected, reconciled payment absent
    rows = [  # invoice AND payment, identical amounts -> NOT an orphan
            L("HA", 1, "20250110", "606", "F", "100,0", "0,0", "Facture Rapprochee"),
            L("HA", 1, "20250110", "401", "F", "0,0", "100,0", "Facture Rapprochee"),
            L("BQ", 2, "20250115", "401", "F", "100,0", "0,0", "Facture Rapprochee"),
            L("BQ", 2, "20250115", "512", "B", "0,0", "100,0", "Facture Rapprochee"),
              # payment ALONE, no invoice at the same amount/supplier -> orphan
            L("BQ", 3, "20250220", "401", "F", "77,0", "0,0", "Facture Orpheline"),
            L("BQ", 3, "20250220", "512", "B", "0,0", "77,0", "Facture Orpheline")]
    res = analyze(write_fec(rows))
    orph = res["accounting_orphans"]
    check("B17 reconciled payment: no orphan under this label",
          not any("rapproch" in o["label"].lower() for o in orph["lines"]))
    check("B17 isolated payment detected as orphan",
          any("orphelin" in o["label"].lower() for o in orph["lines"]))

    # B18 DOCUMENTED FALSE NEGATIVE (payments_without_invoice note): an old
    # unpaid invoice from the same supplier, at the same amount as a truly
    # orphan payment (another invoice), hides that orphan in pass 2 (net
    # balance per supplier). KNOWN and accepted behavior, not a regression --
    # this test makes it explicit for any future evolution.
    rows = [  # open invoice never paid (stays in "invoices" as a balance)
            L("HA", 1, "20250110", "606", "F", "90,0", "0,0", "Facture MemeFournisseur ancienne"),
            L("HA", 1, "20250110", "401", "F", "0,0", "90,0", "Facture MemeFournisseur ancienne"),
              # 90 € payment truly tied to ANOTHER never-booked invoice
            L("BQ", 2, "20250601", "401", "F", "90,0", "0,0", "Facture MemeFournisseur recente"),
            L("BQ", 2, "20250601", "512", "B", "0,0", "90,0", "Facture MemeFournisseur recente")]
    res = analyze(write_fec(rows))
    orph = res["accounting_orphans"]
    check("B18 false negative reproduced: the recent payment is NOT flagged as an orphan "
          "(hidden by the balance of the old invoice from the same supplier/amount)",
          not any("recente" in o["label"].lower() for o in orph["lines"]))

    # B14 fuzz: arbitrary content -> diagnostic, no crash
    d = tempfile.mkdtemp()
    p = os.path.join(d, "123456789FEC20251231.txt")
    with open(p, "wb") as f:
        f.write("Journal|nimporte|quoi\n\x00\xff binaire ; virgules,,,\nzzz".encode("latin-1"))
    try:
        res = analyze(p)
        check("B14 arbitrary file: no crash", True)
    except Exception as e:
        check("B14 arbitrary file: no crash", False, repr(e))


# ============================================== C client-config robustness ==
def client_config_tests():
    """Each case writes an invalid client-config.json and checks, in a
    subprocess (the modules cache their config at import), that the script
    degrades cleanly instead of crashing."""
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    real_fec = write_fec([L("HA", 1, "20250110", "606", "F", "10,0", "0,0", "x")])

    def run(script, code, config_content):
        cfg_dir = tempfile.mkdtemp()
        cfg_path = os.path.join(cfg_dir, "client-config.json")
        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write(config_content)
        env = {**os.environ, "VAT_RECOVERY_CLIENT_CONFIG": cfg_path}
        r = subprocess.run([sys.executable, "-c", code], cwd=scripts_dir,
                           env=env, capture_output=True, text=True, timeout=30)
        return r

    # C1 — extract_fec.py: syntactically invalid JSON
    r = run("extract_fec", "import extract_fec; print('OK', extract_fec._ALIASES)",
            '{"supplier_aliases": [}')
    check("C1 extract_fec: malformed JSON -> no crash", r.returncode == 0, r.stderr[-200:])
    check("C1 extract_fec: empty aliases as fallback", "OK {}" in r.stdout)

    # C2 — extract_fec.py: valid JSON schema but wrong type
    r = run("extract_fec", "import extract_fec; print('OK', extract_fec._ALIASES)",
            '{"supplier_aliases": ["not_an_object"]}')
    check("C2 extract_fec: invalid schema -> no crash", r.returncode == 0, r.stderr[-200:])
    check("C2 extract_fec: warning emitted on stderr", "ignored" in r.stderr)

    # C3 — route_label.py: syntactically invalid JSON
    r = run("route_label", "import route_label; print('OK', route_label.CLIENT_RULES)",
            '{"client_rules": [}')
    check("C3 route_label: malformed JSON -> no crash", r.returncode == 0, r.stderr[-200:])
    check("C3 route_label: empty rules as fallback", "OK []" in r.stdout)

    # C4 — route_label.py: one invalid pattern does not take down the others
    code = ("import route_label as rl\n"
            "print('rules:', rl.CLIENT_RULES)\n"
            "print('route:', rl.route('Facture MonFournisseurValide'))")
    r = run("route_label", code,
            ('{"client_rules": ['
             '{"pattern": "(unclosed", "category": "x"}, '
             '{"pattern": "\\\\bmonfournisseurvalide\\\\b", "category": "professional_fees"}'
             ']}'))
    check("C4 route_label: broken rule isolated, no global crash",
          r.returncode == 0, r.stderr[-300:])
    check("C4 route_label: neighboring valid rule still active",
          "'professional_fees'" in r.stdout)
    check("C4 route_label: warning pointing to rule #0", "client_rule #0" in r.stderr)


# ================================================================ A real ==
def real_file_tests(f_n: str, f_n1: str):
    print(f"\n--- Cross-validations: {os.path.basename(f_n)} / {os.path.basename(f_n1)}")
    res_n, res_n1 = analyze(f_n), analyze(f_n1)

    # A1 independent counter-computation of the reserve (raw read, no module)
    def raw_balance(path, prefix):
        tot = defaultdict(lambda: Decimal(0))
        with open(path, encoding="utf-8-sig") as f:
            rd = csv.DictReader(f, delimiter="\t")
            for r in rd:
                if r["CompteNum"].startswith(prefix):
                    tot[r["CompteNum"]] += Decimal(r["Debit"].replace(",", ".")) - Decimal(r["Credit"].replace(",", "."))
        return {k: str(v.quantize(Decimal("0.01"))) for k, v in tot.items()}
    raw = raw_balance(f_n, "445")
    gis = res_n["vat"]["unfiled_deductible_reserve"]
    ok = all(raw.get(num) == g["unfiled_balance"] for num, g in gis.items())
    check("A1 reserve == raw counter-computation per account", ok,
          f"reserve={ {k: v['unfiled_balance'] for k, v in gis.items()} } raw={ {k: raw.get(k) for k in gis} }")

    # A2 internal invariant of the filings: sum(D-C) of 445x ≈ rounding gaps
    rows_n, _ = detect_and_read(f_n)
    by_entry = defaultdict(list)
    for r in rows_n:
        by_entry[(r["JournalCode"], r["EcritureNum"])].append(r)
    bad = []
    for l in res_n["vat"]["detected_ca3_filings"]:
        lines = by_entry[(l["journal"], l["entry"])]
        s = sum((x["_debit"] - x["_credit"] for x in lines if x["CompteNum"].startswith("445")), Decimal(0))
        if s.copy_abs() > Decimal("2"):
            bad.append((l["period"], str(s)))
    check("A2 each filing: sum of 445x ≤ 2 € (rounding)", not bad, str(bad))

    # A3 closing N == opening balances N+1 (445x accounts, AN journal of N+1)
    rows_n1, _ = detect_and_read(f_n1)
    an_n1 = defaultdict(lambda: Decimal(0))
    for r in rows_n1:
        if r["JournalCode"].upper() in ("AN", "RAN") and r["CompteNum"].startswith("445"):
            an_n1[r["CompteNum"]] += r["_debit"] - r["_credit"]
    close_n = defaultdict(lambda: Decimal(0))
    for r in rows_n:
        if r["CompteNum"].startswith("445"):
            close_n[r["CompteNum"]] += r["_debit"] - r["_credit"]
    all_accounts = set(an_n1) | set(close_n)
    mismatches = []
    for a in sorted(all_accounts):
        # tolerance: subdivision reclassifications -> also compare aggregate
        if (close_n[a] - an_n1[a]).copy_abs() > Decimal("0.01"):
            mismatches.append((a, str(close_n[a].quantize(Decimal('0.01'))), str(an_n1[a].quantize(Decimal('0.01')))))
    agg_ok = (sum(close_n.values(), Decimal(0)) - sum(an_n1.values(), Decimal(0))).copy_abs() <= Decimal("0.01")
    check("A3 closing N == opening balances N+1 (445x aggregate)", agg_ok,
          f"delta={sum(close_n.values(), Decimal(0)) - sum(an_n1.values(), Decimal(0))}")
    if mismatches:
        print(f"      info: {len(mismatches)} accounts reclassified between years (normal if the chart changed): {mismatches[:4]}")

    # A4 detected 'to pay' == actual 44551 credits (excl. AN)
    cred_44551 = sum((r["_credit"] - r["_debit"] for r in rows_n
                      if r["CompteNum"].startswith("44551")
                      and r["JournalCode"].upper() not in ("AN", "RAN")
                      and "nouveau" not in (r["JournalLib"] or "").lower()), Decimal(0))
    # 44551 debits outside AN = payments to the Treasury via bank: count credits only
    cred_only = sum((r["_credit"] for r in rows_n
                     if r["CompteNum"].startswith("44551")
                     and r["JournalCode"].upper() not in ("AN", "RAN")), Decimal(0))
    pay_total = sum(Decimal(l["vat_to_pay"]) for l in res_n["vat"]["detected_ca3_filings"])
    check("A4 sum of detected 'to pay' == 44551 credits of the file",
          (pay_total - cred_only).copy_abs() <= Decimal("0.01"),
          f"detected={pay_total} credits44551={cred_only}")

    # A5 purity of the candidates
    cand = res_n["ticket_candidates"]["lines"]
    entries_with_ded = {k for k, lines in by_entry.items() if any(x["CompteNum"].startswith("4456") for x in lines)}
    bad = [c for c in cand if (c["journal"], c["entry"]) in entries_with_ded]
    check("A5 no candidate in an entry containing 4456x", not bad, str(bad[:2]))
    bad = [c for c in cand if c["journal"].upper() in ("AN", "RAN")]
    check("A5 no candidate from the opening balances", not bad)
    bad = [c for c in cand if c["account"].startswith(("64", "616", "627", "6582"))]
    check("A5 no candidate on VAT-less accounts (payroll/insurance/bank/fines)", not bad, str(bad[:2]))
    bad = [c for c in cand if Decimal(c["expense_amount"]) <= Decimal("1")]
    check("A5 no candidate ≤ 1 €", not bad)
    bad = [c for c in cand if c["date"] and c["line21_deadline"] != f"{int(c['date'][:4]) + 2}-12-31"]
    check("A5 all deadlines equal to 31/12 N+2", not bad, str(bad[:2]))

    # A6 determinism
    check("A6 two analyses -> identical JSON",
          json.dumps(analyze(f_n), sort_keys=True, default=str) == json.dumps(res_n, sort_keys=True, default=str))

    # A7 monthly coverage of the filings
    months_sales = {r["_date"].strftime("%Y-%m") for r in rows_n
                    if r["_date"] and r["CompteNum"].startswith("7") and not r["JournalCode"].upper() in ("AN",)}
    months_liq = {l["period"] for l in res_n["vat"]["detected_ca3_filings"]}
    missing = sorted(months_sales - months_liq)
    check("A7 each month with sales has a detected filing", not missing, f"months without CA3: {missing}")

    # A8 CA3 arithmetic identity per filing:
    #     pay + L22 - L27 == coll + reverse_charge_cleared - ded  (± 2 € rounding)
    # (L27 = credit recorded = negative overflow; L22 = prior credit applied)
    bad = []
    for l in res_n["vat"]["detected_ca3_filings"]:
        lines = by_entry[(l["journal"], l["entry"])]
        autoliq = sum((x["_debit"] - x["_credit"] for x in lines
                       if x["CompteNum"].startswith(("4452", "4453"))), Decimal(0))
        lhs = Decimal(l["vat_to_pay"]) + Decimal(l["credit_applied_L22"]) - Decimal(l["credit_recorded_L27"])
        rhs = Decimal(l["collected_filed"]) + autoliq - Decimal(l["deductible_filed"])
        if (lhs - rhs).copy_abs() > Decimal("2"):
            bad.append((l["period"], str(lhs), str(rhs)))
    check("A8 CA3 identity (pay + L22 - L27 == coll + reverse_charge - ded) each month", not bad, str(bad))

    # A9 filing entries touch only 445x + 658/758 gaps
    foreign = set()
    for l in res_n["vat"]["detected_ca3_filings"]:
        for x in by_entry[(l["journal"], l["entry"])]:
            if not x["CompteNum"].startswith("445") and not x["CompteNum"].startswith(("658", "758")):
                foreign.add(x["CompteNum"])
    check("A9 filings: only 445x + 658/758 gap accounts", not foreign, str(foreign))

    print(f"\n  Reconstruction {os.path.basename(f_n)}:")
    for p, v in res_n["vat"]["reconstruction_by_period"].items():
        print(f"    {p}: coll {v['collected']:>10s} | ded {v['deductible']:>9s} | pay {v['to_pay']:>9s}")


if __name__ == "__main__":
    print("=== B. Synthetic cases ===")
    synthetic_tests()
    print("\n=== C. client-config.json robustness ===")
    client_config_tests()
    if len(sys.argv) >= 3:
        print("\n=== A. Real FEC ===")
        real_file_tests(sys.argv[1], sys.argv[2])
    print(f"\n{'='*50}\nResult: {PASS} PASS / {FAIL} FAIL")
    sys.exit(1 if FAIL else 0)
