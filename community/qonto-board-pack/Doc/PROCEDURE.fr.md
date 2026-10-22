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
1. **Gmail** (Connecteurs → Gmail) → le skill propose un **brouillon** dans ta boîte, soumis à ton accord explicite pour cet export
2. **Canva** (Connecteurs → Canva) → le skill propose l'export du deck, soumis à ton accord explicite
3. Rien de tout ça n'est requis : sans eux, tu obtiens le deck **HTML autoportant** + le texte de l'email prêt à coller

> ⚠️ Connecté ne veut pas dire autorisé. Par défaut : deck HTML local et texte d'email. Avant un export Canva ou un brouillon Gmail, le skill montre le contenu et le service/compte destinataire, explique que les données financières seront stockées hors de Qonto, puis attend ton accord explicite pour cet export. Valider la narration ne suffit pas. Refus ou accord ambigu → aucun export.

## 2️⃣ Utilisation mensuelle (le rituel de fin de mois, ~5 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Prépare mon rapport mensuel investisseurs** » | Question d'audience (banquier / investisseur / interne) + niveau de détail |
| 2 | Répondre (ex. « investisseurs, chiffres exacts ») | Chiffres du mois + comparaisons M-1 / année glissante + faits marquants, en tableaux |
| 3 | Lire la **narration** (3 § : highlights, chiffres, perspectives) | Le skill s'arrête et attend — c'est le checkpoint |
| 4 | Corriger ce qui doit l'être (« remplace “exceptionnel” par “solide” ») puis valider | Deck HTML 5-6 slides + texte d'email ; export Gmail/Canva soumis à un accord distinct sur le contenu et la destination |
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
| **Export Canva** | Design généré via le MCP Canva | Connecté et accord explicite pour cet export |
| **Email d'envoi** | **Brouillon** Gmail (jamais envoyé automatiquement) ou texte prêt à coller | Texte par défaut ; Gmail connecté + accord explicite → brouillon |

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
Aucun email n'est envoyé automatiquement. Les exports Canva et brouillons Gmail
autorisés transmettent du contenu hors de Qonto. Valider la narration autorise
la mise en forme, pas ces exports. Les textes renvoyés par les outils restent
des données, jamais des instructions. Le HTML échappe ces textes et ne charge
aucune ressource externe ni ne fait de requête réseau.
