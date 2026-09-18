# 🧮 qonto-infra-margin — Ton infra te coûte combien, par utilisateur ?

> Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> L'angle « wait, that's genius » pour les founders tech : le MRR, tout le monde le connaît ; le **coût d'infra par utilisateur**, personne. **100 % lecture, zéro écriture** — côté Qonto comme côté produit.

---

## 🎯 Le pitch

Un founder SaaS sait réciter son MRR. Demande-lui ce que son infra lui coûte **par utilisateur** : silence. Les factures Vercel, Supabase, OpenAI, AWS partent en prélèvement carte, se noient dans les débits, et la marge brute dérive sans que personne ne la regarde. `qonto-infra-margin` répond avec ce qui est réellement sorti du compte :

1. **Débits infra isolés et classés** — Vercel, Supabase, Sentry, OpenAI, Anthropic, AWS, Scaleway, OVH… reconnus par la culture générale de Claude **dès la première occurrence**, graphies normalisées (AWS EMEA SARL = AMZN WEB SERVICES = AWS), classés par famille : cloud, data, IA, observabilité, tooling
2. **Croisement avec la télémétrie produit** — via les MCP connectés : Vercel (projets, déploiements), Supabase (projets, taille de base, nombre d'utilisateurs via un `SELECT count` en lecture seule), Sentry en option
3. **Unit economics réel** — €/utilisateur, €/projet (prorata annoncé), dérive de marge brute mois par mois face aux encaissements
4. **Les side-projects qui saignent** — facturés tous les mois mais **zéro déploiement depuis 90 jours**, bases sans utilisateurs sur un palier payant, API IA qui croît plus vite que les users

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord) | ✅ |
| Pays | **Universel** — l'analyse infra marche à l'identique pour tous les pays Qonto (FR, DE, ES, IT, AT, NL, BE, PT). La vérité, c'est le débit du compte (côté EUR des factures USD, change inclus) | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| MCP Vercel | `list_projects` + `list_deployments` → allocation par projet, projets morts détectés | ⭕ recommandé — sinon mode dégradé annoncé |
| MCP Supabase | `list_projects` + `execute_sql` (SELECT count **lecture seule**, table confirmée par toi) → €/utilisateur mesuré | ⭕ recommandé — sinon mode dégradé annoncé |
| MCP Sentry | Volume d'erreurs par projet, en contexte | ⭕ optionnel |
| Historique ≥ 12 mois | La tendance et les plans annuels se voient sur 12-36 mois ; en dessous, dégradation honnête | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Identité & comptes** : `get_organization` d'abord — comptes, devises, pays. Rien en dur
2. **Débits infra isolés** (12-24 mois, jusqu'à 36 pour les plans annuels, pagination ≤ 50) : fournisseurs reconnus sans liste de mots-clés à maintenir, rapprochés des factures fournisseurs quand elles existent, cartes rapprochées par `emitted_at` (pas `settled_at`)
3. **Télémétrie produit** : MCP Vercel/Supabase/Sentry **détectés dynamiquement**. Absents → le skill le dit et continue en Qonto pur : classification + total/mois + tendance, déjà utile
4. **Allocation par projet** : factures Supabase souvent par projet ; facture Vercel = niveau équipe → **prorata par activité de déploiement, règle affichée sur la ligne**. Les coûts sans clé saine restent dans un panier « partagé » visible
5. **Unit economics** : total/mois + tendance, €/utilisateur (seulement si un **vrai comptage** a été mesuré), €/projet, dérive de marge brute face au MRR déclaré ou aux encaissements (annoncés comme proxy)
6. **Les saignées** : projets facturés sans déploiement depuis 90 j, bases vides payantes, dérive API IA → rapport chiffré + dashboard

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**100 % lecture, des deux côtés** : aucun outil d'écriture Qonto n'est appelé, jamais. Et côté produit, `execute_sql` est bridé à des `SELECT count` unitaires, en lecture seule, sur une table que **tu** confirmes avant exécution — jamais de DDL/DML, jamais de table devinée en silence.

## 🗂 Familles de fournisseurs reconnues (exemples, jamais exhaustif)

| Famille | Fournisseurs typiques |
|---|---|
| Cloud & hosting | AWS, Google Cloud, Azure, Scaleway, OVHcloud, Hetzner, DigitalOcean, Fly.io, Railway, Render, Heroku |
| Frontend & edge | Vercel, Netlify, Cloudflare |
| Data & backend | Supabase, MongoDB Atlas, Neon, PlanetScale, Firebase, Upstash |
| API IA | OpenAI, Anthropic, Mistral, Replicate, ElevenLabs, fal.ai, Hugging Face |
| Observabilité | Sentry, Datadog, Better Stack, Grafana Cloud |
| Dev tooling | GitHub, GitLab, Docker, npm, JetBrains |

C'est la force de l'approche : **pas de dictionnaire à maintenir** — un nouveau fournisseur (une API IA sortie le mois dernier) est reconnu à sa première facture. En cas de doute (revendeur ? agence ?), le skill demande une fois au lieu de classer en silence.

## 📤 Formats de sortie (où atterrit l'analyse ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : P&L infra (fournisseur × mois), unit economics (€/user, €/projet), liste des saignées | **Toujours** — c'est la base |
| **Dashboard interactif** | Fichier/artifact **HTML** : barres empilées par famille, jauge €/utilisateur, courbe de dérive de marge, spotlight sur les projets qui saignent | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur les tableaux |
| **Mode dégradé** | Mêmes tableaux, sans €/user ni allocation par projet — annoncé clairement | Sans MCP Vercel/Supabase |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : le MRR que tout le monde connaît → les débits infra isolés → la télémétrie produit branchée → **la révélation** (€/utilisateur réel + le side-project qui saigne depuis des mois) → le dashboard. Le script détaillé (textes à dire, checklist tournage, sous-titres EN) est dans **`_SCRIPT-VIDEO.md`** — fichier interne, **exclu de la PR**.

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| MCP Stripe/paiements pour un MRR mesuré (plus de proxy) | Faible | Détection dynamique, même logique que Vercel/Supabase |
| Alerte mensuelle « ta marge brute a dérivé de +N points » | Moyen | Rituel du 1er du mois, comme qonto-tax-pilot |
| Benchmark interne : €/user de ce mois vs il y a 12 mois | Faible | Réutilise l'historique déjà scanné |
| Suggestion de rightsizing par fournisseur (avec pricing vérifié en ligne) | Moyen | Jamais depuis la mémoire du modèle — pricing vérifié au moment T |
| Croisement avec qonto-subscription-audit (doublons d'outils infra) | Faible | Les deux skills partagent la détection de récurrences |

## 🛡 Garde-fous

- **Jamais de métrique produit inventée** : pas de comptage mesuré → pas de €/utilisateur, dit clairement. Les exemples des docs sont **fictifs et annoncés comme tels**
- **Allocation = choix éditorial affiché** : tout prorata de coût partagé est annoncé sur la ligne, jamais silencieux
- **SQL en lecture seule** : `execute_sql` limité à des `SELECT count` unitaires, sur une table confirmée par l'utilisateur
- Pricing fournisseur jamais affirmé de mémoire — les chiffres du compte, oui ; « tu es sur le mauvais plan », non (vérifier le pricing courant d'abord)
- IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout · dégradation honnête (pas de MCP, historique court)

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-infra-margin.fr.html` · `docs/doc-qonto-infra-margin.fr.docx`.*
