# 🤝 qonto-crm-truth — Le CRM qui ne ment plus

> **Hackathon Qonto × Anthropic MCP (10-13/07/2026)** · Agent Skill pour le MCP Qonto
> La banque comme source de vérité : deals « gagnés » jamais encaissés, CA réel, score payeur A/B/C — écrits dans le CRM, toujours après confirmation.

---

## 🎯 Le pitch

Dans le CRM, un deal « Closed Won » ressemble à du chiffre d'affaires. Tant que l'argent n'est pas sur le compte, **c'est une fiction**. `qonto-crm-truth` réconcilie les fiches CRM (HubSpot **ou** Airtable) avec la vérité bancaire Qonto :

1. **Deals « won » jamais encaissés** — chaque deal gagné sans un euro correspondant sur le compte, listé avec montant et ancienneté
2. **CA réel, LTV & délais constatés** — le chiffre encaissé (pas déclaré), la LTV cash, le délai moyen de paiement observé (« paie à J+X »), la date du dernier encaissement
3. **Score de fiabilité payeur A/B/C** — calculé depuis la banque, formule affichée, jamais de score inventé (moins de 2 factures payées → « non noté »)
4. **Écriture dans le CRM** — propriétés custom HubSpot ou colonnes Airtable, après un rapprochement fiche CRM ↔ client Qonto **toujours montré et confirmé**, jamais silencieux

Résultat : les commerciaux priorisent les clients **qui paient vraiment**.

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Universel** — aucune règle fiscale locale : fonctionne à l'identique pour tous les pays Qonto (FR, DE, ES, IT, AT, NL, BE, PT) | ℹ️ détecté |
| MCP Qonto connecté | Connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| MCP HubSpot **ou** Airtable | Le CRM — requis pour l'écriture. Sans lui : mode dégradé, rapport « clients Qonto scorés » dans la conversation (déjà utile) | ⭕ requis pour écrire |
| Factures clients dans Qonto | Ancrent les délais de paiement et le matching. Sans elles : analyse par contrepartie des crédits, annoncée comme telle | ⭕ recommandé |
| Historique ≥ 6 mois | En dessous, dégradation honnête (scores « non noté », avertissement) | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Vérité bancaire d'abord** (24 mois, paginé ≤ 50) : crédits par compte, clients Qonto, factures clients avec statuts — chaque encaissement rattaché à son client, graphies multiples normalisées et fusionnées (casse, accents, suffixes SARL/SAS/GmbH), avoirs déduits
2. **Métriques par client** : CA réellement encaissé, LTV cash, délai moyen constaté (médiane et moyenne de J+X), date du dernier encaissement, score payeur A/B/C — **depuis la banque, jamais depuis le CRM**
3. **Lecture du CRM** (détecté dynamiquement) : deals « won », montants, fiches sociétés — HubSpot ou Airtable (`search_bases` → `get_table_schema` → lecture). Aucun CRM ? Le skill le dit et livre le rapport scoré en conversation
4. **Rapprochement assisté** — LE garde-fou : paires fiche CRM ↔ client Qonto proposées sur nom normalisé / email / SIREN-TVA, tableau de correspondance **toujours montré et confirmé** avant toute suite ; les ambigus, le skill demande, il ne choisit jamais seul
5. **Fiction vs réalité** : deals gagnés jamais encaissés, top client CRM vs top payeur réel, retardataires chroniques — chaque écart chiffré, les impayés découverts prêts pour `qonto-invoice-chaser`
6. **Écriture dans le CRM** (uniquement après aperçu champ par champ + go explicite) : `create_field` puis `update_records_for_table` côté Airtable, propriétés custom côté HubSpot — champs dédiés au skill, jamais d'écrasement des champs natifs

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de sécurité** : côté Qonto, le skill est en **lecture pure** — zéro écriture bancaire, rien à approuver, rien à risquer. Les seules écritures visent le CRM, et elles passent deux verrous : le rapprochement confirmé (jamais de matching silencieux) puis l'aperçu exact de ce qui sera écrit, validé explicitement dans la conversation.

## 🅰️ Le score payeur (formule affichée, jamais boîte noire)

| Score | Définition |
|---|---|
| **A** | Règlement médian dans les 5 jours après l'échéance, aucun impayé en cours |
| **B** | Paie toujours, mais en retard — retard médian ≤ 30 jours après échéance |
| **C** | Retard médian > 30 jours, ou facture impayée > 60 jours, ou deal « won » jamais encaissé |
| **—** | Moins de 2 factures payées → **non noté** (jamais de score deviné) |

⚠️ Le score décrit le **comportement de paiement observé sur ce compte** — pas une solvabilité générale ; rappelé dans chaque rapport.

## ✍️ Ce que le skill écrit dans le CRM (champs dédiés)

| Champ | Contenu | Exemple (inventé) |
|---|---|---|
| CA réel (banque) | Cash encaissé sur la période | 24 300 € |
| LTV (banque) | Cash encaissé depuis toujours | 61 750 € |
| Délai moyen constaté | Médiane de J+X (émission → encaissement) | J+38 |
| Score payeur | A / B / C / non noté | C |
| Dernier encaissement | Date du dernier crédit rattaché | 12/05/2026 |
| Deals won non encaissés | Drapeau + montant cumulé | ⚠️ 2 deals · 9 800 € |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : le mensonge du CRM → vérité bancaire & matching confirmé → scores et écarts → **l'écriture dans le CRM après confirmation** → mode dégradé sans CRM. Le script détaillé (textes à dire, checklist tournage) est dans **`_SCRIPT-VIDEO.md`** — fichier interne, **exclu de la PR**.

## 📤 Formats de sortie (où atterrit la vérité ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : clients scorés, deals non encaissés, tableau de correspondance, bilan d'écriture | **Toujours** — c'est la base |
| **Écriture CRM** | Propriétés custom HubSpot / colonnes Airtable (champs dédiés) | Après matching confirmé + go explicite |
| **One-pager HTML** | Classement CRM vs classement banque côte à côte, distribution des scores | Si l'hôte affiche les fichiers ; sinon repli automatique sur les tableaux |

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Relance automatique des deals non encaissés via `qonto-invoice-chaser` | Faible | Cross-skill naturel — l'un découvre, l'autre agit |
| Score payeur dans les devis (`list_quotes`) : alerter avant de signer un C | Moyen | La vérité au moment où elle sert le plus |
| Historique du score (colonne datée) pour voir les clients qui se dégradent | Faible | Une écriture de plus, même garde-fou |
| Support d'autres CRM (Notion, Salesforce…) via détection dynamique | Moyen | Même logique : lire, matcher, confirmer, écrire |

## 🛡 Garde-fous

- **Zéro écriture Qonto** — lecture pure côté banque ; les seules écritures visent le CRM
- **Jamais** d'écriture CRM sans (a) tableau de correspondance confirmé et (b) go explicite sur un aperçu exact ; jamais présentée comme faite si elle a échoué ou été partielle
- Rapprochement assisté, **jamais silencieux** : les paires ambiguës sont posées comme questions
- Dégradation honnête : < 2 factures payées → non noté ; pas de factures → analyse par contrepartie ; pas de CRM → rapport en conversation
- IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout · répétitions sur base Airtable dupliquée ou champs de test (les écritures CRM sont réelles)

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-crm-truth.fr.html` · `docs/doc-qonto-crm-truth.fr.docx`.*
