# 📖 Procédure d'installation et d'utilisation — qonto-tax-pilot

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-tax-pilot/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Créer le sous-compte impôts (recommandé)
1. Dans l'**app Qonto** : Comptes → **Créer un sous-compte**
2. Le nommer avec un mot-clé reconnaissable : « **Impôts & TVA** », « Taxes », « TVA »…
3. C'est tout — le skill le **détectera automatiquement** par son nom

> ⚠️ Cette étape est manuelle car le MCP Qonto n'a pas d'outil de création de compte.
> Sans sous-compte : le skill calcule et affiche tout, mais ne propose pas de virement.

## 2️⃣ Utilisation mensuelle (le rituel du 1er du mois, ~3 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Provisionne mes impôts du mois** » | Calcul TVA nette + IS/12 + CFE/12, détail affiché |
| 2 | Lire le détail (collectée, déductible, tags de confiance) | Tu sais exactement d'où vient chaque euro |
| 3 | Confirmer explicitement (« oui, crée la demande ») | Demande de virement créée vers le sous-compte |
| 4 | Sur l'**iPhone** : notification push Qonto → ouvrir → vérifier la note (le calcul y est) → **approuver (SCA)** | L'argent est provisionné ✅ |

## 3️⃣ Utilisations ponctuelles

- « **Où en sera ma tréso fin septembre ?** » → projection 90 j + échéancier fiscal
- « **Quand tombe ma prochaine TVA et combien ?** » → échéancier daté et chiffré
- « **Et si mon client paie avec 30 jours de retard ?** » → simulation what-if
- « **Je peux me permettre cet achat de 5 000 € ?** » → impact sur le point bas

## 4️⃣ Formats de sortie (où atterrit l'échéancier ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (échéancier, provision, alertes) | **Toujours** — c'est la base |
| **Dashboard interactif** | Fichier/artifact **HTML** : courbe 90 j, échéancier avec ✅/⚠️, jauge du coffre | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur les tableaux |
| **Note de la demande Qonto** | Texte joint à la demande de virement, **visible au moment de l'approbation SCA** | À chaque provision créée |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `422` à la création de la demande | Champ `credit_account_currency` manquant (non documenté) | Le skill l'envoie systématiquement |
| Refus d'une demande de test impossible | `decline_request` exige `request_type: "multi_transfers"` (au pluriel) | Géré par le skill |
| Le sous-compte n'est pas détecté | Nom sans mot-clé (taxe/tax/impôt/TVA) | Renommer le sous-compte dans l'app |
| Pas de notification push | Notifs Qonto désactivées | App Qonto → Réglages → Notifications |

## 🔒 Rappel sécurité

Le skill **ne peut pas** déplacer d'argent. Il crée une *demande*, que **toi seul** peux approuver
avec ta 2FA dans l'app Qonto. Tu peux la refuser en un tap. Chaque demande contient le calcul
complet dans sa note — tu approuves en connaissance de cause.
