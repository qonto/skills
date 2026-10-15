# 📖 Procédure d'installation et d'utilisation — qonto-brand-shield

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-brand-shield/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Accès INPI (optionnel)
1. L'API de data.inpi.fr demande un **compte INPI** puis une **demande d'accès API** (formulaire sur data.inpi.fr) — ce n'est pas immédiat
2. **Sans cet accès, le skill fonctionne quand même** : il produit tout le côté financier, puis te donne un lien de recherche pré-rempli sur data.inpi.fr — la vérification manuelle prend ~2 minutes
3. Le skill n'intègre au rapport **que** ce que l'API ou toi lui rapportez — jamais de scraping, jamais de supposition

## 2️⃣ Utilisation type (~5 min, vérification INPI comprise)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Ma marque est-elle protégée ?** » | Scan 12-36 mois → cumul d'investissement par marque (design, domaines, pub, impression) |
| 2 | Lire le tableau (postes, montants, tags 🟢🟡) | Tu sais combien la marque t'a déjà coûté, poste par poste |
| 3 | Cliquer le lien data.inpi.fr pré-rempli, regarder 2 min, rapporter ce que tu vois | Statut de protection intégré au rapport (déposée ? par toi ? classes ? renouvellement ?) |
| 4 | Lire l'**exposition** + le **dossier de pré-dépôt** (nom, classes suggérées, coût indicatif) | Décision éclairée : déposer (~190-270 €) ou assumer le risque |

## 3️⃣ Utilisations ponctuelles

- « **Combien j'ai investi dans ma marque depuis 18 mois ?** » → cumul par marque et par poste
- « **Suggère-moi mes classes de Nice** » → 1-3 classes depuis l'activité réelle, à valider
- « **Prépare mon dossier de pré-dépôt INPI** » → nom, classes, coût indicatif, lien inpi.fr
- « **Mon renouvellement de marque approche-t-il ?** » → fenêtre des 10 ans (si le dépôt est connu)

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (investissement, statut, exposition, alertes) | **Toujours** — c'est la base |
| **One-pager interactif** | Fichier/artifact **HTML** : jauge d'exposition, postes, statut INPI, dossier | Si l'hôte affiche les fichiers ; sinon repli automatique sur les tableaux |
| **Dossier de pré-dépôt** | Texte structuré prêt à emporter sur inpi.fr | À chaque marque non protégée |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue | L'outil exige `bank_account_id`/`iban` | Le skill appelle `get_organization` d'abord — toujours |
| Réponses énormes / lenteur | Pagination trop large | Le skill pagine `per_page` ≤ 50, par fenêtres de 3 mois |
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Normal — le skill classe par tiers + libellés, pas par catégories |
| Le justificatif ne donne pas le nom de marque | Document sans mention exploitable | Repli sur libellé + tiers ; rattachement tagué 🟡 |
| Domaines non vus comme dépense annuelle | Historique trop court | Les cadences annuelles se détectent sur 24-36 mois |
| « Je n'ai pas d'accès API INPI » | Compte + demande d'accès requis | Mode dégradé assumé : lien pré-rempli data.inpi.fr + checklist 2 min |

## 🔒 Rappel sécurité

Le skill est **100 % lecture** : il ne crée aucune écriture MCP — pas de virement, pas de facture,
rien à approuver. Le dépôt de marque se fait sur inpi.fr, par toi, après validation humaine.
La similarité de marques est une alerte indicative, **pas un avis juridique** : pour le dépôt,
un conseil en propriété industrielle est recommandé.
