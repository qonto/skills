# 🌉 qonto-shopify-bridge — Ce que la boutique annonce vs ce que la banque encaisse

> **Skill #10 · le multi-MCP e-commerce** · Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> Réconciliation payouts Shopify/Stripe/PayPal ↔ encaissements Qonto · **0 écriture** (lecture pure)
> Démo prévue sur une boutique e-commerce réelle (POD Shopify, encaissements Qonto réels)

---

## 🎯 Le pitch

Tout marchand Shopify vit le même angle mort : les **ventes brutes** dans Shopify, les **payouts nets** sur le compte — et entre les deux, des frais (Shopify Payments, Stripe, PayPal), des remboursements, des délais J+2/J+3. Le skill rapproche les deux côtés :

1. **Cadence des payouts** — le skill apprend le rythme de chaque PSP (Shopify, Stripe, PayPal, SumUp…) et repère toute rupture : versement manquant ou en retard
2. **Frais réels vs annoncés** — taux effectif calculé payout par payout : (brut − net) ÷ brut, comparé au tarif de ton plan (si tu l'indiques — jamais de barème deviné)
3. **Remboursements & chargebacks** — remboursé côté boutique mais pas répercuté côté compte (ou l'inverse) : détecté, documenté
4. **La vraie marge** — net encaissé par période, après toutes les commissions — pas le chiffre flatteur du dashboard Shopify

Le rapport type : « **14 payouts attendus, 13 reçus, 1 en retard de 4 jours ; frais réels 2,9 % + 0,30 € conformes ; net encaissé du mois : X €** ».

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Tous pays Qonto** (FR, DE, ES, IT, AT, NL, BE, PT) — la réconciliation de payouts est universelle. Multi-devises : rapport par devise, jamais de conversion silencieuse | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Encaissements PSP dans l'historique | Des crédits SHOPIFY / STRIPE / PAYPAL / SUMUP… identifiables — c'est la matière première du cœur Qonto pur | ✅ |
| MCP **Shopify** (ou Stripe) connecté | Détecté dynamiquement. Avec : rapprochement fin ventes ↔ payouts. Sans : le skill l'annonce et continue en mode Qonto pur (déjà utile) | ⭕ recommandé |
| Historique PSP ≥ 3 mois | En dessous, la cadence est annoncée en confiance basse | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Cartographie des encaissements** : 12-24 mois de crédits (paginé ≤ 50), contreparties PSP normalisées (SHOPIFY, STRIPE, PAYPAL, SUMUP, ADYEN, MOLLIE…), regroupées par prestataire et par boutique. Date d'arrivée = `settled_at`
2. **Rythme des payouts** (Qonto pur, déjà utile seul) : cadence par PSP (quotidienne jours ouvrés, hebdo, à la demande), délai typique, montant habituel → **calendrier des versements attendus**. Toute rupture = alerte. ⚠️ PayPal fonctionne souvent en retraits manuels — le skill reconnaît ce pattern et ne crie pas au payout manquant à tort
3. **Enrichissement Shopify** (si le MCP est présent) : ventes brutes, remboursements et commandes par période (`run-analytics-query`, `list-orders`, `get-order` — outils Shopify, graphie à tirets). Multi-boutiques : une réconciliation par boutique. MCP absent → annoncé, le skill continue
4. **Rapprochement ventes ↔ payouts** : un payout regroupe *n* commandes moins frais moins remboursements, avec un délai J+2/J+3. Le skill fait correspondre fenêtres de vente et versements reçus, et calcule le **taux de frais effectif**
5. **Détection des écarts** : payout manquant (avec **brouillon de ticket support** prêt à envoyer, références incluses — relevé officiel via `list_statements`), retard inhabituel, dérive des frais, remboursement non répercuté
6. **Rapport de réconciliation** : tableaux + net encaissé + vraie marge après commissions ; dashboard HTML si l'hôte l'affiche

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé** : ce skill est en **lecture pure** — aucun outil d'écriture, ni côté Qonto ni côté Shopify. Il lit, rapproche, documente. La seule « action » qu'il produit est un texte : le brouillon de ticket support que **toi** tu décides d'envoyer. Risque : zéro.

## 🔍 Ce que le skill détecte

| Anomalie | Comment | Ce que tu obtiens |
|---|---|---|
| **Payout manquant** | Attendu selon la cadence apprise (et/ou annoncé côté boutique), rien sur le compte au-delà du délai typique | Brouillon de ticket support avec date, montant attendu, plage de commandes, référence du relevé |
| **Payout en retard** | Arrivé, mais N jours au-delà du délai appris | Alerte datée, historique des délais |
| **Dérive des frais** | Taux effectif (brut − net) ÷ brut qui bouge mois après mois | Courbe de tendance, comparaison au tarif annoncé de ton plan (si fourni) |
| **Remboursement non répercuté** | Remboursé côté boutique, pas de déduction correspondante côté compte (ou l'inverse) | Liste des cas, références des deux côtés |
| **Retraits manuels (PayPal)** | Pattern « à la demande » reconnu | Pas de fausse alerte — cadence requalifiée |

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (réconciliation, frais, net encaissé, anomalies) | **Toujours** — c'est la base |
| **Dashboard interactif** | Fichier/artifact **HTML** : timeline des payouts avec les trous en évidence, tendance du taux de frais, barres net/mois | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli sur les tableaux |
| **Brouillon de ticket support** | Texte prêt à envoyer à Shopify/Stripe, toutes références incluses | À chaque payout manquant détecté |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : le problème (Shopify dit X, la banque dit Y) → cadence des payouts en Qonto pur → réconciliation enrichie Shopify → **le payout manquant détecté, ticket support prêt** (le moment « it just works ») → rapport final et vraie marge. Tournée sur une boutique réelle (données de production). Le script détaillé de tournage est conservé en interne (hors dépôt).

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| MCP Stripe en second enrichissement symétrique | Faible | Même logique que Shopify — détection dynamique |
| Alerte récurrente « payout manquant » (rituel du lundi matin) | Faible | Le skill est déjà idempotent, il suffit de le relancer |
| Rapprochement commande par commande (payout → liste exacte des orders) | Moyen | `get-order` le permet déjà, coût en appels |
| Marge nette par produit (commissions ventilées) | Moyen | Combine `run-analytics-query` + frais réels |
| Multi-PSP consolidé (Shopify + PayPal + SumUp sur un seul rapport) | Faible | Le cœur Qonto pur le fait déjà par PSP |

## 🛡 Garde-fous

- **Lecture pure** : aucun outil d'écriture, rien n'est créé ni modifié, ni côté Qonto ni côté boutique
- Jamais de barème de frais inventé : taux **calculés** uniquement, taille d'échantillon affichée
- Un « payout manquant » est une **hypothèse documentée**, pas une accusation — le support a le dernier mot
- Rapport par devise, jamais de conversion silencieuse · IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout
- Dégradation honnête : sans MCP Shopify → mode Qonto pur annoncé ; historique < 3 mois → confiance basse annoncée

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-shopify-bridge.fr.html` · `docs/doc-qonto-shopify-bridge.fr.docx`.*
