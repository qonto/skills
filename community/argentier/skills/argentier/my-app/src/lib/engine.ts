// ---------------------------------------------------------------------------
// engine.ts — le moteur de calcul DÉTERMINISTE d'Argentier.
//
// RÈGLE D'OR : tout montant en euros est calculé ICI. Le LLM ne fait que
// classer (nature, pôle, action, ratio) ; il ne multiplie jamais.
//
// Produit un AnalyzeResult complet à partir des transactions normalisées et
// des verdicts de catégorisation.
// ---------------------------------------------------------------------------

import type {
  AnalyzeResult,
  FluxItem,
  Hausse,
  Lever,
  Localized,
  MerchantVerdict,
  Nature,
  NatureSlice,
  PoleSlice,
  TvaPerdue,
  Tx,
} from "./types";
import { classifyEI, type MerchantInput } from "./categorize";

const DAY = 86_400_000;
const NATURE_LABEL: Record<Nature, string> = {
  pilotable: "Pilotable",
  structurel: "Structurel",
  ponctuel: "Ponctuel",
  perso: "Perso",
};

const eurL = (n: number): Localized => ({
  fr: Math.round(n).toLocaleString("fr-FR") + " €",
  en: Math.round(n).toLocaleString("en-US") + " €",
});

// (ancien formateur FR conservé mais inutilisé — remplacé par eurL bilingue)
const eur = (n: number) =>
  Math.round(n).toLocaleString("fr-FR").replace(/ /g, " ") + " €";

// --- Utilitaires numériques ------------------------------------------------
function median(xs: number[]): number {
  if (xs.length === 0) return 0;
  const s = [...xs].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

function ordinal(dateStr: string): number {
  return Math.floor(new Date(dateStr + "T00:00:00Z").getTime() / DAY);
}

interface MerchantAgg {
  name: string;
  txs: Tx[];
  total: number;
  occurrences: number;
  isRecurring: boolean;
  monthly: number; // run-rate mensuel normalisé
  dominantOp: string;
}

function aggregate(debits: Tx[], months: number): MerchantAgg[] {
  const groups = new Map<string, Tx[]>();
  for (const tx of debits) {
    const key = tx.merchant.toLowerCase();
    (groups.get(key) ?? groups.set(key, []).get(key)!).push(tx);
  }

  const out: MerchantAgg[] = [];
  for (const txs of groups.values()) {
    const amounts = txs.map((t) => t.amount);
    const total = amounts.reduce((a, b) => a + b, 0);
    const n = txs.length;

    // Opération dominante
    const opCounts = new Map<string, number>();
    for (const t of txs) opCounts.set(t.operationType, (opCounts.get(t.operationType) ?? 0) + 1);
    const dominantOp = [...opCounts.entries()].sort((a, b) => b[1] - a[1])[0][0];

    // Récurrence + normalisation mensuelle (règle : jamais annualiser un one-off)
    let isRecurring = false;
    let monthly = total / months; // défaut : dépense variable lissée
    if (n >= 2) {
      const ords = txs.map((t) => ordinal(t.date)).sort((a, b) => a - b);
      const intervals = ords.slice(1).map((v, i) => v - ords[i]);
      const medInt = median(intervals);
      const monthlyCadence = medInt >= 20 && medInt <= 45;
      if (monthlyCadence || dominantOp === "direct_debit") {
        isRecurring = true;
        monthly = median(amounts); // abonnement mensuel réel
      }
    }

    out.push({
      name: txs[0].merchant,
      txs,
      total,
      occurrences: n,
      isRecurring,
      monthly,
      dominantOp,
    });
  }
  return out;
}

export function toMerchantInputs(debits: Tx[], months: number): MerchantInput[] {
  return aggregate(debits, months).map((m) => ({
    name: m.name,
    occurrences: m.occurrences,
    monthlyEstimate: m.monthly,
    isRecurring: m.isRecurring,
  }));
}

function slug(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "").slice(0, 24) || "x";
}

export interface BuildInput {
  account: { name: string; bank: string; balance: number };
  windowLabel: Localized;
  txs: Tx[];
  verdicts: MerchantVerdict[];
  windowDays: number;
  source: "qonto" | "mock";
  categorized: "claude" | "rules";
}

export function build(input: BuildInput): AnalyzeResult {
  const { txs, verdicts, windowDays } = input;
  const months = Math.max(1, windowDays / 30);

  const verdictOf = new Map(verdicts.map((v) => [v.name.toLowerCase(), v]));
  const natureOf = (name: string): Nature =>
    verdictOf.get(name.toLowerCase())?.nature ?? "ponctuel";

  const debits = txs.filter((t) => t.side === "debit");
  const credits = txs.filter((t) => t.side === "credit");

  // Fenêtre « ce mois » = 30 derniers jours (le relevé affiché).
  const monthCutoff = ordinal(new Date().toISOString().slice(0, 10)) - 30;
  const recentDebits = debits.filter((t) => ordinal(t.date) >= monthCutoff);

  // --- natures : montants OBSERVÉS sur 30 j (non annualisés) ----------------
  const natureSums: Record<Nature, number> = {
    pilotable: 0, structurel: 0, ponctuel: 0, perso: 0,
  };
  for (const t of recentDebits) natureSums[natureOf(t.merchant)] += t.amount;
  const natures: NatureSlice[] = (["structurel", "ponctuel", "perso", "pilotable"] as Nature[]).map(
    (key) => ({ key, label: NATURE_LABEL[key], amount: Math.round(natureSums[key]) }),
  );
  const totalOut = Math.round(recentDebits.reduce((s, t) => s + t.amount, 0));

  // --- run-rate pilotable + pôles (mensuel normalisé) -----------------------
  const aggs = aggregate(debits, months);
  const poleSums = new Map<string, number>();
  let runRate = 0;
  for (const a of aggs) {
    const v = verdictOf.get(a.name.toLowerCase());
    if (!v || v.nature !== "pilotable") continue;
    runRate += a.monthly;
    poleSums.set(v.pole, (poleSums.get(v.pole) ?? 0) + a.monthly);
  }
  runRate = Math.round(runRate);
  const poles: PoleSlice[] = [...poleSums.entries()]
    .map(([label, amount]) => ({ label, amount: Math.round(amount) }))
    .filter((p) => p.amount > 0)
    .sort((a, b) => b.amount - a.amount)
    .slice(0, 6);

  // --- leviers : économie €/mois = monthly × savingRatio (moteur) ----------
  const levers: Lever[] = [];
  const leverNames = new Set<string>();
  for (const a of aggs) {
    const v = verdictOf.get(a.name.toLowerCase());
    if (!v || v.nature !== "pilotable" || v.action === "keep") continue;
    const saving = Math.round(a.monthly * clamp01(v.savingRatio));
    if (saving <= 0) continue;
    const hausse = detectHausse(a);
    levers.push({
      id: slug(a.name),
      label: a.name,
      to: v.alternative || v.action,
      saving,
      risk: v.risk,
      active: v.risk === "safe",
      action: v.action,
      monthly: Math.round(a.monthly),
      ...(hausse ? { hausse } : {}),
    });
    leverNames.add(a.name.toLowerCase());
  }

  // Hausses silencieuses sur des récurrents pilotables non déjà couverts par un
  // levier : on les remonte comme un levier « renégocier / revenir au tarif ».
  // Le montant récupérable = delta mensuel (dernière − 1re occurrence).
  for (const a of aggs) {
    const key = a.name.toLowerCase();
    if (leverNames.has(key)) continue;
    const v = verdictOf.get(key);
    if (!v || v.nature !== "pilotable") continue;
    const hausse = detectHausse(a);
    if (!hausse) continue;
    levers.push({
      id: slug(a.name),
      label: a.name,
      to: v.alternative || "revenir au tarif précédent",
      saving: Math.max(0, Math.round(hausse.apresEur - hausse.avantEur)),
      risk: "safe",
      active: true,
      action: "renegotiate",
      monthly: Math.round(a.monthly),
      hausse,
    });
    leverNames.add(key);
  }
  levers.sort((x, y) => y.saving - x.saving);

  // Ids de leviers UNIQUES : slug() tronque à 24 car. et écrase la ponctuation,
  // donc deux marchands distincts peuvent produire le même id. La dédup ci-dessus
  // se fait sur le NOM, pas sur l'id → on suffixe -2, -3… pour garantir l'unicité
  // et ne jamais casser les clés React / le drag-and-drop / le toggle côté front.
  const seenIds = new Set<string>();
  for (const l of levers) {
    let id = l.id;
    for (let n = 2; seenIds.has(id); n++) id = `${l.id}-${n}`;
    l.id = id;
    seenIds.add(id);
  }

  // --- score /100 : grille transparente ------------------------------------
  const drivers: Localized[] = [];
  let score = 100;

  const consolidations = levers.filter((l) =>
    verdictOf.get(l.label.toLowerCase())?.action === "consolidate",
  );
  if (consolidations.length > 0) {
    const pen = 8;
    score -= pen;
    drivers.push({
      fr: `Doublons fonctionnels (${consolidations.length}) −${pen}`,
      en: `Functional duplicates (${consolidations.length}) −${pen}`,
    });
  }

  const needJustif = recentDebits.filter((t) => t.attachmentRequired && !t.hasAttachment);
  if (needJustif.length > 0) {
    const pen = Math.min(8, Math.ceil((needJustif.length / Math.max(1, recentDebits.length)) * 20));
    score -= pen;
    drivers.push({
      fr: `Justificatifs TVA manquants (${needJustif.length}) −${pen}`,
      en: `Missing VAT receipts (${needJustif.length}) −${pen}`,
    });
  }

  const activeSavings = levers.filter((l) => l.active).reduce((s, l) => s + l.saving, 0);
  if (runRate > 0 && activeSavings > 0) {
    const pen = Math.min(12, Math.round((activeSavings / runRate) * 12));
    if (pen > 0) {
      score -= pen;
      drivers.push({
        fr: `Part optimisable du run-rate −${pen}`,
        en: `Optimizable share of run-rate −${pen}`,
      });
    }
  }
  score = Math.max(0, Math.min(100, score));

  // --- runway : solde ÷ burn net mensuel, hors ponctuel --------------------
  const recentCredits = credits.filter((t) => ordinal(t.date) >= monthCutoff);
  const burnOut = recentDebits
    .filter((t) => natureOf(t.merchant) !== "ponctuel")
    .reduce((s, t) => s + t.amount, 0);
  const inflow = recentCredits.reduce((s, t) => s + t.amount, 0);
  const netBurn = burnOut - inflow;
  const months_left = netBurn > 0 ? input.account.balance / netBurn : 99;
  const runway = {
    months: Math.round(Math.min(99, Math.max(0, months_left)) * 10) / 10,
    note: { fr: "hors exceptionnel", en: "excl. one-offs" } as Localized,
  };

  // --- flux nouveaux & anomalies -------------------------------------------
  const flux = detectFlux(debits, aggs, verdictOf, monthCutoff);

  // --- TVA déductible perdue : dépenses PRO sans justificatif ---------------
  // PÉRIMÈTRE ALIGNÉ SUR engine.py (règle #2, engine.py fait foi) : on ne compte
  // QUE les marchands classés PRO par mots-clés (classifyEI, whitelist
  // PRO_KEYWORDS) — jamais A-CLARIFIER, structurel, voyage… On agrège les
  // transactions où un justificatif était requis mais absent. TVA = base × 20/120.
  // Levier fiscal indicatif : à confirmer avec un comptable.
  const tvaConcerned = debits.filter(
    (t) => t.attachmentRequired && !t.hasAttachment && classifyEI(t.merchant) === "PRO",
  );
  let tvaPerdue: TvaPerdue | undefined;
  if (tvaConcerned.length > 0) {
    const baseTtc = tvaConcerned.reduce((s, t) => s + t.amount, 0);
    const tva = (baseTtc * 20) / 120;
    if (tva > 0) {
      tvaPerdue = {
        transactions: tvaConcerned.length,
        baseTtcEur: Math.round(baseTtc * 100) / 100,
        tvaRecuperableEur: Math.round(tva * 100) / 100,
      };
    }
  }

  const noFlag: Localized = { fr: "Aucun point de vigilance majeur", en: "No major red flag" };

  return {
    account: input.account,
    window: { label: input.windowLabel },
    totals: { out: totalOut, runRate },
    natures,
    poles,
    score: { value: score, drivers: drivers.length ? drivers : [noFlag] },
    runway,
    levers,
    flux,
    ...(tvaPerdue ? { tvaPerdue } : {}),
    meta: { source: input.source, categorized: input.categorized, txCount: txs.length },
  };
}

function clamp01(x: number): number {
  return Math.max(0, Math.min(1, x || 0));
}

/**
 * Hausse silencieuse : sur un marchand RÉCURRENT, compare le montant de la 1re
 * et de la dernière occurrence (triées par date). Seuil de déclenchement : +5 %.
 * Jamais sur un one-off (on exige isRecurring + ≥ 2 occurrences).
 */
function detectHausse(agg: MerchantAgg): Hausse | null {
  if (!agg.isRecurring || agg.txs.length < 2) return null;
  const ordered = [...agg.txs].sort((a, b) => ordinal(a.date) - ordinal(b.date));
  const avant = ordered[0].amount;
  const apres = ordered[ordered.length - 1].amount;
  if (avant <= 0 || apres < avant * 1.05) return null;
  return {
    pct: Math.round((apres / avant - 1) * 1000) / 10, // arrondi 1 décimale
    avantEur: Math.round(avant * 100) / 100,
    apresEur: Math.round(apres * 100) / 100,
  };
}

function detectFlux(
  debits: Tx[],
  aggs: MerchantAgg[],
  verdictOf: Map<string, MerchantVerdict>,
  monthCutoff: number,
): FluxItem[] {
  const flux: FluxItem[] = [];
  const prevCutoff = monthCutoff - 30;

  const recentByMerchant = new Map<string, Tx[]>();
  const prevByMerchant = new Map<string, Tx[]>();
  for (const t of debits) {
    const o = ordinal(t.date);
    const key = t.merchant.toLowerCase();
    if (o >= monthCutoff) (recentByMerchant.get(key) ?? recentByMerchant.set(key, []).get(key)!).push(t);
    else if (o >= prevCutoff) (prevByMerchant.get(key) ?? prevByMerchant.set(key, []).get(key)!).push(t);
  }

  // Nouveaux marchands (présents ce mois, absents le mois précédent)
  for (const [key, txs] of recentByMerchant) {
    if (prevByMerchant.has(key)) continue;
    const v = verdictOf.get(key);
    if (v?.nature === "perso") continue; // bruit
    const monthly = txs.reduce((s, t) => s + t.amount, 0);
    const m = eurL(monthly);
    flux.push({
      kind: "new",
      label: { fr: `${txs[0].merchant} · nouveau flux`, en: `${txs[0].merchant} · new flow` },
      value: v?.isSubscription
        ? { fr: `${m.fr}/mois`, en: `${m.en}/mo` }
        : m,
      tone: "amber",
    });
  }

  // Doublons même jour ce mois
  for (const [, txs] of recentByMerchant) {
    const byDay = new Map<string, number>();
    for (const t of txs) byDay.set(t.date, (byDay.get(t.date) ?? 0) + 1);
    for (const [day, cnt] of byDay) {
      if (cnt >= 2) {
        flux.push({
          kind: "dup",
          label: {
            fr: `Doublon : ${txs[0].merchant} ×${cnt} le ${day}`,
            en: `Duplicate: ${txs[0].merchant} ×${cnt} on ${day}`,
          },
          value: eurL(median(txs.map((t) => t.amount))),
          tone: "danger",
        });
      }
    }
  }

  // Abonnements dormants (vus avant, plus ce mois)
  for (const a of aggs) {
    const key = a.name.toLowerCase();
    const v = verdictOf.get(key);
    if (v?.isSubscription && prevByMerchant.has(key) && !recentByMerchant.has(key)) {
      flux.push({
        kind: "ghost",
        label: {
          fr: `${a.name} · abo dormant, plus prélevé`,
          en: `${a.name} · dormant subscription, no longer charged`,
        },
        value: { fr: "à confirmer", en: "to confirm" },
        tone: "neutral",
      });
    }
  }

  return flux.slice(0, 8);
}
