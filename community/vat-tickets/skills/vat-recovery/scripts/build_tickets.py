#!/usr/bin/env python3
"""THE TICKET FACTORY — the deterministic core of the product.

    FEC (extract_fec.py --json)   ─┐
    Invoices read by vision       ─┼──>  build_tickets.py  ──>  tickets.json
    Bank transactions             ─┘                              │
                                                                 ├─> the interface (board)
                                                                 └─> build_pack.py (deliverables)

WHY THIS FILE EXISTS
--------------------
Before it, the path « FEC candidates + orphans + invoices -> tickets » lived
in the agent's head, redone from scratch on every run. That is what produced
the « Émilie » bug (12/07/2026): a line promoted to « firm won, €1,076 » on
the supplier's history, while the invoice carried « VAT not applicable —
€0 ». Exactly the opposite of the product.

Invariant 5 of SKILL.md already forbade this fault. A prose rule is not
enough: an LLM under pressure violates it. Here it becomes MECHANICAL.

THE THREE LOCKS (never loosen them)
-----------------------------------
1. TWO FIELDS THAT NEVER MERGE.
   - `vat_amount`          : filled ONLY by the vision reading of an invoice.
                             None by default. It is the ONLY declarable amount.
   - `estimated_potential` : filled by categorical inference. NEVER declarable.
   No function in this module adds them. The pot has two segments and does NOT
   expose a total: `Pot` has no `total` attribute.

2. `won` IS IMPOSSIBLE WITHOUT A READ INVOICE.
   `_assert_invariants()` raises TicketInvariantError if a `won` ticket lacks
   (invoice AND vat_amount > 0). The script stops. Not a warning: a stop.

3. GRAMMAR IMPOSED BY THE CODE, NOT BY THE PROMPT.
   `amount_label` is generated here. An invoice-less ticket cannot show a bare
   amount, nor the words « probable »/« likely » (indefensible statistical
   assertion — accountant's note, 13/07/2026), nor a countdown (urgency
   manufactured on a right we don't know exists: art. L. 121-6 C. conso).
   Single format: « Up to X € — if your <F> invoice carries French VAT. »
   + the action + the effort. Never an amount alone.

CONVENTIONS
-----------
- The amount of an expense with no VAT deducted is gross (it's precisely
  because the VAT was not isolated that it stayed inside the expense): the
  estimated VAT is therefore « VAT included », m - m/(1+rate).
- CONSERVATIVE rounding of the potential: floor to the euro. We announce ~€25,
  the invoice reveals €25.80 -> the effort is retroactively a good deal. We
  never disappoint on the only number that matters. (And we SAY so to the user.)
- The countdown only exists on a ticket with a read invoice.

Usage:
  python3 build_tickets.py --fec fec2024.json --fec fec2025.json \
                           --invoices invoices.json [--out tickets.json]
  python3 build_tickets.py --test
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import re
import sys
import unicodedata
from dataclasses import dataclass, field, asdict
from decimal import Decimal
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from route_label import route                         # label -> category
    from qualify_ticket import qualify                     # category -> verdict
except ImportError:                                        # execution outside the folder
    route = None                                          # type: ignore
    qualify = None                                        # type: ignore


# ============================================================ exceptions ====
class TicketInvariantError(AssertionError):
    """A product invariant was violated. We stop. We do not silently 'fix' it:
    a false ticket is worth less than no ticket at all."""


# ============================================================== statuses ====
WON = "won"                     # invoice read + French VAT + never declared + within the deadline
TO_PLAY = "to_play"             # no invoice -> potential + action + effort
TO_SECURE = "to_secure"         # current flow: invoice to provide before the next CA3 return
DEAD = "dead"                   # excluded by law, or time-barred, or nothing to recover
ALREADY_DEDUCTED = "already_deducted"   # already filed on a CA3 return
TO_REVIEW = "to_review"         # contradictory signals -> the accountant decides
FIX = "fix"                     # foreign SaaS without an intra-EU VAT number: a LEAK,
                                # not a ticket. Nothing to « recover » on the CA3 return —
                                # you stop the bleeding, and sometimes claw back the
                                # past from the supplier (Google, AWS, OpenAI).
                                # This is the €1,500 card of the true story.

# Statuses whose amount is CERTAIN (invoice read). The only declarable ones.
FIRM_STATUSES = {WON}
# Scratchable statuses (the user can click). A dead one isn't scratched:
# making someone scratch a zero is theft of time.
SCRATCHABLE_STATUSES = {TO_PLAY, TO_SECURE, FIX}

# Suppliers who refund VAT wrongly charged once the intra-EU VAT number is
# filled in (references/invoice-retrieval.md, recovery table). The rest only
# counts for the future — hence the urgency of doing it TODAY.
RETROACTIVE_VAT_ID = {
    "google": "Written procedure « Get credit for previous VAT charges » — no announced limit",
    "aws": "AWS reissues past invoices via a support case",
    "openai": "Refund on explicit request to support (invoice numbers + amounts)",
    "slack": "Within 90 days only",
    "figma": "Within 30 days only",
    "canva": "Limited cases, ~30 days",
}


# ====================================================== retrieval index =====
# Where to retrieve the invoice, and what it costs. Source: references/invoice-retrieval.md
# (sourced research, 2 sources minimum per supplier). The `verified` field
# reflects reliability: we NEVER invent a navigation path — a false path
# destroys trust more surely than a « I don't know ».
DEFAULT_RETRIEVAL_INDEX: dict[str, dict[str, Any]] = {
    "darty":       {"where": "darty.com > Mon compte > Mes commandes > la commande > Facture (PDF)",
                    "url": "https://www.darty.com/mon-compte/commandes",
                    "minutes": 3, "prerequisite": "customer account", "verified": True},
    "fnac":        {"where": "fnac.com > Mon compte > Mes commandes > Télécharger la facture",
                    "url": "https://www.fnac.com/Account/Orders",
                    "minutes": 3, "prerequisite": "customer account", "verified": True},
    "amazon":      {"where": "amazon.fr > Vos commandes > Facture > Télécharger",
                    "url": "https://www.amazon.fr/gp/css/order-history",
                    "minutes": 3, "prerequisite": "customer account",
                    "pitfall": "order under a personal name -> corrective invoice to request from the seller",
                    "verified": True},
    "ldlc":        {"where": "ldlc.com > Mon compte > Mes commandes > Facture",
                    "url": "https://secure.ldlc.com/fr-fr/Account/Orders",
                    "minutes": 3, "prerequisite": "customer account", "verified": True},
    "boulanger":   {"where": "boulanger.com > Mon compte > Mes achats > Facture",
                    "url": "https://www.boulanger.com/mon-compte/mes-achats",
                    "minutes": 3, "prerequisite": "customer account", "verified": True},
    "apple":       {"where": "reportaproblem.apple.com (App Store) ou apple.com > Mon compte > Commandes",
                    "url": "https://reportaproblem.apple.com",
                    "minutes": 5, "prerequisite": "Apple ID", "verified": True},
    "leroy":       {"where": "leroymerlin.fr > Mon compte > Mes commandes > Facture",
                    "url": "https://www.leroymerlin.fr/mon-compte/mes-commandes",
                    "minutes": 4, "prerequisite": "customer account", "verified": True},
    "castorama":   {"where": "castorama.fr > Mon compte > Mes commandes",
                    "url": "https://www.castorama.fr/mon-compte",
                    "minutes": 4, "prerequisite": "customer account", "verified": True},
    "orange":      {"where": "Espace client Orange > Factures. PRO : téléchargement groupé par année (6 ans d'historique)",
                    "url": "https://espace-client.orange.fr/factures-paiement",
                    "minutes": 6, "prerequisite": "Orange account",
                    "pitfall": "consumer plans: rolling 24 months only, no more duplicates since 10/03/2026",
                    "verified": True},
    "sfr":         {"where": "Espace client SFR > Mes factures (SFR Business : 3 ans + export)",
                    "url": "https://espace-client.sfr.fr/facture-mobile/consultation",
                    "minutes": 6, "prerequisite": "SFR account", "verified": True},
    "bouygues":    {"where": "Espace client Bouygues Pro > Factures > « Export multi-CF »",
                    "url": "https://www.bouyguestelecom.fr/mon-compte/mes-factures",
                    "minutes": 5, "prerequisite": "Bouygues account", "verified": True},
    "free":        {"where": "Espace abonné Free > Mes factures",
                    "url": "https://subscribe.free.fr/login/",
                    "minutes": 5, "prerequisite": "Free account", "verified": True},
    "totalenergies": {"where": "Espace client TotalEnergies (carte pro) > Factures",
                    "minutes": 6, "prerequisite": "pro fuel card",
                    "pitfall": "card payment without a pro card: till receipt to find, duplicates rare",
                    "verified": True},
    "vinci":       {"where": "Ulys / Bip&Go / APRR > Espace abonné > Factures mensuelles",
                    "minutes": 4, "prerequisite": "electronic toll subscription", "verified": True},
    "ulys":        {"where": "ulys.vinci-autoroutes.com > Mon compte > Mes factures",
                    "minutes": 4, "prerequisite": "Ulys account", "verified": True},
    # --- Foreign SaaS: the real subject is not the invoice, it's the VAT ID ---
    "anthropic":   {"where": "console.anthropic.com > Settings > Billing > Invoices",
                    "url": "https://console.anthropic.com/settings/billing",
                    "minutes": 3, "prerequisite": "console access",
                    "pitfall": "VAT ID missing -> local VAT charged, NOT recoverable. Anthropic does NOT refund retroactively: entering the intra-EU VAT number TODAY stops the bleeding.",
                    "verified": True},
    "openai":      {"where": "platform.openai.com > Settings > Billing > Invoices",
                    "url": "https://platform.openai.com/settings/organization/billing/history",
                    "minutes": 3, "prerequisite": "account access",
                    "pitfall": "retroactive VAT refund possible ON explicit request to support (invoice numbers + amounts)",
                    "verified": True},
    "google":      {"where": "admin.google.com > Facturation > Documents de facturation",
                    "url": "https://admin.google.com/ac/billing/documents",
                    "minutes": 4, "prerequisite": "admin account",
                    "pitfall": "Google Ireland: WRITTEN retroactive VAT refund procedure (« Get credit for previous VAT charges ») — the best recovery on the market",
                    "verified": True},
    "microsoft":   {"where": "admin.microsoft.com > Facturation > Factures et paiements",
                    "url": "https://admin.microsoft.com/#/billoverview/invoice-list",
                    "minutes": 4, "prerequisite": "admin account", "verified": True},
    "adobe":       {"where": "account.adobe.com > Plans > Historique de facturation",
                    "url": "https://account.adobe.com/plans",
                    "minutes": 3, "prerequisite": "Adobe ID", "verified": True},
    "aws":         {"where": "console.aws.amazon.com/billing > Bills > Invoice",
                    "url": "https://console.aws.amazon.com/billing/home#/bills",
                    "minutes": 4, "prerequisite": "console access",
                    "pitfall": "AWS REISSUES invoices with the VAT ID retroactively, via a support case",
                    "verified": True},
    "github":      {"where": "github.com > Settings > Billing > Payment information > Invoices",
                    "url": "https://github.com/settings/billing",
                    "minutes": 3, "prerequisite": "account", "verified": True},
    "notion":      {"where": "notion.so > Settings > Billing > Invoice history",
                    "url": "https://www.notion.so/my-settings",
                    "minutes": 3, "prerequisite": "workspace admin",
                    "pitfall": "Notion does NOT refund VAT already charged",
                    "verified": True},
    "figma":       {"where": "figma.com > Admin > Billing > Invoices",
                    "url": "https://www.figma.com/files/settings",
                    "minutes": 3, "prerequisite": "admin",
                    "pitfall": "VAT refund possible within 30 days only",
                    "verified": True},
    "slack":       {"where": "slack.com > Réglages admin > Facturation > Factures",
                    "url": "https://slack.com/billing",
                    "minutes": 3, "prerequisite": "admin",
                    "pitfall": "VAT refund possible within 90 days only",
                    "verified": True},
    "canva":       {"where": "canva.com > Paramètres du compte > Facturation",
                    "url": "https://www.canva.com/settings/billing-and-plans",
                    "minutes": 3, "prerequisite": "account", "verified": True},
    "linkedin":    {"where": "linkedin.com > Préférences > Abonnements > Historique de facturation",
                    "url": "https://www.linkedin.com/premium/my-premium/",
                    "minutes": 4, "prerequisite": "account",
                    "pitfall": "written non-retroactivity: the VAT ID only applies to future invoices",
                    "verified": True},
    "vercel":      {"where": "vercel.com > Settings > Billing > Invoices",
                    "url": "https://vercel.com/account/billing",
                    "minutes": 3, "prerequisite": "account", "verified": True},
}

EFFORT_LABELS = [(2, "⚡"), (10, "🔧"), (10 ** 6, "🧗")]


def _effort_icon(minutes: int) -> str:
    for threshold, icon in EFFORT_LABELS:
        if minutes <= threshold:
            return icon
    return "🧗"


# ================================================================= tools ====
def _norm(s: str) -> str:
    """Normalizes a label for matching: lowercase, no accents, no punctuation.
    Never used for a verdict — only to find."""
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", " ", s)


_NOISE = {"facture", "fact", "fac", "avoir", "virement", "sepa", "carte", "cb",
          "paiement", "prelevement", "achat", "sarl", "sas", "eurl", "sa"}


def _token(label: str) -> str:
    """Approximate supplier key: first significant word of the label."""
    for word in _norm(label).split():
        if word not in _NOISE and len(word) > 2:
            return word
    return ""


def _supplier_word_match(tok: str, supplier: str) -> bool:
    """Match BY WHOLE WORD, never by substring. « darty » must NOT match
    « dartyimmo » (two different companies, same amount -> false deduction
    declared). Flaw C3 of the 2nd adversarial review."""
    if not tok or not supplier:
        return False
    words = set(_norm(supplier).split())
    return tok in words


def _date_iso(s: str | None) -> str | None:
    """Returns the date if it is a valid ISO one, else None. Prevents a
    `date="not-a-date"` from crashing qualify_ticket downstream."""
    if not s:
        return None
    try:
        dt.date.fromisoformat(s)
        return s
    except (ValueError, TypeError):
        return None


def _readable_supplier(label: str) -> str:
    """Display name. The bank label is noise ('CB DARTY 1234 CARTE 45XX'):
    we extract from it a name a human recognizes."""
    tok = _token(label)
    if not tok:
        return "Unknown supplier"
    known = {"totalenergies": "TotalEnergies", "leroy": "Leroy Merlin",
             "openai": "OpenAI", "aws": "AWS", "sfr": "SFR", "ldlc": "LDLC",
             "github": "GitHub", "linkedin": "LinkedIn"}
    return known.get(tok, tok.capitalize())


def _floor_euro(x: Decimal | float) -> int:
    """CONSERVATIVE rounding down. We under-promise, the invoice over-delivers."""
    return int(math.floor(float(x)))


def _ticket_id(*parts: Any) -> str:
    """STABLE identifier: two runs on the same data produce the same ids
    (replayability requirement of SKILL.md — without it, no diff possible)."""
    raw = "|".join(str(p) for p in parts)
    return "T-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]


def _days_until(deadline: str | None, today: dt.date) -> int | None:
    if not deadline:
        return None
    return (dt.date.fromisoformat(deadline) - today).days


def _positive_vat(x: Any) -> bool:
    """A usable VAT amount: a finite strictly positive number. Rejects 0,
    negatives, NaN, Inf, and bools (True equals 1.0 in Python). Flaw B2 of the
    adversarial review: NaN/Inf are floats and slipped past
    `isinstance(x, float) and x > 0`."""
    return (isinstance(x, (int, float)) and not isinstance(x, bool)
            and math.isfinite(x) and x > 0)


def _line21_deadline(payment_date: str | None, invoice_date: str | None) -> str | None:
    """31/12 of N+2, N = min(invoice year, payment year) — conservative rule
    (CE 31/12/2008 n° 305517; BOI-TVA-DED-40-20 §50). We take the OLDEST of the
    two years: never wrong, at worst conservative by a few weeks. A single known
    date -> we use it. None -> None (no invented deadline: without a date, we
    don't fabricate a favorable term)."""
    years = []
    for d in (payment_date, invoice_date):
        if d:
            try:
                years.append(dt.date.fromisoformat(d).year)
            except ValueError:
                pass
    if not years:
        return None
    return f"{min(years) + 2}-12-31"


# ================================================================= model ====
@dataclass
class Invoice:
    """Tuple extracted from an invoice BY VISION. The only legitimate source of
    a `vat_amount`. Self-checked: net + VAT = gross."""
    file: str
    supplier: str
    invoice_date: str | None = None
    number: str | None = None
    net_amount: float | None = None
    vat_amount: float | None = None
    gross_amount: float | None = None
    rate: float | None = None
    vat_country: str = "FR"
    client_name: str | None = None
    mentions: list[str] = field(default_factory=list)

    def consistent(self) -> bool:
        """net + VAT = gross to the cent. A tuple that fails -> we re-read the
        invoice, we NEVER force it (statement-reconciliation.md §1)."""
        if None in (self.net_amount, self.vat_amount, self.gross_amount):
            return False
        return abs((self.net_amount + self.vat_amount) - self.gross_amount) <= 0.02

    def french_vat(self) -> bool:
        """The VAT country is read on the INVOICE, never from the brand
        (Tesla France = FR VAT; Tesla Spain = IVA 21 %)."""
        return (self.vat_country or "").upper() in ("FR", "FRANCE")

    def plausible_rate(self) -> bool:
        """The actual rate (VAT/net) must land on an accepted French rate:
        20 %, 10 %, 5.5 %, 2.1 % (± rounding tolerance). A net=100/VAT=50
        « consistent » one (net+VAT=gross) but at a 50 % rate is an absurd
        invoice — vision that misread, or a dubious invoice. We refuse to
        declare it. (« absurd rate » flaw from the adversarial review.)"""
        if not self.net_amount or self.net_amount <= 0 or self.vat_amount is None:
            return False
        actual = self.vat_amount / self.net_amount
        return any(abs(actual - r) <= 0.01 for r in (0.20, 0.10, 0.055, 0.021))


@dataclass
class Ticket:
    id: str
    status: str
    zone: str
    supplier: str
    nature: str
    category: str | None
    date: str | None
    expense_amount: float

    # --- THE TWO FIELDS THAT NEVER MERGE ---
    vat_amount: float | None = None         # vision only. The only declarable one.
    estimated_potential: int | None = None  # inference. Never declarable.
    # ------------------------------------------------

    rate: float | None = None
    invoice: dict | None = None
    verdict: str | None = None
    legal_source: str | None = None
    deadline: str | None = None
    days_left: int | None = None            # None if no invoice: no hourglass
    action: str | None = None
    url: str | None = None          # deep-link to the supplier's customer account:
                                    # the product's central gesture (« Open LDLC and
                                    # retrieve the invoice »). Without it, the card
                                    # says where to go without taking you there.
    effort_minutes: int | None = None
    effort_icon: str | None = None
    effort_prerequisite: str | None = None
    pitfall: str | None = None
    hourly_rate: int | None = None
    group_count: int = 1
    group_lines: list[str] = field(default_factory=list)
    scratchable: bool = False
    amount_label: str = ""
    note: str | None = None


@dataclass
class Pot:
    """TWO SEGMENTS. No total. Deliberately: there exists no attribute and no
    method that adds the two. A single counter mixing confirmed and inferred is
    the trigger of a misleading commercial practice (art. L. 121-2 C. conso) —
    and the best way to disappoint."""
    confirmed: float = 0.0         # sum of vat_amount (read invoices)
    max_to_recover: int = 0        # sum of estimated_potential (upper bounds)
    confirmed_count: int = 0
    to_recover_count: int = 0
    dead_count: int = 0
    fix_count: int = 0             # foreign-VAT leaks to plug
    expiry: dict[str, float] = field(default_factory=dict)  # {"2026-12-31": 412.0}


# ========================================================= qualification ====
def _qualify_line(label: str, account: str, date: str | None, alert_level: str | None,
                  today: dt.date) -> tuple[str | None, dict]:
    """Category + legal verdict. SKILL.md hierarchy: accounting account >
    alert_level > label. As a last resort TO_REVIEW — never guess."""
    if alert_level == "exclusion":
        return "public_transport", {
            "verdict": "NON_DEDUCTIBLE",
            "reason": "Passenger transport — CGI ann. II, art. 206, IV-2-5°",
            "regime": "line21", "legal_deadline": None, "status_pre_invoice": "dead"}

    category, foreign = (route(label) if route else (None, False))
    if category is None:
        return None, {"verdict": "TO_REVIEW",
                      "reason": "Label not routable — the invoice or the accountant decides",
                      "regime": "line21", "legal_deadline": None,
                      "status_pre_invoice": "qualifiable"}
    if qualify is None:
        return category, {"verdict": "TO_REVIEW", "reason": "qualify_ticket unavailable",
                          "regime": "line21", "legal_deadline": None,
                          "status_pre_invoice": "qualifiable"}
    q = qualify(category, date or today.isoformat(), None, foreign, None, today.isoformat())
    return category, q


# VAT rate to extract from the gross by verdict. PARTIAL_80 is NOT a rate:
# it's « 80 % of the 20 % VAT », handled separately (flaw B1: 0.16 over-estimated
# by +3 %, exactly where doctrine says to under-promise).
RATE_BY_VERDICT = {
    "DEDUCTIBLE": Decimal("0.20"),
    "REVERSE_CHARGE": Decimal("0"),     # cash-neutral: nothing to « gain »
    "NON_DEDUCTIBLE": Decimal("0"),
    "DEAD": Decimal("0"),
    "EXEMPT": Decimal("0"),
    "FOREIGN_VAT": Decimal("0"),
    "NOTHING_TO_RECOVER": Decimal("0"),
    "TO_REVIEW": Decimal("0.20"),       # upper bound, to confirm on the invoice
}
PARTIAL_COEFF = {"PARTIAL_80": Decimal("0.80")}   # fraction of the deductible VAT


def _potential(expense_amount: float, verdict: str, account: str) -> int:
    """CATEGORICAL estimate, never a flat 20 % (SKILL.md §3 quater). VAT
    included in the expense. Rounded DOWN."""
    try:
        m = Decimal(str(expense_amount))
    except Exception:
        return 0
    if m <= 0:
        return 0
    rate = RATE_BY_VERDICT.get(verdict)
    if verdict in PARTIAL_COEFF:         # e.g. passenger-car fuel: 80 % of a 20 % VAT
        full_vat = m - m / Decimal("1.20")
        return _floor_euro(full_vat * PARTIAL_COEFF[verdict])
    if rate is None:
        rate = Decimal("0.20")
    if account.startswith("6257"):       # entertainment / dining
        rate = Decimal("0.10")
    if rate == 0:
        return 0
    return _floor_euro(m - m / (1 + rate))


# ================================================================ labels ====
def _amount_label(t: Ticket) -> str:
    """THE GRAMMAR. Generated by the code, never by the prompt.

    Forbidden (accountant's note, 13/07/2026):
      - the words « probable »/« likely » (indefensible statistical assertion)
      - a bare amount on a ticket without an invoice
      - a countdown on a potential (manufactured urgency)
    """
    if t.status == WON:
        return f"{t.vat_amount:.2f} €".replace(".", ",")
    if t.status in (TO_PLAY, TO_SECURE):
        if not t.estimated_potential:
            return "Amount unknown — the invoice is needed"
        return (f"Up to {t.estimated_potential} € — if your {t.supplier} invoice "
                f"carries French VAT. "
                f"You cannot declare anything until you have it.")
    if t.status == FIX:
        return ("Fix needed — you are paying foreign VAT you cannot recover on this "
                "expense. Enter your intra-EU VAT number with this supplier: they "
                "will invoice net (excl. VAT).")
    if t.status == DEAD:
        return f"0 € — {t.legal_source or 'not recoverable'}"
    if t.status == ALREADY_DEDUCTED:
        return "Already recovered"
    return "For your accountant to decide"


def _readable_nature(account_label: str, category: str | None) -> str:
    """Plain language. Zero jargon: the user is not an accountant."""
    human = {
        "restaurant": "Dining", "director_hotel": "Hotel night",
        "taxi": "Taxi/ride fare", "train": "Train ticket",
        "plane": "Plane ticket", "toll": "Toll", "parking": "Parking",
        "saas": "Online software", "french_software": "Software",
        "telecom": "Phone / internet", "professional_fees": "Professional fees",
        "supplies": "Equipment / supplies", "insurance": "Insurance",
        "passenger_car_fuel": "Fuel", "fine": "Fine",
        "leasing": "Leasing", "gift": "Client gift",
        "ev_charging": "EV charging",
        "franchise_subcontractor": "Subcontracting",
    }
    if category in human:
        return human[category]
    return (account_label or "Expense").capitalize()


# ============================================================== matching ====
def _match_invoice(line: dict, invoices: list[Invoice], consumed: set[int],
                   k_days: int = 45) -> Invoice | None:
    """Invoice <-> FEC line. Hierarchical keys (statement-reconciliation.md §2):
    exact gross amount + POSITIVE SUPPLIER MATCH + date window.

    Three guardrails learned from the adversarial review (13/07/2026):
    - UNIQUENESS (flaw C1): an invoice already consumed by another line cannot
      be reused. Without it, an invoice read once is deducted twice.
    - POSITIVE SUPPLIER MATCH REQUIRED (flaw C3): an amount that matches is NEVER
      enough. If the FEC label is noise (« VIREMENT SEPA ») or the invoice has no
      read supplier, we refuse — the amount alone glues the wrong invoice onto
      the wrong line.
    A doubt = no match: a false match produces a false `won`, the worst possible
    bug."""
    amount = float(line["expense_amount"])
    tok = _token(line.get("label", ""))
    date_l = line.get("date")
    if not tok:
        return None                       # C3: noisy label -> no match possible
    for i, p in enumerate(invoices):
        if i in consumed:                 # C1: invoice already used elsewhere
            continue
        if p.gross_amount is None:
            continue
        if abs(p.gross_amount - amount) > 0.02:
            continue
        if not _supplier_word_match(tok, p.supplier):
            continue                      # C3: supplier match BY WHOLE WORD
        if date_l and p.invoice_date:
            try:
                d1 = dt.date.fromisoformat(date_l)
                d2 = dt.date.fromisoformat(p.invoice_date)
                if abs((d1 - d2).days) > k_days:
                    continue
            except ValueError:
                pass
        consumed.add(i)
        return p
    return None


def _enrich_retrieval(t: Ticket, index: dict) -> None:
    """Where to retrieve the invoice, in how much time, and what it yields per
    hour. Without action or effort, a card is just an amount that dangles — the
    betrayal #1 identified in user testing."""
    tok = _token(t.supplier) or _token(t.nature)
    info = index.get(tok)
    if not info:
        t.action = (f"Retrieve the {t.supplier} invoice "
                    f"(customer account, confirmation e-mail, or ask for a duplicate)")
        t.effort_minutes = 10
        t.effort_icon = _effort_icon(10)
        t.note = "Retrieval path not verified for this supplier"
    else:
        t.action = info["where"]
        t.url = info.get("url")
        t.effort_minutes = int(info.get("minutes", 10))
        t.effort_icon = _effort_icon(t.effort_minutes)
        t.effort_prerequisite = info.get("prerequisite")
        t.pitfall = info.get("pitfall")
    if t.estimated_potential and t.effort_minutes:
        # The number that decides EVERYTHING for a director: they arbitrate their time.
        t.hourly_rate = int(round(t.estimated_potential * 60 / t.effort_minutes))


# =============================================================== factory ====
def build(fecs: list[dict], invoices_raw: list[dict],
          retrieval_index: dict | None = None,
          today: dt.date | None = None) -> dict:
    today = today or dt.date.today()
    index = retrieval_index if retrieval_index is not None else DEFAULT_RETRIEVAL_INDEX

    invoices: list[Invoice] = []
    inconsistent_invoices: list[dict] = []
    for p in invoices_raw:
        invoice = Invoice(**{k: v for k, v in p.items() if k in Invoice.__dataclass_fields__})
        if invoice.vat_amount is not None and not invoice.consistent():
            inconsistent_invoices.append({"file": invoice.file,
                                          "reason": "net + VAT ≠ gross — re-read the invoice"})
            continue                      # never force an inconsistent tuple
        invoices.append(invoice)

    consumed: set[int] = set()            # C1: an invoice serves only once, across all FECs
    tickets: list[Ticket] = []
    for fec in fecs:
        cand = fec.get("ticket_candidates", {})
        for line in cand.get("lines", []):
            tickets.append(_line_to_ticket(line, invoices, consumed, index, today))

        # Accounting orphans: payment with no booked invoice. These are the till
        # receipts from the shoebox — the most forgotten deposit.
        for o in fec.get("accounting_orphans", {}).get("lines", []):
            tickets.append(_orphan_to_ticket(o, index, today))

    tickets = _group(tickets)
    for t in tickets:
        t.amount_label = _amount_label(t)
        t.scratchable = t.status in SCRATCHABLE_STATUSES
    _assert_invariants(tickets)

    pot = _pot(tickets, today)
    # Final DETERMINISTIC sort: id last breaks ties, otherwise two runs on
    # reordered data produce a byte-for-byte different JSON.
    tickets.sort(key=lambda t: (-(t.vat_amount or 0), -(t.estimated_potential or 0), t.id))
    return {
        "generated_on": today.isoformat(),
        "pot": asdict(pot),
        "tickets": [asdict(t) for t in tickets],
        "inconsistent_invoices": inconsistent_invoices,
        "warning": (
            "vat_amount = read from the invoice, the only declarable amount. "
            "estimated_potential = inferred, NEVER declarable, floored to the euro. "
            "The two are never added together."),
    }


def _line_to_ticket(line: dict, invoices: list[Invoice], consumed: set[int],
                    index: dict, today: dt.date) -> Ticket:
    label = line.get("label", "")
    account = line.get("account", "")
    date = line.get("date")
    raw_amount = line.get("expense_amount")
    if raw_amount is None:                # B3: FEC line without amount -> not a ticket
        return Ticket(id=_ticket_id("bad", line.get("journal"), line.get("entry")),
                      status=TO_REVIEW, zone="undetermined",
                      supplier=_readable_supplier(label),
                      nature="Line without amount", category=None, date=date,
                      expense_amount=0.0, verdict="TO_REVIEW",
                      legal_source="Amount missing from the FEC — to check", action="—")
    amount = float(raw_amount)
    date = _date_iso(date)                 # non-ISO -> None (never a crash downstream)
    zone = line.get("zone", "undetermined")

    category, q = _qualify_line(label, account, date, line.get("alert_level"), today)
    verdict = q["verdict"]
    tid = _ticket_id("fec", line.get("journal"), line.get("entry"), account, date, amount)

    t = Ticket(
        id=tid, status=TO_PLAY, zone=zone,
        supplier=_readable_supplier(label),
        nature=_readable_nature(line.get("account_label", ""), category),
        category=category, date=date, expense_amount=amount,
        verdict=verdict, legal_source=q["reason"],
    )

    # 1. Excluded by law -> dead. We don't make anyone scratch a zero.
    if q["status_pre_invoice"] == "dead":
        t.status = DEAD
        t.estimated_potential = 0
        t.note = "Don't hunt for this invoice — you just saved yourself some time."
        return t

    # 2. Was an invoice READ for this line? It's the only path to a firm amount.
    #    No other. Not history, not the SIREN, not the legal status, not the
    #    supplier's habit.
    invoice = _match_invoice(line, invoices, consumed)
    if invoice is not None and invoice.vat_amount is not None:
        if not invoice.french_vat():
            t.status = DEAD
            t.estimated_potential = 0
            t.legal_source = (f"{invoice.vat_country} VAT on the invoice: never deductible "
                              f"on the French CA3 return (art. 271) — 2008/9 route, "
                              f"€400/quarter thresholds")
            return t
        if not _positive_vat(invoice.vat_amount):   # B2: rejects 0, NaN, Inf
            t.status = DEAD
            t.estimated_potential = 0
            t.legal_source = ("No usable VAT on the invoice (293 B small-business franchise, "
                              "exemption, reverse charge, or unreadable amount) — "
                              "nothing to recover")
            return t
        # Absurd rate (net+VAT=gross but VAT/net ∉ FR rates) -> vision misread,
        # or the invoice is dubious. We don't declare -> to review, not won.
        if invoice.net_amount and not invoice.plausible_rate():
            t.status = TO_REVIEW
            t.estimated_potential = None
            t.action = "Have this invoice checked by your accountant"
            t.legal_source = ("Inconsistent VAT rate on the invoice "
                              f"(VAT/net ≠ accepted French rate) — to review")
            return t
        # Invoice without a usable identifier: the factory must not produce a won
        # that the pack will refuse. Consistency factory <-> pack.
        invoice_id = invoice.file or invoice.number
        if not invoice_id:
            t.status = TO_REVIEW
            t.estimated_potential = None
            t.action = "Attach an identifiable invoice file to this line"
            t.legal_source = "Invoice read without a file name or number — not traceable"
            return t
        # C2: the deadline is computed on N = min(invoice year, payment year),
        # with the INVOICE date now known — not just the FEC date.
        # A 2023 invoice paid in 2024 has been time-barred since 31/12/2025.
        # Without a READABLE invoice date, we refuse the won: the date is a
        # mandatory mention (art. 242 nonies A ann. II) and the start point
        # of the deadline. A « favorable » deadline computed on the FEC date
        # alone would make a 2015 invoice look recoverable (residual C2 flaw).
        invoice_date = _date_iso(invoice.invoice_date)
        if not invoice_date:
            t.status = TO_REVIEW
            t.estimated_potential = None
            t.action = "Confirm the invoice date (it sets the legal deadline)"
            t.legal_source = ("Invoice date missing or unreadable — impossible "
                              "to check the time bar (CGI, ann. II, art. 208)")
            return t
        t.deadline = _line21_deadline(date, invoice_date)
        t.days_left = _days_until(t.deadline, today)
        if t.days_left is not None and t.days_left < 0:
            t.status = DEAD
            t.estimated_potential = 0
            t.invoice = {"file": invoice.file, "number": invoice.number,
                         "date": invoice.invoice_date, "client_name": invoice.client_name}
            t.vat_amount = None
            t.days_left = None                     # no hourglass on a dead one
            t.legal_source = (f"TIME-BARRED: deadline {t.deadline} passed "
                              f"(CGI, ann. II, art. 208, I) — deduction right lost")
            return t
        t.status = WON
        t.vat_amount = round(float(invoice.vat_amount), 2)
        t.rate = invoice.rate
        t.invoice = {"file": invoice.file, "number": invoice.number,
                     "date": invoice.invoice_date, "client_name": invoice.client_name}
        if invoice.client_name and "sarl" not in _norm(invoice.client_name) \
                and "sas" not in _norm(invoice.client_name):
            t.note = ("Check that the invoice is in the company's name: in the "
                      "director's name, a corrective invoice is mandatory (art. 271, "
                      "II-1-a) and it does NOT restart the deadline (CE 31/12/2008 n° 305517).")
        return t

    # 3. Foreign SaaS without an invoice: it's not a ticket to recover, it's a
    #    LEAK. Foreign VAT charged for lack of an intra-EU VAT number is neither
    #    deductible on the CA3 return (art. 271) nor refundable under 2008/9 when
    #    it was wrongly charged. The gain is elsewhere: with the supplier, and
    #    above all in the future. We don't drown it in the pile of invoices to retrieve.
    if verdict == "REVERSE_CHARGE" and category == "saas":
        t.status = FIX
        _enrich_retrieval(t, index)
        tok = _token(t.supplier)
        t.estimated_potential = None
        t.hourly_rate = None
        retro = RETROACTIVE_VAT_ID.get(tok)
        t.note = (f"Past recovery possible: {retro}" if retro
                  else "This supplier does not refund VAT already charged — "
                       "only the future is recoverable. Every month of waiting is lost.")
        return t

    # 4. No invoice -> potential + action + effort. Never a bare amount.
    t.status = TO_SECURE if zone == "to_secure" else TO_PLAY
    t.estimated_potential = _potential(amount, verdict, account)
    _enrich_retrieval(t, index)
    return t


def _orphan_to_ticket(o: dict, index: dict, today: dt.date) -> Ticket:
    """Payment with no booked invoice: the till receipt from the shoebox. We
    don't know the nature -> conservative potential, verdict at the invoice."""
    amount = float(o["amount"])
    date = o.get("date", "")
    date_iso = f"{date[:4]}-{date[4:6]}-{date[6:8]}" if len(date) == 8 else None
    label = o.get("label", "")
    t = Ticket(
        id=_ticket_id("orph", date, label, amount),
        status=TO_SECURE if o.get("zone") == "to_secure" else TO_PLAY,
        zone=o.get("zone", "undetermined"),
        supplier=_readable_supplier(label),
        nature="Payment with no invoice found",
        category=None, date=date_iso, expense_amount=amount,
        verdict="TO_REVIEW",
        legal_source="Nature of the expense unknown — the invoice will decide",
    )
    t.estimated_potential = _potential(amount, "TO_REVIEW", "")
    _enrich_retrieval(t, index)
    return t


def _group(tickets: list[Ticket]) -> list[Ticket]:
    """24 Orange invoices = ONE card, not 24. Otherwise the board drowns the user
    and the total promises more than they will recover (disappointment gradient).
    We group ONLY invoice-less tickets of the same supplier/category: a `won`
    stays one invoice, one invoice, one line of the pack."""
    groups: dict[tuple, list[Ticket]] = {}
    others: list[Ticket] = []
    for t in tickets:
        if t.status in (TO_PLAY, TO_SECURE) and t.category in ("telecom", "saas"):
            groups.setdefault((_token(t.supplier), t.category, t.status), []).append(t)
        else:
            others.append(t)
    for (tok, cat, status), lst in groups.items():
        if len(lst) == 1:
            others.append(lst[0])
            continue
        lst.sort(key=lambda t: t.id)     # B4: lead and group_lines independent
        lead = lst[0]                    #     of the arrival order of FEC lines
        lead.id = _ticket_id("grp", tok, cat, status, len(lst))
        lead.group_count = len(lst)
        lead.group_lines = [t.id for t in lst]
        lead.expense_amount = round(sum(t.expense_amount for t in lst), 2)
        lead.estimated_potential = sum(t.estimated_potential or 0 for t in lst)
        lead.nature = f"{lead.nature} — {len(lst)} invoices"
        if lead.effort_minutes and lead.estimated_potential:
            # Grouping divides the effort: a single pass on the customer account.
            lead.effort_minutes = min(lead.effort_minutes + len(lst), 20)
            lead.effort_icon = _effort_icon(lead.effort_minutes)
            lead.hourly_rate = int(round(lead.estimated_potential * 60 / lead.effort_minutes))
        others.append(lead)
    return others


def _pot(tickets: list[Ticket], today: dt.date) -> Pot:
    c = Pot()
    for t in tickets:
        if t.status == WON and t.vat_amount:
            c.confirmed = round(c.confirmed + t.vat_amount, 2)
            c.confirmed_count += 1
            if t.deadline:                       # expiry: read invoices ONLY
                c.expiry[t.deadline] = round(
                    c.expiry.get(t.deadline, 0.0) + t.vat_amount, 2)
        elif t.status in (TO_PLAY, TO_SECURE):
            c.max_to_recover += (t.estimated_potential or 0)
            c.to_recover_count += 1
        elif t.status == FIX:
            c.fix_count += 1          # never an amount: this is not part of the pot
        elif t.status == DEAD:
            c.dead_count += 1
    return c


# =============================================================== INVARIANTS =
def _assert_invariants(tickets: list[Ticket]) -> None:
    """The firewall. If a single one of these conditions breaks, the run stops.
    A false ticket is worth less than no ticket at all."""
    for t in tickets:
        if t.status == WON:
            if not t.invoice:
                raise TicketInvariantError(
                    f"[{t.id}] status 'won' WITHOUT a read invoice. Invariant 5 of SKILL.md: "
                    f"no firm amount can arise from an inference "
                    f"(history, SIREN, legal status, supplier habit). "
                    f"This is the « Émilie » bug. We stop.")
            if not t.vat_amount or t.vat_amount <= 0:
                raise TicketInvariantError(
                    f"[{t.id}] status 'won' without a positive vat_amount read from the invoice.")
            if t.estimated_potential:
                raise TicketInvariantError(
                    f"[{t.id}] a won ticket carries NO estimated potential: "
                    f"the two fields never coexist on the same card.")
        if t.status == FIX:
            if t.estimated_potential is not None or t.vat_amount is not None:
                raise TicketInvariantError(
                    f"[{t.id}] a 'fix' ticket carries NO amount: foreign VAT "
                    f"wrongly charged is neither deductible (art. 271, II-1-a) "
                    f"nor refundable under 2008/9. Showing a gain here would be a lie.")
            if not t.action:
                raise TicketInvariantError(f"[{t.id}] 'fix' ticket without an action.")
        if t.status in (TO_PLAY, TO_SECURE):
            if t.vat_amount is not None:
                raise TicketInvariantError(
                    f"[{t.id}] vat_amount set without a read invoice. "
                    f"vat_amount can ONLY come from vision.")
            if t.days_left is not None:
                raise TicketInvariantError(
                    f"[{t.id}] countdown on a potential: urgency manufactured on "
                    f"a right whose existence is unknown (art. L. 121-6 C. conso).")
            if not t.action:
                raise TicketInvariantError(
                    f"[{t.id}] card without an invoice WITHOUT a retrieval action. "
                    f"An amount that dangles without saying where to go get it is "
                    f"the product's betrayal #1.")
            if t.effort_minutes is None:
                raise TicketInvariantError(
                    f"[{t.id}] card without an invoice WITHOUT an estimated effort. A director "
                    f"arbitrates their time: without the duration, they cannot decide — and "
                    f"the interface would show « null min ».")
        label = (t.amount_label or "").lower()
        if "probable" in label or "likely" in label:
            raise TicketInvariantError(
                f"[{t.id}] the word « probable » is forbidden: indefensible statistical "
                f"assertion. Imposed grammar: « Up to X € — if… ».")


# =================================================================== tests ==
def _fixtures() -> None:
    today = dt.date(2026, 7, 13)
    fec = {"ticket_candidates": {"lines": [
        {"journal": "AC", "entry": "1", "date": "2024-03-12", "account": "6063",
         "account_label": "Fournitures", "label": "CB DARTY PARIS",
         "expense_amount": "154.80", "zone": "omission", "alert_level": None},
        {"journal": "AC", "entry": "2", "date": "2024-04-02", "account": "6251",
         "account_label": "Voyages", "label": "TAXI G7",
         "expense_amount": "42.00", "zone": "omission", "alert_level": "exclusion"},
        {"journal": "AC", "entry": "3", "date": "2025-05-02", "account": "6262",
         "account_label": "Telecom", "label": "ORANGE FACTURE",
         "expense_amount": "60.00", "zone": "omission", "alert_level": None},
        {"journal": "AC", "entry": "4", "date": "2025-06-02", "account": "6262",
         "account_label": "Telecom", "label": "ORANGE FACTURE",
         "expense_amount": "60.00", "zone": "omission", "alert_level": None},
    ]}, "accounting_orphans": {"lines": []}}

    # -- 1. Invoice read, French VAT -> WON, exact amount from the invoice
    invoices = [{"file": "darty.pdf", "supplier": "Darty", "invoice_date": "2024-03-12",
                 "net_amount": 129.0, "vat_amount": 25.80, "gross_amount": 154.80,
                 "rate": 20, "vat_country": "FR", "client_name": "ACME SARL"}]
    r = build([fec], invoices, today=today)
    tk = {t["id"]: t for t in r["tickets"]}
    darty = next(t for t in r["tickets"] if t["supplier"] == "Darty")
    assert darty["status"] == WON, darty
    assert darty["vat_amount"] == 25.80
    assert darty["estimated_potential"] is None
    assert darty["days_left"] is not None, "countdown expected on a read invoice"
    assert r["pot"]["confirmed"] == 25.80
    assert "total" not in r["pot"], "the pot must NOT expose a total"
    print("PASS  invoice read -> won, exact amount, countdown active")

    # -- 2. The taxi isn't scratched: excluded by law
    taxi = next(t for t in r["tickets"] if t["category"] == "public_transport")
    assert taxi["status"] == DEAD and taxi["estimated_potential"] == 0
    assert "206" in taxi["legal_source"], "the exclusion reason must cite the article"
    assert taxi["scratchable"] is False, "we don't make anyone scratch a zero"
    print("PASS  taxi -> dead, not scratchable, sourced reason")

    # -- 3. Orange x2 -> ONE grouped card, with action + effort + hourly rate
    orange = next(t for t in r["tickets"] if t["supplier"] == "Orange")
    assert orange["group_count"] == 2, orange
    assert orange["vat_amount"] is None
    assert orange["estimated_potential"] == 20   # floor(120 - 120/1.2) = 20
    assert orange["action"] and orange["effort_minutes"] and orange["hourly_rate"]
    assert orange["days_left"] is None, "no countdown without an invoice"
    assert "Up to" in orange["amount_label"]
    assert "probable" not in orange["amount_label"].lower()
    print(f"PASS  Orange grouped x2 -> {orange['amount_label'][:48]}… "
          f"({orange['effort_icon']} {orange['effort_minutes']} min, "
          f"{orange['hourly_rate']} €/h)")

    # -- 4. THE TEST THAT COUNTS: the « Émilie » bug can no longer happen.
    #    Invoice read carrying 0 € of VAT -> never won, whatever the supplier's
    #    history says.
    emilie = [{"file": "emilie.pdf", "supplier": "Darty", "invoice_date": "2024-03-12",
               "net_amount": 154.80, "vat_amount": 0.0, "gross_amount": 154.80,
               "rate": 0, "vat_country": "FR", "client_name": "ACME SARL"}]
    r2 = build([fec], emilie, today=today)
    d2 = next(t for t in r2["tickets"] if t["supplier"] == "Darty")
    assert d2["status"] == DEAD, d2
    assert r2["pot"]["confirmed"] == 0.0
    print("PASS  « Émilie » bug: invoice with 0 € VAT -> dead, secured pot at 0")

    # -- 5. Foreign VAT read on the invoice -> never line 21
    esp = [{"file": "es.pdf", "supplier": "Darty", "invoice_date": "2024-03-12",
            "net_amount": 129.0, "vat_amount": 25.80, "gross_amount": 154.80,
            "rate": 21, "vat_country": "ES", "client_name": "ACME SARL"}]
    r3 = build([fec], esp, today=today)
    d3 = next(t for t in r3["tickets"] if t["supplier"] == "Darty")
    assert d3["status"] == DEAD and r3["pot"]["confirmed"] == 0.0
    print("PASS  Spanish VAT on the invoice -> dead (never CA3 return), pot at 0")

    # -- 6. The invariant is a WALL: we try to force a won without an invoice.
    fake = Ticket(id="X", status=WON, zone="omission", supplier="Darty",
                  nature="Equipment", category="supplies", date="2024-03-12",
                  expense_amount=154.80, vat_amount=25.80)
    try:
        _assert_invariants([fake])
        raise SystemExit("FAIL: a won without an invoice slipped through. The lock is broken.")
    except TicketInvariantError as e:
        assert "Émilie" in str(e)
    print("PASS  invariant: impossible to force a 'won' without a read invoice")

    # -- 6 bis. Foreign SaaS -> FIX card, without any amount, with past recovery
    #    when the supplier allows it.
    fec_saas = {"ticket_candidates": {"lines": [
        {"journal": "AC", "entry": "9", "date": "2025-02-10", "account": "6226",
         "account_label": "Honoraires", "label": "ANTHROPIC CLAUDE SUB",
         "expense_amount": "240.00", "zone": "omission", "alert_level": None},
        {"journal": "AC", "entry": "10", "date": "2025-02-11", "account": "6226",
         "account_label": "Honoraires", "label": "GOOGLE WORKSPACE",
         "expense_amount": "180.00", "zone": "omission", "alert_level": None},
    ]}, "accounting_orphans": {"lines": []}}
    r4 = build([fec_saas], [], today=today)
    anth = next(t for t in r4["tickets"] if t["supplier"] == "Anthropic")
    goog = next(t for t in r4["tickets"] if t["supplier"] == "Google")
    assert anth["status"] == FIX and anth["estimated_potential"] is None
    assert "Up to" not in anth["amount_label"] and "0 €" not in anth["amount_label"]
    assert "does not refund" in anth["note"]
    assert "Get credit" in goog["note"], "Google refunds retroactively — it must be said"
    assert r4["pot"]["fix_count"] == 2
    assert r4["pot"]["max_to_recover"] == 0, "a fix is not part of the pot"
    print("PASS  foreign SaaS -> FIX card (no amount), Google recovery flagged")

    # -- C1. An invoice read ONCE cannot found TWO wons.
    fec_dbl = {"ticket_candidates": {"lines": [
        {"journal": "AC", "entry": "1", "date": "2024-03-12", "account": "6063",
         "account_label": "Fournitures", "label": "CB DARTY", "expense_amount": "154.80",
         "zone": "omission", "alert_level": None},
        {"journal": "AC", "entry": "2", "date": "2024-03-13", "account": "6063",
         "account_label": "Fournitures", "label": "CB DARTY", "expense_amount": "154.80",
         "zone": "omission", "alert_level": None}]},
        "accounting_orphans": {"lines": []}}
    rc1 = build([fec_dbl], invoices, today=today)  # a single Darty invoice
    wons = [t for t in rc1["tickets"] if t["status"] == WON]
    assert len(wons) == 1, f"double consumption: {len(wons)} won for 1 invoice"
    assert rc1["pot"]["confirmed"] == 25.80
    print("PASS  C1: one invoice = a single won (no double deduction)")

    # -- C2. 2023 invoice paid in 2024 -> time-barred 31/12/2025 -> never won.
    fec_old = {"ticket_candidates": {"lines": [
        {"journal": "AC", "entry": "1", "date": "2024-01-15", "account": "6063",
         "account_label": "Fournitures", "label": "CB DARTY", "expense_amount": "154.80",
         "zone": "omission", "alert_level": None}]},
        "accounting_orphans": {"lines": []}}
    p2023 = [dict(invoices[0], invoice_date="2023-12-20")]
    rc2 = build([fec_old], p2023, today=today)
    d = next(t for t in rc2["tickets"] if t["supplier"] == "Darty")
    assert d["status"] == DEAD and "TIME-BARRED" in d["legal_source"], d
    assert rc2["pot"]["confirmed"] == 0.0
    print("PASS  C2: 2023 invoice (min of the two dates) -> time-barred, never declared")

    # -- C3. Noisy label ('VIREMENT SEPA') does not glue an invoice by the amount.
    fec_noise = {"ticket_candidates": {"lines": [
        {"journal": "BQ", "entry": "1", "date": "2024-03-12", "account": "6063",
         "account_label": "Divers", "label": "VIREMENT SEPA", "expense_amount": "154.80",
         "zone": "omission", "alert_level": None}]},
        "accounting_orphans": {"lines": []}}
    rc3 = build([fec_noise], invoices, today=today)
    assert all(t["status"] != WON for t in rc3["tickets"]), "match on amount alone!"
    print("PASS  C3: amount alone is not enough — supplier match required")

    # -- B1. PARTIAL_80 (passenger-car fuel): 80 % of a 20 % VAT, not 16 % of the gross.
    assert _potential(1200.0, "PARTIAL_80", "6061") == 160, _potential(1200.0, "PARTIAL_80", "6061")
    # 1200 gross -> full VAT 200 -> 80 % = 160. (0.16*gross would have given 165.)
    print("PASS  B1: passenger-car fuel 80 % computed on the VAT, not on the gross")

    # -- C3bis. « DARTY » does NOT glue the invoice of « DartyImmo » (substring).
    fec_immo = {"ticket_candidates": {"lines": [
        {"journal": "AC", "entry": "1", "date": "2024-03-12", "account": "6063",
         "account_label": "F", "label": "CB DARTY", "expense_amount": "154.80",
         "zone": "omission", "alert_level": None}]}, "accounting_orphans": {"lines": []}}
    p_immo = [dict(invoices[0], supplier="DartyImmo Holding")]
    ri = build([fec_immo], p_immo, today=today)
    assert all(t["status"] != WON for t in ri["tickets"]), "substring: false won!"
    print("PASS  C3bis: « darty » does not match « dartyimmo » (whole word required)")

    # -- C2bis. Invoice WITHOUT an invoice date -> no won with a favorable deadline.
    p_nodate = [dict(invoices[0])]
    p_nodate[0]["invoice_date"] = None
    rn = build([fec_immo], p_nodate, today=today)  # same supplier Darty
    dn = next(t for t in rn["tickets"] if t["supplier"] == "Darty")
    assert dn["status"] == TO_REVIEW, dn
    print("PASS  C2bis: invoice without a readable date -> to review, never won")

    # -- Absurd rate: net+VAT=gross but VAT/net = 50 % -> to review, not won.
    p_abs = [{"file": "x.pdf", "supplier": "Darty", "invoice_date": "2024-03-12",
              "net_amount": 103.20, "vat_amount": 51.60, "gross_amount": 154.80,
              "rate": 50, "vat_country": "FR", "client_name": "ACME SARL"}]
    ra = build([fec_immo], p_abs, today=today)
    da = next(t for t in ra["tickets"] if t["supplier"] == "Darty")
    assert da["status"] == TO_REVIEW and "Inconsistent" in da["legal_source"]
    print("PASS  absurd rate (50 %) -> to review, never declared")

    # -- Non-ISO FEC date: does not crash the build.
    fec_bad = {"ticket_candidates": {"lines": [
        {"journal": "AC", "entry": "1", "date": "pas-une-date", "account": "6063",
         "account_label": "F", "label": "CB LDLC", "expense_amount": "50.00",
         "zone": "omission", "alert_level": None}]}, "accounting_orphans": {"lines": []}}
    build([fec_bad], [], today=today)  # must not raise
    print("PASS  non-ISO FEC date: robust build, no crash")

    # -- 7. Idempotence: same inputs -> same ids (replayability)
    assert [t["id"] for t in build([fec], invoices, today=today)["tickets"]] == \
           [t["id"] for t in r["tickets"]]
    print("PASS  idempotence: two runs -> identical ids (diff possible)")

    print("\n17/17 fixtures OK — the three locks hold.")


# ==================================================================== main ==
def main() -> None:
    ap = argparse.ArgumentParser(description="VAT ticket factory")
    ap.add_argument("--fec", action="append", default=[],
                    help="JSON produced by extract_fec.py --json (repeatable)")
    ap.add_argument("--invoices", help="JSON of invoices read by vision")
    ap.add_argument("--retrieval-index", help="Retrieval index JSON (default: built-in)")
    ap.add_argument("--out", default="tickets.json")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()

    if a.test:
        _fixtures()
        return
    if not a.fec:
        ap.error("--fec required (or --test)")

    fecs = [json.load(open(f, encoding="utf-8")) for f in a.fec]
    invoices = json.load(open(a.invoices, encoding="utf-8")) if a.invoices else []
    index = json.load(open(a.retrieval_index, encoding="utf-8")) if a.retrieval_index else None

    res = build(fecs, invoices, index)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)

    c = res["pot"]
    print(f"{len(res['tickets'])} tickets -> {a.out}")
    print(f"  ✅ SECURED (invoice in hand) : {c['confirmed']:.2f} € "
          f"on {c['confirmed_count']} tickets")
    print(f"  🔒 TO RECOVER (upper bound)  : up to {c['max_to_recover']} € "
          f"on {c['to_recover_count']} tickets")
    print(f"  ⚪ Excluded by law            : {c['dead_count']} "
          f"(checked for you — don't hunt for these invoices)")
    if c["expiry"]:
        for d, m in sorted(c["expiry"].items()):
            print(f"  ⏳ {m:.2f} € to declare before {d} (CGI, ann. II, art. 208)")
    print("  (the two counters are never added together — this is intentional)")


if __name__ == "__main__":
    main()
