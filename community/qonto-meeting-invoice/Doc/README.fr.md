# 📞 qonto-meeting-invoice — Du call au devis, avant la fin de la réunion

> **Skill #12 · nouveau** · Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> C'est le cas d'usage cité par le jury au kickoff (call de vente → facture) — pas le plus original, donc on gagne sur **l'exécution** : extraction prudente, brouillon d'abord, envoi sous confirmation.

---

## 🎯 Le pitch

Un bon call de vente, tout le monde est chaud… et le devis part trois jours plus tard. L'élan est retombé, le prospect a vu deux concurrents. `qonto-meeting-invoice` raccourcit ce délai à quelques minutes :

1. **Transcript en entrée** — fichier, note Notion/Drive (si le MCP est là) ou texte collé : le skill ne dépend d'aucun MCP tiers
2. **Extraction prudente** — prestations, quantités, prix, remises, conditions, échéance : **uniquement ce qui a été dit**. Prix, TVA ou délai absents → question à l'utilisateur, jamais d'invention. Chaque terme extrait cite sa ligne du transcript
3. **Rapprochement Qonto réel** — catalogue produits (`list_products` : prix, TVA), fiches clients (`list_clients` — création proposée si nouveau, avec confirmation), devis existants (`list_quotes`, anti-doublon)
4. **Brouillon puis envoi** — `create_quote` (ou `create_client_invoice` sur demande) en **brouillon**, récap ligne à ligne, et envoi **seulement** après un « oui, envoie » explicite. Le prospect reçoit le devis pendant que le café est encore chaud

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | Création de devis/factures : **tous les pays Qonto**. Mentions légales = paramètres de facturation Qonto du pays ; taux de TVA jamais supposés (catalogue ou confirmation) — pas de « 20 % par défaut » | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Facturation Qonto configurée | Numérotation, mentions légales, coordonnées de paiement — réglé une fois dans l'app Qonto ; le skill s'appuie dessus, il ne les réinvente pas | ✅ |
| Transcript du call | Fichier, note Notion/Google Drive, ou texte collé dans la conversation | ✅ |
| Catalogue produits Qonto | Prestations avec prix et taux de TVA (`list_products`) — sinon le skill construit les lignes depuis le call et demande ce qui manque | ⭕ recommandé |
| MCP Notion / Google Drive | Source du transcript détectée dynamiquement — absente, le skill le dit et demande un collage | ⭕ optionnel |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Ingestion du transcript** : fichier, note Notion/Drive (MCP optionnel, détecté dynamiquement) ou texte collé — les transcripts sales (hésitations, plusieurs interlocuteurs, langues mélangées) sont le cas normal
2. **Extraction des termes négociés** : prestations, quantités, prix unitaires, remises, conditions de paiement, échéance/validité — chaque terme justifié par sa citation du transcript ; ce qui n'a pas été dit ne rentre **pas** dans le document
3. **Rapprochement Qonto** : catalogue produits (titre canonique, prix, TVA — divergences signalées : « le call dit 850 €/j, ton catalogue dit 900 € »), client existant retrouvé ou création proposée avec relecture des coordonnées, anti-doublon sur les devis récents
4. **Levée des ambiguïtés** : une seule liste, AVANT toute écriture — « le tarif habituel », condition de paiement non citée, TVA incertaine. Tu tranches chaque point
5. **Brouillon** : `create_quote` (défaut) ou `create_client_invoice` (si demandé) — jamais envoyé à ce stade. Récap ligne à ligne : client, lignes (titre · qté · PU · TVA · total), totaux, dates, conditions
6. **Envoi après confirmation** : `send_quote` / `send_client_invoice` sur ton « oui » explicite, adresse email confirmée. Sinon le document reste en brouillon dans Qonto

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de sécurité** : les documents créés via MCP sont **réels**. Le trait plein (lecture : catalogue, clients, devis) ne présente aucun risque ; le trait pointillé (écriture) ne produit qu'un **brouillon** — et l'envoi au prospect exige une confirmation explicite dans la conversation, après le récap ligne à ligne. Rien ne part sans ton accord.

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : extraction citée, liste d'ambiguïtés, récap ligne à ligne | **Toujours** — c'est la base |
| **Brouillon dans Qonto** | Devis ou facture sur le modèle de facturation de l'organisation (numérotation, mentions légales natives) | Après la levée des ambiguïtés |
| **Email au prospect** | Envoi natif Qonto (`send_quote` / `send_client_invoice`) | **Seulement** après confirmation explicite |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : le problème (le devis qui part 3 jours après le call) → transcript collé & extraction citée → rapprochement catalogue/client & ambiguïtés → **le devis complet qui apparaît dans Qonto ~90 secondes après la fin de la réunion, puis l'envoi** → garde-fous. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Acompte automatique (« 30 % à la commande ») via `create_payment_link` joint à l'envoi | Faible | Outil MCP officiel, même logique de confirmation |
| Relance du devis non signé après N jours (statut via `list_quotes`) | Faible | Se combine avec un skill de relance |
| Transcription audio directe (fichier m4a → texte) quand l'hôte le permet | Moyen | Le skill reste centré transcript texte |
| Multi-devis : variantes A/B (avec/sans option) issues du même call | Moyen | Deux `create_quote` en brouillon, comparés en tableau |
| Détection de la langue du prospect → devis dans sa langue | Faible | Qonto gère les modèles ; le skill adapte les libellés |

## 🛡 Garde-fous

- Documents créés via MCP = **réels** : brouillon d'abord, toujours ; **jamais** d'envoi sans confirmation explicite dans la conversation en cours ; jamais présenté comme envoyé s'il est en brouillon
- Rien d'inventé : prix, TVA, quantité ou échéance absents du call → question. Pas de TVA « par défaut »
- `create_client` seulement après relecture des coordonnées ; `list_clients` d'abord (anti-doublon)
- Répétitions : client fictif + `delete_quote` / `delete_client_invoice` (brouillons uniquement — une facture finalisée ne se supprime pas, d'où le brouillon d'abord)
- Pagination ≤ 50 partout · données personnelles masquées dans les échos de fiches clients
- Le skill rédige des documents commerciaux, pas du conseil juridique ou fiscal — les paramètres Qonto et l'expert-comptable restent la référence

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-meeting-invoice.fr.html` · `docs/doc-qonto-meeting-invoice.fr.docx`.*
