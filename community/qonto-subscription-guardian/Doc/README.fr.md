# 🛡 qonto-subscription-guardian — Une carte plafonnée par abonnement

> **Skill #8** · Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> Héritier de **P7 — Gardien des Abonnements** (42/50, coup de cœur) · utilitaire d'action pur sur la surface « cartes » du MCP
> Pour l'audit complet des récurrences (coût annuel, zombies, doublons, hausses) : **`qonto-subscription-audit`**

---

## 🎯 Le pitch

Chaque abonnement prélève ce qu'il veut sur TA carte principale. Ce skill fait une seule chose, et la fait bien : **générer des cartes virtuelles plafonnées, une par abonnement — sans plus**.

1. **Détection légère** — les prélèvements récurrents sur **24-36 mois** d'historique (assez large pour attraper les **annuels**, qui exigent 2 occurrences à plus de 12 mois d'écart) : contrepartie normalisée, cadence **mensuelle, trimestrielle ou annuelle**, montant stable ±15 %. Une simple liste de candidats, aucun verdict
2. **Tu choisis** — le skill compte tes cartes existantes (`list_cards`), rappelle la grille de ton plan et propose un **nombre de cartes adapté** — jamais de rafale
3. **Une carte plafonnée PAR abonnement choisi** — `create_card` virtuelle + `payment_monthly_limit` = prix actuel + petite marge (annuel : `payment_transaction_limit`), **une par une, consentement explicite + SCA à chaque fois**
4. **Nickname `SUB-<Fournisseur>`** via `update_card` — et les cartes `SUB-` déjà en place sont reconnues, jamais reproposées (idempotence)

**Positionnement assumé** : la protection par carte dédiée est une feature que Qonto proposera sans doute nativement un jour — ce skill te la donne aujourd'hui.

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord, zéro valeur en dur) | ✅ |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Rôle Owner/Admin/Manager | Pour créer la carte directement ; sinon repli sur `create_card_request` (approuvée par un admin) | ⭕ pour agir — la détection marche pour tous |
| Cartes virtuelles du plan | **Basic : 2 incluses (2 €/mois au-delà) · Smart/Premium : 50 incluses (1 €/carte au-delà) · Essential/Business/Enterprise : illimité**. Le plan exact n'est pas lisible via MCP (`get_subscription` → 403) : le skill compte les cartes, rappelle cette grille et te demande ton plan | ℹ️ vérifié avant toute proposition |
| Historique **≥ 24 mois recommandé** | Pour attraper les abonnements **annuels** ; en dessous, les annuels peuvent passer sous le radar — annoncé honnêtement | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Cartographie du compte** : `get_organization` d'abord, puis les cartes existantes via `list_cards` — les cartes `SUB-` déjà en place sont reconnues (jamais reproposées), et le comptage sert à la vérification du plan
2. **Détection légère** (24-36 mois, paginé ≤ 50, fenêtres de 3 mois) : contrepartie normalisée + cadence 28-32 j / 85-95 j / **350-380 j (annuel)** + montant ±15 % + ≥ 3 occurrences (2 en annuel). Cartes ET prélèvements SEPA. Rapprochement sur `emitted_at` (pas `settled_at`, décalé de 1-2 j). Sortie : un tableau de candidats — fournisseur, prix, cadence M/T/**A**, carte payeuse, déjà protégé ou non
3. **Rappel du plan** : grille publique 2/50/illimité + comptage — le skill propose un nombre de cartes adapté au plan que tu annonces
4. **Tu choisis** les abonnements à protéger, un par un
5. **Carte plafonnée par abonnement** : `create_card` virtuelle, plafond mensuel = prix + marge (annuel : plafond par transaction) ; **chaque création exige la SCA** — notification push à confirmer dans l'app ; nickname `SUB-<Fournisseur>` posé juste après via `update_card`
6. **Bascule** : changer le moyen de paiement chez chaque fournisseur protégé (`get_card_iframe_url`, pour tes yeux uniquement) ; récap final des cartes créées

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de sécurité** : le trait plein (lecture) ne présente aucun risque ; le trait pointillé (écriture) exige le consentement explicite dans la conversation ET la confirmation SCA — l'appel `create_card` **bloque tant que tu n'as pas validé la notification push** sur ton appareil Qonto appairé, et ce pour CHAQUE carte. Selon ton rôle, la création directe peut être interdite : le skill bascule alors sur `create_card_request` et le dit. **C'est le modèle de sécurité, pas une limitation.**

## 🔁 Le cycle de vie d'une carte SUB-

| Étape | Outil | Note |
|---|---|---|
| Création plafonnée | `create_card` (virtuelle, plafond = prix + marge) | Consentement explicite + SCA, une carte à la fois |
| Nommage | `update_card` → `SUB-<Fournisseur>` | `create_card` n'a pas de champ nickname |
| Bascule chez le fournisseur | `get_card_iframe_url` (PAN/CVV) | Étape manuelle — URL éphémère, pour tes yeux uniquement |
| Pause réversible | `change_card_status` → `lock` | Prévient d'abord : un prélèvement refusé peut suspendre le service |
| Suppression définitive | `change_card_status` → `discard` | Le contrat, lui, survit — plafonner ≠ résilier |
| Ajuster le plafond | App Qonto uniquement | Les plafonds ne sont **pas éditables via MCP** — dit tel quel |

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Liste des candidats** | Tableau markdown : fournisseur · prix · cadence M/T/A · carte payeuse · déjà protégé | Après la détection légère |
| **Récap des cartes créées** | Tableau markdown : carte · plafond · fournisseur · reste à basculer | En fin de session |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : problème → liste des candidats + rappel de la grille du plan → choix utilisateur → **LA carte plafonnée créée en live, SCA filmée sur iPhone, carte visible dans l'app avec son plafond** → « chaque abonnement a sa boîte » + wrap-up. Le script détaillé (textes à dire, checklist tournage, notes de montage) est conservé en interne (hors dépôt).

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Catégorisation Qonto des abonnements protégés (`modify_transaction_cash_flow_category`) | Faible | Les lignes SUB- deviennent lisibles dans l'app aussi |
| Benchmark prix public par outil (web search) | Moyen | Pour dimensionner le plafond au juste prix |
| Détection multi-devises (abonnements en USD/GBP) | Moyen | Normalisation des montants avant le calcul de stabilité |

## 🛡 Garde-fous

- **Jamais** de création de carte (ou de demande) sans confirmation explicite pour CETTE carte dans la conversation en cours ; jamais présentée comme faite tant que la SCA n'est pas validée
- Vérification du plan d'abord, toujours : comptage `list_cards` + grille 2/50/illimité avant toute proposition — nombre de cartes adapté, jamais de rafale
- **Plafonner ≠ résilier** : le contrat survit à la carte — un prélèvement refusé peut déclencher relance ou suspension de service, le skill le dit AVANT
- Répétitions : 1 carte de démo max, nommée clairement, `discard` en fin de session ; jamais de PAN complet à l'écran (`get_card_iframe_url` = pour tes yeux uniquement)
- IBAN et numéros de carte masqués (4 derniers chiffres) · pagination ≤ 50 partout

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-subscription-guardian.fr.html` · `docs/doc-qonto-subscription-guardian.fr.docx`.*
