// ---------------------------------------------------------------------------
// POST/GET /api/analyze — orchestration (PRD §15, étape 3) :
//   Source Qonto (lecture seule) → catégorisation (Claude) → engine.ts → JSON.
//
// Sources, par ordre de priorité :
//   1. data/qonto-snapshot.json  — export réel tiré via le MCP Qonto (gitignoré).
//   2. Business API (clés .env)  — fetch live.
//   3. mock                      — démo, sans aucune clé.
// Aucune action bancaire n'est déclenchée. Tout euro vient d'engine.ts.
// ---------------------------------------------------------------------------

import { NextResponse } from "next/server";
import { MOCK } from "@/lib/mock";
import { build, toMerchantInputs } from "@/lib/engine";
import {
  categorizeByRules,
  categorizeWithClaude,
  hasAnthropicKey,
  type MerchantInput,
} from "@/lib/categorize";
import { getOrganization, listTransactions, readQontoConfig } from "@/lib/qonto";
import type { Localized, MerchantVerdict, Tx } from "@/lib/types";

export const dynamic = "force-dynamic";

function windowLabel(days: number): Localized {
  const end = new Date();
  const start = new Date(end.getTime() - 30 * 86_400_000);
  const fmt = (d: Date, locale: string) =>
    d.toLocaleDateString(locale, { day: "numeric", month: "long" });
  return {
    fr: `${fmt(start, "fr-FR")} – ${fmt(end, "fr-FR")} ${end.getFullYear()}`,
    en: `${fmt(start, "en-US")} – ${fmt(end, "en-US")}, ${end.getFullYear()}`,
  };
}

/** OBSERVE terminé → CATÉGORISE (Claude) → CALCULE (engine.ts). */
async function runPipeline(
  account: { name: string; bank: string; balance: number },
  txs: Tx[],
  windowDays: number,
) {
  const months = Math.max(1, windowDays / 30);
  const inputs: MerchantInput[] = toMerchantInputs(
    txs.filter((t) => t.side === "debit"),
    months,
  );

  let verdicts: MerchantVerdict[];
  let categorized: "claude" | "rules" = "rules";
  if (hasAnthropicKey() && inputs.length > 0) {
    try {
      verdicts = await categorizeWithClaude(inputs);
      categorized = "claude";
    } catch (err) {
      console.error("Catégorisation Claude échouée, fallback règles :", err);
      verdicts = categorizeByRules(inputs);
    }
  } else {
    verdicts = categorizeByRules(inputs);
  }

  return build({
    account,
    windowLabel: windowLabel(windowDays),
    txs,
    verdicts,
    windowDays,
    source: "qonto",
    categorized,
  });
}

async function analyze() {
  const windowDays = Number(process.env.ARGENTIER_WINDOW_DAYS || 60);

  // Business API live (clés .env) — sinon démo mock.
  const qonto = readQontoConfig();
  if (qonto) {
    const [org, txs] = await Promise.all([
      getOrganization(qonto),
      listTransactions(qonto, windowDays),
    ]);
    return runPipeline({ name: org.name, bank: "Qonto", balance: org.balance }, txs, windowDays);
  }

  // 3) Démo mock.
  return { ...MOCK, meta: { ...MOCK.meta!, source: "mock" as const } };
}

export async function GET() {
  try {
    return NextResponse.json(await analyze());
  } catch (err) {
    console.error("Analyse échouée, fallback mock :", err);
    return NextResponse.json(
      { ...MOCK, meta: { ...MOCK.meta!, source: "mock" as const } },
      { status: 200 },
    );
  }
}

export const POST = GET;
