# 🛡 qonto-chargeback-defender — Les litiges de paiement, de la détection au dossier de défense

> Hackathon Qonto × Anthropic MCP (10-13/07/2026) · Agent Skill pour le MCP Qonto
> Le skill prépare tout — détection, chronologie, dossier sourcé, deadline — et **toi seul soumets** la réponse sur le portail Stripe/PayPal.

---

## 🎯 Le pitch

Un chargeback, c'est triple peine : l'argent **repris** sur le compte, des **frais** en plus (souvent 15-20 €, indicatif), et un **délai de réponse court** (7-21 jours) — et la plupart des marchands ne répondent jamais. `qonto-chargeback-defender` transforme le compte Qonto en poste de défense :

1. **Détection des litiges ouverts** — via le MCP Stripe/PayPal s'il est connecté (motifs, montants, deadlines réelles) ; sinon repérage dans Qonto des débits de reprise (libellés dispute / chargeback / reversal + frais associés)
2. **Le débit retrouvé** — la reprise est rapprochée de l'encaissement d'origine : chronologie complète paiement → payout → reprise → frais
3. **Dossier de défense assemblé et sourcé** — commande Shopify, preuve de livraison si disponible, échanges client Gmail : chaque pièce listée avec sa source ; les pièces manquantes listées avec où les trouver
4. **Traçabilité comptable** — avec ton accord explicite, un mémo de synthèse daté est attaché au débit de reprise dans Qonto (upload confirmé) ; la transaction contestée porte toute son histoire

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Universel** : les chargebacks suivent les règles des réseaux carte et des PSP, pas le droit fiscal national — même comportement pour tous les pays Qonto (FR, DE, ES, IT, AT, NL, BE, PT) | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| MCP Stripe / PayPal | Source autoritaire des litiges et **des deadlines**. Sans lui : mode dégradé Qonto pur (détection des reprises + chronologie + checklist), déjà utile | ⭕ recommandé |
| MCP Shopify · Gmail | Enrichissements du dossier (commande, tracking, échanges client) — détectés dynamiquement, annoncés s'ils manquent | ⭕ |
| Encaissements via un PSP | Stripe, PayPal, Adyen, Mollie… c'est là que naissent les chargebacks | ✅ de fait |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Détection des litiges** : MCP Stripe/PayPal si présent (litiges ouverts, motifs, deadlines réelles) ; sinon scan des transactions Qonto — débits de reprise `dispute` / `chargeback` / `reversal` (+ variantes FR), souvent doublés d'un débit de frais du même PSP le même jour. Le mode actif est annoncé clairement
2. **Débit retrouvé** : encaissement d'origine rapproché (montant ± frais, fenêtre de dates, tiers via `get_transaction`), chronologie complète reconstituée. Rapprochement carte sur `emitted_at`, pas `settled_at`
3. **Deadline de réponse** : celle du litige lui-même, jamais estimée à la légère ; en mode Qonto pur, fenêtres types annoncées comme **indicatives** avec consigne de vérifier sur le portail. Litiges triés par urgence
4. **Dossier de défense** : pièces adaptées au motif (commande Shopify, tracking livré, échanges Gmail, facture ou remboursement déjà émis côté Qonto), chaque pièce **avec sa source**, les manquantes **listées avec où les trouver**
5. **Mémo attaché à la transaction** (avec consentement explicite) : `request_attachment_upload` → upload → **confirmé via `list_transaction_attachments`** avant d'annoncer le succès
6. **Toi, tu soumets** : réponse pré-rédigée dans la structure du formulaire du PSP, à déposer sur le portail Stripe/PayPal avant la deadline. Le skill prépare, il ne soumet jamais

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé d'intégrité** : le mémo attaché est un **document de synthèse daté qui cite les pièces sources** (système · identifiant · date · ce que la pièce prouve). Ce n'est ni un reçu, ni une facture, ni une « preuve » générée — jamais de pièce fabriquée. Les vraies pièces sont rassemblées et soumises par l'utilisateur. Cette distinction est écrite dans le mémo lui-même.

## ⚖️ Motifs de litige × pièces qui gagnent

| Motif (reason code) | Ce qui gagne | Où le skill le trouve |
|---|---|---|
| Produit non reçu | Preuve de livraison / tracking « delivered » | Shopify (fulfillment + tracking) |
| Fraude / transaction non reconnue | Adresses facturation-livraison concordantes, client récurrent, historique de commandes | Shopify + Stripe (détails de charge) |
| Produit non conforme | Description produit, échanges client, politique de retour proposée | Shopify + Gmail |
| Débit dupliqué / déjà remboursé | **Le remboursement déjà émis** — l'argument massue | Qonto (transaction de remboursement) + Stripe |
| Abonnement annulé | Date d'annulation vs date de débit, CGV, échanges | Stripe + Gmail |

## 🧪 Robuste sur données sales

- Pas de MCP Stripe/PayPal ? → mode Qonto pur annoncé : détection des reprises + chronologie + checklist de réponse
- Pas de ligne de reprise visible ? → **Stripe compense souvent le litige dans le payout suivant** : le skill signale les payouts anormalement bas comme candidats et recommande le MCP Stripe, plutôt que de deviner
- Pièce manquante (pas de tracking, pas d'échange client) ? → listée comme manquante, avec où la chercher — une checklist, pas un haussement d'épaules
- Aucun litige trouvé ? → le skill le dit et n'en invente jamais
- Deadline inconnue ? → fenêtres types données comme indicatives + renvoi explicite au portail

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : litiges ouverts (urgence triée), chronologie de l'argent, checklist de pièces ✅/⚠️ | **Toujours** — c'est la base |
| **Mémo de défense** | Document de synthèse daté, sourcé, attaché au débit de reprise dans Qonto | Par litige, avec consentement explicite |
| **Brouillon de réponse** | L'argumentaire restructuré selon le formulaire du PSP, prêt à coller | Dès que le motif du litige est connu |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : le problème (l'argent repris + frais + deadline) → détection → dossier 4 pièces assemblé et sourcé → mémo attaché à la transaction → « tu n'as plus qu'à soumettre ». Le script détaillé de tournage est conservé en interne (hors dépôt).

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Score de gagnabilité par motif (taux de succès typiques par reason code) | Moyen | Aide à prioriser quand plusieurs litiges tombent en même temps |
| Suivi post-litige : détecter le re-crédit en cas de victoire et clore le mémo | Faible | Réutilise le moteur de détection |
| Rappel de deadline via MCP calendrier détecté dynamiquement | Faible | Multi-MCP optionnel, dans l'esprit du kickoff |
| Synergie `qonto-shopify-bridge` (réconciliation commandes-payouts) | Faible | Le débit d'origine est déjà rapproché |
| Synergie `qonto-fraud-sentinel` (débits inhabituels → reprises candidates) | Faible | Détection croisée |

## 🛡 Garde-fous

- **Jamais** de pièce fabriquée : le mémo est une synthèse datée qui cite les originaux — la distinction est écrite dedans
- **Jamais** « réponse soumise » ni « litige gagné » : la soumission se fait sur le portail Stripe/PayPal, par l'utilisateur
- Deadlines = celles du litige ; les fenêtres génériques sont toujours étiquetées indicatives
- Upload de pièce jointe uniquement avec consentement explicite, et annoncé seulement après confirmation par `list_transaction_attachments`
- IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout · tous les montants d'exemple de cette doc sont inventés

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-chargeback-defender.fr.html`.*
