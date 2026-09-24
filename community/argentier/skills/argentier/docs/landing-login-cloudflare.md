# Landing page + App login + Cloudflare — plan

> Brainstorm marketing (landing) + découpe produit (landing publique / app connectée)
> + architecture Cloudflare (front, backend, secrets). **Statut infra : à déployer hors
> session non-interactive** (Cloudflare MCP = auth OAuth requise). Le code est prêt à scaffolder.

---

## 0. ⚠️ Sécurité (à lire en premier)

Un mot de passe réel a été collé en clair dans le chat. **Change-le.** Et on ne met
**jamais** de mot de passe en dur dans le repo (il est poussé sur GitHub public).
L'auth se fait proprement :
- Mot de passe **hashé** (bcrypt/argon2 ou, pour le MVP, un hash stocké en secret).
- Le hash (et toutes les clés) vivent dans **Cloudflare Secrets** (`wrangler secret put`),
  lus côté Worker. Rien de sensible dans le repo ni dans le bundle front.
- Un seul compte autorisé au départ (`mameri.kevin@gmail.com`) → une liste d'e-mails
  autorisés en secret, pas en code.

---

## 1. Découpe produit : landing publique vs app connectée

| | **Landing (publique)** | **App (connectée)** |
|---|---|---|
| URL | `argentier.xyz` (racine) | `argentier.xyz/app` (derrière login) |
| Contenu | Pitch DAF autonome, démo, **voix ElevenLabs**, liste d'attente | Le dashboard actuel (audit, natures, leviers, **Autopilote**) |
| Source repo | nouveau `web/app/page.tsx` (landing) | l'actuel `Argentier.tsx` déplacé sous `/app` |
| Accès | ouvert à tous | e-mail autorisé + mot de passe (hash en secret) |

Le **pitch deck** actuel (elevator pitch bilingue + section Architecture) devient le
**cœur de la landing**, réhabillé façon page marketing.

## 2. Brainstorm marketing — la landing (angle : DAF autonome)

**Promesse (hero) :** « **Le DAF autonome que ton entreprise n'embauchera jamais.** »
Sous-titre : *Il lit ton compte Qonto, trouve l'argent qui fuit, et prouve chaque euro
économisé — tu approuves en 1 tap, il ne bouge jamais d'argent.*

**Structure de page (au-dessus de la ligne de flottaison → bas) :**
1. **Hero** — la promesse + 2 CTA : `Voir la démo (30 s)` · `Rejoindre la liste d'attente`.
   Fond : la carte d'Europe animée + bulles (déjà construite) — « 24 M PME, 0 DAF ».
2. **Le hook chiffré** — « 90 % des TPE n'auront jamais de DAF » + « plusieurs milliers d'€/an récupérés ».
3. **Démo interactive** — le flux **Autopilote** rejouable inline (observe→analyse→benchmark→
   **gate 1-tap**→preuve). C'est le wahou : le visiteur *clique Approuver* lui-même.
4. **Voix ElevenLabs** — un bouton « ▶ Écouter le pitch » qui lit l'elevator pitch (FR/EN),
   et sous-titres traduits. (Voir §5.)
5. **Preuve & confiance** — les 4 règles (read-only, moteur déterministe, zéro PII, source+date).
6. **Business model** — « agent gratuit · 5 % au succès sur les économies prouvées · pas d'économie, pas de coût ».
7. **Liste d'attente** — champ e-mail → stocké (Cloudflare KV/D1). Confirmation « Tu es sur la liste ».
8. **Footer** — Qonto × Anthropic MCP Hackathon.

**Ton (expert marketing) :** bénéfice d'abord, jargon zéro dans le hero, chiffres concrets,
1 seul CTA dominant (la liste d'attente), le reste en preuve. Bilingue FR/EN (marché européen).

## 3. Fonctionnalités « fake-it » (grisées + liste d'attente)

À afficher dans l'app **et** teaser sur la landing, grisées, avec `Rejoindre la liste d'attente` :
- **Simulation affacturage** — « combien débloquer en cédant tes factures clients ».
- **Balance âgée** — « tes créances clients par ancienneté (30/60/90 j) ».
- (extensible : prévision de trésorerie, récupération TVA automatisée…)

Objectif : mesurer la demande (signaux de liste d'attente) avant de construire — discovery
Cagan, pur signal produit.

## 4. Architecture Cloudflare

```
Cloudflare Pages  ── front Next.js (landing publique + /app)
Cloudflare Worker ── API + orchestrateur :
   • POST /api/waitlist         → écrit l'e-mail (KV ou D1)
   • POST /api/login            → vérifie e-mail autorisé + hash mdp (secret)
   • POST /api/analyze          → proxy vers Qonto (RO) + engine + Linkup
   • POST /webhooks/cma         → reçoit session.status_idled (gate async CMA)
Secrets (wrangler secret put)   → ANTHROPIC_API_KEY, QONTO_*, LINKUP_API_KEY,
                                   BRIGHTDATA_TOKEN, ELEVENLABS_API_KEY,
                                   AUTH_ALLOWED_EMAILS, AUTH_PASSWORD_HASH,
                                   CMA_WEBHOOK_SIGNING_KEY
Stockage                        → KV (waitlist, sessions) ou D1 (ledger multi-tenant)
```

**Login MVP (proprement) :**
- `AUTH_ALLOWED_EMAILS` = `mameri.kevin@gmail.com` (secret, extensible).
- `AUTH_PASSWORD_HASH` = hash argon2/bcrypt du mot de passe (généré **hors repo**), en secret.
- Le Worker compare `email ∈ allowed` && `verify(hash, password)` → pose un cookie de session signé.
- **Jamais** de mot de passe ni de hash dans le code versionné.

## 5. ElevenLabs — voix & traduction (BLOQUÉ ici)

`ElevenLabs` n'est **pas** dans les MCP connectés de cette session → je ne peux pas
l'activer. À faire via `/mcp` en session interactive (ou brancher l'API ElevenLabs
directement côté Worker avec `ELEVENLABS_API_KEY` en secret).
Usage prévu :
- **Text-to-Speech** de l'elevator pitch (FR/EN) sur la landing (bouton « Écouter »).
- **Traduction / dubbing** des sous-titres de la démo pour le marché européen.
Intégration : un endpoint Worker `POST /api/tts` qui appelle ElevenLabs et renvoie l'audio,
la clé restant côté serveur (jamais dans le front).

## 6. Bright Data (BLOQUÉ ici) — renfort règle 4

Dans l'allowlist mais non branché + MCP auth requise. Rôle : quand Linkup ne renvoie pas
de **prix daté**, scraper la vraie page pricing du marchand pour obtenir source + date.
Fallback : `linkup-search` → si `verified=false` → `brightdata scrape <pricing_url>` →
extraire prix + date. À câbler côté Worker avec `BRIGHTDATA_TOKEN` en secret.

## 7. Ordre de déploiement suggéré

1. Déplacer le dashboard sous `/app`, créer la landing sous `/`.
2. Waitlist (KV) + endpoint — le plus vite au marché (mesure la demande).
3. Login Worker (secrets) — hash hors repo.
4. Voix ElevenLabs + Bright Data (une fois les MCP/API branchés).
5. Autopilote réel sur CMA (voir `autopilote-cma-spec.md`).
