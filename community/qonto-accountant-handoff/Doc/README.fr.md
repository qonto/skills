# 🗂 qonto-accountant-handoff — La passation mensuelle au comptable, sans la corvée

> **Skill #19 · nouveau** · Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> **Zéro écriture Qonto** — les seules écritures sont hors Qonto : dépôt Google Drive + brouillon Gmail, jamais envoyé sans toi

---

## 🎯 Le pitch

Chaque mois, le même message : « tu peux m'envoyer les pièces de mars ? » — et une soirée à fouiller mails et téléchargements. `qonto-accountant-handoff` prépare le pack comptable complet depuis le compte Qonto :

1. **Relevés & factures réunis** — les relevés officiels de la période (`list_statements` / `get_statement`) + toutes les factures clients et fournisseurs, avec leur statut
2. **État des justificatifs** — chaque transaction croisée avec ses pièces : ✅ complète · ⚠️ manquante · ➖ sans objet, avec **la liste précise de ce qui manque** (date, tiers, montant)
3. **Transactions annotées, jamais imputées** — labels, TVA, notes factuelles (« ce remboursement correspond au paiement du 12/05 ») ; **aucune écriture comptable inventée** — le comptable reste le pro
4. **Lettre de passation + dépôt organisé** — le mois en 10 lignes, les 3 points d'attention, les questions en attente ; arborescence AAAA/MM sur Google Drive + brouillon d'email récap au cabinet via Gmail (si ces MCP sont présents)

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord) | ✅ |
| Pays | **Fonctionne pour tous les pays Qonto** — relevés, factures et justificatifs sont universels. Remarques fiscales locales (ex. TVA française) seulement si détectées, jamais de règle inventée | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Mois clos | Les relevés n'existent qu'une fois le mois terminé ; mois en cours → pack partiel, annoncé | ℹ️ |
| MCP Google Drive | Pour le dépôt en arborescence AAAA/MM — sinon pack local structuré (markdown + CSV) | ⭕ optionnel |
| MCP Gmail | Pour le brouillon d'email récap au cabinet — sinon la lettre reste dans le pack | ⭕ optionnel |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Cadrage de la période** : `get_organization` d'abord (comptes, pays), mois précédent par défaut (ou trimestre à la demande), détection des MCP Google Drive et Gmail — présents ou non, le skill le dit et continue
2. **Relevés** : `list_statements` puis `get_statement` par compte — les relevés officiels de la période ; un compte sans relevé est signalé, jamais masqué
3. **État des justificatifs** : `list_transactions` (pagination ≤ 50, délais carte `emitted_at` vs `settled_at` gérés en bord de mois) + `list_transaction_attachments` par transaction → ✅/⚠️/➖ et la liste précise des manquants ; suggestion : lancer **qonto-receipt-hunter** sur cette liste *avant* d'envoyer
4. **Annotations factuelles** : labels, `vat_amount` (le nombre de débits non renseignés est annoncé — la vue TVA est un plancher), notes utiles au comptable ; tout ce qui ressemble à une imputation devient une **question** dans la lettre
5. **Factures & lettre de passation** : factures clients et fournisseurs de la période avec statut, puis la lettre rédigée — le mois en 10 lignes, 2-3 points d'attention, questions en attente
6. **Dépôt & récap** : arborescence `Comptabilité/AAAA/MM/` sur Drive si le MCP est là (sinon pack local décrit fichier par fichier) + **brouillon** Gmail au cabinet — rien ne part sans toi

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé** : côté Qonto, tout est en lecture — aucun outil d'écriture n'est utilisé, il n'y a littéralement rien à approuver. Les deux seules « écritures » sont hors Qonto : un dossier déposé sur ton Google Drive (annoncé avant), et un **brouillon** d'email dans ta boîte Gmail — c'est toujours toi qui cliques sur envoyer.

## 🗂 Le contenu du pack

| Élément | Source MCP | Forme dans le pack |
|---|---|---|
| Lettre de passation | Rédigée par le skill (depuis les données lues) | `00-lettre-de-passation` — markdown + corps du brouillon Gmail |
| Relevés bancaires | `list_statements` + `get_statement` | `01-releves` — PDF officiels par compte |
| Factures clients | `list_client_invoices` | `02-factures-clients` — liste + statuts (payée / en attente) |
| Factures fournisseurs | `list_supplier_invoices` | `03-factures-fournisseurs` — liste + statuts |
| État des justificatifs | `list_transactions` + `list_transaction_attachments` | `04-justificatifs` — tableau de couverture + **liste des manquants** (CSV) |
| Transactions annotées | `list_transactions` (labels, TVA, notes factuelles) | CSV/markdown joint à l'état |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : la corvée mensuelle → le pack qui se construit (relevés, factures, justificatifs manquants listés) → les annotations factuelles + la lettre → **l'arborescence Drive qui se remplit + le brouillon Gmail** (le moment « it just works ») → le repli local sans Drive/Gmail. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 📤 Formats de sortie (où atterrit le pack ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : contenu du pack, couverture des justificatifs, liste des manquants, lettre | **Toujours** — c'est la base |
| **Dossier Google Drive** | Arborescence `Comptabilité/AAAA/MM/` (lettre, relevés, factures, état des justificatifs) | Si le MCP Drive est détecté — dépôt annoncé avant |
| **Brouillon Gmail** | Email récap au cabinet, lettre en corps, lien vers le dossier Drive | Si le MCP Gmail est détecté — **jamais envoyé par le skill** |
| **Pack local** | Dossier structuré markdown + CSV, décrit fichier par fichier | Sans Drive/Gmail — tu transmets comme tu veux |

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Enchaînement automatique avec **qonto-receipt-hunter** | Faible | La liste des manquants part directement à la chasse aux pièces avant la passation |
| Contrôle qualité **qonto-monthly-close** intégré au pack | Faible | La lettre cite le verdict du close en un badge |
| Export FEC-friendly (CSV normalisé pour l'outil du cabinet) | Moyen | Toujours factuel — le format change, pas le contenu |
| Rappel récurrent en début de mois (calendrier MCP détecté) | Faible | Multi-MCP optionnel, dans l'esprit du kickoff |
| Historique des packs (AAAA/MM cumulés) + suivi des questions ouvertes | Moyen | La question posée en mars ne se reperd pas en juin |

## 🛡 Garde-fous

- **Le skill ne fait pas la compta** : aucune écriture, aucune imputation, aucun conseil fiscal — annotation factuelle uniquement, le comptable valide tout
- Rien ne part sans toi : brouillon Gmail (jamais envoyé), dépôt Drive annoncé, aucune donnée vers un MCP non détecté et nommé
- Un pack incomplet n'est **jamais** présenté comme complet — la liste des manquants est le titre de la lettre, pas une note de bas de page
- IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout · `403` sur `list_cash_flow_categories` (connecteur claude.ai) → repli sur les labels

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-accountant-handoff.fr.html` · `docs/doc-qonto-accountant-handoff.fr.docx`.*
