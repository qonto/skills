// ---------------------------------------------------------------------------
// Contrat d'API d'Argentier.
// Le front (Argentier.tsx) consomme exactement cette forme ; /api/analyze la
// produit. Garder les clés stables : account, window, totals, natures, poles,
// levers, flux, score, runway (cf. PRD §15).
// ---------------------------------------------------------------------------

/** Langues supportées. */
export type Lang = "fr" | "en" | "de" | "es" | "it";

/**
 * Chaîne bilingue produite côté serveur (engine.ts), résolue par le front.
 * Volontairement limitée à fr/en : de/es/it retombent sur `en` via le resolver
 * `loc()` du front. Ne PAS élargir cette interface.
 */
export interface Localized {
  fr: string;
  en: string;
}

/** Les 4 natures de flux — le tri est le cœur différenciant (PRD §4). */
export type Nature = "pilotable" | "structurel" | "ponctuel" | "perso";

/** Pôles métier pour agréger le pilotable. */
export type Pole =
  | "IA & Dev"
  | "Outbound / Sales"
  | "Infra / Prod"
  | "Marketing Ads"
  | "Bureau / Telco / Banque"
  | "Perso"
  | "Sous-traitance"
  | "Certif"
  | "Voyage"
  | "Autre";

export type Risk = "safe" | "med" | "hard";

/** Actions proposées par le classifieur — l'euro est calculé par le moteur. */
export type LeverAction =
  | "keep"
  | "cancel"
  | "downgrade"
  | "switch"
  | "consolidate"
  | "renegotiate";

export interface NatureSlice {
  key: Nature;
  label: string;
  /** Montant OBSERVÉ sur la fenêtre (pas annualisé). Somme = totals.out. */
  amount: number;
}

export interface PoleSlice {
  label: string;
  /** Run-rate mensuel pilotable de ce pôle (€/mois). */
  amount: number;
}

/**
 * Hausse silencieuse détectée sur un abonnement récurrent :
 * comparaison de la 1re et de la dernière occurrence (triées par date).
 * Seuil de déclenchement : +5 %. Présent seulement si détecté.
 */
export interface Hausse {
  /** % d'augmentation (arrondi à 1 décimale), ex : 12.5. */
  pct: number;
  /** Montant de la 1re occurrence (€). */
  avantEur: number;
  /** Montant de la dernière occurrence (€). */
  apresEur: number;
}

export interface Lever {
  id: string;
  label: string;
  /** Alternative / action lisible (« 1 seul workspace », « Claude seul »…). */
  to: string;
  /** Économie mensuelle en € — calculée par engine.ts, jamais par le LLM. */
  saving: number;
  risk: Risk;
  active: boolean;
  /** Type d'action, pour contextualiser la lettre (résiliation vs renégo…). */
  action?: LeverAction;
  /** Dépense mensuelle observée du marchand (€) — sert au benchmark. */
  monthly?: number;
  /** Hausse silencieuse (1re vs dernière occurrence) — présent seulement si détectée. */
  hausse?: Hausse;
}

export interface FluxItem {
  kind: "new" | "check" | "dup" | "ghost";
  label: Localized;
  value: Localized;
  tone: "amber" | "danger" | "neutral";
}

export interface Score {
  value: number;
  drivers: Localized[];
}

export interface Runway {
  months: number;
  note: Localized;
}

/**
 * TVA déductible perdue : dépenses PRO où un justificatif était requis
 * (attachment_required) mais absent (aucune pièce jointe). Levier fiscal :
 * à confirmer avec un comptable. Présent seulement si tvaRecuperableEur > 0.
 */
export interface TvaPerdue {
  /** Nombre de transactions concernées. */
  transactions: number;
  /** Base TTC totale (€) = somme des montants. */
  baseTtcEur: number;
  /** TVA récupérable estimée (€) = baseTTC × 20/120 (taux France standard 20 %). */
  tvaRecuperableEur: number;
}

export interface AnalyzeResult {
  account: { name: string; bank: string; balance: number };
  window: { label: Localized };
  totals: { out: number; runRate: number };
  natures: NatureSlice[];
  poles: PoleSlice[];
  score: Score;
  runway: Runway;
  levers: Lever[];
  flux: FluxItem[];
  /** TVA déductible perdue (justificatifs PRO manquants) — présent seulement si > 0. */
  tvaPerdue?: TvaPerdue;
  /** Métadonnées non affichées : d'où viennent les données. */
  meta?: { source: "qonto" | "mock"; categorized: "claude" | "rules"; txCount: number };
}

// --- Transaction normalisée (interne, entre qonto.ts et engine.ts) ----------
export interface Tx {
  id: string;
  merchant: string;        // clean_counterparty_name || label
  amount: number;          // EUR, positif
  localCurrency: string;   // pour repérer le FX
  isFx: boolean;
  side: "debit" | "credit";
  operationType: string;
  date: string;            // YYYY-MM-DD (settled_at || emitted_at)
  attachmentRequired: boolean;
  hasAttachment: boolean;
}

// --- Sortie du classifieur LLM (par marchand) -------------------------------
export interface MerchantVerdict {
  name: string;
  nature: Nature;
  pole: Pole;
  isSubscription: boolean;
  action: LeverAction;
  /** Texte de l'alternative (vide si action = keep). */
  alternative: string;
  /** Part de l'économie sur le montant mensuel [0..1] — le moteur multiplie. */
  savingRatio: number;
  risk: Risk;
}
