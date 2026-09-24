/// <reference types="@cloudflare/workers-types" />
// ---------------------------------------------------------------------------
// Argentier MCP — serveur MCP sur Cloudflare (McpAgent).
// Expose le MOTEUR DÉTERMINISTE d'Argentier comme outils MCP : n'importe quel
// client MCP (Claude, un agent CMA, l'agent vocal) peut auditer des flux, sans
// que le LLM ne calcule un seul euro (règle #2). 100 % déterministe.
// ---------------------------------------------------------------------------

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { McpAgent } from "agents/mcp";
import { z } from "zod";
import { build } from "./lib/engine";
import { categorizeByRules, classifyEI, type MerchantInput } from "./lib/categorize";
import type { Tx } from "./lib/types";

const RULES = [
  "1. Read-only Qonto : seuls les tools de lecture. Aucune écriture, aucun mouvement d'argent.",
  "2. Le moteur (code déterministe) calcule chaque euro, jamais le LLM.",
  "3. Zéro PII vers le web : seulement nom marchand + catégorie.",
  "4. Chaque prix affiché = source + date, sinon « non vérifié ».",
];

export class ArgentierMCP extends McpAgent<Env, Record<string, never>, Record<string, never>> {
  server = new McpServer({ name: "argentier-engine", version: "1.0.0" });
  initialState = {};

  async init() {
    // 1) Les 4 règles non négociables (contexte pour l'agent appelant).
    this.server.registerTool(
      "argentier_rules",
      { description: "Renvoie les 4 règles non négociables d'Argentier.", inputSchema: {} },
      async () => ({ content: [{ type: "text", text: RULES.join("\n") }] }),
    );

    // 2) Classification EI d'un marchand (miroir déterministe de engine.py).
    this.server.registerTool(
      "argentier_classify_ei",
      {
        description: "Classe un marchand en PRO / PERSO / A-CLARIFIER (déterministe, mots-clés).",
        inputSchema: { merchant: z.string().describe("Nom du marchand") },
      },
      async ({ merchant }) => ({
        content: [{ type: "text", text: classifyEI(merchant) }],
      }),
    );

    // 3) Annualisation déterministe (règle : mensuel × 12 × facteur de cadence).
    this.server.registerTool(
      "argentier_annualize",
      {
        description: "Annualise un montant mensuel (× 12). Un one-off n'est jamais annualisé.",
        inputSchema: {
          monthly: z.number().describe("Montant mensuel en €"),
          cadenceFactor: z.number().default(1).describe("1 = mensuel, 1/3 = trimestriel…"),
        },
      },
      async ({ monthly, cadenceFactor }) => ({
        content: [{ type: "text", text: String(Math.round(monthly * cadenceFactor * 12)) }],
      }),
    );

    // 4) Audit complet d'une liste de transactions (le moteur, en MCP).
    this.server.registerTool(
      "argentier_analyze",
      {
        description:
          "Audite des transactions Qonto et renvoie l'analyse déterministe : natures, leviers " +
          "d'économie, TVA récupérable, hausses silencieuses. Aucun euro n'est calculé par le LLM.",
        inputSchema: {
          transactions: z
            .array(
              z.object({
                merchant: z.string(),
                amount: z.number().describe("Montant en € (positif)"),
                date: z.string().describe("AAAA-MM-JJ"),
                side: z.enum(["debit", "credit"]).default("debit"),
                isFx: z.boolean().default(false),
                attachmentRequired: z.boolean().default(false),
                hasAttachment: z.boolean().default(false),
              }),
            )
            .describe("Les transactions à auditer"),
          windowDays: z.number().default(90).describe("Fenêtre d'analyse en jours"),
        },
      },
      async ({ transactions, windowDays }) => {
        const txs: Tx[] = transactions.map((t, i) => ({
          id: `tx-${i}`,
          merchant: t.merchant,
          amount: t.amount,
          localCurrency: "EUR",
          isFx: t.isFx,
          side: t.side,
          operationType: "card",
          date: t.date,
          attachmentRequired: t.attachmentRequired,
          hasAttachment: t.hasAttachment,
        }));

        const months = Math.max(1, windowDays / 30);
        const byName = new Map<string, { occ: number; sum: number }>();
        for (const t of txs) {
          if (t.side !== "debit") continue;
          const e = byName.get(t.merchant) ?? { occ: 0, sum: 0 };
          e.occ += 1;
          e.sum += t.amount;
          byName.set(t.merchant, e);
        }
        const merchants: MerchantInput[] = [...byName.entries()].map(([name, { occ, sum }]) => ({
          name,
          occurrences: occ,
          monthlyEstimate: sum / months,
          isRecurring: occ >= 2,
        }));

        const result = build({
          account: { name: "Compte", bank: "Qonto", balance: 0 },
          windowLabel: { fr: `${windowDays} j`, en: `${windowDays} days` },
          txs,
          verdicts: categorizeByRules(merchants),
          windowDays,
          source: "mock",
          categorized: "rules",
        });

        const summary = {
          totals: result.totals,
          natures: result.natures,
          tvaPerdue: result.tvaPerdue ?? null,
          levers: result.levers.map((l) => ({
            label: l.label,
            to: l.to,
            savingMonthly: l.saving,
            savingYearly: l.saving * 12,
            action: l.action,
            hausse: l.hausse ?? null,
          })),
        };
        return { content: [{ type: "text", text: JSON.stringify(summary, null, 2) }] };
      },
    );
  }
}

const CORS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext) {
    const url = new URL(request.url);

    // Liste d'attente — stocke l'email dans Cloudflare KV.
    if (url.pathname === "/waitlist") {
      if (request.method === "OPTIONS") return new Response(null, { headers: CORS });
      if (request.method !== "POST") {
        return new Response("Method not allowed", { status: 405, headers: CORS });
      }
      let email = "";
      let lang = "";
      let source = "";
      try {
        const body = (await request.json()) as { email?: string; lang?: string; source?: string };
        email = (body.email ?? "").trim().toLowerCase();
        lang = (body.lang ?? "").slice(0, 5);
        source = (body.source ?? "").slice(0, 40);
      } catch {
        /* body invalide */
      }
      if (!email.includes("@") || email.length < 5 || email.length > 200) {
        return Response.json({ ok: false, error: "invalid_email" }, { status: 400, headers: CORS });
      }
      await env.WAITLIST.put(
        `wl:${email}`,
        JSON.stringify({ email, lang, source, at: new Date().toISOString() }),
      );
      return Response.json({ ok: true }, { headers: CORS });
    }

    if (url.pathname === "/" || url.pathname === "/health") {
      return new Response("Argentier MCP — Streamable HTTP sur POST /mcp · POST /waitlist");
    }
    if (url.pathname.startsWith("/mcp")) {
      return ArgentierMCP.serve("/mcp", { binding: "ArgentierMCP" }).fetch(request, env, ctx);
    }
    return new Response("Not found", { status: 404 });
  },
};
