# 📖 Procédure d'installation et d'utilisation — qonto-sector-benchmark

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Connecter le MCP Datagouv (recommandé)
1. Même chemin : Paramètres → **Connecteurs** → chercher **Datagouv** (data.gouv.fr) → *Ajouter*
2. Vérifier : « *Cherche les statistiques structurelles d'entreprises INSEE sur data.gouv* » → des datasets s'affichent

> ⚠️ Sans Datagouv : le skill fonctionne quand même — ratios internes + auto-benchmark
> « toi vs toi il y a un an ». Il te le dira explicitement au lancement.

### Étape 3 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-sector-benchmark/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 4 — Avoir son code NAF sous la main (optionnel)
Il est sur le KBIS et sur l'avis SIRENE. Si `get_organization` ne l'expose pas, le skill te le demandera — ou le déduira de ton activité et **te le fera confirmer**.

## 2️⃣ Usage type (le rituel trimestriel, ~3 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Suis-je normal ? Compare mes ratios à mon secteur** » | Le skill lit l'organisation, confirme le secteur (NAF), annonce le mode (sectoriel ou interne) |
| 2 | Laisser tourner l'analyse (24 mois de transactions + factures) | Les 5 ratios réels s'affichent, calculs détaillés |
| 3 | Vérifier la liste des abonnements logiciels détectés | Tu corriges en une phrase si un tiers est mal classé |
| 4 | Lire la scorecard | Ratio · ta valeur · référence (source · millésime · granularité) · verdict · tendance N-1 |
| 5 | Creuser le constat principal (« pourquoi mes délais clients dérivent ? ») | Le skill détaille par client, sur les données Qonto |

## 3️⃣ Prompts à copier-coller

- « **Suis-je normal ? Compare mes ratios à mon secteur** » → le bulletin complet
- « **Mes clients me paient en combien de jours, et c'est bien ou pas ?** » → focus délai de paiement, référence sectorielle sourcée
- « **Est-ce que je paie trop d'abonnements logiciels pour une boîte comme la mienne ?** » → focus SaaS, liste détectée + verdict
- « **Compare-moi à moi-même il y a un an** » → auto-benchmark seul (marche partout, même sans Datagouv)
- « **Refais le bulletin en niveau division NAF** » → force la granularité supérieure si tu doutes de la classe exacte

## 4️⃣ Formats de sortie (où atterrit le bulletin ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Scorecard markdown : ratio · valeur · référence sourcée · verdict · tendance, + 2-3 constats narratifs + liste des sources | **Toujours** — c'est la base |
| **Scorecard interactive** | Fichier/artifact **HTML** : 5 jauges face aux fourchettes secteur, sources en bas de page | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli sur le markdown |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Normal — le skill classe par détection de récurrences + labels |
| « MCP Datagouv non détecté » | Connecteur absent ou déconnecté | Le skill continue en auto-benchmark ; reconnecter le connecteur pour le sectoriel |
| Aucun dataset au niveau de ma classe NAF | L'INSEE ne publie pas tout au niveau classe | Comparaison au niveau division, **annoncée sur la ligne** — comportement voulu |
| `query_resource_data` échoue sur une ressource | Ressource non tabulaire ou trop volumineuse | Le skill essaie une autre ressource du dataset ou un dataset agrégé — jamais un chiffre de mémoire |
| Délai clients « non calculable » | Peu ou pas de factures émises via Qonto | Le ratio n'est calculé que sur les factures Qonto ; facturer ailleurs = le dire au skill |
| Saisonnalité « indisponible » | Historique < 12 mois pleins | Honnête par conception — revenir dans quelques mois |
| Le secteur proposé est faux | NAF absent des données du compte, déduction erronée | Donner le bon code NAF dans la conversation — le skill le confirme toujours avant usage |

## 🔒 Rappel sécurité

Le skill est **100 % lecture seule** : il n'appelle aucun outil d'écriture — ni virement, ni facture,
ni modification. Rien à approuver, rien qui puisse bouger. Côté chiffres : chaque comparaison
sectorielle porte sa source, son millésime et sa granularité — s'il n'y a pas de référence fiable,
le skill le dit au lieu d'inventer.
