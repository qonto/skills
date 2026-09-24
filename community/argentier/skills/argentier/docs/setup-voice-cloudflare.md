# Setup — Voix ElevenLabs + Cloudflare

> Ce qui est **déjà branché dans le code** vs ce qui **te reste à faire** (les 2 exigent
> une action interactive que je ne peux pas faire depuis une session non-interactive).

---

## 1. ElevenLabs — voix

### ✅ Déjà fait (dans le code)
- Route serveur **`/api/voice`** (TTS) : la clé `ELEVENLABS_API_KEY` reste **côté serveur**, jamais exposée au client. Testée → renvoie du `audio/mpeg`.
- Bouton flottant **« 🔊 Explique-moi »** : lit une explication de la page **dans la langue courante** (FR/EN/DE/ES/IT), avec le chiffre du hero.
- **Widget Q&A conversationnel** scaffoldé : s'active **automatiquement** dès que `NEXT_PUBLIC_ELEVENLABS_AGENT_ID` est renseigné (suit la langue via `override-language`).

### ⚠️ À faire toi
1. **RÉGÉNÉRER la clé** `sk_f3a9…` (elle a été collée en clair → compromise). Dashboard ElevenLabs → API Keys → Regenerate. Mets la **nouvelle** clé dans `web/.env.local` (gitignoré) et en **secret Cloudflare** pour la prod.
2. **Créer un agent conversationnel PUBLIC** (pour le Q&A vocal) :
   - elevenlabs.io → *Conversational AI* → *Create Agent*.
   - System prompt : décris Argentier (DAF autonome read-only, run-rate, leviers, Autopilote, 4 règles). Active le multilingue.
   - **Authentication disabled** (le widget public l'exige).
   - Copie l'**Agent ID** → `NEXT_PUBLIC_ELEVENLABS_AGENT_ID=` dans `web/.env.local`.
3. (Optionnel) Voix perso : `ELEVENLABS_VOICE_ID=` (sinon voix multilingue par défaut).

Le widget s'appuie sur `https://unpkg.com/@elevenlabs/convai-widget-embed` (chargé à la volée).

---

## 2. Cloudflare — backend / frontend

### Pourquoi je n'ai pas pu le faire d'ici
Le setup Cloudflare (d'après `developers.cloudflare.com/agent-setup/prompt.md`) passe par les **skills + serveurs MCP Cloudflare**, avec **OAuth au premier appel d'outil**. Cette session est **non-interactive** → je ne peux pas faire le flux OAuth. À lancer depuis une session interactive.

### À faire toi (session interactive)
```bash
# 1. Installer skills + MCP Cloudflare (Claude Code)
claude plugin marketplace add cloudflare/skills
claude plugin install cloudflare@cloudflare
/reload-plugins            # dans Claude
# → au 1er appel d'un outil Cloudflare, l'OAuth s'ouvre dans le navigateur

# 2. Déployer (wrangler)
npm i -D wrangler@4.110.0
npx wrangler@4.110.0 login # OAuth navigateur
```

### Architecture cible (déjà décrite dans landing-login-cloudflare.md)
- **Cloudflare Pages** → le front Next.js (landing publique + `/app`).
- **Cloudflare Worker** → les routes API (`/api/analyze`, `/api/benchmark`, `/api/letter`, `/api/voice`) + l'orchestrateur CMA (webhook `session.status_idled` → gate 1-tap).
- **Secrets** (`wrangler secret put`) — **jamais dans le repo** :
  `ANTHROPIC_API_KEY`, `LINKUP_API_KEY`, `QONTO_*`, `ELEVENLABS_API_KEY`,
  `AUTH_ALLOWED_EMAILS`, `AUTH_PASSWORD_HASH`, `CMA_WEBHOOK_SIGNING_KEY`.
- **KV / D1** → waitlist + ledger multi-tenant.

> Note : les routes `/api/*` actuelles sont des Route Handlers Next.js. Sur Cloudflare
> Pages, elles tournent en **Pages Functions** (runtime edge) ou sont portées en Worker.
> `/api/voice` (fetch ElevenLabs) marche tel quel sur le runtime edge.

---

## 3. Sécurité — rappel
- **2 clés exposées en clair** dans le chat (ElevenLabs + un mot de passe perso) → **régénère/change les deux**.
- Toutes les clés/secrets → `.env.local` (local, gitignoré) + **secrets Cloudflare** (prod). Jamais dans le repo (poussé sur GitHub public).
