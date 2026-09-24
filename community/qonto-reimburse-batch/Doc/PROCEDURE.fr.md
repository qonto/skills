# 📖 Procédure d'installation et d'utilisation — qonto-reimburse-batch

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-reimburse-batch/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Brancher la source des demandes + définir la politique (recommandé)
1. **Optionnel** : connecter le MCP **Slack** ou **Notion** (même chemin que l'étape 1) — le skill lira le canal `#notes-de-frais` ou ta base de demandes. **Sans eux, tout marche quand même** : tu colles les demandes dans la conversation
2. Définir ta **politique de frais** une fois : « repas 30 €, repas client 90 €, taxi 50 €, matériel 150 € » (exemple inventé — mets tes propres plafonds)
3. S'assurer que chaque demande (ou ta fiche salariés) porte l'**IBAN** du salarié — le skill n'en invente jamais

## 2️⃣ Utilisation type (le rituel de fin de mois, ~5 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Rembourse les notes de frais du mois** » | Demandes collectées (Slack/Notion ou collage), tableau normalisé affiché |
| 2 | Le skill déroule les 3 contrôles (justificatif · doublon · politique) | Tableau des verdicts : ✅ dans le lot · ⚠️ en attente · ❌ doublon avec la transaction citée |
| 3 | Trancher les ⚠️ et ❌ (plafonner, accepter, rejeter) | Liste finale du lot arrêtée |
| 4 | Confirmer explicitement (« oui, crée la demande groupée ») | UNE demande créée : N virements en attente |
| 5 | Sur le **téléphone** : push Qonto → ouvrir → vérifier la note (le résumé du lot y est) → **approuver (SCA)** | Toute l'équipe remboursée d'un seul geste ✅ |

## 3️⃣ Prompts à copier-coller

- « **Rembourse les notes de frais du mois : lis le canal `#notes-de-frais`, vérifie chaque demande (justificatif, doublon carte, politique) et prépare la demande groupée.** »
- « **Voici notre politique de frais : repas 30 €, repas client 90 €, taxi 50 €, matériel 150 €. Applique-la aux contrôles.** » *(plafonds d'exemple — mets les tiens)*
- « **Voici 3 demandes en tableau markdown : [salarié · montant · date · catégorie · motif · IBAN · justificatif]. Vérifie doublons et justificatifs, puis prépare le lot.** »
- « **Cette demande de 129 € pour un écran — est-ce qu'elle n'a pas déjà été payée par la carte entreprise ?** »
- « **Où en est la demande groupée ?** » *(statut via `list_requests`)*

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : verdicts, contenu du lot, mises en attente | **Toujours** — c'est la base |
| **Demande groupée Qonto** | N virements en attente (section Demandes), résumé du lot dans la note, **visible à l'approbation SCA** | À chaque lot validé |
| **Rapport de remboursement** | Récap markdown (qui · combien · pourquoi rejeté, preuve) — ou artifact HTML si l'hôte affiche les fichiers | Après approbation |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `422` à la création du lot | Champ `credit_account_currency` manquant (non documenté) | Le skill l'envoie systématiquement |
| Refus d'une demande de test impossible | `decline_request` exige `request_type: "multi_transfers"` (au pluriel) | Géré par le skill |
| `list_transactions` échoue | `bank_account_id`/`iban` requis | `get_organization` d'abord — le skill le fait toujours |
| Doublon raté ou faux positif | Délai de règlement carte : `emitted_at` vs `settled_at` (1-2 j d'écart) | Fenêtre ±5 j sur `emitted_at` ; la présomption est citée, c'est toi qui tranches |
| Le canal Slack / la base Notion n'est pas lu(e) | MCP absent ou non connecté | Normal — mode dégradé : colle les demandes dans la conversation, les contrôles sont identiques |
| Un salarié absent du lot | IBAN manquant (le skill n'invente jamais) | Ajouter l'IBAN à la demande ou à la fiche salarié, relancer |
| Réponses lentes / tronquées | Pagination | `per_page` ≤ 50 partout — fait par le skill |

## 🔒 Rappel sécurité

Le skill **ne peut pas** déplacer d'argent. Il crée une *demande groupée*, que **toi seul** peux approuver
avec ta 2FA dans l'app Qonto — les N virements d'un geste, ou refus en un tap. La demande porte le résumé
complet du lot dans sa note — tu approuves en connaissance de cause. Et chaque rejet est documenté :
la transaction en doublon est citée, jamais un verdict silencieux.
