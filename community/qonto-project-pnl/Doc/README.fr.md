# 📓 qonto-project-pnl — La doc projet raconte enfin la vérité économique

> **Hackathon Qonto × Anthropic MCP (10-13/07/2026)** · Agent Skill pour le MCP Qonto + connecteur Notion
> Qonto en lecture seule · l'unique écriture vit dans Notion, dans une base dédiée, toujours prévisualisée et confirmée

---

## 🎯 Le pitch

Les studios, agences et indie hackers pilotent leurs projets dans Notion : la doc est belle, les specs sont à jour… mais **la rentabilité par projet reste un mystère**. Les revenus sont à la banque, les coûts aussi — et la doc n'en sait rien. `qonto-project-pnl` referme la boucle :

1. **Revenus réels** — uniquement l'argent encaissé : factures clients payées, rapprochées des virements entrants (matching montré et confirmé), rattachées à leur projet
2. **Coûts attribués** — labels Qonto ↔ projets (mapping confirmé puis mémorisé), remboursements déduits, scan 24-36 mois pour attraper les renouvellements annuels
3. **Marge & burn mensuel** — par projet : marge en € et en %, burn moyen des 3 derniers mois, tags de confiance 🟢🟡
4. **Le P&L vit dans Notion** — une base « Finance » dédiée, une entrée par projet, **mise à jour à chaque exécution** (idempotent : relance = mise à jour, jamais de doublon), avec alertes ⚠️ facture en retard · coût inhabituel · marge négative

## 🆚 Ne pas confondre : `qonto-project-burn` vs `qonto-project-pnl`

| | `qonto-project-burn` | `qonto-project-pnl` (ce skill) |
|---|---|---|
| La question | « On tient le budget ? » | « Ce projet gagne-t-il de l'argent ? » |
| Périmètre | **Coûts** vs budget déclaré, date de dépassement projetée | **Revenus ET coûts** → marge, burn |
| Destination | Linear / Jira — l'équipe produit | Notion — la doc projet |
| Alertes | Seuils budget (80 % / 100 %) | Facture en retard, coût inhabituel, marge négative |

Les deux se complètent ; pour la vue **entreprise** (runway, cockpit tous coûts), voir `qonto-ceo-cockpit`.

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Universel** — labels + factures + transactions, aucune règle fiscale : tous les pays Qonto (FR, DE, ES, IT, AT, NL, BE, PT) à l'identique | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Connecteur **Notion** | Le connecteur officiel — requis pour l'écriture de la base Finance. Sans lui : mode dégradé propre (P&L en tableaux dans la conversation + dashboard HTML) | ⭕ recommandé |
| Labels Qonto par projet | La dimension « projet » du compte. Sans labels : mapping proposé depuis les tiers récurrents, tout en 🟡 | ⭕ recommandé |
| Factures clients dans Qonto | Pour les revenus encaissés et les alertes de retard. Sans : repli sur les crédits labellisés (🟡) | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Lecture du compte** : `get_organization` puis `list_labels` (paginé ≤ 50) — l'arborescence de labels est la liste des projets candidats. `list_cash_flow_categories` n'est jamais appelé (403 sur le connecteur claude.ai)
2. **Mapping label ↔ projet** : tableau proposé (label → projet → page Notion → clients), **toujours montré et confirmé**, puis mémorisé en bloc prêt à coller — aux relances, seul ce qui change est reconfirmé
3. **Revenus encaissés** : factures payées rapprochées des transactions entrantes (montant + fenêtre de dates + tiers normalisé), matching confirmé sur les cas ambigus ; une facture émise non payée n'est **jamais** un revenu — passée l'échéance, elle devient une alerte ⚠️
4. **Coûts attribués + P&L** : débits groupés par label sur 24-36 mois (les renouvellements *annuels* ne se voient que là), remboursements déduits, orphelins listés à part — puis marge (€ et %), burn mensuel, alertes chiffrées
5. **Écriture Notion** (uniquement avec consentement explicite, après aperçu) : base dédiée « Finance — P&L (générée) », une entrée par projet, **mise à jour en place** aux relances — jamais de doublon, jamais d'écrasement du reste du workspace
6. **Rapport** : tableaux markdown dans la conversation (toujours) + dashboard HTML si l'hôte affiche les fichiers

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de sécurité** : côté Qonto, le skill est en **lecture seule — zéro écriture**, aucun risque. Le trait pointillé (écriture) vit côté Notion : il exige le consentement explicite donné dans la conversation, ne touche **que** la base dédiée marquée comme générée, et ne modifie jamais un contenu Notion existant. Aucun argent ne bouge, nulle part.

## 📓 La base « Finance » dans Notion (une entrée par projet)

| Propriété | Contenu | Exemple (inventé) |
|---|---|---|
| Projet | Nom du projet (clé de mise à jour idempotente) | Aurora |
| Revenus encaissés | Somme des factures payées rapprochées | 18 400 € |
| Coûts attribués | Débits labellisés, remboursements déduits | 7 150 € |
| Marge | € et % | 11 250 € · 61 % |
| Burn mensuel | Moyenne des 3 derniers mois pleins | 2 380 €/mois |
| Alertes | ⚠️ en clair, chiffrées | ⚠️ 1 facture en retard (INV-2026-042, J+12) |
| Période · Mise à jour | Fenêtre couverte · horodatage de la dernière exécution | 2024-08 → 2026-07 · il y a 1 min |

## 📤 Formats de sortie (où atterrit le P&L ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (P&L par projet, alertes, orphelins) | **Toujours** — c'est la base |
| **Base « Finance » dans Notion** | Base dédiée, une entrée par projet, mise à jour à chaque exécution | Si le connecteur Notion est présent + consentement explicite |
| **Dashboard interactif** | Fichier/artifact **HTML** : barres revenus vs coûts, badge de marge, burn, marqueurs d'alertes | Si l'hôte affiche les fichiers ; repli automatique sur les tableaux |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : le mystère de la rentabilité → mapping confirmé → P&L calculé → **la page projet Notion qui affiche « mise à jour il y a 1 min »** → relance idempotente. Le script détaillé (textes à dire, checklist tournage, notes de montage) est dans **`_SCRIPT-VIDEO.md`** — fichier interne, **exclu de la PR**.

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Historique mensuel par projet (une sous-table par entrée) | Moyen | La base Finance gagne une dimension temps |
| Devis en cours (`list_quotes`) en colonne « pipeline » | Faible | Revenus signés vs encaissés, sans jamais les confondre |
| Relance des factures en retard détectées | Faible | Passer la main à `qonto-invoice-chaser` |
| Taux horaire implicite (marge ÷ temps déclaré) | Moyen | Le temps resterait déclaratif — jamais inventé |

## 🛡 Garde-fous

- **Zéro écriture Qonto** ; l'unique écriture est la base Notion dédiée, marquée comme générée — après aperçu et « oui » explicite, jamais présentée comme faite si l'appel a échoué
- **Idempotence** : relance = mise à jour en place (clé : nom du projet), jamais de doublon, jamais de suppression
- Mapping label → projet et matching facture ↔ transaction **toujours montrés et corrigeables** — aucune attribution silencieuse
- Revenus = encaissé rapproché uniquement ; tout repli ou estimation porte un tag 🟡 ; aucun montant inventé
- IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout · dégradation honnête (pas de labels, pas de factures, pas de Notion, historique court)

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-project-pnl.fr.html` · `docs/doc-qonto-project-pnl.fr.docx`.*
