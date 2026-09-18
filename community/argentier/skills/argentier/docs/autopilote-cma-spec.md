# Spec technique — Argentier en Autopilote (Claude Managed Agents)

> Implémentation de la feature du [PRD](./autopilote-PRD.md). Cible : **CMA (beta)**.
> Anthropic héberge la boucle + le sandbox ; toi tu ne gères ni scheduler, ni state.
> **Secrets → Cloudflare / vault CMA. Jamais dans le repo.**

---

## 1. Vue d'ensemble

```
                       ┌────────────────────────────────────────────┐
   Deployment (cron) ─▶│  Session  (Anthropic orchestration layer)  │
   • audit mensuel     │  Claude + boucle agent                     │
   • verify quotidien  └───────────────┬────────────────────────────┘
                                       │ tool calls
                                       ▼
                       Sandbox (bash/python) ── engine.py y tourne
                          │
              ┌───────────┼─────────────────────────────┐
              │           │                             │
      MCP Qonto (RO)   MCP Linkup            Memory store (par tenant)
      via vault        via vault             ledger decisions.json + profile.json
```

| Objet CMA | Rôle Argentier |
|---|---|
| **Agent** (versionné) | Le persona « DAF read-only » : model, system, tools, mcp_servers, skill `argentier-audit`. Créé 1×. |
| **Environment** | Sandbox cloud où tourne `engine.py`. |
| **Deployment** (cron) | Déclenche les sessions : 1 audit mensuel + 1 verify quotidien. |
| **Vault** (par client) | Creds MCP Qonto + Linkup (OAuth auto-refresh, jamais dans le sandbox). |
| **Memory store** (par client) | Le ledger `decisions.json` + `profile.json`, persistants entre sessions. |
| **Custom tool** `request_human_approval` | Le **gate async 1-tap** : la session s'idle, on notifie, l'humain décide. |

---

## 2. Agent — `argentier.agent.yaml`

```yaml
name: Argentier Autopilote
model: claude-opus-4-8
system: |
  Tu es Argentier, un agent DAF en LECTURE SEULE sur Qonto.
  Les 4 règles non négociables :
  1. Read-only Qonto : seuls les tools de lecture sont activés. Ne tente jamais d'écrire.
  2. engine.py calcule, jamais toi. Tu lances le moteur (bash) et tu reprends ses chiffres.
  3. Zéro PII vers le web : vers Linkup, seulement nom marchand + catégorie.
  4. Chaque prix affiché = source + date, sinon 1 retry puis « non vérifié ».
  Boucle : OBSERVE (Qonto 90j) → ANALYSE (engine.py) → BENCHMARK (Linkup) →
  RECOMMANDER (carte sourcée+datée) → pour chaque levier PRO optimisable, appelle
  request_human_approval et ATTENDS la décision → si approuvé, écris le livrable
  dans /mnt/session/outputs/ et inscris la décision (statut pending) dans le ledger
  monté (memory store) → sinon inscris le refus dans profile.json (refus_passes) et
  ne le re-propose jamais.
skills:
  - { type: custom, skill_id: argentier-audit, version: latest }   # engine.py + runbook
tools:
  # Sandbox : bash pour lancer engine.py, read/write pour le livrable
  - type: agent_toolset_20260401
    default_config: { enabled: true }
    configs:
      - { name: web_search, enabled: false }   # le web passe par Linkup, pas web_search
  # Qonto MCP — ALLOWLIST lecture seule (deny-by-default)
  - type: mcp_toolset
    mcp_server_name: qonto
    default_config: { enabled: false }
    configs:
      - { name: get_organization, enabled: true }
      - { name: list_transactions, enabled: true }
      - { name: list_labels, enabled: true }
      - { name: list_transaction_attachments, enabled: true }
  # Linkup MCP — benchmark, egress marchand+catégorie seulement, gate humain
  - type: mcp_toolset
    mcp_server_name: linkup
    default_config: { enabled: false }
    configs:
      - { name: linkup-search, enabled: true }
  # Le gate humain (custom → exécuté côté orchestrateur)
  - type: custom
    name: request_human_approval
    description: >-
      Soumet UNE recommandation d'action à l'humain et attend sa décision.
      À appeler pour chaque levier PRO optimisable, une fois par levier.
    input_schema:
      type: object
      properties:
        marchand:        { type: string }
        action:          { type: string, enum: [cancel, downgrade, switch, consolidate, renegotiate] }
        montant_mensuel: { type: number }
        montant_annuel:  { type: number }
        alternative:     { type: string }
        source_url:      { type: string }
        source_date:     { type: string }
      required: [marchand, action, montant_mensuel, montant_annuel]
mcp_servers:
  - { type: url, name: qonto,  url: https://<endpoint-mcp-qonto> }
  - { type: url, name: linkup, url: https://<endpoint-mcp-linkup> }
```

> **Read-only, prouvé par construction :** l'allowlist `mcp_toolset` (deny-by-default +
> opt-in explicite) est l'équivalent CMA du `deny > allow` de `.claude/settings.json`.
> Aucun tool d'écriture Qonto n'est activé. Et Qonto exige de toute façon la SCA du
> membre pour tout mouvement d'argent.

## 3. Environment — `argentier.environment.yaml`

```yaml
name: argentier-sandbox
config:
  type: cloud
  networking:
    type: limited
    allow_mcp_servers: true          # Qonto + Linkup joignables
    allowed_hosts: []                # rien d'autre ne sort
```

## 4. Vault + Memory store (par tenant)

```python
# Vault : creds MCP du client (jamais dans le sandbox — substitués à l'egress)
vault = client.beta.vaults.create(display_name=f"argentier-{tenant_id}")
client.beta.vaults.credentials.create(vault.id, auth={
    "type": "mcp_oauth", "mcp_server_url": "https://<endpoint-mcp-qonto>",
    "access_token": "...", "refresh": { ... },   # OAuth Qonto du client
})
client.beta.vaults.credentials.create(vault.id, auth={
    "type": "mcp_oauth", "mcp_server_url": "https://<endpoint-mcp-linkup>",
    "access_token": "...", "refresh": { ... },
})

# Memory store : le ledger + le profil, persistants entre sessions
store = client.beta.memory_stores.create(
    name=f"argentier-ledger-{tenant_id}",
    description="Ledger des décisions (proven/pending) + profil (refus, intouchables).",
)
```

## 5. Les deux deployments (cron)

```python
# (1) AUDIT — mensuel : trouve → gate → prépare
client.beta.deployments.create(
    name=f"argentier-audit-{tenant_id}",
    agent=agent.id, environment_id=env.id,
    initial_events=[{ "type": "user.message", "content": [{ "type": "text",
        "text": "Lance l'audit mensuel : OBSERVE 90j → engine → benchmark → gate." }]}],
    resources=[{ "type": "memory_store", "memory_store_id": store.id, "access": "read_write" }],
    vault_ids=[vault.id],
    schedule={ "type": "cron", "expression": "0 8 1 * *", "timezone": "Europe/Paris" },  # le 1er à 08:00
)

# (2) VERIFY — quotidien : sweep de toute décision dont la preuve est due
client.beta.deployments.create(
    name=f"argentier-verify-{tenant_id}",
    agent=agent.id, environment_id=env.id,
    initial_events=[{ "type": "user.message", "content": [{ "type": "text",
        "text": "Sweep verify : pour chaque décision du ledger dont preuve_attendue_le <= aujourd'hui, "
                "relis 90j, compare, passe pending → proven (ou laisse pending) avec le delta réel." }]}],
    resources=[{ "type": "memory_store", "memory_store_id": store.id, "access": "read_write" }],
    vault_ids=[vault.id],
    schedule={ "type": "cron", "expression": "0 9 * * *", "timezone": "Europe/Paris" },
)
```

> **Pourquoi un verify quotidien plutôt que « J+30 » exact ?** Un cron ne peut pas
> planifier dynamiquement « 30 j après chaque action ». Le sweep quotidien lit le
> ledger et ne traite que les entrées arrivées à échéance (`preuve_attendue_le`).
> Plus robuste, idempotent, et ça survit aux ratés. (Le PRD parle de « J+30 » —
> c'est l'expérience utilisateur ; l'implémentation est un sweep quotidien.)

## 6. Le gate async 1-tap (le cœur produit)

```
Session audit :
  OBSERVE (Qonto RO) → engine.py (sandbox) → BENCHMARK (Linkup)
    └─▶ pour chaque levier : appelle request_human_approval(...)
          └─▶ agent.custom_tool_use émis → session IDLE (stop_reason: requires_action)

Webhook  session.status_idled  ──▶  backend (Cloudflare Worker)
  1. fetch les events, trouve le agent.custom_tool_use (name = request_human_approval)
  2. push/email au client : la carte + [ Approuver ] [ Refuser ]  (deep-link signé)

Client tape Approuver / Refuser
  └─▶ backend : sessions.events.send(user.custom_tool_result,
                  tool_use_id = <event.id>, content = { approved: true|false })
        └─▶ session RESUME :
              approved → écrit le draft dans /mnt/session/outputs/ + ledger pending
              refused  → profile.json.refus_passes += marchand (jamais re-proposé)
```

Orchestrateur (extrait — patterns CMA : stream-first, idle-gate, dedupe) :

```python
def handle_idle_webhook(session_id):
    # thin payload → on fetch
    for ev in client.beta.sessions.events.list(session_id).data:
        if ev.type == "agent.custom_tool_use" and ev.name == "request_human_approval":
            notify_user(session_id, ev.id, ev.input)   # push app / email deep-link

def on_user_decision(session_id, tool_use_id, approved, reason=None):
    client.beta.sessions.events.send(session_id, events=[{
        "type": "user.custom_tool_result",
        "custom_tool_use_id": tool_use_id,
        "content": [{ "type": "text", "text": json.dumps(
            {"approved": approved, "reason": reason}) }],
    }])

def collect_drafts(session_id):
    # après idle end_turn : récupère les livrables
    for f in client.beta.files.list(scope_id=session_id,
                                    betas=["managed-agents-2026-04-01"]).data:
        save_to_app(client.beta.files.download(f.id))
```

**Gate d'idle correct** (piège classique CMA) : ne pas casser sur `session.status_idle`
seul — la session s'idle transitoirement. Casser sur `status_terminated`, ou `status_idle`
avec `stop_reason.type != "requires_action"`. Sur `requires_action` → on gère la décision.

## 7. Mapping aux 4 règles (traçabilité)

| Règle | Où c'est câblé dans CMA |
|---|---|
| 1. Read-only Qonto | allowlist `mcp_toolset` deny-by-default (aucun tool d'écriture activé) |
| 2. engine.py calcule | `engine.py` packagé dans le skill, exécuté via `bash` dans le sandbox |
| 3. Zéro PII web | seul `linkup-search` activé ; le system prompt impose marchand+catégorie |
| 4. Prix = source+date | passe de vérification dans le runbook du skill ; sinon « non vérifié » |

## 8. Secrets → Cloudflare (jamais dans le repo)

- Clé API Anthropic, tokens OAuth Qonto/Linkup, signing key des webhooks : **Cloudflare
  secrets** (`wrangler secret put`), lus par le Worker orchestrateur.
- Le Worker : reçoit le webhook `session.status_idled`, vérifie la signature HMAC
  (`webhooks.unwrap`), notifie l'utilisateur, renvoie `user.custom_tool_result`.
- Rien de sensible ne descend dans le sandbox : les creds MCP vivent dans le **vault CMA**
  et sont substitués à l'egress.

## 10. Preuve live (2026-07-13)

Un vrai agent CMA a été créé et exécuté via [`scripts/create-cma-agent.mjs`](../scripts/create-cma-agent.mjs)
(raw HTTP, beta `managed-agents-2026-04-01`, clé Anthropic locale) :

- `agent_id  : agent_01FWBSaAxykzZFe1xEECdpYG`
- `env_id    : env_01D6AWTbu6CnzT3vaKqck2mV`
- `session_id: sesn_01JGjFuaG3sXmpUxKX7T4rHE`

L'agent a provisionné un sandbox, écrit + exécuté `engine_demo.py` (annualisation ×12) et
rapporté **480 €/an** — la règle « le moteur calcule, jamais le LLM » démontrée sur CMA.
Version minimale (agent_toolset seul). Pour l'autopilote complet : ajouter MCP Qonto/Linkup
(via vault), le custom tool `request_human_approval` (gate), et les deployments cron (§5).

## 9. Bloqueurs de cette session

- La création réelle (agents/deployments/vaults) exige des appels API + auth interactive
  → à exécuter hors session non-interactive. Ce doc est prêt à appliquer.
- Le Worker Cloudflare : scaffold séparé (voir `docs/landing-login-cloudflare.md`).
