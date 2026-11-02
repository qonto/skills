# 🧭 qonto-oss-navigator — La TVA e-commerce européenne, avant qu'elle te rattrape

> Hackathon Qonto × Anthropic MCP (10-13/07/2026) · Agent Skill pour le MCP Qonto
> Guichet unique OSS : jauge du seuil des 10 000 €, brouillon de déclaration trimestrielle pays par pays, provision optionnelle sous SCA
> ⚠️ **Aide à la préparation, PAS une déclaration** : le dépôt OSS se fait sur impots.gouv.fr (guichet unique)

---

## 🎯 Le pitch

Dès **10 000 € de ventes B2C transfrontalières UE** sur l'année (seuil unique, toutes ventes à distance cumulées — pas par pays), la TVA se déclare **au taux du pays du client**, via le guichet unique OSS. La plupart des e-commerçants le découvrent trop tard — souvent au premier contrôle. `qonto-oss-navigator` transforme le compte Qonto en vigie OSS :

1. **Ventes par pays de livraison** — Shopify si connecté (pays d'expédition réel par commande), sinon inférence depuis les factures clients et les libellés/devises des encaissements Qonto — **annoncée comme partielle**, jamais maquillée en couverture complète
2. **Jauge du seuil des 10 000 €** — cumul B2C transfrontalier de l'année (et contrôle de l'année passée) : « tu es à X € sur 10 000 € », franchissement daté ou estimé au rythme actuel
3. **Brouillon OSS trimestriel** — pays par pays : base HT, taux du pays du client (table des 27 États membres embarquée, millésimée), TVA due, total, date limite et portail de dépôt
4. **Provision optionnelle** — demande de virement du total OSS vers le sous-compte impôts ; l'argent ne bouge **que** après l'approbation SCA dans l'app Qonto

Et les ventes **B2B intracommunautaires** (numéro de TVA client valide) ? **Exclues de l'OSS** — autoliquidation. Le skill les isole et les signale à part, jamais mélangées à la jauge.

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord) | ✅ |
| Pays | **Pensé pour un vendeur établi en UE.** Le seuil des 10 000 € et la table des taux sont des règles européennes — valables pour tous les pays Qonto (FR, DE, ES, IT…). Seul le **portail de dépôt** est national (France : impots.gouv.fr, guichet OSS) | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| MCP Shopify | **Optionnel, détecté dynamiquement** : pays de livraison réels par commande (`list-orders`, `run-analytics-query`). Absent → mode Qonto pur, annoncé comme partiel | ⭕ recommandé |
| Sous-compte « impôts » | Créé une fois dans l'app Qonto — détecté par son nom (taxe/tax/impôt/TVA/OSS) | ⭕ recommandé — sinon le skill calcule sans agir |
| Ventes transfrontalières UE | Sans ventes B2C vers d'autres pays UE, le skill le dit et s'arrête là — pas de jauge inventée | ℹ️ détecté |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Identité & sources** : `get_organization` d'abord (pays d'établissement, comptes, sous-compte impôts), détection du MCP Shopify → le skill annonce son mode : **Shopify** (pays réels) ou **Qonto pur** (inférence partielle)
2. **Ventes par pays de livraison** : commandes Shopify nettes de remboursements, ou factures clients + indices devises (SEK, PLN, DKK, CZK…) côté Qonto. Ventes domestiques et exports hors UE exclus du calcul ; B2B intracom isolé (autoliquidation)
3. **Jauge du seuil** : cumul B2C transfrontalier de l'année civile en cours ET contrôle de l'année précédente (la règle regarde les deux) — franchissement daté ou estimé
4. **Taux du pays du client** : table statique des 27 États membres, **millésimée (2026-07)** — le skill affiche le millésime et demande de vérifier avant tout dépôt ; taux réduits jamais devinés, toujours demandés
5. **Brouillon OSS du trimestre** : pays par pays (base · taux · TVA due), conversion au taux BCE du dernier jour du trimestre pour les devises non-euro, date limite (fin du mois suivant le trimestre) et portail
6. **Provision** (uniquement avec consentement explicite) : `create_multi_transfer_request` avec le détail pays par pays dans la note → **approbation SCA** dans l'app Qonto

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de sécurité** : le trait plein (lecture) ne présente aucun risque ; le trait pointillé (écriture) exige le consentement explicite dans la conversation et ne produit qu'une *demande* — c'est la SCA (2FA) du titulaire, dans l'app Qonto, qui déplace l'argent. Ni Claude ni le MCP ne le peuvent. **C'est le modèle de sécurité, pas une limitation.**

## 📅 Références OSS (les règles que le skill applique)

| Règle | Détail |
|---|---|
| Seuil unique | **10 000 € HT / année civile**, toutes ventes à distance B2C UE cumulées (biens + services numériques TBE) — évalué sur l'année en cours **et** l'année précédente |
| Sous le seuil | TVA du pays du vendeur autorisée (option OSS volontaire possible, engagement 2 ans) |
| Au-dessus | TVA du pays du **client**, dès la transaction qui franchit le seuil — immatriculation pays par pays OU guichet unique OSS |
| Déclaration OSS | Trimestrielle, dépôt **avant la fin du mois suivant le trimestre** : 30/04 · 31/07 · 31/10 · 31/01 — corrections des trimestres passés dans la déclaration courante |
| Exclusions | Ventes domestiques (→ TVA nationale, voir `qonto-vat-return`) · **B2B intracom** (autoliquidation, état récapitulatif — pas l'OSS) · exports hors UE |
| Taux 2026-07 | 17 % LU · 18 % MT · 19 % DE, CY · 20 % AT, BG, FR · 21 % BE, CZ, ES, LT, LV, NL, RO · 22 % IT, SI · 23 % IE, PL, PT, SK · 24 % EE, EL · 25 % DK, HR, SE · 25,5 % FI · 27 % HU — **à vérifier avant dépôt** |

## ✨ Le moment « it just works »

> « Ventes UE B2C : tu es à **8 420 € sur 10 000 €** — franchissement estimé en **octobre** au rythme actuel. Voici ta déclaration OSS du trimestre, pays par pays, et la **provision de 612 €** à mettre de côté. » *(chiffres inventés pour l'exemple)*

Une question, trois réponses : où j'en suis, ce que je devrai déclarer, combien je mets de côté.

## 📤 Formats de sortie (où atterrit le brouillon ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (jauge, brouillon OSS pays par pays, flux exclus) | **Toujours** — c'est la base |
| **Dashboard interactif** | Fichier/artifact **HTML** : barre de jauge, tableau par pays, frise des trimestres | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur les tableaux |
| **Note de la demande Qonto** | Détail pays par pays joint à la demande de virement, visible à l'approbation SCA | À chaque provision créée |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : le piège du seuil → la jauge → le brouillon OSS pays par pays → la provision + approbation SCA → dashboard. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| IOSS (importations ≤ 150 €) | Moyen | Le pendant import du guichet unique — même moteur, autre régime |
| Taux réduits par catégorie produit | Moyen | Croiser les produits Shopify avec les catégories à taux réduit par pays |
| Rappel d'échéance OSS dans le calendrier (MCP calendrier détecté dynamiquement) | Faible | Multi-MCP optionnel, dans l'esprit du kickoff |
| Historique de jauge trimestre par trimestre | Faible | Réutilise les fenêtres de scan existantes |
| WooCommerce / autres sources de commandes | Moyen | Même interface : « pays de livraison par commande » |

## 🛡 Garde-fous

- **Aide à la préparation, PAS une déclaration** : le dépôt se fait sur le portail national (France : impots.gouv.fr, guichet OSS) ; validation expert-comptable recommandée dans chaque rapport
- La table des taux porte son **millésime (2026-07)** et doit être vérifiée avant dépôt ; taux réduits demandés, jamais devinés
- **B2B intracom exclu de l'OSS** (autoliquidation) — signalé à part, jamais dans la jauge
- Mode Qonto pur = couverture **partielle** annoncée (la jauge est un plancher) ; jamais de répartition par pays inventée
- **Jamais** de demande de virement sans confirmation explicite ; jamais présentée comme exécutée — en attente de la SCA
- IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout · compte vide → le skill le dit et s'arrête

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-oss-navigator.fr.html`. Voir aussi : `qonto-vat-return` (TVA domestique) · `qonto-tax-pilot` (provision fiscale).*
