# 🧾 qonto-monthly-close — Clôture Zen, le CFO de fin de mois en 3 minutes

> **Skill #6** · Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> Héritier de la proposition P1 « Clôture Zen » (notée 43/50), modernisé : **100 % lecture seule** — le rapport propose, toi tu agis
> Pièges MCP vérifiés sur compte réel les 03-04/07 (403 cash-flow categories, pagination, `on_receipts`)

---

## 🎯 Le pitch

Chaque fin de mois, le dirigeant de TPE passe 2 à 4 heures à compiler relevés, justificatifs, TVA et impayés pour son comptable. Un seul prompt — « **clôture mon mois** » — déclenche la revue complète du mois écoulé :

1. **Justificatifs manquants, priorisés par enjeu** — un café à 3 € et un laptop à 1 200 € ne pèsent pas pareil : classement par montant et TVA récupérable en jeu, score de complétude du mois
2. **TVA du mois** — collectée (sur les **encaissements** si `on_receipts` est détecté) − déductible (plancher annoncé si des débits sont non renseignés) = net à provisionner
3. **Anomalies** — dépense inhabituelle chez un tiers connu, **doublon de prélèvement**, nouveau bénéficiaire jamais vu — signalées avec preuves, jamais accusées
4. **Le reste de la revue** — transactions sans label (catégorie proposée), impayés clients (retard + historique payeur), comparaison vs mois précédent (top hausses/baisses par poste)

→ **Rapport de clôture** actionnable, avec la to-do de régularisation classée par priorité (P1 argent en jeu → P2 conformité → P3 hygiène).

## 🧭 Positionnement dans la gamme

`qonto-monthly-close` est le **chef d'orchestre mensuel** : il détecte et priorise, en lecture seule. Chaque chantier a ensuite son spécialiste :

| Il détecte… | Le spécialiste qui agit |
|---|---|
| Justificatifs manquants | `qonto-receipt-hunter` (chasse + upload) |
| Impayés clients | `qonto-invoice-chaser` (relances rédigées) |
| TVA à provisionner | `qonto-tax-pilot` (échéancier + provision sous SCA) |

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | Justificatifs, anomalies, impayés, comparaisons : **tous les pays Qonto**. Module TVA : logique France ; autres pays (DE, ES, IT…) → estimation générique collectée−déductible, annoncée comme telle | ℹ️ détecté |
| MCP Qonto connecté | Connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Historique ≥ 3 mois | Les détecteurs d'anomalies et la comparaison mensuelle ont besoin d'une base ; en dessous, le skill dégrade honnêtement | ⭕ |
| MCP Gmail | Optionnel, détecté dynamiquement : recherche des reçus manquants dans la boîte mail ; sinon le skill le dit et continue | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Cadrage du mois** : `get_organization` d'abord (comptes, pays, forme juridique), mois à clôturer (défaut : dernier mois complet), lecture paginée ≤ 50 des transactions **+ 3-6 mois d'historique** pour les bases de comparaison. Opérations carte rapprochées par `emitted_at` (1-2 j de décalage avec `settled_at`)
2. **Justificatifs manquants** : `attachment_required` sans `attachment_ids`, priorisés par montant et TVA récupérable, score de complétude. Gmail connecté → proposition de chasse aux reçus dans la boîte mail
3. **TVA du mois** : collectée depuis les factures clients (**sur les encaissements** si `vat_payment_condition: "on_receipts"`) − déductible (somme des `vat_amount`, plancher annoncé) ; lien chiffré avec les justificatifs manquants (pas de facture = TVA non déductible)
4. **Anomalies** : trois détecteurs comparés à l'historique — dépense inhabituelle, doublon de prélèvement (même tiers, même montant, même mois), nouveau bénéficiaire. Chaque signalement avec ses preuves et une sévérité
5. **Sans label & impayés** : catégorie proposée depuis la taxonomie `list_labels` (les cash-flow categories renvoient 403 sur le connecteur claude.ai — fallback prévu) ; impayés clients avec jours de retard et historique payeur
6. **Rapport de clôture** : scorecard + comparaison vs mois précédent + **to-do priorisée**, chaque ligne pointant vers le skill dédié ou l'action en un tap dans l'app

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé** : tous les traits sont pleins — **lecture seule intégrale**. Ce skill n'appelle aucun outil d'écriture : rien n'est créé, modifié, envoyé ni déplacé. C'est le seul skill de la gamme qu'on peut lancer sur n'importe quel compte, n'importe quand, sans le moindre effet de bord — y compris celui d'un juge du hackathon.

## 📤 Formats de sortie (où atterrit le rapport ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : scorecard, justificatifs, TVA, anomalies, comparaison, impayés, to-do | **Toujours** — c'est la base |
| **Dashboard de clôture** | Fichier/artifact **HTML** : scorecard du mois, jauge de complétude, tuile TVA, cartes anomalies, checklist to-do | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur les tableaux |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : la corvée de fin de mois → un seul prompt → la revue en direct → **le rapport complet qui tombe en une passe** (« 96 transactions passées en revue, 3 justificatifs manquants, 1 doublon détecté, TVA du mois : 717 € — voilà ta to-do de 10 minutes ») → le dashboard. Le script détaillé (textes à dire, checklist tournage, notes de montage) est conservé en interne (hors dépôt).

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Rapport « prêt pour l'expert-comptable » (export PDF structuré) | Faible | Le contenu existe déjà, il manque la mise en forme cabinet |
| Mémoire de clôture : comparer les scorecards mois après mois | Moyen | La complétude qui monte = la boîte qui se tient |
| Détecteur d'abonnements zombies (prélèvement récurrent jamais labellisé, jamais justifié) | Faible | Réutilise les baselines des anomalies |
| Multi-MCP : reçus depuis Google Drive en plus de Gmail | Faible | Détection dynamique, même modèle que Gmail |

## 🛡 Garde-fous

- **Lecture seule intégrale** : aucun outil d'écriture appelé, jamais — le rapport propose, l'utilisateur dispose
- Anomalies = **signalements avec preuves, pas des accusations** : la baseline qui a déclenché le flag est toujours montrée
- TVA = estimation, pas déclaration — validation expert-comptable recommandée dans chaque rapport
- Dégradation honnête : mois vide, pas de factures, société non française → le skill dit ce qu'il a pu et n'a pas pu calculer
- IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-monthly-close.fr.html` · `docs/doc-qonto-monthly-close.fr.docx`.*
