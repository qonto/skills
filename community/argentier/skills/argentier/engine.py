#!/usr/bin/env python3
"""
engine.py — le moteur de calcul DETERMINISTE d'Argentier.

REGLE D'OR : tout calcul en euros est fait ICI, par du code Python.
Le LLM (Claude) ne calcule JAMAIS un montant lui-meme.

Ce moteur distingue 4 natures de depenses, pour ne PAS gonfler les chiffres :
  1. ABONNEMENT       : prelevement SEPA, OU carte a cadence reguliere (~mensuel /
                        trimestriel). Seuls ceux-la sont ANNUALISES (x12).
  2. DOUBLON          : 2 prelevements le meme jour chez le meme marchand.
                        -> recuperation PONCTUELLE (jamais x12), a verifier.
  3. FX               : frais de change Qonto (qonto_fee + fx_card) agreges.
  4. DEPENSE VARIABLE : voyages, cash, restaurants, virements... qui se repetent
                        mais NE sont PAS des abonnements. Montre le total observe
                        sur 90 j, JAMAIS annualise.

Usage :
    python3 engine.py data/flows-2026-07-05.json          # tableau lisible
    python3 engine.py data/flows-2026-07-05.json --json    # sortie JSON (machine)
"""

import json
import sys
import statistics
from collections import defaultdict, Counter
from datetime import date

WINDOW_DAYS = 90
# Une depense variable n'est affichee que si elle depasse ce total sur 90 j
# (sinon trop de bruit). Purement informatif.
VARIABLE_MIN_EUR = 100.0
# Retraits cash / especes : hors perimetre d'optimisation.
CASH_KEYS = {"atm", "retrait", "distributeur"}

# --- Classification EI : pro vs perso -------------------------------------
PRO_KEYWORDS = [
    "hubspot", "apollo", "ringover", "google workspace", "google gsuite",
    "notion", "slack", "aws", "amazon web services", "github", "gitlab",
    "linkedin", "stripe", "ovh", "scaleway", "figma", "zoom", "microsoft",
    "adobe", "openai", "anthropic", "vercel", "cloudflare", "sentry",
    "calendly", "typeform", "mailchimp", "mailjet", "sendgrid", "twilio",
    "make", "make.com", "zapier", "airtable", "pipedrive", "salesforce",
    "intercom", "canva", "webflow", "instantly", "waalaxy", "loom", "replit",
    "skool", "hiscox",
]
PERSO_KEYWORDS = [
    "zara", "h&m", "uniqlo", "restaurant", "uber eats", "deliveroo",
    "just eat", "carrefour", "monoprix", "leclerc", "franprix", "auchan",
    "lidl", "intermarche", "boulangerie", "mcdonald", "starbucks", "fnac",
    "decathlon", "sephora", "ikea", "netflix", "spotify", "disney+",
    "pharmacie", "nespresso", "barber", "action",
]


def classify(name):
    """Renvoie 'PRO', 'PERSO' ou 'A-CLARIFIER' pour un nom de marchand."""
    n = name.lower()
    if any(k in n for k in PRO_KEYWORDS):
        return "PRO"
    if any(k in n for k in PERSO_KEYWORDS):
        return "PERSO"
    return "A-CLARIFIER"


# --- Utilitaires -----------------------------------------------------------
def get_amount(tx):
    """Montant en euros, positif. amount_cents si present, sinon amount."""
    if tx.get("amount_cents") is not None:
        return abs(int(tx["amount_cents"])) / 100.0
    return abs(float(tx.get("amount", 0) or 0))


def get_date(tx):
    raw = tx.get("emitted_at") or tx.get("settled_at") or ""
    return raw[:10]


def to_ordinal(d):
    y, m, day = d.split("-")
    return date(int(y), int(m), int(day)).toordinal()


def merchant_key(tx):
    name = tx.get("clean_counterparty_name") or tx.get("label") or "inconnu"
    return " ".join(name.split()).strip().lower()


def merchant_display(txs):
    names = [
        (tx.get("clean_counterparty_name") or tx.get("label") or "inconnu").strip()
        for tx in txs
    ]
    return Counter(names).most_common(1)[0][0]


def dominant_op(txs):
    return Counter(t.get("operation_type") for t in txs).most_common(1)[0][0]


def is_fx_fee(tx):
    return (tx.get("operation_type") == "qonto_fee"
            and "fx_card" in str(tx.get("reference", "")).lower())


def similar(amount, reference):
    return abs(amount - reference) <= max(1.0, 0.15 * reference)


def cluster_amounts(txs):
    """Regroupe les transactions par montant similaire (tolerance 15%)."""
    clusters = []
    for tx in sorted(txs, key=get_amount):
        amt = get_amount(tx)
        for c in clusters:
            if similar(amt, statistics.median([get_amount(t) for t in c])):
                c.append(tx)
                break
        else:
            clusters.append([tx])
    return clusters


def _cluster_span(cluster):
    """(debut, fin) en jours ordinaux couvertes par les dates d'un cluster."""
    ords = [to_ordinal(get_date(t)) for t in cluster]
    return min(ords), max(ords)


def clusters_overlap_in_time(clusters):
    """
    True si au moins deux clusters de montants se CHEVAUCHENT dans le temps.
    Chevauchement = abonnements reellement PARALLELES (consolidation).
    Clusters SEQUENTIELS (l'un s'arrete quand l'autre commence) = le MEME
    abonnement dont le prix a change (hausse) -> a NE PAS compter comme deux.
    """
    spans = [_cluster_span(c) for c in clusters]
    for i in range(len(spans)):
        for j in range(i + 1, len(spans)):
            (a0, a1), (b0, b1) = spans[i], spans[j]
            if a0 <= b1 and b0 <= a1:
                return True
    return False


def cadence_of(median_interval):
    """
    A partir de l'ecart median (en jours) entre 2 prelevements, dit s'il s'agit
    d'une cadence d'ABONNEMENT. Renvoie (facteur_mensuel, libelle) ou (None, None).
    Volontairement STRICT : des depenses groupees sur quelques jours (un voyage)
    ne sont PAS une cadence -> elles ne seront jamais annualisees.
    """
    if 20 <= median_interval <= 45:
        return 1.0, "mensuel"
    if 45 < median_interval <= 110:
        return 1 / 3, "trimestriel"
    return None, None


def confidence(n_occ, amounts):
    med = statistics.median(amounts) if amounts else 0
    spread = (max(amounts) - min(amounts)) / med if med else 1.0
    if n_occ >= 3 and spread <= 0.10:
        return "eleve"
    if n_occ >= 2 and spread <= 0.25:
        return "moyen"
    return "faible"


def subscription_cadence(cluster, op_dominant):
    """
    Dit si un groupe de prelevements est un ABONNEMENT annualisable.
    - prelevement SEPA (direct_debit) -> oui (cadence mensuelle par defaut).
    - carte -> oui SEULEMENT si cadence reguliere mensuelle/trimestrielle.
    Renvoie (facteur_mensuel, libelle) ou None.
    """
    dates = [get_date(t) for t in cluster]
    if len(set(dates)) < 2:
        return None  # tout le meme jour = doublon, pas une cadence
    ords = sorted(to_ordinal(d) for d in dates)
    intervals = [b - a for a, b in zip(ords, ords[1:])]
    med_int = statistics.median(intervals) if intervals else 0

    if op_dominant == "direct_debit":
        factor, cad = cadence_of(med_int)
        return (factor, cad) if factor else (1.0, "mensuel")
    if op_dominant == "card":
        factor, cad = cadence_of(med_int)
        return (factor, cad) if factor else None
    return None


# --- Detection hausse silencieuse -----------------------------------------
def detect_hausse(txs, factor=1.0):
    """
    Hausse silencieuse : sur un RECURRENT (marchand deja reconnu comme
    abonnement), compare le montant de la 1re et de la derniere occurrence
    (triees par date), TOUTES occurrences confondues -- jamais par cluster de
    montant : une hausse > 15 % serait sinon scindee en deux clusters et ratee.
    Seuil de declenchement : +5 %. Renvoie un dict ou None.

    `factor` = facteur de cadence (1.0 mensuel, 1/3 trimestriel...). Le moteur
    normalise tout en mensuel ; l'impact annuel du delta est donc lui aussi
    normalise en mensuel AVANT l'annualisation x12.

    Ne JAMAIS appeler sur un one-off : ce helper n'est invoque que pour des
    marchands deja reconnus comme abonnements (>= 2 occ a cadence reguliere).
    """
    ordered = sorted(txs, key=get_date)
    avant = get_amount(ordered[0])
    apres = get_amount(ordered[-1])
    if avant <= 0 or apres < avant * 1.05:
        return None
    return {
        "pct": round((apres / avant - 1) * 100, 1),
        "avant_eur": round(avant, 2),
        "apres_eur": round(apres, 2),
        # Impact annuel = delta normalise en mensuel (delta brut x facteur de
        # cadence) x 12. Un abo trimestriel n'est donc pas sur-annualise.
        "impact_annuel_eur": round((apres - avant) * factor * 12, 2),
    }


# --- Detection TVA deductible perdue (justificatifs manquants) --------------
def tva_perdue_candidate(debits):
    """
    TVA deductible perdue : depenses PRO ou un justificatif etait requis
    (attachment_required == True) mais absent (attachment_ids vide/absent).
    Agrege : nombre de transactions, base TTC, TVA recuperable = base * 20/120.
    Levier fiscal indicatif -> a confirmer avec un comptable. None si rien.
    """
    concerned = [
        tx for tx in debits
        if tx.get("attachment_required") is True
        and not (tx.get("attachment_ids") or [])
        and classify(merchant_key(tx)) == "PRO"
    ]
    if not concerned:
        return None
    base_ttc = sum(get_amount(t) for t in concerned)
    tva = base_ttc * 20.0 / 120.0
    if tva <= 0:
        return None
    return {
        "transactions": len(concerned),
        "base_ttc_eur": round(base_ttc, 2),
        "tva_recuperable_eur": round(tva, 2),
        "note": "TVA recuperable estimee (20%) sur depenses PRO sans justificatif "
                "— a confirmer avec un comptable.",
    }


# --- Detection FX ----------------------------------------------------------
def fx_candidate(transactions, window_days):
    fx = [tx for tx in transactions if is_fx_fee(tx)]
    if not fx:
        return None
    total = sum(get_amount(t) for t in fx)
    annual = total * (365.0 / window_days)
    return {
        "marchand": "Frais de change Qonto (fx_card)",
        "categorie_ei": "PRO",
        "operation_type": "qonto_fee",
        "nature": "fx",
        "occurrences": len(fx),
        "cadence": "{} frais / {} j".format(len(fx), window_days),
        "montant_mensuel": round(total / (window_days / 30.0), 2),
        "montant_optimisable_eur": round(annual, 2),
        "base": "annuel (frais 90 j extrapoles)",
        "niveau_confiance": "eleve" if len(fx) >= 3 else "moyen",
    }


# --- Coeur : construction des candidats ------------------------------------
def analyze(transactions, window_days=WINDOW_DAYS):
    """
    Renvoie un dict a 4 listes :
      abonnements, doublons, variables, fx  (fx = liste de 0 ou 1 element).
    """
    debits = [tx for tx in transactions
              if tx.get("side") == "debit" and not is_fx_fee(tx)]

    groups = defaultdict(list)
    for tx in debits:
        groups[merchant_key(tx)].append(tx)

    abonnements, doublons, variables = [], [], []

    for key, txs in groups.items():
        if key in CASH_KEYS:
            continue  # retraits especes : hors perimetre
        display = merchant_display(txs)
        cat = classify(key)
        op_dom = dominant_op(txs)
        clusters = cluster_amounts(txs)

        # 1) doublons "meme jour" (toutes natures confondues)
        had_doublon = False
        for c in clusters:
            by_day = Counter(get_date(t) for t in c)
            for day, cnt in by_day.items():
                if cnt >= 2:
                    unit = statistics.median([get_amount(t) for t in c])
                    had_doublon = True
                    doublons.append({
                        "marchand": display,
                        "categorie_ei": cat,
                        "operation_type": op_dom,
                        "nature": "doublon",
                        "occurrences": cnt,
                        "cadence": "meme jour ({})".format(day),
                        "montant_mensuel": None,
                        "montant_optimisable_eur": round(unit * (cnt - 1), 2),
                        "base": "ponctuel — a verifier",
                        "niveau_confiance": confidence(cnt, [get_amount(t) for t in c]),
                    })

        # 2) abonnements reels (annualises)
        # Carte = ABONNEMENT seulement si vu >= 3 fois sur 90 j (un vrai
        # abonnement mensuel apparait ~3x). Prelevement SEPA : >= 2 suffit
        # (c'est presque toujours un contrat).
        min_occ = 2 if op_dom == "direct_debit" else 3
        sub_clusters = []
        for c in clusters:
            if len(c) < min_occ:
                continue
            cad = subscription_cadence(c, op_dom)
            if cad:
                sub_clusters.append((c, cad))

        # Les virements ne sont pas des abonnements : on ne garde que le doublon.
        if op_dom == "transfer":
            continue

        if sub_clusters:
            # Vrais abonnements PARALLELES seulement si les clusters de montants
            # se chevauchent dans le temps. Sinon (clusters sequentiels), c'est le
            # MEME abonnement dont le prix a change -> un seul abo + hausse, pas
            # deux "consolidation" fantomes qui gonfleraient l'economie.
            sub_only = [c for c, _ in sub_clusters]
            parallel = len(sub_clusters) >= 2 and clusters_overlap_in_time(sub_only)

            if parallel:
                for c, (factor, cadence) in sub_clusters:
                    amounts = [get_amount(t) for t in c]
                    monthly = statistics.median(amounts) * factor
                    cand = {
                        "marchand": display,
                        "categorie_ei": cat,
                        "operation_type": op_dom,
                        "nature": "consolidation",
                        "occurrences": len(c),
                        "cadence": cadence,
                        "montant_mensuel": round(monthly, 2),
                        "montant_optimisable_eur": round(monthly * 12, 2),
                        "base": "mensuel x12 (annuel)",
                        "niveau_confiance": confidence(len(c), amounts),
                    }
                    hausse = detect_hausse(c, factor)
                    if hausse:
                        cand["hausse"] = hausse
                    abonnements.append(cand)
            else:
                # Un seul abonnement : mono-cluster, OU clusters sequentiels (meme
                # abo dont le prix a change). La hausse est detectee au NIVEAU DU
                # MARCHAND (toutes les occurrences recurrentes), avant le clustering
                # par montant, pour ne pas rater une hausse > 15 %.
                recurring_txs = [t for c, _ in sub_clusters for t in c]
                factor, cadence = (subscription_cadence(recurring_txs, op_dom)
                                   or sub_clusters[0][1])
                amounts = [get_amount(t) for t in recurring_txs]
                monthly = statistics.median(amounts) * factor
                cand = {
                    "marchand": display,
                    "categorie_ei": cat,
                    "operation_type": op_dom,
                    "nature": "abonnement",
                    "occurrences": len(recurring_txs),
                    "cadence": cadence,
                    "montant_mensuel": round(monthly, 2),
                    "montant_optimisable_eur": round(monthly * 12, 2),
                    "base": "mensuel x12 (annuel)",
                    "niveau_confiance": confidence(len(recurring_txs), amounts),
                }
                # Hausse silencieuse : uniquement sur ce recurrent (jamais un one-off).
                hausse = detect_hausse(recurring_txs, factor)
                if hausse:
                    cand["hausse"] = hausse
                abonnements.append(cand)
        elif not had_doublon and len(txs) >= 2:
            # 3) depense variable repetee (voyage, resto, cash card...) : NON annualisee
            total = sum(get_amount(t) for t in txs)
            if total >= VARIABLE_MIN_EUR:
                variables.append({
                    "marchand": display,
                    "categorie_ei": cat,
                    "operation_type": op_dom,
                    "nature": "depense_variable",
                    "occurrences": len(txs),
                    "cadence": "variable",
                    "montant_mensuel": None,
                    "montant_optimisable_eur": 0.0,
                    "montant_observe_90j": round(total, 2),
                    "base": "observe 90 j (NON annualise)",
                    "niveau_confiance": "-",
                })

    fx = fx_candidate(transactions, window_days)
    fx_list = [fx] if fx else []

    abonnements.sort(key=lambda c: c["montant_optimisable_eur"], reverse=True)
    doublons.sort(key=lambda c: c["montant_optimisable_eur"], reverse=True)
    variables.sort(key=lambda c: c.get("montant_observe_90j", 0), reverse=True)

    result = {
        "abonnements": abonnements,
        "doublons": doublons,
        "fx": fx_list,
        "variables": variables,
    }
    # TVA deductible perdue (justificatifs manquants) : present seulement si > 0.
    tva = tva_perdue_candidate(debits)
    if tva:
        result["tva_perdue"] = tva
    return result


# --- Entree / sortie -------------------------------------------------------
def load_transactions(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("transactions") or data.get("data") or []
    return data


def _row(c):
    m = "{:.2f}E".format(c["montant_mensuel"]) if c["montant_mensuel"] is not None else "  -"
    return "{:<30} {:<12} {:>10} {:>11.2f}E  {:<13} {}".format(
        c["marchand"][:30], c["categorie_ei"], m,
        c["montant_optimisable_eur"], c["nature"], c["niveau_confiance"])


def print_report(res):
    ab, db, fx, var = res["abonnements"], res["doublons"], res["fx"], res["variables"]
    tva = res.get("tva_perdue")

    print("\n=== ABONNEMENTS RECURRENTS (annualises x12) ===")
    print("{:<30} {:<12} {:>10} {:>12}  {:<13} {}".format(
        "MARCHAND", "CATEGORIE", "MENSUEL", "ANNUEL", "NATURE", "CONF."))
    print("-" * 92)
    total_ab = 0
    for c in ab + fx:
        total_ab += c["montant_optimisable_eur"]
        print(_row(c))
        h = c.get("hausse")
        if h:
            print("   ^ HAUSSE SILENCIEUSE +{}% : {:.2f}E -> {:.2f}E "
                  "(impact {:.2f}E/an)".format(
                      h["pct"], h["avant_eur"], h["apres_eur"],
                      h["impact_annuel_eur"]))
    print("-" * 92)
    print("Base annuelle optimisable (abonnements + FX) : {:.2f} EUR / an".format(total_ab))

    if db:
        print("\n=== DOUBLONS MEME JOUR (recuperation PONCTUELLE, a verifier) ===")
        total_db = 0
        for c in db:
            total_db += c["montant_optimisable_eur"]
            print("{:<30} {:<12} {:>10.2f}E  {}".format(
                c["marchand"][:30], c["categorie_ei"],
                c["montant_optimisable_eur"], c["cadence"]))
        print("Recuperation ponctuelle potentielle : {:.2f} EUR (one-shot)".format(total_db))

    if var:
        print("\n=== DEPENSES VARIABLES REPETEES (info — NON annualisees) ===")
        print("{:<30} {:<12} {:>14}  occ".format("MARCHAND", "CATEGORIE", "TOTAL 90 j"))
        for c in var:
            print("{:<30} {:<12} {:>13.2f}E  {}".format(
                c["marchand"][:30], c["categorie_ei"],
                c["montant_observe_90j"], c["occurrences"]))
        print("(Ces montants ne sont PAS des economies : ce sont des depenses observees.)")

    if tva:
        print("\n=== TVA DEDUCTIBLE PERDUE (justificatifs PRO manquants) ===")
        print("Transactions concernees : {}".format(tva["transactions"]))
        print("Base TTC totale          : {:.2f} EUR".format(tva["base_ttc_eur"]))
        print("TVA recuperable estimee  : {:.2f} EUR (20/120)".format(
            tva["tva_recuperable_eur"]))
        print("({})".format(tva["note"]))


def main(argv):
    if len(argv) < 2:
        print("Usage : python3 engine.py <fichier_flux.json> [--json]")
        return 1
    txs = load_transactions(argv[1])
    res = analyze(txs)
    if "--json" in argv:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("Transactions lues : {}".format(len(txs)))
        print_report(res)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
