# 📥 qonto-einvoice-ready — Prêt pour la facturation électronique du 1er septembre 2026 ?

> **Hackathon Qonto × Anthropic MCP (10-13/07/2026)** · Agent Skill pour le MCP Qonto
> L'audit de préparation à la réforme : mesure l'écart, puis le comble — fiche par fiche, avec ta confirmation.

---

## 🎯 Le pitch

Le **1er septembre 2026**, toutes les entreprises françaises assujetties à la TVA devront pouvoir **recevoir** des factures électroniques (émission : 2026 pour les grandes entreprises et ETI, 2027 pour les PME/TPE). Le piège n'est pas la date — c'est le **fichier clients** : sans SIREN, sans n° de TVA intracom, sans adresse structurée, impossible d'émettre un Factur-X valide. `qonto-einvoice-ready` transforme le compte Qonto en check-up de préparation :

1. **Score de readiness** — fichier clients complet pour Factur-X (SIREN/SIRET, TVA intracom, adresse structurée), qualité des factures émises, calendrier connu, exposition e-reporting — formule transparente, avant/après
2. **Calendrier applicable** — taille de l'entreprise retrouvée au registre public (GE/ETI/PME) ou demandée, jamais devinée → « réception dans N semaines, émission pour toi en 2026 ou 2027 »
3. **Exposition e-reporting** — clients étrangers et particuliers (B2C) repérés dans les fiches ET dans les flux : hors e-invoicing, mais soumis à la transmission des données
4. **Correction en live** — SIREN retrouvés via l'**API publique recherche-entreprises** (data.gouv, sans clé), TVA intracom dérivée du SIREN, aperçu ligne par ligne → `update_client` **uniquement après ta confirmation**, jamais en masse

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Réforme française.** Autres pays Qonto (DE, ES, IT…) : dégradation propre — audit générique de complétude du fichier clients, jamais de calendrier inventé | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Des fiches clients dans Qonto | C'est la matière première de l'audit ; sans clients : le skill explique le référentiel et s'arrête là | ⭕ |
| Accès à l'API publique recherche-entreprises | Sans clé ni compte ; si indisponible, l'audit tourne quand même — seule la correction en live se dégrade | ⭕ |
| Taille de l'entreprise | Retrouvée au registre (`categorie_entreprise`) ou demandée — détermine ta date d'émission (2026 ou 2027) | ℹ️ détecté |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Photo de l'entreprise** : `get_organization` (toujours en premier), pays, identité ; taille retrouvée au registre public ou demandée → calendrier applicable, compte à rebours vers le 01/09/2026
2. **Audit du fichier clients** : chaque fiche B2B notée sur 3 identifiants exigés par Factur-X — SIREN/SIRET (aussi la clé de l'annuaire central), n° de TVA intracom, adresse structurée (une adresse en vrac dans un seul champ ne compte pas). Les particuliers sont fléchés B2C
3. **Qualité des factures émises** : sur 12 mois, quelle part est rattachée à une fiche complète et passerait en Factur-X aujourd'hui ? Ce qui bloquerait est nommé précisément
4. **Exposition e-reporting** : clients étrangers + B2C, croisés avec les flux réels (`list_transactions`) → « X % de tes encaissements relèvent de l'e-reporting, sur le même calendrier que ton émission »
5. **Correction en live** : requête au registre public par nom (+ code postal si dispo) ; homonymes → le skill **demande toujours** ; TVA intracom dérivée du SIREN et **annoncée comme dérivée** ; aperçu ligne par ligne (fiche · champ · actuel → proposé · source) → confirmation → `update_client` champ par champ
6. **Score & plan d'action** : readiness avant/après, ce qui a été corrigé, ce qui reste de ton côté — dont le **choix de la plateforme agréée (PDP), qui t'appartient** (le skill donne les critères, ne choisit jamais)

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de sécurité** : le trait plein (lecture) ne présente aucun risque ; le trait pointillé (écriture) est `update_client` — il **ne touche jamais à l'argent**, seulement aux fiches clients, et n'écrit qu'après l'aperçu complet et ta confirmation explicite dans la conversation. Jamais de mise à jour en masse silencieuse ; chaque écriture est confirmée réussie ou signalée en échec.

## 📅 Référentiel réforme embarqué (arrêté à juillet 2026 — à revérifier ensuite)

| Date | Obligation | Qui |
|---|---|---|
| **01/09/2026** | **Recevoir** des factures électroniques | **Toutes les entreprises françaises assujetties à la TVA** |
| 01/09/2026 | Émettre en électronique | Grandes entreprises & ETI |
| 01/09/2027 | Émettre en électronique | PME, TPE, micro-entreprises |
| Aligné sur l'émission | E-reporting (B2C + transactions internationales) | Tous, selon leur date d'émission |

- **Formats** : Factur-X (PDF/A-3 + XML CII embarqué), UBL 2.1, CII — socle sémantique EN 16931 ; l'identification de l'acheteur (SIREN/SIRET) y est obligatoire
- **Circuit** : les factures transitent par des **plateformes agréées (PDP)** ; un annuaire central relie chaque SIREN/SIRET à sa plateforme. Être joignable via une PDP au 01/09/2026, c'est ça, « être prêt »
- **Mentions** déjà obligatoires (décret 2022) : SIREN du client, adresse de livraison si différente, nature de l'opération (biens / services / mixte), option « TVA sur les débits »

## 🔎 La correction en live (le cœur du skill)

| Étape | Ce qui se passe |
|---|---|
| Recherche | `recherche-entreprises.api.gouv.fr` par nom + code postal — API publique, sans clé |
| Homonymes | Plusieurs candidats plausibles → le skill affiche nom, ville, SIREN de chacun et **demande** |
| TVA intracom | Dérivée du SIREN (clé FR + 2 chiffres) — toujours **marquée « dérivée, à confirmer »** |
| Aperçu | Un tableau unique : fiche · champ · valeur actuelle → proposée · source (registre / dérivé / toi) |
| Écriture | Après ton « oui » explicite : `update_client` champ par champ, résultat annoncé honnêtement |

*Exemple (fictif, chiffres inventés) : « Readiness : 62 %. 9 de tes 14 clients n'ont pas de SIRET — j'en ai retrouvé 7 au registre national. Aperçu ligne par ligne, tu confirmes ? » → après écriture : 91 %.*

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : score détaillé, fiches incomplètes, calendrier, exposition e-reporting | **Toujours** — c'est la base |
| **Aperçu de correction** | Tableau fiche · champ · actuel → proposé · source, soumis à confirmation | À chaque correction proposée |
| **Rapport de readiness** | Fichier/artifact **HTML** : jauge de score avant/après, compte à rebours, plan d'action | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli sur les tableaux |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : le mur du 01/09/2026 → audit et score → correction en live (registre public → aperçu → confirmation) → score après / plan d'action. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Vérification périodique (« re-scanne mon fichier clients chaque mois ») | Faible | Le score se dégrade à chaque nouveau client incomplet |
| Contrôle de validité des n° de TVA intracom européens | Moyen | Service public VIES — même logique « API publique sans clé » |
| Extension fournisseurs : audit des fiches côté achats | Moyen | Réutilise le moteur de scoring tel quel |
| Modules pays (DE XRechnung · IT SdI · ES Verifactu…) | Moyen | Qonto est paneuropéen ; v1 = France + détection du pays |

## 🛡 Garde-fous

- **Audit ≠ conseil juridique ou fiscal** — annoncé dans chaque rapport ; cas limites → expert-comptable
- Le **choix de la PDP appartient à l'utilisateur** : critères fournis, décision jamais prise à sa place
- Homonymes du registre → confirmation systématique ; TVA dérivée → marquée comme telle
- `update_client` : aperçu complet + confirmation explicite, champ par champ, **jamais en masse silencieux** ; échec = annoncé, jamais présenté comme réussi
- Tous les exemples des rapports sont inventés et le disent ; pagination ≤ 50 partout
- Compte vide, pays ≠ FR, registre indisponible → dégradation propre, jamais de données ou d'échéances inventées

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-einvoice-ready.fr.html` · `docs/doc-qonto-einvoice-ready.fr.docx`.*
