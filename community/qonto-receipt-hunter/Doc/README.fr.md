# 🧾 qonto-receipt-hunter — Justificatif Zéro : le chasseur de reçus

> **Skill #5** · Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> La chasse ne s'arrête plus à la détection — elle **fouille Gmail et Drive** et rattache les originaux.

---

## 🎯 Le pitch

La corvée universelle : ~20 % des transactions n'ont pas de justificatif. Chaque reçu perdu = TVA non récupérable, charge réintégrable, comptable furieux. `qonto-receipt-hunter` transforme la corvée en chasse automatique :

1. **Inventaire priorisé** — les transactions sans pièce (`attachment_ids` vide + `attachment_required`), classées par urgence : TVA récupérable en jeu, montant, ancienneté — tags 🔴 urgent · 🟠 bientôt · 🟢 faible
2. **Chasse dans les sources connectées** — Gmail (marchand + montant + fenêtre de dates autour de `emitted_at`) et Google Drive, détectés dynamiquement
3. **Rattachement confirmé** — match affiché (transaction ↔ document original), confirmation explicite, puis `request_attachment_upload` + `upload_attachment` ; jamais en masse
4. **Rapport de chasse** — rattachées ✅, à joindre 📎, introuvables ❌ avec une piste concrète chacune (portail marchand, boîte secondaire, collecte auto Qonto, duplicata fournisseur) + score de complétude avant/après

**Le garde-fou majeur (vécu)** : le skill n'attache QUE des documents **originaux** (PDF du marchand, pièce jointe d'e-mail). Il ne régénère ni ne fabrique JAMAIS un justificatif — aucune valeur probante, risque réel en contrôle fiscal.

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Fonctionne pour tous les pays Qonto.** L'estimation « TVA en jeu » par plafond 20/120 : France uniquement ; ailleurs, seul le `vat_amount` renseigné est utilisé — jamais de taux deviné | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| MCP Gmail | Alimente la chasse e-mails. Absent : le skill le dit et livre l'inventaire priorisé + où chercher | ⭕ recommandé |
| MCP Google Drive | Alimente la chasse fichiers | ⭕ optionnel |
| Périmètre | 90 derniers jours par défaut — extensible (trimestre, exercice) sur demande | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Inventaire des trous** : scan paginé (≤ 50) de toutes les transactions ; pièce manquante = `attachment_ids` vide + `attachment_required` vrai + `attachment_lost` faux. Encaissements clients et pièces non exigées mis de côté (ils ne polluent pas le score)
2. **Classement par urgence** : TVA récupérable en jeu (`vat_amount`, sinon plafond estimé — annoncé comme tel), montant, ancienneté. En-tête : « X pièces manquantes, ~Y € de TVA récupérable en jeu »
3. **Chasse Gmail** : marchand + montant + fenêtre autour de **`emitted_at`** (pas `settled_at` — délai carte 1-2 j), tolérance de montant (pourboires, devises, captures partielles)
4. **Chasse Google Drive** : PDF par marchand/date/montant, téléchargement et lecture du candidat avant toute proposition
5. **Rattachement confirmé** : contrôle de cohérence (marchand, montant, date), match affiché, confirmation explicite **pour chaque pièce**, puis `request_attachment_upload` → `upload_attachment` → vérification `list_transaction_attachments`
6. **Rapport de chasse** : ✅ / 📎 / ❌ avec pistes, score de complétude avant/après

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de sécurité** : la lecture (trait plein) est sans risque ; l'écriture (trait pointillé) **n'ajoute qu'un document à une transaction** — elle ne touche jamais à l'argent — et exige une confirmation explicite par pièce dans la conversation. Et surtout : **originaux uniquement** — le skill localise et transporte des documents existants, il n'en crée jamais.

## 🧮 Classement par urgence (les critères)

| Critère | Signal | Effet |
|---|---|---|
| TVA récupérable en jeu | `vat_amount` renseigné ; sinon (France) plafond montant × 20/120, annoncé comme estimation | Poids principal |
| Montant | Les gros débits d'abord — c'est là que la réintégration fait mal | Fort |
| Ancienneté | Plus c'est vieux, plus la clôture approche et plus le duplicata est dur à obtenir | Fort |
| Exclusions | `attachment_required: false` · encaissements clients (`side: credit`) · `attachment_lost` | Hors score |

## 🔎 Sources de chasse

| Source | Méthode | Condition |
|---|---|---|
| **Gmail** | Marchand (variantes du nom) + montant + fenêtre ±quelques jours autour de `emitted_at`, tolérance de montant ; cible : le PDF original du marchand | MCP Gmail connecté |
| **Google Drive** | Recherche par marchand/date/montant dans noms et contenus, téléchargement + contrôle de cohérence | MCP Drive connecté |
| **Introuvable ?** | Piste concrète par trou : portail marchand (section factures), boîte pro secondaire ou perso, collecte auto de reçus Qonto, demande de duplicata au fournisseur | Toujours |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : problème → inventaire priorisé (7 pièces manquantes, TVA en jeu chiffrée) → chasse Gmail en live → **5 reçus retrouvés et rattachés en un clic chacun** → rapport final avec pistes pour les 2 restants. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (inventaire priorisé, TVA en jeu, rapport de chasse) | **Toujours** — c'est la base |
| **Rattachements Qonto** | Pièces jointes réelles sur les transactions, visibles immédiatement dans l'app Qonto | À chaque confirmation |
| **Rapport de complétude** | Score avant/après + pistes restantes ; version **HTML** si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code), sinon repli sur les tableaux | Fin de session |

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Brouillons Gmail de demande de duplicata au fournisseur (héritage P5) | Faible | `create_draft` — brouillons seulement, envoi par l'utilisateur |
| Rituel mensuel : score de complétude suivi mois par mois (streak) | Faible | Réutilise le rapport existant |
| Autres boîtes mail (Outlook/M365) détectées dynamiquement | Moyen | Même logique de chasse, autre MCP |
| Détection de doublons de pièces (`remove_transaction_attachment` sous confirmation) | Moyen | Nettoyage inverse, mêmes garde-fous |
| Contrôle fin montant/TVA par lecture du PDF (multi-lignes, devises) | Moyen | Renforce le contrôle de cohérence |

## 🛡 Garde-fous

- **JAMAIS de justificatif fabriqué** : ni PDF généré, ni facture reconstituée, ni capture d'écran maquillée — sans original, la transaction reste en ❌ avec une piste
- **Jamais** de rattachement sans confirmation explicite du match affiché ; plusieurs candidats plausibles → le skill demande, il ne devine pas ; jamais de lot silencieux
- Rapprochement par `emitted_at` + tolérance de montant, tolérance annoncée dans chaque proposition
- MCP Gmail/Drive absents → annoncé clairement, inventaire Qonto pur livré quand même
- IBAN et numéros de carte masqués · pagination ≤ 50 partout

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-receipt-hunter.fr.html` · `docs/doc-qonto-receipt-hunter.fr.docx`.*
