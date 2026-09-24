# 📖 Procédure d'installation et d'utilisation — qonto-board-pack

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-board-pack/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Connecter les MCP optionnels (recommandé, pas obligatoire)
1. **Gmail** (Connecteurs → Gmail) → le skill crée le **brouillon** d'email d'envoi directement dans ta boîte
2. **Canva** (Connecteurs → Canva) → le skill propose l'export du deck vers Canva
3. Rien de tout ça n'est requis : sans eux, tu obtiens le deck **HTML autoportant** + le texte de l'email prêt à coller

> ⚠️ Le skill détecte ces MCP dynamiquement : présents → il les utilise ; absents → il le dit une fois et continue. Le cœur marche en Qonto pur.

## 2️⃣ Utilisation mensuelle (le rituel de fin de mois, ~5 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Prépare mon rapport mensuel investisseurs** » | Question d'audience (banquier / investisseur / interne) + niveau de détail |
| 2 | Répondre (ex. « investisseurs, chiffres exacts ») | Chiffres du mois + comparaisons M-1 / année glissante + faits marquants, en tableaux |
| 3 | Lire la **narration** (3 § : highlights, chiffres, perspectives) | Le skill s'arrête et attend — c'est le checkpoint |
| 4 | Corriger ce qui doit l'être (« remplace “exceptionnel” par “solide” ») puis valider | Deck HTML 5-6 slides généré + email d'envoi rédigé (brouillon Gmail si connecté) |
| 5 | Relire le deck et le brouillon, joindre, **envoyer toi-même** | Le pack est parti — rien n'est jamais envoyé par le skill |

## 3️⃣ Utilisations ponctuelles

- « **Fais-moi le pack de juin pour mon banquier, en tendances seulement** » → pack calibré banquier, sans chiffres exacts
- « **Quels ont été les faits marquants du mois dernier ?** » → détection seule, sans pack
- « **Compare mes dépenses par poste sur les 3 derniers mois** » → tableau comparatif
- « **Refais la narration avec un ton plus prudent sur les perspectives** » → réécriture avant mise en forme

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (chiffres + deltas, postes, faits marquants) + narration 3 § | **Toujours** — c'est la base |
| **Deck HTML autoportant** | 5-6 slides, CSS pur, thème clair/sombre, zéro dépendance externe | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli sur les tableaux |
| **Export Canva** | Design généré via le MCP Canva | Si le MCP Canva est présent |
| **Email d'envoi** | **Brouillon** Gmail (jamais envoyé) ou texte prêt à coller | Gmail présent → brouillon ; sinon texte |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue d'emblée | `bank_account_id`/`iban` requis | Le skill appelle toujours `get_organization` d'abord |
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Normal — le skill groupe les dépenses par **labels** à la place |
| Réponses énormes / lenteur | Pagination trop large | Le skill pagine `per_page` ≤ 50 partout |
| Un « CA » anormalement élevé | Virements internes entre tes propres comptes comptés comme encaissements | Le skill les exclut du CA et du burn (débit/crédit appariés sur tes IBAN) |
| Dépenses carte à cheval sur deux mois | Délai de règlement 1-2 j (`emitted_at` vs `settled_at`) | Géré : fenêtre sur `settled_at`, recoupée par `emitted_at` en bord de mois |
| Pas de solde « relevé officiel » pour le mois | Relevé pas encore généré par Qonto | Le skill calcule le solde et **annonce la méthode** ; relevé utilisé dès qu'il existe |
| Pas de brouillon Gmail / pas d'export Canva | MCP non connecté | Normal — repli automatique : texte d'email + deck HTML |

## 🔒 Rappel sécurité

Le skill est en **lecture seule sur Qonto** : il n'utilise aucun outil d'écriture Qonto, jamais.
Il **n'envoie rien** : l'email est un brouillon, le deck est un fichier. La narration passe
**toujours** par ta relecture avant mise en forme — un rapport investisseurs ne s'envoie
jamais tout seul. C'est toi qui signes.
