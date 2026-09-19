# 🔭 qonto-counterparty-watch — Savoir qui te doit de l'argent… et qui coule

> **Skill #2** · Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> Surveillance de la santé légale des clients & fournisseurs : encours Qonto × données publiques (SIRENE, BODACC)
> **100 % lecture** — le skill n'écrit jamais rien, nulle part

---

## 🎯 Le pitch

Un impayé fait mal. Un impayé chez un client **déjà en redressement judiciaire** peut être perdu pour toujours — et personne ne t'a prévenu. `qonto-counterparty-watch` transforme le compte Qonto en radar tiers :

1. **Encours par tiers** — factures clients impayées (montants, ancienneté), engagements fournisseurs, dépense récurrente annualisée : combien chaque tiers pèse vraiment
2. **Comportement de paiement réel** — délai observé vs `due_date` sur l'historique : retard moyen, pire retard, tendance qui se dégrade
3. **Santé légale** (si le MCP Datagouv est présent) — SIRENE (radiations, cessations) et BODACC (redressement, liquidation, sauvegarde), avec la date de vérification sur chaque ligne
4. **Score de risque 🟢🟡🔴 justifié** — croisement encours × santé légale × retard, et des alertes du type : *« ton client X te doit N € ET vient d'entrer en redressement → relance-le AUJOURD'HUI, en recommandé »*

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Santé légale : France** (SIRENE + BODACC). Autres pays Qonto (DE, ES, IT…) : dégradation propre — le cœur Qonto (encours + retards) marche partout, jamais de registre inventé | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| MCP Datagouv (data.gouv.fr) | Détecté dynamiquement. Absent → le skill le dit et livre le scoring Qonto pur | ⭕ recommandé — active la santé légale |
| SIREN des tiers | Extrait des fiches clients Qonto (`tax_identification_number` : TVA FR = SIREN + 2 clés) ou du nom exact. Sans SIREN → ligne « non vérifiable », annoncée | ⭕ |
| Historique de factures | Plus il y a de factures payées, plus le retard moyen par client est fiable | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Inventaire des tiers** : clients via `list_clients` + factures, fournisseurs via `list_supplier_invoices` + `list_transactions` (12-24 mois, paginé ≤ 50). **Normalisation des noms** — les libellés bancaires sont sales (mentions SEPA, références, suffixes SARL/SAS) : le skill fusionne fiches clients et contreparties de transactions sur une clé normalisée
2. **Encours par tiers** : impayés clients à leur échéance (tranches 0-30 / 31-60 / 61-90 / 90+ jours), factures fournisseurs à payer, récurrence annualisée
3. **Comportement de paiement** : date de paiement observée − `due_date` par client → retard moyen, pire retard, tendance (un client qui glisse de 15 à 45 jours est un signal, même sans événement légal)
4. **Santé légale** (MCP Datagouv présent) : SIRENE (statut administratif) + BODACC (procédures collectives) par SIREN. ⚠️ **Honnêteté d'abord** : chaque verdict porte sa preuve — « ✅ vérifié sur BODACC le JJ/MM, rien trouvé » vs « ⚠️ non vérifiable » ; la couverture BODACC via data.gouv peut être partielle, le skill l'annonce
5. **Score 🟢🟡🔴** : encours × santé légale × retard, justifié en une ligne par tiers
6. **Rapport & alertes** : tableau de risque trié, alertes prioritaires croisées, note de couverture (vérifiés / non vérifiables), dashboard HTML optionnel

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé** : tout est en trait plein — **100 % lecture**. Le skill ne crée rien, ne modifie rien, n'envoie rien. Il croise deux mondes qui ne se parlent jamais : ton compte Qonto (qui te doit quoi) et les registres publics français (qui est en train de couler). La donnée sort, rien ne rentre.

## 📊 Grille de score (encours × santé légale × retard)

| Score | Déclencheurs | Exemple |
|---|---|---|
| 🔴 Critique | Procédure collective ouverte ou radiation **avec encours** ; ou impayé 90+ jours significatif | « Doit 9 700 €, redressement publié récemment → déclarer la créance (délai 2 mois) + relance recommandée » |
| 🟡 À surveiller | Tendance de paiement qui se dégrade ; gros encours non vérifiable (pas de SIREN) ; procédure trouvée sans encours actuel | « Retard moyen passé de 12 à 38 jours sur les 3 dernières factures » |
| 🟢 Sain | Vérifié sans signal (avec date) et paiements dans les temps | « ✅ BODACC vérifié le 11/07, rien trouvé · retard moyen 4 jours » |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : problème → tableau de risque → le moment croisé (impayé + BODACC) → dashboard. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 📤 Formats de sortie (où atterrit le tableau de risque ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (risque trié, alertes, couverture) | **Toujours** — c'est la base |
| **Dashboard interactif** | Fichier/artifact **HTML** : matrice encours × santé, tranches d'ancienneté, cartes d'alerte | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur les tableaux |
| **Note de couverture** | Compteur vérifiés / non vérifiables / registre indisponible | À chaque rapport — l'honnêteté fait partie du livrable |

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Registres européens (Handelsregister DE, Registro Mercantil ES…) | Moyen | Qonto est paneuropéen ; v1 = France, v2 = un module registre par pays |
| Brouillon de relance par email (MCP Gmail détecté dynamiquement) | Faible | Multi-MCP optionnel — brouillon seulement, jamais d'envoi automatique |
| Suivi dans le temps : diff entre deux scans (« nouveau 🔴 depuis lundi ») | Moyen | Le rituel du lundi matin devient un delta, pas un rapport complet |
| Score de dépendance fournisseur (part du CA / des achats) | Faible | Réutilise l'inventaire, éclaire le risque de rupture |

## 🛡 Garde-fous

- **100 % lecture** — aucun outil d'écriture Qonto appelé, jamais ; rien à approuver, rien à exécuter
- Jamais de statut légal sans **source + date** ; « rien trouvé » ≠ « garanti sain » quand la couverture est partielle
- Alertes = signaux, pas conseil juridique : procédure ouverte → confirmer sur bodacc.fr, en parler à l'avocat/expert-comptable
- Dégradation honnête : sans Datagouv → scoring Qonto pur annoncé ; tiers non français → encours + retards seulement
- IBAN masqués (4 derniers chiffres) ; pagination ≤ 50 partout

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-counterparty-watch.fr.html` · `docs/doc-qonto-counterparty-watch.fr.docx`.*
