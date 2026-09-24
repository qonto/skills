#!/usr/bin/env python3
"""
Tests du moteur engine.py — avec 'unittest' (livre d'origine avec Python).
Lancer :  python3 -m unittest discover -s tests

Regles verifiees :
  1. Detection d'abonnement recurrent (cadence mensuelle)
  2. Annualisation (mensuel x 12)
  3. One-off JAMAIS annualise
  4. Voyage / depense groupee sur quelques jours JAMAIS annualise (le vrai piege)
  5. Virement JAMAIS traite comme abonnement
  6. Doublon meme jour -> recuperation PONCTUELLE (pas x12)
  7. Deux abonnements paralleles -> consolidation
  8. Agregation des frais de change (FX)
  9. Classification PRO / PERSO / A-CLARIFIER
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine  # noqa: E402


def tx(name, amount, day, op="card", ref="", side="debit",
       attachment_required=None, attachment_ids=None):
    """Fausse transaction Qonto minimale. day = 'MM-JJ'. amount en euros.

    attachment_required / attachment_ids : optionnels (pour tester la TVA perdue).
    """
    t = {
        "clean_counterparty_name": name,
        "label": name,
        "amount": amount,
        "amount_cents": None,
        "emitted_at": "2026-{}T10:00:00.000Z".format(day),
        "operation_type": op,
        "reference": ref,
        "side": side,
    }
    if attachment_required is not None:
        t["attachment_required"] = attachment_required
    if attachment_ids is not None:
        t["attachment_ids"] = attachment_ids
    return t


def find(rows, marchand):
    for c in rows:
        if marchand.lower() in c["marchand"].lower():
            return c
    return None


class TestAbonnement(unittest.TestCase):
    def test_detecte_abonnement_mensuel(self):
        txs = [tx("HubSpot", 50, "04-05", op="direct_debit"),
               tx("HubSpot", 50, "05-05", op="direct_debit"),
               tx("HubSpot", 50, "06-05", op="direct_debit")]
        c = find(engine.analyze(txs)["abonnements"], "HubSpot")
        self.assertIsNotNone(c)
        self.assertEqual(c["cadence"], "mensuel")

    def test_annualisation_x12(self):
        txs = [tx("HubSpot", 50, "04-05", op="direct_debit"),
               tx("HubSpot", 50, "05-05", op="direct_debit"),
               tx("HubSpot", 50, "06-05", op="direct_debit")]
        c = find(engine.analyze(txs)["abonnements"], "HubSpot")
        self.assertEqual(c["montant_mensuel"], 50.0)
        self.assertEqual(c["montant_optimisable_eur"], 600.0)


class TestPasDAnnualisationAbusive(unittest.TestCase):
    def test_one_off_ignore(self):
        txs = [tx("Zara", 80, "05-10")]
        self.assertIsNone(find(engine.analyze(txs)["abonnements"], "Zara"))

    def test_voyage_jamais_annualise(self):
        # 3 debits carte sur 3 jours consecutifs = un seul sejour, pas un abonnement.
        txs = [tx("Sofitel", 332, "05-24"),
               tx("Sofitel", 377, "05-25"),
               tx("Sofitel", 40, "05-26")]
        res = engine.analyze(txs)
        self.assertIsNone(find(res["abonnements"], "Sofitel"),
                          "Un voyage ne doit JAMAIS etre annualise")

    def test_carte_deux_fois_pas_abonnement(self):
        # 2 paiements carte a ~1 mois d'ecart (ex: Western Union) : PAS un abonnement.
        txs = [tx("Western Union", 560, "05-03"),
               tx("Western Union", 631, "06-01")]
        self.assertIsNone(find(engine.analyze(txs)["abonnements"], "Western Union"))

    def test_virement_pas_abonnement(self):
        # Virements de facture (montants variables) : jamais un abonnement.
        txs = [tx("inkrea", 456, "04-06", op="transfer"),
               tx("inkrea", 912, "05-23", op="transfer"),
               tx("inkrea", 384, "06-23", op="transfer")]
        self.assertIsNone(find(engine.analyze(txs)["abonnements"], "inkrea"))


class TestDoublons(unittest.TestCase):
    def test_doublon_meme_jour_ponctuel(self):
        txs = [tx("Ringover", 39, "05-15"),
               tx("Ringover", 39, "05-15")]
        c = find(engine.analyze(txs)["doublons"], "Ringover")
        self.assertIsNotNone(c)
        self.assertEqual(c["nature"], "doublon")
        self.assertEqual(c["base"], "ponctuel — a verifier")
        # Recuperation = 1 fois le montant duplique, PAS x12.
        self.assertEqual(c["montant_optimisable_eur"], 39.0)

    def test_deux_abonnements_paralleles(self):
        txs = [tx("Google Workspace", 12, "04-03", op="direct_debit"),
               tx("Google Workspace", 12, "05-03", op="direct_debit"),
               tx("Google Workspace", 12, "06-03", op="direct_debit"),
               tx("Google Workspace", 6, "04-20", op="direct_debit"),
               tx("Google Workspace", 6, "05-20", op="direct_debit"),
               tx("Google Workspace", 6, "06-20", op="direct_debit")]
        goog = [c for c in engine.analyze(txs)["abonnements"]
                if "google" in c["marchand"].lower()]
        self.assertGreaterEqual(len(goog), 2)
        self.assertTrue(all(c["nature"] == "consolidation" for c in goog))


class TestFX(unittest.TestCase):
    def test_agregation_frais_change(self):
        txs = [tx("Frais", 5, "04-10", op="qonto_fee", ref="fx_card"),
               tx("Frais", 5, "05-10", op="qonto_fee", ref="fx_card")]
        c = engine.analyze(txs)["fx"][0]
        self.assertEqual(c["nature"], "fx")
        self.assertEqual(c["occurrences"], 2)
        self.assertAlmostEqual(c["montant_optimisable_eur"], 40.56, places=1)


class TestClassification(unittest.TestCase):
    def test_pro(self):
        self.assertEqual(engine.classify("hubspot"), "PRO")

    def test_perso(self):
        self.assertEqual(engine.classify("zara paris"), "PERSO")

    def test_a_clarifier(self):
        self.assertEqual(engine.classify("boucherie du coin"), "A-CLARIFIER")


class TestCredits(unittest.TestCase):
    def test_encaissements_ignores(self):
        txs = [tx("Client SAS", 1000, "05-01", op="income", side="credit"),
               tx("Client SAS", 1000, "06-01", op="income", side="credit")]
        res = engine.analyze(txs)
        self.assertIsNone(find(res["abonnements"], "Client SAS"))


class TestHausseSilencieuse(unittest.TestCase):
    def test_hausse_detectee(self):
        # SaaS mensuel passe de 40E a 45E => +12.5% (>= 5%) : hausse detectee.
        txs = [tx("Figma", 40, "04-08", op="direct_debit"),
               tx("Figma", 40, "05-08", op="direct_debit"),
               tx("Figma", 45, "06-08", op="direct_debit")]
        c = find(engine.analyze(txs)["abonnements"], "Figma")
        self.assertIsNotNone(c)
        h = c.get("hausse")
        self.assertIsNotNone(h, "La hausse silencieuse devrait etre detectee")
        self.assertEqual(h["pct"], 12.5)
        self.assertEqual(h["avant_eur"], 40.0)
        self.assertEqual(h["apres_eur"], 45.0)
        # Impact annualise = delta mensuel (45-40) x 12 = 60.
        self.assertEqual(h["impact_annuel_eur"], 60.0)

    def test_pas_de_hausse_si_moins_5pct(self):
        # 40 -> 41 = +2.5% (< 5%) : aucune hausse marquee.
        txs = [tx("Notion", 40, "04-10", op="direct_debit"),
               tx("Notion", 40, "05-10", op="direct_debit"),
               tx("Notion", 41, "06-10", op="direct_debit")]
        c = find(engine.analyze(txs)["abonnements"], "Notion")
        self.assertIsNotNone(c)
        self.assertIsNone(c.get("hausse"),
                          "Une hausse < 5% ne doit PAS etre marquee")

    def test_one_off_jamais_de_hausse(self):
        # 2 paiements carte a ~1 mois (pas un abonnement) avec un montant qui monte :
        # ce n'est PAS un recurrent -> jamais de hausse ni d'annualisation.
        txs = [tx("Western Union", 560, "05-03"),
               tx("Western Union", 720, "06-01")]
        res = engine.analyze(txs)
        self.assertIsNone(find(res["abonnements"], "Western Union"))
        hausses = [c for c in res["abonnements"] if c.get("hausse")]
        self.assertEqual(hausses, [], "Aucune hausse ne doit exister hors recurrent")

    def test_hausse_trimestrielle_impact_normalise(self):
        # BUG #2 : abo TRIMESTRIEL 120E -> 135E. Le delta (15E) est trimestriel ;
        # l'impact annuel doit etre normalise en mensuel : 15 * (1/3) * 12 = 60E/an.
        # (Le bug historique multipliait betement par 12 -> 180E/an, faux.)
        txs = [tx("Adobe", 120, "01-05", op="direct_debit"),
               tx("Adobe", 120, "04-05", op="direct_debit"),
               tx("Adobe", 135, "07-05", op="direct_debit")]
        c = find(engine.analyze(txs)["abonnements"], "Adobe")
        self.assertIsNotNone(c)
        self.assertEqual(c["cadence"], "trimestriel")
        h = c.get("hausse")
        self.assertIsNotNone(h, "La hausse trimestrielle devrait etre detectee")
        self.assertEqual(h["pct"], 12.5)
        self.assertEqual(h["avant_eur"], 120.0)
        self.assertEqual(h["apres_eur"], 135.0)
        # Impact NORMALISE mensuel : (135-120) * (1/3) * 12 = 60, PAS 180.
        self.assertEqual(h["impact_annuel_eur"], 60.0)

    def test_hausse_superieure_15pct_un_seul_abonnement(self):
        # BUG #5 : 40,40 puis 50,50 (mensuel) = MEME abo dont le prix a bondi de
        # +25% (> 15%). L'ancien moteur scindait en 2 clusters -> 2 faux
        # "consolidation" et ratait la hausse. Attendu : UN seul abonnement + hausse.
        txs = [tx("Webflow", 40, "04-05", op="direct_debit"),
               tx("Webflow", 40, "05-05", op="direct_debit"),
               tx("Webflow", 50, "06-05", op="direct_debit"),
               tx("Webflow", 50, "07-05", op="direct_debit")]
        subs = [c for c in engine.analyze(txs)["abonnements"]
                if "webflow" in c["marchand"].lower()]
        self.assertEqual(len(subs), 1, "Une hausse de prix ne doit PAS creer 2 abonnements")
        c = subs[0]
        self.assertEqual(c["nature"], "abonnement")
        self.assertEqual(c["occurrences"], 4)
        h = c.get("hausse")
        self.assertIsNotNone(h, "La hausse > 15% doit etre detectee au niveau du marchand")
        self.assertEqual(h["pct"], 25.0)
        self.assertEqual(h["avant_eur"], 40.0)
        self.assertEqual(h["apres_eur"], 50.0)
        self.assertEqual(h["impact_annuel_eur"], 120.0)


class TestTvaPerdue(unittest.TestCase):
    def test_tva_perdue_agregee(self):
        # 3 depenses PRO, justificatif requis mais absent -> TVA recuperable.
        txs = [tx("AWS", 120, "06-15", attachment_required=True),
               tx("OVH", 60, "06-18", attachment_required=True),
               tx("Notion", 60, "06-20", attachment_required=True)]
        tva = engine.analyze(txs).get("tva_perdue")
        self.assertIsNotNone(tva)
        self.assertEqual(tva["transactions"], 3)
        self.assertEqual(tva["base_ttc_eur"], 240.0)
        # 240 * 20/120 = 40.
        self.assertEqual(tva["tva_recuperable_eur"], 40.0)

    def test_pas_de_tva_si_justificatifs_presents(self):
        # Memes depenses mais avec pieces jointes : aucune TVA perdue.
        txs = [tx("AWS", 120, "06-15", attachment_required=True,
                  attachment_ids=["att_1"]),
               tx("OVH", 60, "06-18", attachment_required=True,
                  attachment_ids=["att_2"])]
        self.assertIsNone(engine.analyze(txs).get("tva_perdue"))

    def test_pas_de_tva_si_attachment_non_requis(self):
        # Justificatif non requis -> hors perimetre TVA perdue.
        txs = [tx("AWS", 120, "06-15", attachment_required=False),
               tx("OVH", 60, "06-18")]
        self.assertIsNone(engine.analyze(txs).get("tva_perdue"))

    def test_tva_ignore_les_depenses_perso(self):
        # Depense PERSO sans justificatif : pas de TVA deductible pro.
        txs = [tx("Zara", 120, "06-15", attachment_required=True)]
        self.assertIsNone(engine.analyze(txs).get("tva_perdue"))

    def test_tva_ignore_les_depenses_a_clarifier(self):
        # BUG #4 : fournisseur A-CLARIFIER (ni PRO ni PERSO) sans justificatif.
        # engine.py ne compte QUE le PRO (whitelist) -> aucune TVA perdue.
        txs = [tx("Boucherie du coin", 120, "06-15", attachment_required=True)]
        self.assertEqual(engine.classify("boucherie du coin"), "A-CLARIFIER")
        self.assertIsNone(engine.analyze(txs).get("tva_perdue"))

    def test_tva_ne_compte_que_le_pro(self):
        # BUG #4 : AWS (PRO) + Boucherie (A-CLARIFIER), tous deux sans justificatif.
        # Seule la depense PRO entre dans la TVA perdue (perimetre = engine.py).
        txs = [tx("AWS", 120, "06-15", attachment_required=True),
               tx("Boucherie du coin", 300, "06-16", attachment_required=True)]
        tva = engine.analyze(txs).get("tva_perdue")
        self.assertIsNotNone(tva)
        self.assertEqual(tva["transactions"], 1)
        self.assertEqual(tva["base_ttc_eur"], 120.0)
        self.assertEqual(tva["tva_recuperable_eur"], 20.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
