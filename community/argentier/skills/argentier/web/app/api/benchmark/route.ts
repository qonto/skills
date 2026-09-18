// ---------------------------------------------------------------------------
// POST /api/benchmark — déclenché SUR ACCORD (règle 3). Claude cherche des
// alternatives moins chères sur le web (sourcé + daté) ; ICI on calcule
// l'économie potentielle par soustraction — le LLM ne chiffre jamais l'euro.
// ---------------------------------------------------------------------------

import { NextResponse } from "next/server";
import { benchmark } from "@/lib/benchmark";
import type { Lang } from "@/lib/types";

export const dynamic = "force-dynamic";
export const maxDuration = 60; // la recherche web peut prendre quelques secondes

const LANGS: Lang[] = ["fr", "en", "de", "es", "it"];

export async function POST(request: Request) {
  let body: { merchant?: string; category?: string; monthly?: number; lang?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Corps JSON invalide" }, { status: 400 });
  }

  const merchant = String(body.merchant ?? "").trim();
  if (!merchant) {
    return NextResponse.json({ error: "Champ 'merchant' requis" }, { status: 400 });
  }
  const category = String(body.category ?? "outil SaaS");
  const monthly = Number(body.monthly ?? 0);
  const lang: Lang = LANGS.includes(body.lang as Lang) ? (body.lang as Lang) : "fr";

  const result = await benchmark(merchant, category, monthly, lang);

  // Économie potentielle = coût actuel − meilleur prix sourcé (calcul TS).
  const priced = result.alternatives.filter((a) => typeof a.monthlyPrice === "number");
  let bestSaving = 0;
  let bestAlternative: string | null = null;
  if (monthly > 0 && priced.length > 0) {
    const cheapest = priced.reduce((min, a) =>
      (a.monthlyPrice as number) < (min.monthlyPrice as number) ? a : min,
    );
    const saving = Math.round(monthly - (cheapest.monthlyPrice as number));
    if (saving > 0) {
      bestSaving = saving;
      bestAlternative = cheapest.name;
    }
  }

  return NextResponse.json({ ...result, bestSaving, bestAlternative });
}
