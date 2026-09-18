// ---------------------------------------------------------------------------
// Catégorisation DÉTERMINISTE (extrait de web/lib/categorize.ts, sans le SDK
// Anthropic — le Worker MCP n'utilise que le classifieur par règles).
// ---------------------------------------------------------------------------

import type { MerchantVerdict, Nature, Pole, Risk, LeverAction } from "./types";

export interface MerchantInput {
  name: string;
  occurrences: number;
  monthlyEstimate: number;
  isRecurring: boolean;
}

// --- Classifieur déterministe (mots-clés) ----------------------------------
const PERSO = [
  "carrefour", "monoprix", "leclerc", "franprix", "auchan", "lidl", "intermarche",
  "grand frais", "boulangerie", "mcdonald", "starbucks", "uber eats", "deliveroo",
  "netflix", "spotify", "disney", "nespresso", "pharmacie", "zara", "h&m", "sephora",
];
const PILOTABLE = [
  "hubspot", "apollo", "ringover", "google workspace", "gsuite", "notion", "slack",
  "aws", "github", "gitlab", "stripe", "ovh", "scaleway", "figma", "zoom", "openai",
  "anthropic", "claude", "chatgpt", "vercel", "make", "zapier", "airtable", "instantly",
  "waalaxy", "loom", "replit", "skool", "webflow", "heygen", "capcut", "mailjet",
  "free mobile", "bouygues", "uber one", "mailchimp", "canva",
];
const STRUCTUREL = ["hiscox", "urssaf", "impot", "salaire", "sous-trait", "certif", "inkrea", "assur"];
const VOYAGE = ["sofitel", "air france", "booking", "sncf", "hotel", "uber", "airbnb"];

const POLE_HINTS: Array<[RegExp, Pole]> = [
  [/hubspot|apollo|instantly|waalaxy|pipedrive|salesforce|mailjet|mailchimp/, "Outbound / Sales"],
  [/openai|anthropic|claude|chatgpt|replit|github|gitlab|cursor|make|zapier/, "IA & Dev"],
  [/meta|google ads|facebook|tiktok ads/, "Marketing Ads"],
  [/aws|ovh|scaleway|vercel|cloudflare/, "Infra / Prod"],
  [/ringover|free mobile|bouygues|orange|sfr|qonto|google workspace/, "Bureau / Telco / Banque"],
];

function classifyRule(name: string): { nature: Nature; pole: Pole } {
  const n = name.toLowerCase();
  if (STRUCTUREL.some((k) => n.includes(k))) return { nature: "structurel", pole: "Certif" };
  if (VOYAGE.some((k) => n.includes(k))) return { nature: "ponctuel", pole: "Voyage" };
  if (PERSO.some((k) => n.includes(k))) return { nature: "perso", pole: "Perso" };
  if (PILOTABLE.some((k) => n.includes(k))) {
    const hit = POLE_HINTS.find(([re]) => re.test(n));
    return { nature: "pilotable", pole: hit ? hit[1] : "IA & Dev" };
  }
  return { nature: "ponctuel", pole: "Autre" };
}

function ruleVerdict(m: MerchantInput): MerchantVerdict {
  const { nature, pole } = classifyRule(m.name);
  let action: LeverAction = "keep";
  let alternative = "";
  let savingRatio = 0;
  let risk: Risk = "safe";
  if (nature === "pilotable" && m.isRecurring) {
    action = "renegotiate";
    alternative = "revoir le plan / le tarif";
    savingRatio = 0.2;
    risk = "med";
  }
  return {
    name: m.name,
    nature,
    pole,
    isSubscription: m.isRecurring && nature === "pilotable",
    action,
    alternative,
    savingRatio,
    risk,
  };
}

export function categorizeByRules(merchants: MerchantInput[]): MerchantVerdict[] {
  return merchants.map(ruleVerdict);
}

// --- Classification EI PRO / PERSO / A-CLARIFIER — miroir de engine.py -------
export const PRO_KEYWORDS = [
  "hubspot", "apollo", "ringover", "google workspace", "google gsuite",
  "notion", "slack", "aws", "amazon web services", "github", "gitlab",
  "linkedin", "stripe", "ovh", "scaleway", "figma", "zoom", "microsoft",
  "adobe", "openai", "anthropic", "vercel", "cloudflare", "sentry",
  "calendly", "typeform", "mailchimp", "mailjet", "sendgrid", "twilio",
  "make", "make.com", "zapier", "airtable", "pipedrive", "salesforce",
  "intercom", "canva", "webflow", "instantly", "waalaxy", "loom", "replit",
  "skool", "hiscox",
];

export const PERSO_KEYWORDS = [
  "zara", "h&m", "uniqlo", "restaurant", "uber eats", "deliveroo",
  "just eat", "carrefour", "monoprix", "leclerc", "franprix", "auchan",
  "lidl", "intermarche", "boulangerie", "mcdonald", "starbucks", "fnac",
  "decathlon", "sephora", "ikea", "netflix", "spotify", "disney+",
  "pharmacie", "nespresso", "barber", "action",
];

export type EiClass = "PRO" | "PERSO" | "A-CLARIFIER";

/** Miroir de engine.py:classify() — PRO l'emporte sur PERSO, défaut A-CLARIFIER. */
export function classifyEI(name: string): EiClass {
  const n = name.toLowerCase().replace(/\s+/g, " ").trim();
  if (PRO_KEYWORDS.some((k) => n.includes(k))) return "PRO";
  if (PERSO_KEYWORDS.some((k) => n.includes(k))) return "PERSO";
  return "A-CLARIFIER";
}
