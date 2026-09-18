# 🔎 qonto-grant-scout — Le chasseur de subventions

> **Skill #15 · le pari créativité** · Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> NOUVEAU — le croisement Datagouv dépend de la disponibilité réelle des référentiels publics : les docs sont volontairement honnêtes sur cette limite (voir « Honnêteté structurelle »)

---

## 🎯 Le pitch

La France compte des centaines de dispositifs d'aides aux entreprises — OPCO, ADEME, Bpifrance, France Num, régions… — et la plupart des TPE n'en touchent aucun, faute de temps pour chercher. Or **ton compte raconte déjà ce que tu investis**. `qonto-grant-scout` fait les présentations :

1. **Profil réel de l'entreprise** — secteur (NAF si présent, sinon inféré des flux), localisation, taille (volume d'encaissements), ancienneté : tout vient de `get_organization` et des transactions, zéro formulaire
2. **Structure de dépenses réelle** — 12-24 mois de flux classés : formation, matériel, numérique, embauche, international, énergie — chaque poste chiffré en €/an avec ses preuves
3. **Croisement avec les référentiels publics** — via le MCP Datagouv (optionnel, détecté dynamiquement) : recherche dans les datasets d'aides, **date de mise à jour vérifiée pour chaque source**
4. **Shortlist honnête** — chaque piste : ce qu'elle couvre, pourquoi ton compte y correspond, les critères à confirmer, la source datée, la prochaine étape concrète. Jamais « tu es éligible » — toujours « piste à vérifier »

Exemple type : « tu dépenses 800 €/mois en formation → ces dispositifs OPCO/FNE existent, voilà le lien et quoi demander » · « tu investis en matériel — cette aide régionale couvre une partie, critères à vérifier ici ».

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Croisement dispositifs : France uniquement** (les aides sont nationales/régionales). Autres pays Qonto (DE, ES, IT…) : profil de dépenses seul, familles d'aides génériques, jamais de dispositif étranger inventé | ℹ️ détecté |
| MCP Qonto connecté | Connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| MCP Datagouv | Connecteur data.gouv.fr — c'est lui qui ouvre la recherche dans les référentiels d'aides. Absent : le skill le dit et livre profil + familles d'aides + portails officiels | ⭕ recommandé — sinon mode dégradé assumé |
| Historique ≥ 12 mois | En dessous, les signaux de dépenses sont fragiles — le skill le dit (tags 🟡) | ⭕ |
| Labels Qonto tenus | Améliorent le classement des dépenses (`list_labels`) ; sinon classement par contreparties | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Profil réel** : forme juridique, secteur (NAF si présent — sinon inféré des flux, et annoncé comme tel), région, ancienneté, taille. Le profil est montré à l'utilisateur, qui peut le corriger avant toute recherche
2. **Lecture des flux** (12-24 mois, paginé ≤ 50) : débits classés en catégories « aidables » — formation, matériel/CAPEX, numérique, R&D-like, embauche, international, énergie. Labels utilisés si disponibles (`list_cash_flow_categories` → 403 sur le connecteur claude.ai, les labels sont le repli). Cartes rapprochées par `emitted_at`
3. **Signaux « aidables »** : chaque poste significatif devient un signal chiffré et daté — 9 600 €/an de formation, un achat matériel, une masse salariale qui monte, des clients à l'export
4. **Recherche Datagouv** : `search_datasets` sur les référentiels d'aides (base nationale des aides aux entreprises, ADEME, France Num, Bpifrance, régions), `get_dataset_info` pour **la date de chaque dataset**, `query_resource_data` pour filtrer par région/secteur/famille
5. **Croisement & shortlist** : signaux × dispositifs, chaque piste avec critères à confirmer + source datée + prochaine étape (OPCO, portail ADEME, guichet région, conseiller Bpifrance)
6. **Rapport honnête** : shortlist classée par plausibilité, tags 🟢🟡🔵, paragraphe des limites (ce qui a été cherché, ce qui n'a pas été trouvé, les datasets trop vieux)

## 🧪 Honnêteté structurelle (le cœur de la crédibilité)

C'est le skill le plus créatif du portefeuille — et celui dont l'exécution dépend le plus de données qu'on ne contrôle pas. Les règles :

- Les référentiels d'aides sur data.gouv.fr sont **hétérogènes et parfois datés** → chaque piste porte sa source ET la date de mise à jour du dataset ; un dataset > 18 mois = tag dégradé
- Le skill dit « **piste à vérifier** », jamais « tu es éligible » — les dispositifs ouvrent, ferment, changent de critères
- Ressource non interrogeable (PDF, CSV cassé) → la piste devient un lien sourcé vers la page du dataset, annoncé comme tel
- MCP Datagouv absent ou en erreur → profil de dépenses + familles d'aides génériques + les bons portails : aides-entreprises.fr, bpifrance.fr, france-num.gouv.fr, le site économique de la région
- Secteur absent de `get_organization` → inféré des flux, confiance abaissée, l'utilisateur peut corriger

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Zéro écriture** : le skill ne touche à rien — ni virement, ni facture, ni dossier déposé. Et côté données : seuls des **mots-clés génériques** (secteur, région, famille d'aide) partent vers Datagouv — jamais un montant, un nom de contrepartie ou un IBAN. Les flux bancaires restent entre Qonto et Claude.

## 🗂 Dépenses détectées → familles d'aides (table de correspondance)

| Dépense vue dans les flux | Famille d'aides | Exemples de dispositifs (à vérifier à la source) | Prochaine étape type |
|---|---|---|---|
| Formation (organismes, e-learning, certifs) | Financement de la formation | Prise en charge OPCO, FNE-Formation | Demander à son OPCO la prise en charge au titre du plan de développement des compétences |
| Matériel / équipement | Aides régionales à l'investissement | Dispositifs des conseils régionaux | Vérifier le dispositif de sa région (guichet éco régional) |
| Numérique (logiciels, SaaS, site) | Transformation numérique | France Num, chèques numériques régionaux | Passer par un activateur France Num |
| Dépenses R&D-like (prototypage, sous-traitance technique) | Fiscalité incitative | CIR / CII, statut JEI | À instruire avec l'expert-comptable |
| Embauche / alternance | Aides à l'embauche | Aides à l'alternance, dispositifs Pôle emploi/France Travail | Simuler sur les portails officiels avant tout recrutement |
| Énergie / véhicules / travaux | Transition écologique | ADEME (Tremplin PME), CEE | Déposer sur le portail ADEME agirpourlatransition |
| Export / clients étrangers | International | Bpifrance Assurance Prospection, Team France Export | Contacter le conseiller export de sa région |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : le problème (des aides que personne ne va chercher) → le profil qui sort tout seul des flux → la recherche Datagouv sourcée et datée → **le croisement magique** (9 600 €/an de formation détectés → le dispositif exact, le lien, quoi demander à l'OPCO) → l'honnêteté par design. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : profil + signaux, shortlist d'aides sourcées et datées, limites | **Toujours** — c'est la base |
| **Grant radar** | Fichier/artifact **HTML** : signaux × familles d'aides, pistes aux intersections, tags 🟢🟡🔵 | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur les tableaux |
| **Fiche par piste** | Bloc texte prêt à envoyer (à l'OPCO, au comptable, au guichet région) : signal, dispositif, critères à confirmer, source | Sur demande, pour chaque piste retenue |

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Veille périodique : re-croiser chaque trimestre et n'alerter que sur les nouvelles pistes | Faible | Réutilise le profil déjà construit |
| Enrichissement Aides-territoires (API dédiée) | Moyen | Source plus fraîche que certains datasets — même logique de datation |
| Dossier pré-rempli : générer le courriel type vers l'OPCO/le guichet avec les chiffres du compte | Faible | Toujours zéro écriture — c'est l'utilisateur qui envoie |
| Modules pays (DE : KfW · ES : ENISA · IT : Invitalia…) | Élevé | Qonto est paneuropéen ; v1 = France + détection du pays |

## 🛡 Garde-fous

- **Zéro écriture** ; seuls des mots-clés génériques partent vers Datagouv — jamais de montants, de noms ou d'IBAN
- **Jamais « tu es éligible »** — chaque piste est datée, sourcée, et formulée « à vérifier » ; confirmation recommandée auprès de l'organisme émetteur ou de l'expert-comptable
- Dégradation honnête : MCP Datagouv absent, compte vide, secteur indétectable, pays ≠ FR → le skill dit ce qu'il peut et ne peut pas faire, n'invente ni dispositif, ni montant, ni échéance
- IBAN masqués (4 derniers chiffres) ; pagination ≤ 50 partout

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-grant-scout.fr.html` · `docs/doc-qonto-grant-scout.fr.docx`.*
