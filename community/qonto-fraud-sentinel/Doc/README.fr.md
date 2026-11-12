# 🛡 qonto-fraud-sentinel — Le garde du corps du compte

> **Skill #14 · NOUVEAU** · Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> Scan quotidien anti-anomalies : 30 secondes chaque matin, café à la main. Une seule écriture possible (verrouillage de carte), toujours proposée, jamais automatique.

---

## 🎯 Le pitch

Les débits frauduleux ou anormaux, on les découvre en général trop tard — au relevé, ou jamais. `qonto-fraud-sentinel` passe les dernières transactions au crible d'une **baseline chiffrée** construite sur l'historique réel :

1. **6 signaux d'anomalie** — bénéficiaire jamais vu, montant ×3+ la moyenne, prélèvement en double, horaire/canal inhabituel, série de petits débits rapprochés (test de carte volée), premier SEPA d'un nouveau créancier
2. **Chaque alerte est expliquée** — la transaction, le pourquoi (baseline chiffrée : « 612 € vs 148 € de moyenne sur 14 débits = ×4,1 »), l'action recommandée, une gravité 🔴🟠🟡
3. **Un signal ≠ une fraude** — le skill dit « inhabituel, vérifie », jamais « fraude détectée ». Les faux positifs sont assumés et expliqués ; tu marques les contreparties de confiance en un message
4. **Action sécurisée** — verrouillage de carte (`change_card_status`) **proposé** si une carte est en cause, exécuté seulement après ta confirmation explicite ; déblocage et opposition définitive restent dans l'app Qonto

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord) | ✅ |
| Pays | **Signaux universels (comportementaux, zone SEPA)** : identiques dans tous les pays Qonto (FR, DE, ES, IT, AT, NL, BE, PT) — seul le discours s'adapte | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Historique ≥ 3 mois | En dessous : **mode prudent annoncé** — baseline plus mince, plus de faux positifs, alertes formulées au conditionnel | ⭕ recommandé (3-6 mois pour calibrer) |
| MCP Gmail | Enrichissement optionnel : brouillon de digest quotidien par email — détecté dynamiquement, le cœur marche sans | ⭕ optionnel |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Calibrage de la baseline** (3-6 mois, paginé ≤ 50) : par contrepartie normalisée — nombre d'occurrences, moyenne et max, cadence, première/dernière apparition, type d'opération et horaires typiques. Les transactions carte sont datées sur **`emitted_at`** (pas `settled_at` : 1-2 jours d'écart fausseraient doublons et horaires)
2. **Scan de la fenêtre** : depuis le dernier scan, ou les dernières 48-72 h au premier passage — élargissable à la demande (« la semaine », « depuis le 1er »)
3. **Crible des 6 signaux** (tableau de référence ci-dessous) — les contreparties de confiance sautent « jamais vu » et « premier SEPA » mais restent surveillées sur montants et doublons
4. **Alertes expliquées et triées** 🔴🟠🟡 — et si rien ne cloche, le skill le dit avec la profondeur de baseline : **un rapport « RAS » est un produit, pas un échec**
5. **Verrouillage de carte proposé** (uniquement si carte en cause + confirmation explicite) : `change_card_status` — jamais automatique
6. **Mémoire de confiance** : « *confiance MAIF* » → mémorisé dans la conversation/le projet, plus d'alerte « jamais vu » pour cette contrepartie

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de sécurité** : le trait plein (lecture) ne présente aucun risque ; le trait pointillé (écriture) est un **verrouillage de carte** — réversible, proposé en réaction à une alerte carte, exécuté seulement après confirmation explicite dans la conversation. Le déblocage, l'opposition définitive, la révocation de mandat SEPA et le remplacement de carte restent dans l'app Qonto, sous la main du titulaire. Aucun argent ne bouge, dans aucun scénario.

## 🚨 Les 6 signaux de référence

| Signal | Critère (baseline chiffrée) | Action recommandée |
|---|---|---|
| **Bénéficiaire jamais vu** | Première apparition d'une contrepartie sortante sur 3-6 mois | Vérifier — nouveau fournisseur légitime ? Marquer de confiance |
| **Montant inhabituel** | ≥ ×3 la moyenne de cette contrepartie (ou du poste si elle est nouvelle) | Vérifier la facture / le contrat correspondant |
| **Prélèvement en double** | Même contrepartie, même montant (±1 %), à 1-5 jours d'écart | Vérifier ; contester le doublon auprès du créancier ou via l'app |
| **Horaire / canal inhabituel** | Paiement carte à une heure jamais vue pour cette contrepartie ; type d'opération inédit | Vérifier ; carte douteuse → verrouillage proposé |
| **Série de petits débits** | ≥ 3 petits débits (dernier décile ou < 10 €) en quelques minutes/heures | Pattern de test de carte volée → verrouillage proposé (`change_card_status`) |
| **Premier SEPA d'un nouveau créancier** | Premier prélèvement d'un créancier absent de la baseline (mandat tout juste utilisé) | Vérifier le mandat ; opposition via l'app si non reconnu |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : problème → baseline → les signaux en action → **la routine du matin filmée (l'alerte du premier SEPA, marquée de confiance en un message)** → wrap-up. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableau markdown des alertes (transaction · signal · baseline · action · gravité) ou « RAS » chiffré | **Toujours** — c'est la base |
| **Rapport du matin** | Fichier/artifact **HTML** compact : alertes triées, baseline, état des cartes | Si l'hôte affiche les fichiers ; repli automatique sur le tableau |
| **Digest email** | Brouillon Gmail du scan quotidien | Seulement si un MCP Gmail est détecté — optionnel |

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Scan planifié (routine quotidienne automatisée) | Faible | Le prompt du matin devient un rendez-vous programmé |
| Seuils personnalisables par l'utilisateur (×2, ×5, montant plancher) | Faible | La baseline reste le défaut intelligent |
| Score de risque par contrepartie sur 12 mois | Moyen | Réutilise le moteur de baseline |
| Alerte Telegram/Slack quand le MCP est présent | Faible | Même logique multi-MCP que Gmail |

## 🛡 Garde-fous

- **Jamais le mot « fraude »** — « inhabituel, vérifie ». Un premier paiement à un nouveau fournisseur, c'est la vie normale d'une boîte, pas un incident
- **Jamais** de `change_card_status` sans confirmation explicite dans la conversation en cours ; jamais présenté comme fait si l'appel a échoué
- Historique < 3 mois : mode prudent annoncé, alertes au conditionnel ; fenêtre vide → le skill le dit, n'invente rien
- IBAN et numéros de carte masqués (4 derniers chiffres) ; pagination ≤ 50 ; horodatage carte sur `emitted_at`
- Répétitions : verrouiller une carte virtuelle/dormante, la débloquer aussitôt dans l'app

> **Voir aussi** : `13-qonto-supplier-detective` — factures fournisseurs historiques et récupération d'argent. Sentinel est son jumeau sécurité : temps réel et quotidien, pas de l'archéologie.

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-fraud-sentinel.fr.html` · `docs/doc-qonto-fraud-sentinel.fr.docx`.*
