# 💸 qonto-reimburse-batch — N remboursements, une seule approbation

> **Hackathon Qonto × Anthropic MCP (10-13/07/2026)** · Agent Skill pour le MCP Qonto
> Chaque demande est vérifiée (justificatif · doublon carte · politique de frais) avant d'entrer dans **une seule demande de virement groupée** — approuvée d'un geste en SCA. *Tous les exemples de cette doc sont inventés.*

---

## 🎯 Le pitch

Les salariés avancent les frais — resto client, taxi, petit matériel — et le remboursement traîne des semaines dans un tableur. Personne n'aime relancer, personne n'aime vérifier. `qonto-reimburse-batch` fait les deux :

1. **Collecte des demandes** — depuis un canal Slack `#notes-de-frais` ou une base Notion (si le MCP est présent), sinon collées dans la conversation ou en tableau markdown : le cœur reste 100 % Qonto
2. **Trois contrôles par demande** — justificatif présent et cohérent (montant/date) · pas un doublon d'une dépense carte entreprise déjà passée (`list_transactions`, transaction citée) ni d'un remboursement déjà fait · politique de frais respectée (plafonds par catégorie définis par toi)
3. **UNE demande groupée** — les N demandes validées deviennent une seule `create_multi_transfer_request` : N virements en attente, IBAN fournis par les demandes (jamais inventés)
4. **Approbation SCA d'un geste** — le dirigeant reçoit une notification push et approuve tout le lot avec sa 2FA dans l'app Qonto ; l'argent ne bouge **que** là

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord) | ✅ |
| Pays | **Universel (SEPA)** : les remboursements sont des virements SEPA en EUR — tous les pays Qonto (FR, DE, ES, IT, AT, NL, BE, PT). IBAN hors SEPA ou devise ≠ EUR → demande mise en attente, annoncé clairement | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| IBAN des salariés | Fournis par les demandes ou une fiche salariés tenue par toi — le skill n'invente **jamais** un IBAN ; sans IBAN la demande reste en attente | ✅ |
| Politique de frais | Plafonds par catégorie (repas, taxi, matériel…) définis une fois par toi ; sans politique le skill l'annonce et fait les autres contrôles | ⭕ recommandé |
| Slack ou Notion (MCP) | Source des demandes, détectée dynamiquement ; sinon **mode dégradé** : demandes collées dans la conversation | ⭕ optionnel |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Collecte des demandes** : Slack (`#notes-de-frais`) ou Notion si le MCP est présent, sinon collage dans la conversation. Chaque demande est normalisée : salarié, montant, date, catégorie, motif, IBAN, justificatif — le tableau normalisé est affiché avant tout contrôle
2. **Contrôle des justificatifs** : présent + montant et date cohérents avec la demande ; manquant ou incohérent → ⚠️ en attente, jamais corrigé ni écarté en silence
3. **Chasse aux doublons** : `list_transactions` scanne les dépenses carte autour de la date (**`emitted_at` ±5 j** — les cartes se règlent avec 1-2 j de décalage) : même montant, tiers proche du motif → ❌ **présomption documentée**, transaction citée (date · montant · tiers). Le skill vérifie aussi qu'un remboursement identique n'est pas déjà parti (virements sortants récents)
4. **Politique de frais** : chaque demande comparée aux plafonds ; dépassement → signalé avec l'écart, trois issues : plafonner, accepter, rejeter — c'est toi qui tranches
5. **Demande groupée** (uniquement avec consentement explicite sur la liste finale) : UNE `create_multi_transfer_request` — un virement par salarié, référence lisible « NDF 2026-07 — motif », résumé du lot dans la note (visible à l'approbation)
6. **Approbation SCA** : push Qonto → le dirigeant approuve les N virements **d'un seul geste** avec sa 2FA → rapport final : qui est remboursé, combien, et pourquoi telle demande a été écartée (preuve jointe)

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de sécurité** : le trait plein (lecture) ne présente aucun risque ; le trait pointillé (écriture) exige le consentement explicite donné dans la conversation, et ne produit qu'une *demande* — c'est la SCA (2FA) du titulaire, dans l'app Qonto, qui déplace l'argent. Ni Claude ni le MCP ne le peuvent. **C'est le modèle de sécurité, pas une limitation.**

## 🔍 Les trois contrôles (le cœur du skill)

| Contrôle | Source | Issue possible |
|---|---|---|
| **Justificatif** | Pièce/référence jointe à la demande — montant et date confrontés à la demande | ✅ cohérent · ⚠️ manquant ou incohérent → en attente, motif précis affiché |
| **Doublon** | `list_transactions` (dépenses carte, `emitted_at` ±5 j, même montant, tiers proche) + virements de remboursement récents | ❌ présomption **documentée** (transaction citée) → hors du lot, tu tranches |
| **Politique de frais** | Plafonds par catégorie définis par toi | ⚠️ dépassement signalé avec l'écart → plafonner / accepter / rejeter |

### Exemple de tableau de verdicts (données inventées)

| Demande | Montant | Contrôles | Verdict |
|---|---|---|---|
| Repas client | 84,00 € | justificatif ✓ · pas de doublon · sous plafond | ✅ dans le lot |
| Taxi aéroport | 32,50 € | justificatif ✓ · pas de doublon · sous plafond | ✅ dans le lot |
| Écran portable | 129,00 € | **déjà réglé par carte entreprise le 03/06** (transaction citée) | ❌ rejeté — preuve fournie |

Résultat : **une** demande groupée de 2 virements dans l'app Qonto, prête à approuver d'un seul geste.

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : verdicts (demande · contrôles · verdict), contenu du lot, mises en attente | **Toujours** — c'est la base |
| **Demande groupée Qonto** | N virements en attente dans la section Demandes, résumé du lot dans la note (visible à l'approbation SCA) | À chaque lot validé |
| **Rapport de remboursement** | Récap markdown — ou artifact HTML si l'hôte affiche les fichiers ; repli automatique sur les tableaux | Après approbation (statut vérifié via `list_requests`) |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : problème → collecte & contrôles → verdicts (1 doublon rejeté avec preuve) → **approbation groupée SCA filmée sur téléphone** → rapport final. Le script détaillé (textes à dire, checklist tournage) est dans **`_SCRIPT-VIDEO.md`** — fichier interne, **exclu de la PR**.

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Verdict posté dans le thread Slack de chaque demande | Faible | Multi-MCP optionnel — s'active si le MCP Slack est présent |
| Rapprochement post-exécution (pointage des virements passés) | Faible | Réutilise `list_transactions` + les références « NDF » |
| OCR des justificatifs joints (montant/date extraits automatiquement) | Moyen | Renforce le contrôle n°1 sur données sales |
| Plafonds par équipe via `list_teams` | Faible | Politiques différenciées commercial / tech / direction |
| Export comptable mensuel des remboursements | Moyen | Se combine avec `qonto-accountant-handoff` |

## 🛡 Garde-fous

- **Jamais** de demande de virement sans confirmation explicite de la liste finale dans la conversation en cours ; jamais présentée comme exécutée (elle est en attente de SCA)
- Un doublon est une **présomption documentée** (transaction citée), jamais un rejet silencieux — c'est toi qui tranches
- Aucune demande recalée n'entre dans le lot sans ton override explicite (consigné dans la note)
- IBAN jamais inventés ; masqués (4 derniers chiffres) dans les rapports ; pagination ≤ 50 partout
- Répétitions : `decline_request` après chaque test (`request_type: "multi_transfers"`, pluriel)
- Sans Slack/Notion : le skill le dit une fois et continue en mode conversation

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-reimburse-batch.fr.html`.*
