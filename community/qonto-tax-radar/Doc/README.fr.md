# 🛰️ qonto-tax-radar — Le pré-contrôle fiscal qui travaille POUR toi

> **Skill #7** · Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> Héritier de P3 « Radar Fiscal » (noté 42/50, plan B historique) · **Lecture seule intégrale — zéro écriture, zéro risque**

---

## 🎯 Le pitch

La peur n°1 du dirigeant français, c'est le contrôle fiscal — et personne ne sait où il est vulnérable. `qonto-tax-radar` inverse les rôles : il passe les transactions Qonto au crible des **8 axes de vérification qu'utilise réellement l'administration** lors d'une vérification de comptabilité, et rend le rapport AVANT que le fisc ne le fasse.

1. **Crible des 8 axes DGFIP** — charges somptuaires, dépenses perso passées en pro, compte courant d'associé, TVA déduite vs justificatifs présents, avantages en nature, doublons de charges, espèces, transactions rondes récurrentes
2. **Chaque signalement est sourcé** — transaction précise + règle fiscale citée (article/principe) + niveau de risque + action corrective. Jamais d'accusation : des « points d'attention », pas de la « fraude »
3. **Chiffrage du risque** — TVA rappelable, réintégrations IS, intérêts et pénalités, en ordres de grandeur pédagogiques
4. **Plan de régularisation** — la liste priorisée des corrections à faire ce mois-ci pour que le dossier soit propre — puis relance le skill et regarde la note s'améliorer

Et surtout : **le seul contrôleur fiscal en lecture seule**. Le skill ne modifie rien, ne tague rien, ne touche à rien. Il regarde, il explique, il dédramatise.

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **8 axes et règles citées : France** (CGI, Code de commerce, CMF). Autres pays Qonto (DE, ES, IT…) : dégradation propre — axes universels seulement (justificatifs, doublons, espèces, montants ronds), jamais un article français cité hors de son champ | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Historique ≥ 12 mois | En dessous, le skill analyse ce qui existe et le dit honnêtement (couverture partielle annoncée) | ⭕ |
| Justificatifs attachés dans Qonto | Pas obligatoire — s'il n'y en a aucun, l'axe 4 devient le premier point d'attention du rapport, pas une erreur | ⭕ |
| Sous-compte, écriture, consentement | **Aucun** : lecture seule intégrale, il n'y a littéralement rien à autoriser | — |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Photographie de l'organisation** : `get_organization` d'abord — pays, forme juridique, comptes. France → 8 axes complets ; autre pays → axes universels, annoncé clairement
2. **Collecte de l'historique** : 12 mois de transactions paginées ≤ 50 par fenêtres trimestrielles (24 sur demande), croisées avec les factures fournisseurs, les labels et les justificatifs attachés. Les champs `attachment_ids`, `vat_amount`, `attachment_required` des transactions font l'essentiel du travail ; `list_transaction_attachments` ne vérifie que les transactions sur le point d'être signalées. Motifs carte lus sur `emitted_at` (le `settled_at` décale d'1-2 jours — un achat du dimanche peut apparaître le mardi)
3. **Crible des 8 axes** (tableau de référence ci-dessous) — la vraie grille de la vérification de comptabilité
4. **Chiffrage** : TVA rappelable + réintégration IS (25 %, ou 15 % sur la part au taux réduit) + intérêts de retard 0,20 %/mois + pénalité de base 10 % — en ordres de grandeur pédagogiques, jamais présenté comme un calcul officiel
5. **Rapport de risque** : niveau 🟢🟡🔴 par axe, note globale = pire axe (un contrôle suit le point faible), chaque signalement = transaction + règle citée + action corrective
6. **Plan de régularisation** : justificatifs à récupérer, dépenses à rembourser ou requalifier, pièces à produire — à valider avec l'expert-comptable, puis relance et compare

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de sécurité** : il n'y a **que des traits pleins** (lecture). Ce skill est le seul de sa catégorie à ne demander aucun consentement d'écriture — parce qu'il n'écrit rien. Aucun outil d'écriture n'est jamais appelé : impossible de modifier une transaction, de poser un label ou de déplacer un centime. C'est le contrôleur qui regarde ton dossier **de ton côté du bureau**.

## 📊 Les 8 axes de vérification (grille de référence)

| # | Axe | Ce que le skill détecte | Règle citée |
|---|---|---|---|
| 1 | **Charges somptuaires** | Restaurants haut de gamme (montant/couvert), voyages, cadeaux au-delà des seuils (TVA cadeaux ≤ 73 € TTC/an/bénéficiaire ; relevé 2067 si cadeaux > 3 000 €/an ou réceptions > 6 100 €/an) | art. 39-4 CGI ; art. 28-00 A ann. IV CGI |
| 2 | **Dépenses perso en pro** | Achats week-end/dimanche, enseignes hors objet social (jeux, habillement, loisirs), abonnements grand public | art. 39-1 CGI ; acte anormal de gestion |
| 3 | **Compte courant d'associé** | Virements vers bénéficiaires « perso », allers-retours avec le dirigeant, motifs de CCA débiteur | art. L223-21 C. com. ; art. 111-a CGI |
| 4 | **TVA déduite vs justificatifs** | `vat_amount` > 0 **et** aucun justificatif attaché → TVA déduite sans facture à présenter | art. 271 II CGI — pas de facture, pas de déduction |
| 5 | **Avantages en nature** | Véhicule, téléphone, logement, abonnements à usage mixte payés par la société sans trace de déclaration | art. 82 CGI ; BOSS avantages en nature |
| 6 | **Doublons de charges** | `has_duplicates` sur factures fournisseurs ; même contrepartie + même montant à ± 72 h | art. 54 CGI ; art. 1729 (40 % si délibéré — contexte seulement) |
| 7 | **Espèces** | Retraits ronds récurrents ; paiements pro en espèces > 1 000 € | art. L112-6 + D112-3 CMF (plafond 1 000 €) |
| 8 | **Transactions rondes récurrentes** | Montants ronds réguliers vers un même bénéficiaire sans facture en face | art. 54 CGI — charge de la preuve |

Vocabulaire imposé partout : « point d'attention », « à documenter », « à requalifier » — jamais « fraude ». Une dépense « restaurant » peut être 100 % légitime ; le skill le rappelle.

## 📤 Formats de sortie (où atterrit le rapport ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Bandeau de risque global + tableau 8 axes + détail des signalements + plan de régularisation, en markdown | **Toujours** — c'est la base |
| **« Avis de pré-contrôle » interactif** | Fichier/artifact **HTML** : note globale, jauges par axe, tableau des signalements, checklist de régularisation | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur le markdown |
| **Relance comparative** | Même rapport après corrections — la note s'améliore, c'est la boucle de rétention | À chaque re-run |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : la peur du contrôle → lancement du pré-contrôle → les signalements axe par axe → **le rapport qui tombe** (« 2 points rouges : 1 430 € de TVA déduite sans justificatif, et 3 dépenses à requalifier — corrige ça ce mois-ci et ton dossier est propre ») → garde-fous et conclusion. Le script détaillé (textes à dire, checklist tournage, notes de montage) est conservé en interne (hors dépôt).

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Mode « remédiation assistée » : demandes de justificatifs (`request_attachment_upload`) + labels « à documenter », sous consentement explicite | Faible | Les writes existent dans le MCP — v1 volontairement lecture seule, c'est le positionnement |
| Axes par pays (DE · ES · IT…) : grilles de vérification locales | Moyen | Qonto est paneuropéen ; v1 = France + axes universels |
| Multi-MCP optionnel : croiser l'axe 4 avec les factures retrouvées dans Gmail/Drive | Moyen | Détection dynamique — s'active si le MCP est présent, sinon le skill le dit et continue |
| Suivi de la note dans le temps (historique des re-runs) | Faible | La boucle de rétention, chiffrée |
| Contrôle de cohérence CA (factures encaissées vs entrées) | Moyen | 9e axe naturel, déjà dans l'ADN de P3 |

## 🛡 Garde-fous

- **Lecture seule intégrale** : aucun outil d'écriture appelé, jamais — c'est un engagement du skill, pas un réglage
- **Jamais d'accusation** : « point d'attention », pas « fraude » ; une dépense signalée peut être parfaitement légitime (le skill manque de contexte par construction, il peut sous- ou sur-estimer)
- **Ce n'est pas un avis fiscal** ni une position de l'administration : simulation pédagogique, validation expert-comptable rappelée dans chaque rapport
- Société non française → axes universels seulement, articles français jamais cités hors de leur champ
- IBAN masqués (4 derniers chiffres), noms sensibles masqués dans tout export ; pagination ≤ 50 partout

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-tax-radar.fr.html` · `docs/doc-qonto-tax-radar.fr.docx`.*
