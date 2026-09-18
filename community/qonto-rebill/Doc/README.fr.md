# 💶 qonto-rebill — Les frais avancés pour tes clients, littéralement récupérés

> Hackathon Qonto × Anthropic MCP (10-13/07/2026) · Agent Skill pour le MCP Qonto
> 100 % Qonto pur : lecture des transactions, labels et justificatifs → facture de refacturation en **brouillon**, envoyée seulement après ta confirmation

---

## 🎯 Le pitch

Freelances et agences avancent des frais pour leurs clients — plugins, banques d'images, hébergement, billets de train, repas de mission — et **oublient d'en refacturer la moitié**. `qonto-rebill` va les rechercher :

1. **Détection des frais attribuables à un client** — labels Qonto « client », équipes, ou attribution assistée par l'historique, transaction par transaction (jamais d'attribution silencieuse)
2. **Regroupement par client et par période** — avec l'inventaire des **justificatifs déjà attachés** aux transactions (les manques sont signalés)
3. **Le point fiscal expliqué, jamais tranché** — débours (hors TVA, au nom du client) vs frais refacturés (TTC, TVA de la prestation principale) : le skill explique la différence et **demande** ton régime
4. **La facture de refacturation, ligne à ligne** — `create_client_invoice` en **brouillon**, majoration optionnelle (frais de gestion 5-10 %, à toi de choisir), envoi uniquement après confirmation explicite

De l'argent littéralement récupéré — sur des frais que tu as déjà payés.

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Le skill s'adapte à toute organisation — `get_organization` d'abord, zéro donnée en dur | ✅ |
| Pays | **Mécanique universelle** (détecter → regrouper → facturer). Le régime **débours** est français (art. 267 II-2° CGI) : hors France, le skill facture pareil mais renvoie la TVA locale à l'expert-comptable — jamais de règle étrangère inventée | ℹ️ détecté |
| MCP Qonto connecté | Connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Labels « client » | Des labels Qonto nommés comme tes clients (ou des équipes par mission). **Sans labels : attribution interactive**, transaction par transaction — plus lent mais rien n'est perdu | ⭕ recommandé |
| Clients dans la facturation Qonto | `list_clients` — la facture a besoin d'un client existant ; sinon le skill explique comment le créer | ⭕ |
| Justificatifs attachés | Inventoriés automatiquement ; pour combler les manques **avant** de refacturer : `qonto-receipt-hunter` | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Cadrage** : `get_organization` d'abord (comptes, identité), puis les référentiels — labels Qonto et clients de la facturation, normalisés et rapprochés (le label « acme studio » = le client « ACME Studio »). Période choisie avec toi (défaut : dernier trimestre plein)
2. **Détection** : scan des débits (paginé ≤ 50), regroupés par `emitted_at` (les frais carte se règlent 1-2 jours plus tard — sinon ils fuient d'une période à l'autre). Attribution par labels client → équipes → **attribution assistée** : le skill présélectionne les candidats (tiers déjà attribués par le passé, dépenses typées mission : SaaS, images, hébergement, transport, repas) et demande transaction par transaction
3. **Regroupement + justificatifs** : tableau par client (date · tiers · montant · TVA d'achat), totaux, et pour chaque ligne le **justificatif déjà attaché** récupéré (`list_transaction_attachments` + `get_attachment`) ou le manque signalé
4. **Le choix fiscal** : débours vs frais refacturés — tableau comparatif affiché, régime **demandé** (ligne à ligne si mixte), majoration 5-10 % proposée (jamais sur un débours)
5. **Brouillon** : `create_client_invoice` en BROUILLON — une ligne par frais (date, tiers, montant), TVA selon le régime choisi, ligne « frais de gestion » séparée. Rien n'est envoyé
6. **Confirmation** : relecture ligne à ligne → envoi seulement si tu confirmes explicitement (`send_client_invoice`). En répétition : client fictif + brouillon + `delete_client_invoice`

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de sécurité** : le trait plein (lecture) ne présente aucun risque ; le trait pointillé (écriture) ne produit qu'un **brouillon de facture** dans Qonto. L'envoi au client exige ta confirmation explicite dans la conversation — et les factures créées via MCP étant réelles, les répétitions se font sur client fictif puis `delete_client_invoice`.

## ⚖️ Débours vs frais refacturés (le tableau que le skill affiche)

| Critère | Débours (art. 267 II-2° CGI) | Frais refacturés (classique) |
|---|---|---|
| Principe | Dépense engagée **au nom et pour le compte** du client (mandat) | Dépense engagée en ton nom propre, refacturée comme élément de ton prix |
| Marge | Interdite — remboursement à l'euro l'euro | Autorisée (frais de gestion 5-10 %…) |
| TVA | **Hors champ** : pas de TVA sur la ligne, TVA de l'achat non déductible | **TTC, au taux de la prestation principale** (souvent 20 %) — même si l'achat était à 10 % ou sans TVA |
| Justificatif | Facture d'origine **au nom du client**, à lui remettre | Facture d'origine à ton nom, conservée |
| Comptabilité | Compte de tiers (pas du chiffre d'affaires) | Produit (chiffre d'affaires) |
| Pays | Régime français | Mécanique universelle ; hors France → expert-comptable local |

Le skill **explique et demande — il ne décide jamais seul**, et chaque rapport recommande la validation de l'expert-comptable.

## 🧪 Robuste sur données sales

- Aucun label client ? → attribution interactive, transaction par transaction, et proposition de labelliser pour que le trimestre suivant soit automatique
- Justificatif manquant sur une ligne ? → signalé, avec renvoi vers `qonto-receipt-hunter` avant d'envoyer
- Client absent de la facturation ? → le skill le dit et explique la création dans l'app (Facturation → Clients)
- Frais carte à cheval sur deux périodes → regroupés par `emitted_at`, pas `settled_at`
- Compte vide, période sans frais, pays ≠ FR → le skill dit ce qu'il peut et ne peut pas faire, sans jamais inventer

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : frais par client (justificatif ✅/⚠️), facture ligne à ligne, total récupéré | **Toujours** — c'est la base |
| **Brouillon de facture Qonto** | `create_client_invoice` en brouillon, visible dans Facturation | Après ton accord sur le régime ; envoi après confirmation explicite |
| **Pack justificatifs** | Liens de téléchargement (`get_attachment`, à durée limitée) à joindre à l'envoi | À chaque facture préparée |
| **Récap HTML** | Cartes par client, jauge justificatifs, montants récupérés | Si l'hôte affiche les fichiers ; sinon repli sur les tableaux |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : le problème (les frais avancés qu'on oublie) → détection par labels → le choix fiscal expliqué → **la facture brouillon ligne à ligne, justificatifs inventoriés** → envoi confirmé et récap. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Apprentissage des tiers « refacturables » par client | Moyen | Le skill mémorise les attributions acceptées et pré-remplit le trimestre suivant |
| Devis d'accord préalable (`create_quote`) pour les gros frais | Faible | Faire valider la dépense par le client AVANT de l'avancer |
| Rituel mensuel/trimestriel automatique | Faible | Un prompt planifié : « frais à refacturer ce mois-ci ? » |
| Chaînage : `qonto-receipt-hunter` avant, `qonto-invoice-chaser` après | Faible | Justificatifs complets → facture → relance de paiement |
| Frais en devises | Moyen | Conversion au taux de la transaction, mention sur la ligne |

## 🛡 Garde-fous

- Les factures créées via MCP sont **réelles** : brouillon jusqu'à confirmation explicite, jamais présenté comme envoyé, répétitions sur client fictif + `delete_client_invoice`
- **Jamais d'attribution silencieuse** : chaque frais douteux est demandé ; rien d'inventé (ni montant, ni justificatif)
- Le choix débours/refacturation t'appartient (avec ton expert-comptable) — le skill explique et demande
- Dégradation honnête (pas de labels, compte vide, pays ≠ FR) ; IBAN masqués (4 derniers chiffres) ; pagination ≤ 50 partout

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-rebill.fr.html` · `docs/doc-qonto-rebill.fr.docx`.*
