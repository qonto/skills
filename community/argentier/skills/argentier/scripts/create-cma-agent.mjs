// ---------------------------------------------------------------------------
// Crée un VRAI Claude Managed Agent (CMA) : environnement → agent → session →
// tâche réelle dans le sandbox → réponse. Raw HTTP (indépendant de la version SDK).
// Clé lue depuis web/.env.local. Beta header managed-agents-2026-04-01.
// ---------------------------------------------------------------------------

import fs from "node:fs";

const envText = fs.readFileSync(new URL("../web/.env.local", import.meta.url), "utf8");
const KEY = (envText.match(/^ANTHROPIC_API_KEY=(.+)$/m) || [])[1]?.trim();
if (!KEY) {
  console.error("❌ ANTHROPIC_API_KEY introuvable dans web/.env.local");
  process.exit(1);
}

const BASE = "https://api.anthropic.com";
const H = {
  "x-api-key": KEY,
  "anthropic-version": "2023-06-01",
  "anthropic-beta": "managed-agents-2026-04-01",
  "content-type": "application/json",
};

async function api(method, path, body) {
  const r = await fetch(BASE + path, {
    method,
    headers: H,
    body: body ? JSON.stringify(body) : undefined,
  });
  const t = await r.text();
  let j;
  try {
    j = JSON.parse(t);
  } catch {
    j = t;
  }
  if (!r.ok) {
    throw new Error(`${method} ${path} → ${r.status} : ${typeof j === "string" ? j : JSON.stringify(j)}`);
  }
  return j;
}

const sleep = (ms) => new Promise((res) => setTimeout(res, ms));

(async () => {
  console.log("1) Environnement (cloud)…");
  const env = await api("POST", "/v1/environments", {
    name: `argentier-${Date.now()}`,
    config: { type: "cloud", networking: { type: "unrestricted" } },
  });
  console.log("   ✓ env:", env.id);

  console.log("2) Agent Argentier…");
  const agent = await api("POST", "/v1/agents", {
    name: "Argentier Autopilote",
    model: "claude-sonnet-5",
    system:
      "Tu es Argentier, un agent DAF en LECTURE SEULE. Règles non négociables : " +
      "le moteur (code déterministe) calcule chaque euro, jamais toi ; tu ne bouges jamais d'argent ni ne fais d'action bancaire ; " +
      "zéro donnée personnelle ne part vers le web. Tu prépares, l'humain décide et envoie.",
    tools: [{ type: "agent_toolset_20260401" }],
  });
  console.log("   ✓ agent:", agent.id, "| version", agent.version);

  console.log("3) Session…");
  const session = await api("POST", "/v1/sessions", {
    agent: agent.id,
    environment_id: env.id,
    title: "Preuve CMA — Argentier",
  });
  console.log("   ✓ session:", session.id);
  console.log("   🔗 Console:", `https://platform.claude.com/workspaces/default/sessions/${session.id}`);

  console.log("4) Tâche réelle (sandbox, calcul déterministe)…");
  await api("POST", `/v1/sessions/${session.id}/events`, {
    events: [
      {
        type: "user.message",
        content: [
          {
            type: "text",
            text:
              "Dans ton sandbox : crée un fichier engine_demo.py qui annualise un abonnement de 40 € par mois " +
              "(règle : montant mensuel × 12), exécute-le avec python3, puis donne-moi le montant annuel obtenu. " +
              "Rappel : c'est le moteur qui calcule, pas toi — reprends le chiffre qu'il imprime.",
          },
        ],
      },
    ],
  });

  console.log("5) Attente de la réponse (provisioning + exécution)…");
  const seen = new Set();
  for (let i = 0; i < 30; i++) {
    await sleep(4000);
    let evs;
    try {
      evs = await api("GET", `/v1/sessions/${session.id}/events`);
    } catch (e) {
      console.log("   (poll)", e.message.slice(0, 120));
      continue;
    }
    for (const ev of evs.data || []) {
      if (seen.has(ev.id)) continue;
      seen.add(ev.id);
      if (ev.type === "agent.message") {
        const txt = (ev.content || []).filter((b) => b.type === "text").map((b) => b.text).join(" ").trim();
        if (txt) console.log("   🤖", txt.slice(0, 400));
      } else if (ev.type === "agent.tool_use" || ev.type === "agent.tool_result") {
        console.log("   🔧", ev.type, ev.name || "");
      } else if (ev.type === "session.status_idle") {
        console.log("   ⏸  idle:", JSON.stringify(ev.stop_reason || {}));
      }
    }
    const s = await api("GET", `/v1/sessions/${session.id}`).catch(() => null);
    if (s && s.status && s.status !== "running" && s.status !== "rescheduling" && i > 1) {
      console.log("   statut:", s.status);
      if (s.status !== "idle") break; // terminated → stop ; idle → une dernière lecture puis stop
      // si idle avec stop terminal, on sort au tour suivant
    }
  }

  console.log("\n✅ VRAI agent CMA créé.");
  console.log("   agent_id  :", agent.id);
  console.log("   env_id    :", env.id);
  console.log("   session_id:", session.id);
})().catch((e) => {
  console.error("\n❌ ÉCHEC CMA :", e.message);
  process.exit(1);
});
