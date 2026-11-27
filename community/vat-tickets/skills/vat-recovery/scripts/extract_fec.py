#!/usr/bin/env python3
"""Precise, VAT-oriented extraction of a FEC (Fichier des Écritures Comptables).

Compliant with the format of art. A47 A-1 of the LPF (arrêté du 29/07/2013):
18 columns, tab or pipe separator, YYYYMMDD dates, comma decimal.

Outputs:
  - integrity checks (balance, per-entry equilibrium, duplicates, bounds)
  - metadata (SIREN, closing, journals, periods)
  - general ledger balance by account and by class
  - full VAT analysis:
      * inventory and automatic classification of the 445x accounts
      * detected CA3 filing entries, reconstructed by period
      * QMG TEST: deductible VAT booked but never filed (reserve)
      * reverse-charge movements (4452 / 4456x intracom-extracom)
      * 6xx expenses with no VAT deducted in the entry -> ticket candidates,
        with the line 21 deadline (31/12 N+2)

Usage:
  python3 extract_fec.py FEC_FILE.txt                 # readable summary
  python3 extract_fec.py FEC_FILE.txt --json out.json # full export
  python3 extract_fec.py FEC_FILE.txt --section vat    # one section
Sections: meta, checks, balance, vat, reserve, candidates, all
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
import re
import sys
from collections import defaultdict
from decimal import Decimal, InvalidOperation

FEC_COLUMNS = ["JournalCode", "JournalLib", "EcritureNum", "EcritureDate",
               "CompteNum", "CompteLib", "CompAuxNum", "CompAuxLib",
               "PieceRef", "PieceDate", "EcritureLib", "Debit", "Credit",
               "EcritureLet", "DateLet", "ValidDate", "Montantdevise", "Idevise"]

# Journals to exclude from real flows (opening balances: balance-sheet carry-
# forward, not operations of the year). Detected by code AND by label.
AN_CODES = {"AN", "RAN"}

CENT = Decimal("0.01")


# ---------------------------------------------------------------- parsing --
def _dec(s: str) -> Decimal:
    s = (s or "").strip().replace(" ", "").replace(" ", "")
    if not s:
        return Decimal("0")
    s = s.replace(",", ".")
    try:
        return Decimal(s)
    except InvalidOperation:
        raise ValueError(f"Unreadable amount: {s!r}")


def _date(s: str) -> dt.date | None:
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def detect_and_read(path: str) -> tuple[list[dict], dict]:
    """Robust read: encoding (UTF-8 then cp1252), separator (tab/pipe),
    validation of the 18 columns. Returns (rows, parsing_diagnostics)."""
    raw = open(path, "rb").read()
    encoding = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(enc)
            encoding = enc
            break
        except UnicodeDecodeError:
            continue
    header_line = text.splitlines()[0]
    sep = "\t" if header_line.count("\t") >= header_line.count("|") else "|"
    reader = csv.reader(text.splitlines(), delimiter=sep)
    header = next(reader)
    header = [h.strip().lstrip("﻿") for h in header]
    diag = {"encoding": encoding, "separator": "tab" if sep == "\t" else "pipe",
            "columns": header, "columns_compliant": header == FEC_COLUMNS,
            "missing_columns": [c for c in FEC_COLUMNS if c not in header],
            "extra_columns": [c for c in header if c not in FEC_COLUMNS],
            "rejected_lines": []}
    rows = []
    for i, vals in enumerate(reader, start=2):
        if not vals or all(not v.strip() for v in vals):
            continue
        if len(vals) != len(header):
            diag["rejected_lines"].append({"line": i, "field_count": len(vals)})
            continue
        r = dict(zip(header, vals))
        try:
            r["_debit"] = _dec(r.get("Debit", "0"))
            r["_credit"] = _dec(r.get("Credit", "0"))
        except ValueError as e:
            diag["rejected_lines"].append({"line": i, "error": str(e)})
            continue
        r["_date"] = _date(r.get("EcritureDate", ""))
        r["_source_line"] = i
        rows.append(r)
    return rows, diag


def parse_filename(path: str) -> dict:
    """SIREN and closing date from the normalized name {siren}FEC{YYYYMMDD}."""
    m = re.search(r"(\d{9})FEC(\d{8})", path)
    if not m:
        return {"siren": None, "closing": None, "name_compliant": False}
    return {"siren": m.group(1),
            "closing": dt.datetime.strptime(m.group(2), "%Y%m%d").date().isoformat(),
            "name_compliant": True}


# ---------------------------------------------------------------- checks --
def integrity_checks(rows: list[dict], meta: dict) -> dict:
    total_d = sum((r["_debit"] for r in rows), Decimal(0))
    total_c = sum((r["_credit"] for r in rows), Decimal(0))
    by_entry = defaultdict(lambda: [Decimal(0), Decimal(0)])
    for r in rows:
        k = (r["JournalCode"], r["EcritureNum"])
        by_entry[k][0] += r["_debit"]
        by_entry[k][1] += r["_credit"]
    unbalanced = [{"journal": j, "entry": n,
                   "debit": str(d), "credit": str(c), "gap": str((d - c).quantize(CENT))}
                  for (j, n), (d, c) in by_entry.items()
                  if (d - c).copy_abs() > CENT]
    seen, dups = set(), 0
    for r in rows:
        k = (r["JournalCode"], r["EcritureNum"], r["CompteNum"], r["EcritureDate"],
             str(r["_debit"]), str(r["_credit"]), r["EcritureLib"])
        if k in seen:
            dups += 1
        seen.add(k)
    dates = [r["_date"] for r in rows if r["_date"]]
    closing = meta.get("closing")
    out_of_period = 0
    if closing:
        cl = dt.date.fromisoformat(closing)
        start = cl.replace(month=1, day=1)
        out_of_period = sum(1 for d in dates if not (start <= d <= cl))
    return {"line_count": len(rows), "entry_count": len(by_entry),
            "total_debit": str(total_d.quantize(CENT)),
            "total_credit": str(total_c.quantize(CENT)),
            "balanced": (total_d - total_c).copy_abs() <= CENT,
            "unbalanced_entries": unbalanced[:20],
            "unbalanced_entry_count": len(unbalanced),
            "strict_duplicates": dups,
            "date_min": min(dates).isoformat() if dates else None,
            "date_max": max(dates).isoformat() if dates else None,
            "out_of_period_lines": out_of_period}


# ----------------------------------------------------------------- balance --
def balance(rows: list[dict]) -> dict:
    per_acct = defaultdict(lambda: {"lib": "", "debit": Decimal(0), "credit": Decimal(0), "nb": 0})
    for r in rows:
        a = per_acct[r["CompteNum"]]
        a["lib"] = a["lib"] or r["CompteLib"]
        a["debit"] += r["_debit"]
        a["credit"] += r["_credit"]
        a["nb"] += 1
    out = {}
    for num in sorted(per_acct):
        a = per_acct[num]
        out[num] = {"label": a["lib"], "debit": str(a["debit"].quantize(CENT)),
                    "credit": str(a["credit"].quantize(CENT)),
                    "balance": str((a["debit"] - a["credit"]).quantize(CENT)),
                    "line_count": a["nb"]}
    per_class = defaultdict(lambda: [Decimal(0), Decimal(0)])
    for num, a in per_acct.items():
        per_class[num[0]][0] += a["debit"]
        per_class[num[0]][1] += a["credit"]
    classes = {c: {"debit": str(d.quantize(CENT)), "credit": str(cr.quantize(CENT)),
                   "balance": str((d - cr).quantize(CENT))}
               for c, (d, cr) in sorted(per_class.items())}
    return {"by_account": out, "by_class": classes}


# --------------------------------------------------------------------- VAT --
def classify_vat_account(num: str, lib: str) -> str:
    """Classify a 445x account. Test order = most specific to most general;
    the label breaks ties between free subdivisions."""
    lib_l = (lib or "").lower()
    if num.startswith("44551") or num.startswith("4455"):
        return "to_pay"
    if num.startswith("44567"):
        return "credit_carryforward"
    if num.startswith("4452") or num.startswith("4453"):
        return "reverse_charge_due"       # VAT due intracom (4452) / extracom (4453 common usage)
    if num.startswith("44583"):
        return "refund_requested"
    if num.startswith("44586") or num.startswith("44587"):
        return "adjustment_fnp_fae"       # invoices not yet received / to be issued
    if num.startswith("4458"):
        return "adjustment_pending"
    if num.startswith("44562"):
        return "deductible_fixed_assets"
    if num.startswith("44563"):
        return "deductible_transferred"
    if num.startswith("4456"):
        if "intracom" in lib_l or "extracom" in lib_l or num.startswith("445662") or num.startswith("445663"):
            return "deductible_reverse_charge"  # deductible mirror of the reverse charge
        if "encaissement" in lib_l or "attente" in lib_l or num.startswith("44564"):
            return "deductible_pending"         # chargeability not yet triggered (supplier on cash basis)
        return "deductible_other"
    if num.startswith("4457"):
        if "encaissement" in lib_l or "attente" in lib_l or num.startswith("44574"):
            return "collected_pending"
        return "collected"
    return "other_445"


CA3_LABEL = re.compile(
    r"\b(ca3|3310|liquidation)\b|"
    r"\btva\s+(janvier|f[ée]vrier|mars|avril|mai|juin|juillet|ao[ûu]t|"
    r"septembre|octobre|novembre|d[ée]cembre)\s*\d{4}", re.I)


def is_an(r: dict) -> bool:
    return r["JournalCode"].upper() in AN_CODES or "nouveau" in (r["JournalLib"] or "").lower()


def vat_analysis(rows: list[dict]) -> dict:
    vat_rows = [r for r in rows if r["CompteNum"].startswith("445")]
    # Inventory + classification
    inventory = {}
    for r in vat_rows:
        num = r["CompteNum"]
        if num not in inventory:
            inventory[num] = {"libelle": r["CompteLib"],
                              "classification": classify_vat_account(num, r["CompteLib"]),
                              "debit": Decimal(0), "credit": Decimal(0), "nb": 0}
        inventory[num]["debit"] += r["_debit"]
        inventory[num]["credit"] += r["_credit"]
        inventory[num]["nb"] += 1

    # Detection of CA3 filing entries:
    # (a) same entry with a debit on collected AND a credit on deductible,
    # or (b) label/piece evoking CA3-3310, or (c) credit 44551 / debit 44567.
    by_entry = defaultdict(list)
    for r in rows:
        by_entry[(r["JournalCode"], r["EcritureNum"])].append(r)
    liquidations = []
    liquidated_line_ids = set()
    for key, lines in by_entry.items():
        v = [l for l in lines if l["CompteNum"].startswith("445")]
        if not v:
            continue
        cls = {classify_vat_account(l["CompteNum"], l["CompteLib"]) for l in v}
        deb_coll = any(l["_debit"] > 0 and classify_vat_account(l["CompteNum"], l["CompteLib"]).startswith("collected") for l in v)
        cred_ded = any(l["_credit"] > 0 and classify_vat_account(l["CompteNum"], l["CompteLib"]).startswith("deductible") for l in v)
        label_hit = any(CA3_LABEL.search(l["EcritureLib"] or "") or CA3_LABEL.search(l["PieceRef"] or "") for l in lines)
        to_pay = any(l["CompteNum"].startswith("44551") and l["_credit"] > 0 for l in v)
        # A CA3 filing is recognized by: a credit on 44551 (VAT to pay),
        # OR a 44567 movement (carryforward recorded/applied) accompanied by
        # collected/deductible movements, OR an explicit label (CA3, 3310,
        # "TVA <month> <year>") with at least 2 VAT lines.
        # The plain debit-collected/credit-deductible pair is NOT enough:
        # per-transaction reverse-charge entries have the same profile.
        if to_pay or ("credit_carryforward" in cls and (deb_coll or cred_ded)) or (label_hit and len(v) >= 2):
            period = None
            dates = [l["_date"] for l in lines if l["_date"]]
            if dates:
                period = f"{max(dates).year}-{max(dates).month:02d}"
            coll = sum((l["_debit"] - l["_credit"] for l in v if classify_vat_account(l["CompteNum"], l["CompteLib"]).startswith("collected")), Decimal(0))
            ded = sum((l["_credit"] - l["_debit"] for l in v if classify_vat_account(l["CompteNum"], l["CompteLib"]).startswith("deductible")), Decimal(0))
            pay = sum((l["_credit"] - l["_debit"] for l in v if classify_vat_account(l["CompteNum"], l["CompteLib"]) == "to_pay"), Decimal(0))
            cred_const = sum((l["_debit"] for l in v if l["CompteNum"].startswith("44567")), Decimal(0))
            cred_imput = sum((l["_credit"] for l in v if l["CompteNum"].startswith("44567")), Decimal(0))
            liquidations.append({"journal": key[0], "entry": key[1], "period": period,
                                 "opening_balance": is_an(lines[0]),
                                 "collected_filed": str(coll.quantize(CENT)),
                                 "deductible_filed": str(ded.quantize(CENT)),
                                 "vat_to_pay": str(pay.quantize(CENT)),
                                 "credit_recorded_L27": str(cred_const.quantize(CENT)),
                                 "credit_applied_L22": str(cred_imput.quantize(CENT)),
                                 "sample_label": lines[0]["EcritureLib"][:80]})
            for l in v:
                liquidated_line_ids.add(id(l))

    # Reconstruction by period (excluding opening balances) — filed flows
    per_period = defaultdict(lambda: {"collected": Decimal(0), "deductible": Decimal(0),
                                      "to_pay": Decimal(0)})
    for liq in liquidations:
        if liq["opening_balance"] or not liq["period"]:
            continue
        p = per_period[liq["period"]]
        p["collected"] += Decimal(liq["collected_filed"])
        p["deductible"] += Decimal(liq["deductible_filed"])
        p["to_pay"] += Decimal(liq["vat_to_pay"])
    reconstruction = {k: {kk: str(vv.quantize(CENT)) for kk, vv in v.items()}
                      for k, v in sorted(per_period.items())}

    # QMG TEST — reserve: deductible balances not cleared by a filing.
    # The final balance of each deductible account (excluding "pending" and
    # excluding reverse-charge mirrors, handled separately) is VAT booked
    # but never put through a CA3 filing => never declared => it expires.
    reserve = {}
    for num, a in inventory.items():
        if a["classification"] in ("deductible_other", "deductible_fixed_assets"):
            solde = (a["debit"] - a["credit"]).quantize(CENT)
            if solde > CENT:
                reserve[num] = {"label": a["libelle"], "classification": a["classification"],
                                "unfiled_balance": str(solde)}
    pending = {}
    for num, a in inventory.items():
        if a["classification"] in ("deductible_pending", "collected_pending"):
            solde = (a["debit"] - a["credit"]).quantize(CENT)
            if solde.copy_abs() > CENT:
                pending[num] = {"label": a["libelle"], "classification": a["classification"],
                                "balance": str(solde)}

    # Reverse charge: balance of due (4452/4453) vs deductible mirror
    due = sum(((a["credit"] - a["debit"]) for n, a in inventory.items()
              if a["classification"] == "reverse_charge_due"), Decimal(0))
    mirror = sum(((a["debit"] - a["credit"]) for n, a in inventory.items()
                 if a["classification"] == "deductible_reverse_charge"), Decimal(0))
    inv_out = {n: {"label": a["libelle"], "classification": a["classification"],
                   "debit": str(a["debit"].quantize(CENT)),
                   "credit": str(a["credit"].quantize(CENT)),
                   "balance": str((a["debit"] - a["credit"]).quantize(CENT)),
                   "line_count": a["nb"]}
               for n, a in sorted(inventory.items())}
    return {"inventory_445_accounts": inv_out,
            "detected_ca3_filings": sorted([l for l in liquidations if not l["opening_balance"]],
                                           key=lambda x: (x["period"] or "", x["entry"])),
            "filings_in_opening_balances": [l for l in liquidations if l["opening_balance"]],
            "reconstruction_by_period": reconstruction,
            "unfiled_deductible_reserve": reserve,
            "accounts_pending_chargeability": pending,
            "reverse_charge": {"net_vat_due": str(due.quantize(CENT)),
                               "net_deductible_mirror": str(mirror.quantize(CENT)),
                               "gap_due_vs_mirror": str((due - mirror).quantize(CENT))}}


# --------------------------------------------------------------- candidates --
# 6xx accounts usually WITHOUT recoverable VAT: do not generate false positives.
NO_VAT_PREFIXES = ("64", "63", "66", "68", "69", "6411", "645", "646", "647",
                   "616",   # insurance (exempt)
                   "627",   # banking services (exempt unless opted in)
                   "6581", "6582",  # penalties and fines
                   "6354",  # registration duties
                   "654",   # bad-debt losses
                   )
EXCLUDED_BY_NATURE = ("6251",)  # travel & displacement: passenger transport (art. 206 IV-2-5°)
# Accounts requiring a breakdown before any verdict (mixed nature).
# STRUCTURED alert levels: ("exclusion"|"breakdown", message).
# Consumers (agents, scripts) must route on `alert_level`, NEVER on the text:
# the breakdown-alert prose contains BOTH "EXCLUDED" and "DEDUCTIBLE" (field
# lesson: a substring filter on 'exclu' deleted perfectly deductible
# restaurant tickets).
MIXED_NATURE_WARN = {
    "625": ("breakdown", "mission/travel: break down — passenger transport EXCLUDED (206 IV-2-5°), "
            "hotel/accommodation EXCLUDED unless for a third party's benefit (206 IV-2-2°), meals DEDUCTIBLE"),
    "6234": ("breakdown", "client gifts: deductible only if ≤ the threshold of art. 28-00 A ann. IV (incl. VAT/item/year/beneficiary)"),
    "6135": ("breakdown", "movable-property rental: EXCLUDED if a passenger vehicle (206 IV-2-10°), deductible otherwise"),
    "612": ("breakdown", "leasing/royalties: EXCLUDED if a passenger vehicle (206 IV-2-10°), deductible otherwise — "
            "nature of the asset to be checked against the contract (often a high stake: recurring rents)"),
}


def candidates(rows: list[dict]) -> dict:
    """6xx expenses with no 4456x line in the same entry -> VAT possibly
    never booked nor deducted. Pre-filtering by nature (structurally VAT-less
    accounts excluded); final verdict = the invoice."""
    by_entry = defaultdict(list)
    for r in rows:
        if not is_an(r):
            by_entry[(r["JournalCode"], r["EcritureNum"])].append(r)
    out, total_base = [], Decimal(0)
    for key, lines in by_entry.items():
        has_ded = any(l["CompteNum"].startswith("4456") for l in lines)
        if has_ded:
            continue
        for l in lines:
            num = l["CompteNum"]
            if not num.startswith("6"):
                continue
            montant = (l["_debit"] - l["_credit"]).quantize(CENT)
            if montant <= Decimal("1"):
                continue
            if any(num.startswith(p) for p in NO_VAT_PREFIXES):
                continue
            nature_excluded = any(num.startswith(p) for p in EXCLUDED_BY_NATURE)
            alerte, niveau = (("passenger transport: excluded art. 206 IV-2-5°", "exclusion")
                              if nature_excluded else (None, None))
            if not alerte:
                for pref, (niv, msg) in MIXED_NATURE_WARN.items():
                    if num.startswith(pref):
                        alerte, niveau = msg, niv
                        break
            year = l["_date"].year if l["_date"] else None
            ddl = f"{year + 2}-12-31" if year else None
            out.append({"journal": key[0], "entry": key[1],
                        "date": l["_date"].isoformat() if l["_date"] else None,
                        "account": num, "account_label": l["CompteLib"][:50],
                        "label": l["EcritureLib"][:90], "piece_ref": l["PieceRef"],
                        "expense_amount": str(montant),
                        "potential_vat_20pc": str((montant * Decimal("0.20")).quantize(CENT)),
                        "line21_deadline": ddl,
                        "alert_nature": alerte, "alert_level": niveau})
            if not nature_excluded:
                total_base += montant
    out.sort(key=lambda x: Decimal(x["expense_amount"]), reverse=True)
    return {"candidate_count": len(out),
            "expense_base_excl_exclusions": str(total_base.quantize(CENT)),
            "max_potential_vat_at_20pc": str((total_base * Decimal("0.20")).quantize(CENT)),
            "warning": ("Maximum-base estimate BEFORE invoice-by-invoice verification. "
                        "Each line must pass the vat-heuristics.md table and the "
                        "formal-conditions.md grid; estimate ≠ declaration."),
            "lines": out}


# -------------------------------------------------------------------- main --


# ------------------------------------------------- time window (208) --
def time_window(rows: list[dict], vat: dict) -> dict:
    """Legal recovery bounds at the analysis date (art. 208, I ann. II:
    deduction possible until 31/12 of the 2nd year following the omission).
    TO SHOW TO THE USER: open years, days left, time-barred years, and the
    downstream bound = last period actually filed (beyond it: current flow,
    NOT omissions)."""
    today = dt.date.today()
    years = sorted({d.year for r in rows if (d := _date(r["EcritureDate"]))})
    liqs = [l["period"] for l in vat.get("detected_ca3_filings", []) if l.get("period")]
    last_filing = max(liqs) if liqs else None
    out_years = {}
    for y in years:
        ddl = dt.date(y + 2, 12, 31)
        remaining = (ddl - today).days
        out_years[str(y)] = {"line21_deadline": ddl.isoformat(),
                             "status": "TIME_BARRED" if remaining < 0 else "OPEN",
                             "days_left": max(remaining, 0) if remaining >= 0 else None}
    return {"analysis_date": today.isoformat(),
            "last_filing_detected": last_filing,
            "years": out_years,
            "current_flow_warning":
                (f"Any expense after the {last_filing} period is not an omission "
                 "(its declaration has not happened yet) but a TO-SECURE ticket: "
                 "VAT lost if the invoice is not provided before the next CA3 return "
                 "closes — counted in the pot, NEVER on line 21."
                 if last_filing else
                 "No CA3 filing detected in this FEC: impossible to distinguish "
                 "omission from current flow — ask for the declared periods."),
            "regimes_reminder": "Strict deadline = French VAT (line 21). Omitted reverse "
                                "charge: no time bar if voluntary disclosure (§100)."}


def _load_aliases() -> dict:
    """Supplier alias -> canonical token, from client-config.json (auto-
    generated at step 0: e.g. payments under the PERSON'S NAME when the
    invoices carry the COMPANY'S NAME). Absent OR malformed = no aliases,
    NEVER a crash — client-config.json is hand-editable by the user
    (SKILL.md, validation) and a typo must not stop the whole run."""
    import os
    path = os.environ.get("VAT_RECOVERY_CLIENT_CONFIG",
                          os.path.join(os.path.dirname(__file__), "..", "client-config.json"))
    if not os.path.exists(path):
        return {}
    try:
        data = json.load(open(path, encoding="utf-8"))
        alias = data.get("supplier_aliases", {})
        if not isinstance(alias, dict):
            raise TypeError("supplier_aliases must be an object {person: company}")
        return {str(k).lower(): str(v).lower() for k, v in alias.items()}
    except Exception as e:
        print(f"⚠ client-config.json ignored (supplier_aliases): {e}", file=sys.stderr)
        return {}


_ALIASES = _load_aliases()


def _token(lib: str) -> str:
    """First meaningful word of a label, normalized, aliases applied —
    an approximate supplier key ('Facture DUPONT - 63' -> 'dupont')."""
    words = re.sub(r"[^a-zà-ÿ]", " ", lib.lower()).split()
    for m in words:
        if m not in ("facture", "fact", "fac", "avoir", "virement", "sepa"):
            return _ALIASES.get(m, m)
    return _ALIASES.get(words[0], words[0]) if words else ""


def supplier_profiles(rows: list[dict]) -> dict:
    """PROBABLE VAT regime per supplier, inferred from the accounting history —
    never asked of the user. A supplier with at least one entry carrying
    deductible VAT (4456x debit) = registered_history; seen only in expenses
    without VAT = presumed_franchise; the invoice decides."""
    ecritures = defaultdict(list)
    for r in rows:
        if not is_an(r):
            ecritures[(r["JournalCode"], r["EcritureNum"], r["EcritureDate"])].append(r)
    stats = defaultdict(lambda: {"with_vat": 0, "without_vat": 0})
    for lignes in ecritures.values():
        has_vat = any(l["CompteNum"].startswith("4456") and _dec(l["Debit"]) > 0 for l in lignes)
        for l in lignes:
            if l["CompteNum"].startswith("6"):
                t = _token(l["EcritureLib"])
                if t:
                    stats[t]["with_vat" if has_vat else "without_vat"] += 1
    profiles = {}
    for t, c in stats.items():
        if c["with_vat"] and not c["without_vat"]:
            profiles[t] = "registered_history"
        elif c["with_vat"] and c["without_vat"]:
            profiles[t] = "mixed_to_verify"
        else:
            profiles[t] = "presumed_franchise"
    return profiles


# ------------------------------------- payments without a booked invoice --
def payments_without_invoice(rows: list[dict]) -> dict:
    """ACCOUNTING orphans: disbursements (debit 401/4716 against credit 512)
    with no matching invoice (credit 401 in an entry carrying a 6xx expense
    or 4456x VAT). Matching by exact amount — candidates to reproduce by hand
    before any flagging (SKILL.md guardrail)."""
    ecritures = defaultdict(list)
    for r in rows:
        if not is_an(r):
            ecritures[(r["JournalCode"], r["EcritureNum"], r["EcritureDate"])].append(r)
    invoices = defaultdict(int)     # (amount, supplier) -> number of 401 credits
    payments = []
    # Opening debts: invoices from the PREVIOUS year unpaid at opening (401/4716
    # credits in the opening balances) — without them, any 2026 payment of a
    # 2025 invoice would be a false orphan.
    for r in rows:
        if is_an(r) and r["CompteNum"].startswith(("401", "4716")):
            m = _dec(r["Credit"])
            if m > 0:
                invoices[(m, _token(r["EcritureLib"]))] += 1
    for lignes in ecritures.values():
        comptes = [l["CompteNum"] for l in lignes]
        has_expense = any(c.startswith("6") for c in comptes)
        has_ded_vat = any(c.startswith("4456") and _dec(l["Debit"]) > 0
                          for l, c in zip(lignes, comptes))
        has_bank = any(c.startswith("512") for c in comptes)
        for l in lignes:
            if l["CompteNum"].startswith(("401", "4716")):
                m = _dec(l["Credit"])
                if m > 0 and (has_expense or has_ded_vat):
                    invoices[(m, _token(l["EcritureLib"]))] += 1
                d = _dec(l["Debit"])
                if d > 0 and has_bank:
                    payments.append((l["EcritureDate"], l["EcritureLib"], d))
    raw_orphans = []
    for date_p, lib, montant in sorted(payments):
        cle = (montant, _token(lib))
        if invoices.get(cle, 0) > 0:
            invoices[cle] -= 1          # exact match (amount + supplier)
        else:
            raw_orphans.append({"date": date_p, "label": lib[:60],
                                "amount": montant, "token": _token(lib)})
    # Pass 2 — net balance per supplier: covers SPLIT payments (N payments for
    # 1 invoice, e.g. an N-1 invoice cleared in N) and GROUPED ones (1 payment
    # for N invoices). We compare the residual totals.
    remaining_credits = defaultdict(lambda: Decimal("0"))
    for (m, tok), n in invoices.items():
        if n > 0:
            remaining_credits[tok] += m * n
    orphans = []
    by_token = defaultdict(list)
    for o in raw_orphans:
        by_token[o["token"]].append(o)
    for tok, lst in by_token.items():
        total_paid = sum(o["amount"] for o in lst)
        cr = remaining_credits.get(tok, Decimal("0"))
        if cr >= total_paid:
            continue                     # payments covered in aggregate -> not orphans
        if cr > 0:
            net = (total_paid - cr).quantize(CENT)
            orphans.append({"date": max(o["date"] for o in lst),
                            "label": f"{tok} — net balance after split reconciliation",
                            "amount": str(net), "net_after_reconciliation": True,
                            "payment_count": len(lst)})
        else:
            for o in lst:
                orphans.append({"date": o["date"], "label": o["label"],
                                "amount": str(o["amount"])})
    orphans.sort(key=lambda o: o["date"])
    groupes = defaultdict(lambda: {"nb": 0, "total": Decimal("0")})
    for o in orphans:
        cle = " ".join(re.sub(r"[^a-zà-ÿ ]", " ", o["label"].lower()).split()[:2]) or "(no label)"
        groupes[cle]["nb"] += 1
        groupes[cle]["total"] += Decimal(o["amount"])
    return {"payments_without_invoice_count": len(orphans),
            "total": str(sum((Decimal(o["amount"]) for o in orphans), Decimal("0")).quantize(CENT)),
            "by_supplier_approx": {k: {"count": v["nb"], "total": str(v["total"].quantize(CENT))}
                                   for k, v in sorted(groupes.items(), key=lambda x: -x[1]["total"])[:15]},
            "lines": orphans,  # COMPLETE list (a truncation here once hid real recent orphans)
            "note": "2-pass matching: (exact amount + supplier, opening AN debts included) "
                    "then net balance per supplier (split/grouped payments): false positives possible "
                    "(deposits, grouped payments) and false negatives (a payment absorbed by an old "
                    "unpaid invoice from the same supplier at the same amount) — reproduce by hand "
                    "before flagging"}


def analyze(path: str) -> dict:
    rows, diag = detect_and_read(path)
    meta = parse_filename(path)
    journaux = defaultdict(lambda: {"label": "", "count": 0})
    for r in rows:
        journaux[r["JournalCode"]]["label"] = journaux[r["JournalCode"]]["label"] or r["JournalLib"]
        journaux[r["JournalCode"]]["count"] += 1
    meta["journals"] = {k: dict(v) for k, v in sorted(journaux.items())}
    vat = vat_analysis(rows)
    window = time_window(rows, vat)
    cand = candidates(rows)
    # Zone of each candidate: period <= last filing = OMISSION (line 21
    # recovery); later = TO_SECURE (current flow: provide the invoice before
    # the next CA3 return, VAT lost otherwise).
    dliq = window["last_filing_detected"]
    profiles = supplier_profiles(rows)
    low = high = Decimal("0")
    tot = {"omission": Decimal("0"), "to_secure": Decimal("0")}
    for l in cand.get("lines", []):
        l["supplier_profile"] = profiles.get(_token(l["label"]), "unknown")
        # PER-LINE CATEGORICAL estimate — never a uniform 20%:
        # exclusion by nature -> 0; catering/hospitality -> 10%;
        # default -> 20% VAT included. The agent then refines via
        # route_label + qualify before any announcement (SKILL.md, 3 quater).
        m = Decimal(l["expense_amount"])
        if l.get("alert_level") == "exclusion":
            taux = Decimal("0")
        elif l["account"].startswith("6257"):
            taux = Decimal("0.10")
        else:
            taux = Decimal("0.20")
        vat_est = (m - m / (1 + taux)).quantize(CENT) if taux else Decimal("0.00")
        l["estimated_vat"] = str(vat_est)
        high += vat_est
        if l["supplier_profile"] == "registered_history":
            low += vat_est
    cand["vat_range"] = {
        "low_corroborated": str(low.quantize(CENT)),
        "high_theoretical": str(high.quantize(CENT)),
        "definition": "PER-LINE CATEGORICAL estimate (estimated_vat: exclusions at 0, reduced rate, VAT included); low = lines of the suppliers registered per "
                      "the accounting history only (excluding exclusions by nature); high = "
                      "VAT-included of the whole base excluding exclusions. Reconciling the "
                      "invoices tightens the range."}
    for l in cand.get("lines", []):
        period = l.get("date", "")[:7]
        zone = "omission" if (dliq and period <= dliq) else ("to_secure" if dliq else "undetermined")
        l["zone"] = zone
        if zone in tot:
            tot[zone] += Decimal(l["expense_amount"])
    cand["omission_zone_base"] = str(tot["omission"].quantize(CENT))
    cand["to_secure_zone_base"] = str(tot["to_secure"].quantize(CENT))
    orph = payments_without_invoice(rows)
    for o in orph.get("lines", []):
        p = f"{o['date'][:4]}-{o['date'][4:6]}" if len(o.get("date", "")) >= 6 else ""
        o["zone"] = "omission" if (dliq and p and p <= dliq) else ("to_secure" if dliq else "undetermined")
    return {"meta": meta, "parsing": diag,
            "time_window": window,
            "checks": integrity_checks(rows, meta),
            "accounting_orphans": orph,
            "balance": balance(rows),
            "vat": vat,
            "ticket_candidates": cand}


def print_summary(res: dict) -> None:
    m, c, t, cand = res["meta"], res["checks"], res["vat"], res["ticket_candidates"]
    p = res["parsing"]
    print(f"SIREN {m['siren']} — closing {m['closing']} | {c['line_count']} lines, "
          f"{c['entry_count']} entries | encoding {p['encoding']}, sep. {p['separator']}, "
          f"columns {'OK' if p['columns_compliant'] else 'NON-COMPLIANT'}")
    print(f"Balance: D {c['total_debit']} / C {c['total_credit']} -> "
          f"{'balanced' if c['balanced'] else 'UNBALANCED'} | "
          f"unbalanced entries: {c['unbalanced_entry_count']} | duplicates: {c['strict_duplicates']} | "
          f"out of period: {c['out_of_period_lines']}")
    journals = ", ".join(f"{k}({v['count']})" for k, v in m["journals"].items())
    print(f"Journals: {journals}")
    f = res["time_window"]
    print(f"\n=== RECOVERY WINDOW at {f['analysis_date']} (art. 208, I ann. II) ===")
    for y, v in f["years"].items():
        if v["status"] == "TIME_BARRED":
            print(f"  VAT {y}: TIME-BARRED since {v['line21_deadline']} (dead ticket)")
        else:
            print(f"  VAT {y}: recoverable until {v['line21_deadline']} — {v['days_left']} days left")
    print(f"  Last CA3 filing detected: {f['last_filing_detected'] or 'NONE'}")
    print(f"  ⚠ {f['current_flow_warning']}")
    print(f"  {f['regimes_reminder']}")
    o = res["accounting_orphans"]
    if o["payments_without_invoice_count"]:
        print(f"\n--- ACCOUNTING ORPHANS: {o['payments_without_invoice_count']} payments without a booked invoice, total {o['total']} €")
        for k, v in list(o["by_supplier_approx"].items())[:8]:
            print(f"  {k[:40]:42s} {v['count']:>3} payment(s)  {v['total']:>10s} €  <- claim the invoices")
        print(f"  ({o['note']})")
    print(f"\n--- VAT: {len(t['inventory_445_accounts'])} 445x accounts, "
          f"{len(t['detected_ca3_filings'])} CA3 filings detected (excl. AN)")
    for period, v in t["reconstruction_by_period"].items():
        print(f"  {period}: collected {v['collected']:>10s} | deductible {v['deductible']:>10s} | to pay {v['to_pay']:>10s}")
    print(f"\n--- RESERVE (QMG test) — deductible booked but never filed:")
    if t["unfiled_deductible_reserve"]:
        for num, g in t["unfiled_deductible_reserve"].items():
            print(f"  {num} {g['label'][:45]:47s} {g['unfiled_balance']:>10s} €  <- to qualify BEFORE the time bar")
    else:
        print("  none")
    if t["accounts_pending_chargeability"]:
        print("  Accounts pending chargeability (normal if supplier/client on cash basis):")
        for num, g in t["accounts_pending_chargeability"].items():
            print(f"    {num} {g['label'][:40]:42s} balance {g['balance']}")
    a = t["reverse_charge"]
    print(f"\n--- Reverse charge: net due {a['net_vat_due']} | deductible mirror {a['net_deductible_mirror']} | gap {a['gap_due_vs_mirror']}")
    print(f"\n--- Ticket candidates (expenses with no VAT deducted, excl. structurally VAT-less accounts):")
    fch = cand.get("vat_range", {})
    print(f"  VAT RANGE (before reconciling invoices): "
          f"{fch.get('low_corroborated','?')} € corroborated — {fch.get('high_theoretical','?')} € theoretical")
    print(f"  POT IN TWO SEGMENTS — omission (line 21, deadline 31/12 N+2): "
          f"{cand.get('omission_zone_base', '?')} € of base | "
          f"to secure (current flow, invoice BEFORE the next CA3 return): "
          f"{cand.get('to_secure_zone_base', '?')} € of base")
    print(f"  {cand['candidate_count']} lines | base excl. exclusions {cand['expense_base_excl_exclusions']} € | "
          f"max theoretical VAT 20% {cand['max_potential_vat_at_20pc']} €")
    for l in cand["lines"][:15]:
        flag = f"  [{l['alert_nature'][:60]}]" if l["alert_nature"] else ""
        print(f"  {l['date']} {l['account']:8s} {l['expense_amount']:>10s} €  ddl {l['line21_deadline']}  {l['label'][:52]}{flag}")
    if cand["candidate_count"] > 15:
        print(f"  ... {cand['candidate_count'] - 15} more (use --json for the full list)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("fec")
    ap.add_argument("--json", metavar="OUT", help="full JSON export")
    ap.add_argument("--section", default="summary",
                    choices=["summary", "meta", "checks", "balance", "vat", "reserve", "candidates", "all"])
    args = ap.parse_args()
    res = analyze(args.fec)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=1, default=str)
        print(f"JSON written: {args.json}", file=sys.stderr)
    if args.section == "summary":
        print_summary(res)
    elif args.section == "all":
        json.dump(res, sys.stdout, ensure_ascii=False, indent=1, default=str)
    elif args.section == "reserve":
        json.dump({"reserve": res["vat"]["unfiled_deductible_reserve"],
                   "pending": res["vat"]["accounts_pending_chargeability"]},
                  sys.stdout, ensure_ascii=False, indent=1)
    elif args.section == "candidates":
        json.dump(res["ticket_candidates"], sys.stdout, ensure_ascii=False, indent=1)
    else:
        json.dump(res[args.section], sys.stdout, ensure_ascii=False, indent=1, default=str)
