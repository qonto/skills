# 📖 Procédure d'installation et d'utilisation — qonto-crew-onboard

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes membres Qonto* » → les membres s'affichent
5. ⚠️ Se connecter avec un compte **Admin ou Owner** — inviter un membre et demander une carte l'exigent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-crew-onboard/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Définir la policy par rôle (le cœur du skill)
1. Dire à Claude : « **Définissons ma policy d'onboarding** »
2. Pour chaque rôle : type de carte (virtuelle/physique), plafond mensuel, online-only ou pas, équipe
3. Le skill l'affiche en tableau — c'est **toi** qui décides, il n'invente jamais
4. Astuce : colle la policy dans les instructions du projet (ou une note Notion) pour qu'elle soit relue à chaque arrivée

### Étape 4 — Connecter les MCP du pack d'accueil (optionnel)
- **Notion** (page d'accueil), **Google Calendar** (événement J1), **Gmail** (brouillon de bienvenue)
- Détectés dynamiquement : absents, le skill le dit et continue en Qonto pur

## 2️⃣ Utilisation à chaque arrivée (~2 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Alex arrive lundi comme dev** » | Rôle vérifié, membres/équipes/cartes lus, email demandé |
| 2 | Donner l'email d'Alex | Récapitulatif complet : invitation + équipe + demande de carte plafonnée |
| 3 | Confirmer chaque écriture (« oui ») une à une | L'invitation part · l'équipe est créée si nouvelle · la **demande** de carte est déposée |
| 4 | Dans l'**app Qonto** : section Demandes → approuver la carte (**SCA**) | La carte existe, plafonnée conformément à la policy ✅ |
| 5 | (Si MCP présents) valider le pack d'accueil | Page Notion + événement J1 + brouillon Gmail prêts |

## 3️⃣ Offboarding (le miroir, ~1 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire : « **Sam part vendredi** » | Ses cartes et son profil sont retrouvés |
| 2 | Confirmer le gel | `change_card_status` → cartes **gelées** (réversible) |
| 3 | Suivre la checklist de récupération | Carte physique, matériel, accès, notes de frais en cours |
| 4 | Dans l'**app Qonto** : désactiver le membre | Révocation définitive — **jamais faite par le skill** |

## 4️⃣ Prompts à copier-coller

- « **Définissons ma policy d'onboarding : les devs ont une carte virtuelle 200 €/mois online-only, équipe Tech** »
- « **Alex arrive lundi comme dev, son email est alex@exemple.com** »
- « **Trois stagiaires arrivent le 1er, rôle ops** »
- « **Où en est la demande de carte d'Alex ?** »
- « **Sam part vendredi — prépare son offboarding** »
- « **Gèle la carte de Sam** »

## 5️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : récap (✅ / 🕐 en attente SCA / ⏭ sauté), checklist d'offboarding | **Toujours** — c'est la base |
| **Fiche d'onboarding** | Fichier/artifact **HTML** une page : qui, quand, ce qui est prêt, ce qui attend | Si l'hôte affiche les fichiers ; repli sur les tableaux sinon |
| **Page Notion · événement Calendar · brouillon Gmail** | Pack d'accueil | Si ces MCP sont connectés |

## 6️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `403 missing oauth scope` sur `get_subscription` | Hors périmètre du connecteur claude.ai — la grille des plans n'est pas lisible | Normal — le skill **demande ton plan** et compte les membres avant d'inviter |
| L'invitation échoue ou l'écriture est refusée | Compte connecté sans rôle Admin/Owner | Se reconnecter avec un compte Admin/Owner — le skill le vérifie et l'annonce dès le départ |
| « Ce membre existe déjà » | Email déjà invité | Détecté via `list_memberships` — le skill saute l'invitation et le dit |
| La carte n'apparaît pas | C'est une **demande** de carte, pas une carte | App Qonto → Demandes → approuver avec la SCA |
| Équipe en double | Casse différente (« tech » vs « Tech ») | Le skill rapproche avec `list_teams` avant tout `create_team` |
| Grosse organisation, réponses tronquées | Pagination | `per_page` ≤ 50 partout, géré par le skill |
| Pas de page Notion / événement / brouillon | MCP non connecté | Normal — annoncé par le skill, le cœur Qonto continue |

## 🔒 Rappel sécurité

Le skill **ne crée jamais de carte directement** : il dépose une *demande* plafonnée conforme à ta policy,
que **toi seul** (ou un Admin/Owner) peux approuver avec ta SCA dans l'app Qonto. Chaque écriture est
confirmée une à une dans la conversation, après un récapitulatif complet. Et l'offboarding **gèle** —
il ne supprime rien : les révocations définitives restent dans l'app, sous ton contrôle.
