# 📆 qonto-money-calendar — La trésorerie dans l'agenda, dans les deux sens

> Hackathon Qonto × Anthropic MCP (10-13/07/2026) · Agent Skill pour le MCP Qonto
> Deux sens : Qonto → agenda (l'échéancier devient des événements) · agenda → Qonto (les jours facturables deviennent des factures)

---

## 🎯 Le pitch

L'argent vit dans des échéances, pas dans des listes. Tu vis dans ton agenda — pas dans un export comptable. `qonto-money-calendar` fait de Google Calendar le tableau de bord de ton mois financier :

1. **Sens 1 — pousser** : toutes les dates financières à venir inscrites dans l'agenda — factures fournisseurs à payer, factures clients à encaisser, échéances récurrentes détectées sur 24-36 mois (loyer, abonnements, prélèvements fiscaux, cadences mensuelles/trimestrielles/annuelles) — **montant dans le titre, rappel J-3** sur chaque événement
2. **Sens 2 — lire** : les jours facturables tagués `[Client]` dans les titres d'événements sont comptés, et le skill génère la **facture de fin de mois** (jours × TJM confirmé) en **brouillon** dans Qonto
3. **Récap avant d'écrire** : aucun événement créé sans récapitulatif confirmé dans la conversation ; relances idempotentes (les événements marqués sont mis à jour, jamais dupliqués)
4. **TJM jamais deviné** : déduit de l'historique de facturation Qonto (factures passées, catalogue produits), puis **systématiquement confirmé** avant tout calcul

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| **MCP Google Calendar** | **Requis pour les 2 sens.** Absent : sens 1 dégradé (échéancier en tableau dans la conversation), sens 2 indisponible — et le skill le dit | ⭕ fortement recommandé |
| Pays | **Universel** — dates de factures et récurrences depuis l'historique, aucune règle fiscale locale inventée. Échéancier fiscal français complet → skill `qonto-tax-pilot` | ℹ️ tous pays Qonto |
| Historique 24-36 mois | Nécessaire pour voir les cadences annuelles (assurances, CFE, renouvellements) ; en dessous, le skill dégrade honnêtement | ⭕ |
| Convention de tag `[Client]` | Pour le sens 2 : un événement `[Acme] sprint sur site` = 1 jour facturable (convention expliquée au premier usage) | ⭕ sens 2 seulement |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Photographie du compte** : `get_organization` d'abord (organisation, comptes, réglages de facturation), puis détection du MCP Google Calendar — présent → mode complet ; absent → tableau seul, sens 2 indisponible
2. **Collecte des échéances** : factures fournisseurs à payer (`due_date`), factures clients à encaisser, récurrences détectées sur 24-36 mois (tiers normalisé, montant stable ±10 %, cadence M/T/A, ≥3 occurrences — 2 pour l'annuel), projetées sur leurs prochaines dates
3. **Sens 1 — pousser** : récapitulatif dans la conversation (date · titre · montant · source 🟢 vu / 🟡 estimé) → après confirmation explicite, événements créés dans l'agenda, montant dans le titre, rappel J-3, marqueur `[qonto-money-calendar]` pour des relances sans doublons
4. **Sens 2 — lire** : lecture des jours tagués `[Client]` sur la période (1 événement-jour = 1 jour, demi-journées via `0.5` dans le titre), comptage par client avec la liste des dates
5. **TJM confirmé** : proposé depuis l'historique (`list_client_invoices` du client, `list_products` type « jour »/« TJM »), source affichée, **puis confirmé par l'utilisateur** — jamais supposé
6. **Facture de fin de mois** : `create_client_invoice` en **brouillon** (jours × TJM, TVA du catalogue ou des réglages — jamais devinée) → l'utilisateur relit et envoie depuis Qonto

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Deux écritures, deux verrous** : les événements d'agenda n'existent qu'après le récapitulatif confirmé dans la conversation ; la facture Qonto n'existe qu'en **brouillon**, après confirmation du TJM et des lignes. Le skill ne déplace aucun argent et n'envoie rien : payer se fait dans l'app Qonto (SCA), envoyer la facture se fait après relecture. **C'est le modèle de sécurité, pas une limitation.**

## 📆 Ce qui atterrit dans l'agenda (sens 1)

| Type d'événement | Source Qonto | Exemple de titre (inventé) | Rappel |
|---|---|---|---|
| Facture fournisseur à payer | `list_supplier_invoices` (due_date) | `💸 Fournisseur Nimbus — 890 €` | J-3 |
| Facture client à encaisser | `list_client_invoices` (impayées) | `💰 Facture INV-2026-042 à encaisser — 4 800 €` | J-3 |
| Récurrence mensuelle | Historique 24-36 mois | `💸 Loyer — 1 200 €` | J-3 |
| Récurrence trimestrielle / annuelle | Historique 24-36 mois | `💸 Assurance annuelle — 640 € (estimé)` | J-3 |
| Prélèvement fiscal détecté | Historique (prélèvements) | `💸 Prélèvement TVA — ~2 100 € (estimé)` | J-3 |

*Tous les montants ci-dessus sont des exemples inventés. Les montants issus de récurrences sont marqués « estimé » dans l'événement.*

## 🏷 La convention de tag (sens 2)

| Dans le titre de l'événement | Compté comme |
|---|---|
| `[Acme] sprint sur site` | 1 jour facturable pour Acme |
| Événement `[Acme]` sur 3 jours | 3 jours |
| `[Acme] 0.5 atelier` | 0,5 jour |
| Sans crochets | Ignoré (pas facturable) |

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : échéancier, récap avant écriture, comptage des jours, résumé de facture | **Toujours** — c'est la base |
| **Google Calendar** | Événements datés, montant dans le titre, rappel J-3, marqueur anti-doublons | Si le MCP Calendar est présent **et** le récap confirmé |
| **Facture Qonto** | `create_client_invoice` en **brouillon**, visible dans la section Facturation | Sens 2, après confirmation du TJM et des lignes |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : le problème (l'argent vit dans des échéances) → sens 1 : le récap puis l'agenda qui se peuple → la convention `[Client]` et le TJM confirmé → **split-screen agenda / Qonto : 12 jours tagués → facture en brouillon** → wrap-up. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Rapprochement au fil de l'eau : marquer ✅ les événements dont le paiement est passé en banque | Moyen | Réutilise `list_transactions` + le marqueur d'événement |
| Multi-calendriers : un agenda « Argent » dédié, séparé de l'agenda perso | Faible | Simple option à la création |
| Échéancier fiscal estimé complet dans l'agenda | Faible | Cross-skill : `qonto-tax-pilot` calcule, ce skill pousse |
| Devis avant facture pour les nouveaux clients tagués | Faible | `create_quote` existe côté MCP |
| Récap hebdo « ta semaine d'argent » chaque lundi | Moyen | Le rituel du lundi matin, prêt à lire |

## 🛡 Garde-fous

- **Aucun événement créé sans récapitulatif confirmé** dans la conversation en cours ; relances idempotentes (mise à jour des événements marqués, pas de doublons)
- **Le TJM n'est jamais deviné** : déduit de l'historique puis confirmé explicitement, à chaque fois
- Factures créées via MCP = **réelles** → toujours en brouillon, relecture avant envoi ; répétitions sur client fictif + brouillon + `delete_client_invoice`
- Montants estimés (récurrences) toujours marqués « estimé » — jamais présentés comme des montants engagés
- Le skill ne déplace aucun argent : payer reste dans l'app Qonto (SCA), envoyer une facture reste une décision explicite
- IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-money-calendar.fr.html` · `docs/doc-qonto-money-calendar.fr.docx`.*
