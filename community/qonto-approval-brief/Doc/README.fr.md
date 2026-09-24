# 🗂 qonto-approval-brief — Instruire chaque demande comme un DAF, avant d'approuver

> **Hackathon Qonto × Anthropic MCP** · Agent Skill pour le MCP Qonto
> Lecture massive, une seule écriture (`decline_request`, toujours confirmée) — **le skill ne peut pas approuver : l'approbation reste dans l'app Qonto, sous ta SCA. Par conception.**

---

## 🎯 Le pitch

Les demandes de virement et de carte de l'équipe s'empilent dans Qonto — et le dirigeant approuve à l'aveugle, ou avec trois jours de retard. Chaque demande mériterait cinq minutes de fouille ; personne ne les a. `qonto-approval-brief` fait le travail d'instruction d'un DAF sur chaque demande en attente :

1. **Historique du bénéficiaire** — déjà payé N fois ? montants habituels ? cadence ? Un 3e paiement identique ne se juge pas comme un premier virement
2. **Signal IBAN** — IBAN déjà vu dans l'historique (rassurant, daté) ou jamais vu (**signal de vigilance, pas une accusation**)
3. **Cohérence & contexte** — montant vs habitude (×4 → alerte forte), budget/label, devis retrouvé dans Gmail si le MCP est connecté
4. **Brief de décision par demande** — ✅ recommandé / 🔶 à vérifier, chaque affirmation avec sa preuve ; refus motivé via MCP (confirmé), **approbations dans l'app Qonto avec ta 2FA**

Exemples de lignes de brief (inventés) : « ✅ recommandé : 3e paiement identique à ce prestataire » · « 🔶 vérifier : IBAN jamais vu, montant ×4 l'habitude ».

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Universel** — l'instruction repose sur l'historique du compte, pas sur des règles nationales ; fonctionne pour tous les pays Qonto (FR, DE, ES, IT…) | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Rôle avec revue des demandes | Owner/Admin/Manager : les demandes en attente doivent être visibles — sinon `list_requests` revient vide et le skill dit pourquoi | ✅ |
| Des demandes en attente | Sinon rien à instruire — le skill le dit et s'arrête proprement | ⭕ |
| Historique ≥ quelques mois | En dessous, tout bénéficiaire paraît « nouveau » — le skill l'annonce et dégrade honnêtement | ⭕ |
| Slack · Gmail (MCP optionnels) | Digest et contexte email — détectés dynamiquement, jamais requis | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Inventaire des demandes** : `get_organization` puis `list_requests` (paginé ≤ 50) — virements, virements groupés, cartes — avec demandeur (`list_memberships`), bénéficiaire, montant, motif, date
2. **Historique du bénéficiaire** : `list_transactions` sur 12-24 mois, graphies du tiers normalisées et fusionnées — déjà payé N fois ? montants ? cadence ?
3. **Signal IBAN** : IBAN de la demande comparé aux IBAN des virements passés — déjà vu (daté) ou jamais vu (vigilance, pas accusation ; vérification directe recommandée, par téléphone, pas en répondant au mail de la facture)
4. **Cohérence & contexte** : montant vs médiane historique (×2 alerte, ×4 forte), doublon récent cité, labels/équipe (`list_labels`), devis Gmail cité si le MCP est présent — sinon le skill le dit et continue
5. **Brief de décision** : un par demande, ✅ recommandé / 🔶 à vérifier, chaque affirmation sourcée — recommandation ≠ décision, c'est toi qui tranches
6. **Refus motivé · approbation SCA** : refus via `decline_request` (confirmé, motif joint, visible par le demandeur) ; **les approbations se font dans l'app Qonto, avec ta 2FA — le skill ne peut pas approuver**

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de sécurité** : le trait plein (lecture) ne présente aucun risque ; le trait pointillé (écriture) est un **refus motivé uniquement**, exigé confirmé dans la conversation. L'approbation n'existe pas dans ce skill : `approve_request` n'est **jamais** appelé. Approuver = app Qonto + ta SCA (2FA). Rien de ce que fait ce skill ne peut déplacer un euro — **c'est le modèle de sécurité, pas une limitation.**

## 🔍 Les signaux du brief

| Signal | Vérifié comment | Lecture |
|---|---|---|
| Bénéficiaire connu | `list_transactions` 12-24 mois, graphies normalisées : N paiements, montants, cadence | ✅ rassurant si stable et daté |
| IBAN jamais vu | Comparé aux IBAN des virements sortants passés | 🔶 vigilance, pas accusation — un nouveau fournisseur est normal, une fois |
| Montant inhabituel | Ratio vs médiane historique du même bénéficiaire | 🔶 ×2 signalé, ×4 alerte forte, les deux chiffres affichés |
| Doublon possible | Même bénéficiaire + même montant payé dans les ~10 derniers jours | 🔶 transaction citée (date, montant) |
| Cohérence budget/label | `list_labels` + équipe du demandeur | ℹ️ signal doux, jamais décisif seul |
| Contexte email | Devis/échange retrouvé dans Gmail (si MCP connecté) | ℹ️ cité dans le brief (objet, date) |
| Demande de carte | Pas d'IBAN : plafonds demandés vs dépenses carte habituelles de l'équipe | ℹ️ instruction adaptée |

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableau des briefs + brief détaillé par demande 🔶 + prochaine étape explicite | **Toujours** — c'est la base |
| **Tableau de bord des briefs** | Fichier/artifact **HTML** : une carte par demande, verdict et preuves | Si l'hôte affiche les fichiers ; repli automatique sur les tableaux |
| **Motif de refus** | Texte joint au refus via `decline_request`, visible par le demandeur dans Qonto | À chaque refus (confirmé) |
| **Digest Slack** | Résumé des briefs posté sur le canal choisi | Si le MCP Slack est connecté (optionnel) |

## ⚡ Le moment « it just works »

4 demandes en attente → **4 briefs sourcés en 30 secondes** ; je refuse la douteuse en un mot, j'approuve les 3 autres dans l'app en 20 secondes — au lieu de 20 minutes de fouille. (Exemple inventé.)

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : la pile de demandes → les briefs sourcés → la demande douteuse (IBAN jamais vu, ×4) refusée en un mot → **les approbations dans l'app, sous SCA, filmées sur téléphone** → wrap-up. Le script détaillé (textes à dire, checklist tournage) est dans **`_SCRIPT-VIDEO.md`** — fichier interne, **exclu de la PR**.

## 🤝 Skills compagnons

- **qonto-fraud-sentinel** — surveille les transactions *passées* ; `qonto-approval-brief` instruit les demandes *futures* : les deux faces de la même vigilance
- **qonto-reimburse-batch** — *crée* des demandes groupées de remboursement ; ce skill les *instruit* ensuite, comme n'importe quelle demande en attente

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Politique d'approbation apprise (seuils par catégorie/label) | Moyen | Les briefs deviennent « conforme / hors politique » |
| Rapprochement facture fournisseur (`list_supplier_invoices`) | Faible | La demande adossée à sa facture = preuve de plus dans le brief |
| Digest quotidien planifié sur Slack | Faible | Multi-MCP optionnel, détecté dynamiquement |
| Mémoire des vérifications passées | Moyen | Un IBAN vérifié une fois avec le demandeur devient « connu » |

## 🛡 Garde-fous

- **Recommandation ≠ décision** : chaque brief cite ses preuves ; le skill ne dit jamais « approuvé » ni « sûr », il dit « recommandé, parce que… »
- **Jamais** de refus sans confirmation explicite dans la conversation en cours ; le motif accompagne toujours le refus (le demandeur le voit)
- « IBAN jamais vu » = **signal, pas accusation** — formulé ainsi dans chaque brief
- Le skill **n'approuve jamais** : `approve_request` n'est pas utilisé — approuver = app Qonto + ta SCA
- IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout · historique court annoncé · exemples inventés et signalés comme tels

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-approval-brief.fr.html` · `docs/doc-qonto-approval-brief.fr.docx`.*
