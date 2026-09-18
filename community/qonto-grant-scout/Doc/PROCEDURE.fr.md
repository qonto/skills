# 📖 Procédure d'installation et d'utilisation — qonto-grant-scout

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
2. Vérifier : demander à Claude « *Cherche des datasets d'aides aux entreprises sur data.gouv* » → des résultats s'affichent

> ⚠️ Sans Datagouv, le skill fonctionne en **mode dégradé assumé** : profil de dépenses complet
> + familles d'aides génériques + les portails officiels à explorer. Il le dit clairement.

### Étape 3 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-grant-scout/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

## 2️⃣ Usage type (~5 min, à refaire chaque trimestre)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Quelles aides publiques je pourrais viser, vu mes dépenses réelles ?** » | Profil de l'entreprise (secteur, région, taille) + tableau des signaux de dépenses |
| 2 | Vérifier/corriger le profil affiché (secteur inféré ? région ?) | Le skill repart du profil corrigé — les recherches sont mieux ciblées |
| 3 | Laisser tourner la recherche Datagouv | Shortlist de pistes : dispositif · pourquoi ton compte matche · critères à confirmer · source datée · prochaine étape |
| 4 | Choisir une piste : « **Fais-moi la fiche de la piste OPCO** » | Bloc texte prêt à envoyer (au comptable, à l'OPCO, au guichet région) |
| 5 | **Vérifier auprès de l'organisme** avant tout dossier | Le skill fournit des pistes, jamais des droits acquis |

## 3️⃣ Prompts à copier-coller

- « **Quelles aides publiques je pourrais viser, vu mes dépenses réelles ?** » → le parcours complet
- « **Profil de ma boîte, vu par mon compte** » → profil + signaux seuls, sans recherche
- « **J'investis dans du matériel cette année — qu'est-ce qui existe dans ma région ?** » → recherche ciblée sur un poste
- « **Analyse mes dépenses de formation : des aides existent ?** » → le scénario vedette de la démo
- « **Refais le point : des nouvelles pistes depuis la dernière fois ?** » → re-croisement trimestriel

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : profil + signaux, shortlist sourcée et datée, limites | **Toujours** — c'est la base |
| **Grant radar** | Fichier/artifact **HTML** : signaux × familles d'aides, pistes aux intersections, tags 🟢🟡🔵 | Si l'hôte affiche les fichiers ; sinon repli automatique sur les tableaux |
| **Fiche par piste** | Bloc texte prêt à envoyer : signal, dispositif, critères à confirmer, source | Sur demande, pour chaque piste retenue |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue d'entrée | `bank_account_id`/`iban` manquant | Le skill appelle **toujours** `get_organization` d'abord |
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Normal — le skill utilise les labels (`list_labels`) à la place |
| Réponses énormes / tronquées | Pagination trop large | Le skill pagine `per_page` ≤ 50 partout |
| « Je ne trouve pas de dataset d'aides » | Référentiel indisponible ou renommé sur data.gouv.fr | Le skill élargit la recherche, puis bascule en mode dégradé (familles d'aides + portails officiels) en le disant |
| `query_resource_data` échoue sur une ressource | Ressource non tabulaire (PDF, CSV cassé) | La piste devient un lien sourcé vers la page du dataset — annoncé comme tel |
| Pistes datées / dispositif fermé | Dataset pas remis à jour | Chaque piste porte la date du dataset ; > ~18 mois = tag dégradé 🟡 — toujours vérifier à la source |
| Secteur vide dans le profil | `get_organization` sans code NAF | Le skill l'infère des flux et l'annonce ; corrige-le dans la conversation, il repart du bon |
| Dépenses carte mal datées | Rapprochement sur la mauvaise date | Le skill utilise `emitted_at`, pas `settled_at` (1-2 j d'écart) |

## 🔒 Rappel sécurité

Le skill est en **lecture seule** : aucune écriture Qonto, aucun dossier déposé, aucun engagement pris.
Côté données : seuls des **mots-clés génériques** (secteur, région, famille d'aide) partent vers Datagouv —
jamais un montant, un nom de contrepartie ou un IBAN. Et chaque piste est une **piste à vérifier** auprès
de l'organisme émetteur : le skill ne dit jamais « tu es éligible ».
