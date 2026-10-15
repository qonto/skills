# 💸 qonto-pay-me-now — Du devis à l'argent, sans friction

> **Skill #11 · nouveau** · Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> Différenciateur clé : **les payment links fonctionnent via MCP malgré la doc officielle qui les dit non supportés** — vérifié en production le 03/07. Personne d'autre ne le sait.

---

## 🎯 Le pitch

Le trou noir du freelance : le devis est accepté… et puis rien. La facture attend, le paiement attend encore plus. Chaque jour entre le « oui » du client et l'argent sur le compte, c'est de la trésorerie gagnée mais intouchable. `qonto-pay-me-now` enchaîne tout le cycle dans une seule conversation :

1. **Devis accepté détecté** — `list_quotes` croisé avec `list_client_invoices` : seuls les devis acceptés **jamais facturés** remontent, avec client, montant et date
2. **Facture générée depuis le devis** — brouillon d'abord, document RÉEL : rien ne part sans ta confirmation explicite
3. **Payment link Qonto** — le client paie par carte ou virement en un clic ; lien court trackable Short.io + **QR code** proposé pour les factures imprimées
4. **Suivi & relance douce** — lien cliqué mais impayé après 48 h → relance douce proposée, jamais envoyée toute seule

Le cycle de paiement passe de « quand il y pense » à « il clique, il paie ».

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Cycle devis → facture → payment link : identique pour tous les pays Qonto** (FR, DE, ES, IT, AT, NL, BE, PT). Ton des relances : France au complet ; ailleurs le skill adapte et n'invente jamais de mention légale locale | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Payment links activés | Activation unique dans l'app Qonto. Si `create_payment_link` refuse, le skill l'explique et continue avec la facture seule | ⭕ recommandé |
| Devis créés dans Qonto | Le skill part de `list_quotes` ; sans devis, il sait aussi partir d'une facture impayée existante | ⭕ |
| MCP Short.io / Gmail | Enrichissements optionnels détectés dynamiquement : lien court trackable + stats de clics / envoi. Sans eux : lien Qonto brut + texte à copier | ⭕ optionnel |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Détection** : `get_organization` puis `list_quotes` paginé ≤ 50 — devis acceptés croisés avec les factures existantes, seuls les jamais facturés sont proposés
2. **Facture depuis le devis** : `create_client_invoice` en **brouillon** (client, lignes, montants, TVA repris du devis) → relecture → envoi seulement après ton OK explicite. Bonus : si tu es en TVA sur les encaissements (`on_receipts`), accélérer le paiement accélère aussi ton cycle de TVA
3. **Payment link** : `create_payment_link` sur le montant de la facture, numéro de facture dans la description pour un rapprochement trivial. **Vérifié le 03/07 : ça marche via MCP, contrairement à ce que dit la doc officielle**
4. **Lien court + QR** : Short.io présent → `create-short-link` avec un slug lisible (`pay-INV-2026-042`) + QR code proposé pour l'imprimé. Absent → le lien Qonto brut suffit, le skill le dit et continue
5. **Envoi maîtrisé** : `send_client_invoice` et/ou brouillon Gmail avec le lien — tu relis, tu envoies. Jamais présenté comme envoyé si en attente
6. **Suivi** : statut du lien (`get_payment_link`) + clics (`link-statistics`) + encaissements réels (`list_transactions`) → cliqué sans payer à J+2 = relance douce proposée ; payé hors lien = `mark_client_invoice_as_paid` proposé avec la transaction en preuve

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de sécurité** : ce skill ne peut pas déplacer ton argent. Un payment link est un moyen de **RECEVOIR** un paiement de ton client — rien à voir avec un virement sortant (de toute façon impossible via MCP : toute demande de virement exige ta SCA dans l'app Qonto). Les trois seules écritures : une facture (brouillon d'abord, envoi après ton OK), un lien de paiement désactivable à tout moment dans l'app, et le marquage « payée » d'une facture — toujours proposé avec la transaction en preuve, jamais automatique.

## 📊 La matrice de suivi (J+2)

| Lien cliqué ? | Paiement reçu ? | Action proposée |
|---|---|---|
| ❌ Non | ❌ Non | Vérifier l'envoi ; proposer de renvoyer le lien par un autre canal |
| ✅ Oui | ❌ Non (> 48 h) | **Relance douce** — « le lien est toujours actif » — rédigée, jamais envoyée seule |
| ✅ Oui | ✅ Oui | Boucle fermée ✅ — confirmation dans le rapport |
| ❌ Non | ✅ Oui | Payé par virement classique hors lien → rapprochement + `mark_client_invoice_as_paid` proposé |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : le trou noir → détection & facture → payment link + lien court → **le QR scanné au téléphone, la page de paiement Qonto qui s'affiche** → suivi & relance. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : pipeline devis → facture → lien, puis matrice de suivi | **Toujours** — c'est la base |
| **Le payment link (+ lien court)** | URL Qonto + URL courte Short.io, prêtes à partager | À chaque cycle |
| **QR code** | Fichier/artifact image encodant le lien, pour les factures imprimées | Si l'hôte affiche les fichiers ; sinon les liens suffisent |
| **Rapport de suivi** | Tableau clics vs encaissements + relances proposées | Sur demande / à J+2 |

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Acompte à la signature : payment link partiel (30 %) dès l'acceptation du devis | Moyen | Le même cycle, encore plus tôt |
| Rappel J+2 dans le calendrier (MCP calendrier détecté dynamiquement) | Faible | Multi-MCP optionnel, dans l'esprit du kickoff |
| Messages client multilingues (langue du client détectée) | Faible | Qonto est paneuropéen |
| Tableau de bord encaissements : taux clic → paiement par client | Moyen | Réutilise `link-statistics` + `list_transactions` |
| Mentions légales locales par pays (DE · ES · IT…) | Moyen | v1 = cycle identique partout, v2 = wording local |

## 🛡 Garde-fous

- Factures via MCP = **RÉELLES** : brouillon d'abord, envoi seulement après confirmation explicite ; répétitions sur un client fictif + `delete_client_invoice` ensuite
- **Aucun paiement sortant** : le skill encaisse-t-il quelque chose lui-même ? Non — le payment link reçoit, il ne débite jamais. Zéro rapport avec les virements sortants (SCA obligatoire dans l'app, hors MCP)
- Rien n'est envoyé (facture, mail, relance) sans confirmation dans la conversation en cours ; jamais présenté comme envoyé/payé si en attente
- Montants toujours repris du devis ou de la facture, jamais inventés · IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout
- Dégradation honnête : pas de devis, payment links non activés, Short.io absent, pays ≠ FR → le skill dit ce qui marche et continue avec ça

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-pay-me-now.fr.html` · `docs/doc-qonto-pay-me-now.fr.docx`.*
