# 📊 qonto-project-burn — Ce que le projet X a *vraiment* coûté

> **Hackathon Qonto × Anthropic MCP (10-13/07/2026)** · Agent Skill pour le MCP Qonto
> Le pont finance ↔ équipe produit : le burn réel par projet, écrit là où l'équipe vit (Linear/Jira)

---

## 🎯 Le pitch

Les équipes pilotent dans Linear ou Jira ; la dépense, elle, vit dans Qonto. Résultat : **personne ne sait ce que le projet X a réellement coûté** — les SaaS dédiés, les freelances, les pubs, le matériel. `qonto-project-burn` referme ce fossé :

1. **Mapping labels ↔ projets** — une table de config simple, proposée depuis tes labels Qonto, corrigeable ligne par ligne, mémorisée dans la conversation ou le projet Claude
2. **Burn réel par projet vs budget déclaré** — jusqu'à 36 mois scannés (les renouvellements *annuels* de SaaS ne passent pas entre les mailles), avoirs déduits, transactions orphelines listées à part — jamais attribuées en douce
3. **Date de dépassement projetée** — rythme mensuel courant → « au rythme actuel, Alpha dépasse son budget le 12/08 », tags de confiance 🟢🟡
4. **Le statut écrit là où l'équipe vit** — avec ton accord : commentaire « X € / Y € — Z % » sur le projet Linear/Jira + issue d'alerte « ⚠️ Budget Alpha 87 % » si un seuil est franchi, avec les transactions Qonto qui la justifient

Côté Qonto : **lecture seule**. La seule écriture notable est côté Linear — toujours montrée avant envoi.

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Universel** — labels + transactions, aucune règle fiscale : tous les pays Qonto (FR, DE, ES, IT, AT, NL, BE, PT) | ℹ️ tous |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Labels Qonto | Quelques transactions labellisées par projet. Aucun label ? Le skill propose un mapping depuis les fournisseurs récurrents (tags 🟡) et explique comment labelliser dans l'app | ⭕ recommandé |
| MCP Linear ou Jira/Atlassian | Détecté dynamiquement — sinon **mode dégradé** : rapport complet par projet dans la conversation + dashboard HTML | ⭕ optionnel |
| Budgets déclarés | Fournis par toi dans le mapping (ou lus dans la description du projet Linear si formatés) — jamais inventés | ✅ à la config |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Lecture du compte** : `get_organization` d'abord (comptes, devise), puis `list_labels` — l'arborescence de labels devient la liste des projets candidats. ⚠️ Pas de `list_cash_flow_categories` (403 sur le connecteur claude.ai) : le mapping se fait sur les **labels**
2. **Mapping labels ↔ projets** : table label → projet → projet Linear/Jira (si MCP présent) → budget déclaré. Affichée, corrigeable, puis restituée en bloc à coller dans les instructions du projet Claude — mémorisée, jamais écrite dans Qonto
3. **Burn réel** : `list_transactions` paginé ≤ 50, 24-36 mois quand l'historique le permet (cadences annuelles), regroupement par label, avoirs déduits, `emitted_at` pour les cartes. Une transaction multi-labels compte **une fois**
4. **Budget vs rythme** : dépensé, % consommé, rythme mensuel (3 derniers mois pondérés), date de dépassement projetée. Seuils par défaut ⚠️ 80 % · 🔴 100 %
5. **Écriture côté équipe** (uniquement avec accord explicite) : commentaire de statut sur le projet Linear/Jira + issue d'alerte si seuil franchi — texte montré verbatim **avant** envoi
6. **Rapport** : tableau par projet ✅/⚠️/🔴, liste des orphelines, alertes, dashboard HTML si l'hôte affiche les fichiers

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de sécurité** : côté Qonto, tout est en lecture — aucun virement, aucun paiement, rien qui touche à l'argent. Le trait pointillé (écriture) part vers **Linear/Jira**, pas vers la banque : un commentaire ou une issue, toujours prévisualisés et confirmés dans la conversation. Le seul rangement optionnel côté Qonto (`modify_transaction_cash_flow_category` pour classer les orphelines) est léger, réversible et confirmé.

## 📊 Exemple de rapport (données inventées)

| Projet | Dépensé | Budget | % | Rythme/mois | Dépassement projeté | Statut |
|---|---|---|---|---|---|---|
| Alpha | 10 440 € | 12 000 € | 87 % | 1 950 €/mois | 12/08 | ⚠️ |
| Kepler | 3 100 € | 8 000 € | 39 % | 620 €/mois | — | ✅ |
| Odyssey | 21 500 € | 20 000 € | 108 % | 1 400 €/mois | dépassé | 🔴 |

*Exemple entièrement fictif — projets, montants et dates inventés pour la démonstration.*

## 📤 Formats de sortie (où atterrit le burn ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (burn par projet, orphelines, alertes) | **Toujours** — c'est la base |
| **Commentaire Linear/Jira** | « X € / Y € — Z % · dépassement estimé le [date] · top 5 lignes » sur le projet mappé | Si MCP tracker détecté + accord explicite |
| **Issue d'alerte Linear/Jira** | « ⚠️ Budget [projet] Z % » + les transactions Qonto qui la justifient | Si seuil franchi + accord explicite |
| **Dashboard interactif** | Fichier/artifact **HTML** : barres dépensé/budget, rythme, marqueurs de dépassement | Si l'hôte affiche les fichiers ; sinon repli sur les tableaux |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : problème → mapping → burn & date de dépassement → **l'issue « ⚠️ Budget Alpha 87 % » découverte dans Linear** → dashboard. Le script détaillé (textes à dire, checklist tournage) est dans **`_SCRIPT-VIDEO.md`** — fichier interne, **exclu de la PR**.

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Budget par sprint/cycle (pas seulement par projet) | Moyen | Réutilise le mapping, découpe par dates de cycle Linear |
| Refacturation client : croiser avec `list_client_invoices` (marge par projet) | Moyen | Burn − facturé = marge réelle du projet |
| Rappel hebdo automatique (statut posté chaque lundi) | Faible | Même écriture, déclenchée en rituel |
| Slack/Notion comme cibles alternatives de statut | Faible | Multi-MCP optionnel, détection dynamique |


## 🆚 Ne pas confondre : `qonto-project-burn` vs `qonto-project-pnl`

| | `qonto-project-burn` (ce skill) | `qonto-project-pnl` |
|---|---|---|
| La question | « On tient le budget ? » | « Ce projet gagne-t-il de l'argent ? » |
| Périmètre | **Coûts** vs budget déclaré, date de dépassement projetée | **Revenus ET coûts** → marge, burn |
| Destination | Linear / Jira — l'équipe produit | Notion — la doc projet |
| Alertes | Seuils budget (80 % / 100 %) | Facture en retard, coût inhabituel, marge négative |

## 🛡 Garde-fous

- **Jamais** d'écriture dans Linear/Jira sans prévisualisation du texte exact et confirmation explicite dans la conversation en cours ; jamais présentée comme faite si l'appel a échoué
- L'attribution label → projet est **toujours montrée et corrigeable** — aucune réattribution silencieuse
- Budgets = déclarés par toi ; dépenses = données Qonto ; le skill n'invente ni l'un ni l'autre
- `list_cash_flow_categories` → 403 sur le connecteur claude.ai : attendu, repli sur les labels
- IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout · dégradation honnête (pas de labels, historique court, pas de MCP tracker)

## 🔗 Skills liés

Pour la vue **entreprise** (runway, cockpit tous coûts confondus) : `qonto-ceo-cockpit`. Ici, c'est la granularité **projet** — la question « et Alpha, il en est où ? » posée le lundi matin.

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-project-burn.fr.html` · `docs/doc-qonto-project-burn.fr.docx`.*
