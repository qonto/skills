// ---------------------------------------------------------------------------
// POST /api/letter — prépare un courrier de résiliation / renégociation prêt à
// envoyer pour un levier donné. Argentier prépare, l'utilisateur envoie.
// ---------------------------------------------------------------------------

import { NextResponse } from "next/server";
import { generateLetter, type LetterRequest } from "@/lib/letters";
import type { Lang, LeverAction } from "@/lib/types";

export const dynamic = "force-dynamic";

const ACTIONS: LeverAction[] = [
  "keep",
  "cancel",
  "downgrade",
  "switch",
  "consolidate",
  "renegotiate",
];

const LANGS: Lang[] = ["fr", "en", "de", "es", "it"];

export async function POST(request: Request) {
  let body: Partial<LetterRequest> & { action?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Corps JSON invalide" }, { status: 400 });
  }

  const merchant = String(body.merchant ?? "").trim();
  if (!merchant) {
    return NextResponse.json({ error: "Champ 'merchant' requis" }, { status: 400 });
  }
  const action: LeverAction = ACTIONS.includes(body.action as LeverAction)
    ? (body.action as LeverAction)
    : "renegotiate";

  const req: LetterRequest = {
    merchant,
    action,
    alternative: String(body.alternative ?? ""),
    savingMonthly: Number(body.savingMonthly ?? 0),
    savingAnnual: Number(body.savingAnnual ?? (Number(body.savingMonthly ?? 0) * 12)),
    lang: body.lang && LANGS.includes(body.lang) ? body.lang : "fr",
    sources: Array.isArray(body.sources) ? body.sources : undefined,
  };

  const letter = await generateLetter(req);
  return NextResponse.json({ letter });
}
