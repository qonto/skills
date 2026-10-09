# 📖 Procédure d'installation et d'utilisation — qonto-fraud-sentinel

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-fraud-sentinel/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — (Optionnel) Connecter Gmail
Même chemin que le MCP Qonto (Connecteurs → Gmail). Le skill le **détecte tout seul** : s'il est là, il propose un brouillon de digest quotidien ; sinon, il fonctionne en Qonto pur sans rien demander.

> 💡 Astuce : utiliser un **projet Claude dédié** (« Scan du matin ») — les contreparties marquées de confiance y restent mémorisées d'un jour à l'autre.

## 2️⃣ Utilisation quotidienne (la routine du matin, ~30 s)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Fais mon scan du matin** » | Baseline calibrée (3-6 mois) + dernières transactions passées au crible des 6 signaux |
| 2 | Lire le rapport : alertes triées 🔴🟠🟡 ou « RAS » chiffré | Chaque alerte = la transaction + le pourquoi (baseline) + l'action recommandée |
| 3 | Pour un faux positif (nouveau fournisseur légitime…) : « **confiance ACME** » | Mémorisé — plus d'alerte « jamais vu » pour cette contrepartie |
| 4 | Si une carte est en cause et que tu veux agir : « **oui, verrouille la carte** » | `change_card_status` verrouille la carte — réversible dans l'app à tout moment |

## 3️⃣ Utilisations ponctuelles

- « **Un truc bizarre sur mon compte cette semaine ?** » → scan élargi à 7 jours
- « **J'ai été prélevé deux fois par X ?** » → recherche ciblée de doublons sur cette contrepartie
- « **Ce débit de 249 €, c'est normal ?** » → comparaison à la baseline de la contrepartie et du poste
- « **Quels prélèvements SEPA sont nouveaux ce mois-ci ?** » → premiers passages de mandats

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableau markdown des alertes (transaction · signal · baseline · action · gravité) ou « RAS » avec fenêtre et profondeur de baseline | **Toujours** — c'est la base |
| **Rapport du matin** | Fichier/artifact **HTML** compact : alertes triées, baseline, état des cartes | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; repli automatique sur le tableau |
| **Digest email** | Brouillon Gmail du scan quotidien | Seulement si un MCP Gmail est détecté — optionnel |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue au premier appel | `bank_account_id`/`iban` manquant | Normal — le skill appelle **toujours** `get_organization` d'abord |
| Réponses énormes / tronquées | Pagination trop large | Le skill pagine `per_page` ≤ 50 partout |
| Doublons carte ratés ou faux doublons | Comparaison sur `settled_at` (1-2 j de décalage) | Le skill horodate les cartes sur **`emitted_at`** |
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Normal — le skill se rabat sur les catégories portées par les transactions et les labels |
| Trop d'alertes « jamais vu » | Compte jeune (< 3 mois) ou beaucoup de nouveaux fournisseurs | Mode prudent annoncé — marquer les contreparties légitimes de confiance, le bruit retombe en quelques jours |
| Pas de digest email | MCP Gmail absent | Optionnel — le cœur fonctionne en Qonto pur |

## 🔒 Rappel sécurité

Le skill **ne peut pas** déplacer d'argent — aucun scénario ne le permet. Sa seule écriture est un
**verrouillage de carte**, réversible, exécuté uniquement après ta confirmation explicite dans la
conversation. Le déblocage, l'opposition définitive, la révocation d'un mandat SEPA et le
remplacement de carte se font dans l'app Qonto, par toi. Et souviens-toi de l'éditorial du skill :
**un signal n'est pas une fraude** — c'est une invitation à vérifier, chiffres à l'appui.
