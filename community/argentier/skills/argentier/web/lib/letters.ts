// ---------------------------------------------------------------------------
// Génération des lettres / emails de résiliation & renégociation (PRD §5.8).
//
// Argentier PRÉPARE le courrier ; l'utilisateur l'envoie lui-même. Aucune action
// bancaire, aucun envoi automatique. Les infos personnelles restent des
// [crochets] à compléter — on n'invente pas les coordonnées de l'utilisateur.
//
// Bilingue : Claude rédige dans la langue demandée ; gabarit de secours FR/EN.
// ---------------------------------------------------------------------------

import Anthropic from "@anthropic-ai/sdk";
import type { Lang, LeverAction } from "./types";

const MODEL = process.env.ARGENTIER_MODEL || "claude-sonnet-5";

export interface LetterSource {
  name: string;
  price: string; // « 21 €/utilisateur/mois »
  date: string;
  url: string;
}

export interface LetterRequest {
  merchant: string;
  action: LeverAction;
  alternative: string;
  savingMonthly: number;
  savingAnnual: number;
  lang?: Lang;
  /** Prix concurrents sourcés + datés (issus de /api/benchmark), optionnels. */
  sources?: LetterSource[];
}

const ACTION_INTENT: Record<Lang, Record<LeverAction, string>> = {
  fr: {
    cancel: "résilier l'abonnement",
    downgrade: "passer à une formule moins chère mieux dimensionnée",
    switch: "migrer vers une alternative moins coûteuse à usage égal",
    consolidate: "regrouper des lignes en doublon en un seul contrat",
    renegotiate: "renégocier le tarif à la baisse",
    keep: "faire le point sur le contrat",
  },
  en: {
    cancel: "cancel the subscription",
    downgrade: "move to a cheaper, better-sized plan",
    switch: "switch to a cheaper alternative at equal usage",
    consolidate: "merge duplicate lines into a single contract",
    renegotiate: "renegotiate the price down",
    keep: "review the contract",
  },
  de: {
    cancel: "das Abonnement kündigen",
    downgrade: "auf einen günstigeren, besser dimensionierten Tarif wechseln",
    switch: "zu einer günstigeren Alternative bei gleichem Nutzen wechseln",
    consolidate: "doppelte Verträge zu einem einzigen zusammenführen",
    renegotiate: "den Preis nach unten verhandeln",
    keep: "den Vertrag überprüfen",
  },
  es: {
    cancel: "cancelar la suscripción",
    downgrade: "cambiar a un plan más barato y mejor dimensionado",
    switch: "migrar a una alternativa más barata de uso equivalente",
    consolidate: "unificar líneas duplicadas en un solo contrato",
    renegotiate: "renegociar el precio a la baja",
    keep: "revisar el contrato",
  },
  it: {
    cancel: "disdire l'abbonamento",
    downgrade: "passare a un piano più economico e meglio dimensionato",
    switch: "migrare verso un'alternativa più economica a uso equivalente",
    consolidate: "unificare le linee duplicate in un unico contratto",
    renegotiate: "rinegoziare il prezzo al ribasso",
    keep: "fare il punto sul contratto",
  },
};

const SYSTEM: Record<Lang, string> = {
  fr: `Tu rédiges, en français, des courriers ou emails PRÊTS À ENVOYER pour un
dirigeant de TPE / entreprise individuelle. Ton professionnel, courtois, direct.

Règles impératives :
- L'utilisateur enverra lui-même : n'écris jamais « envoyé par Argentier ».
- Ne fabrique aucune donnée personnelle : mets des [crochets] pour tout ce que
  l'utilisateur doit compléter ([Nom], [n° de client], [email], [date]).
- Reste factuel et réaliste : pas de menace, pas de chiffre inventé. Tu peux
  mentionner que l'utilisateur compare les offres du marché.
- Structure : objet, corps clair (2 à 4 paragraphes), formule de politesse.
- Renvoie UNIQUEMENT le texte du courrier (objet inclus), sans commentaire.`,
  en: `You write ready-to-send letters or emails, in English, for a small-business
owner / sole trader. Professional, courteous, direct tone.

Hard rules:
- The user sends it themselves: never write "sent by Argentier".
- Fabricate no personal data: use [brackets] for everything the user must fill in
  ([Name], [account number], [email], [date]).
- Stay factual and realistic: no threats, no invented figures. You may mention that
  the user is comparing market offers.
- Structure: subject line, clear body (2–4 paragraphs), sign-off.
- Return ONLY the letter text (subject included), with no commentary.`,
  de: `Du verfasst auf Deutsch VERSANDFERTIGE Briefe oder E-Mails für eine
Kleinunternehmerin / einen Einzelunternehmer. Professioneller, höflicher, direkter Ton.

Zwingende Regeln:
- Der Nutzer sendet selbst: schreibe nie „von Argentier gesendet".
- Erfinde keine personenbezogenen Daten: setze [Klammern] für alles, was der Nutzer
  ausfüllen muss ([Name], [Kundennummer], [E-Mail], [Datum]).
- Bleibe sachlich und realistisch: keine Drohungen, keine erfundenen Zahlen. Du darfst
  erwähnen, dass der Nutzer Marktangebote vergleicht.
- Struktur: Betreff, klarer Textkörper (2 bis 4 Absätze), Grußformel.
- Gib NUR den Brieftext zurück (inklusive Betreff), ohne Kommentar.`,
  es: `Redactas, en español, cartas o correos LISTOS PARA ENVIAR para un
propietario de pequeña empresa / autónomo. Tono profesional, cortés y directo.

Reglas imperativas:
- El usuario lo enviará él mismo: nunca escribas «enviado por Argentier».
- No inventes ningún dato personal: usa [corchetes] para todo lo que el usuario deba
  completar ([Nombre], [número de cliente], [email], [fecha]).
- Mantente factual y realista: sin amenazas, sin cifras inventadas. Puedes mencionar que
  el usuario compara las ofertas del mercado.
- Estructura: asunto, cuerpo claro (2 a 4 párrafos), fórmula de cortesía.
- Devuelve ÚNICAMENTE el texto de la carta (asunto incluido), sin comentarios.`,
  it: `Redigi, in italiano, lettere o email PRONTE DA INVIARE per un
titolare di piccola impresa / lavoratore autonomo. Tono professionale, cortese e diretto.

Regole imperative:
- L'utente la invierà da sé: non scrivere mai «inviato da Argentier».
- Non inventare alcun dato personale: usa le [parentesi] per tutto ciò che l'utente deve
  completare ([Nome], [numero cliente], [email], [data]).
- Resta fattuale e realistico: nessuna minaccia, nessuna cifra inventata. Puoi menzionare
  che l'utente confronta le offerte di mercato.
- Struttura: oggetto, corpo chiaro (2-4 paragrafi), formula di cortesia.
- Restituisci SOLO il testo della lettera (oggetto incluso), senza commenti.`,
};

export function hasAnthropicKey(): boolean {
  return !!process.env.ANTHROPIC_API_KEY;
}

const LETTER_LANGS: Lang[] = ["fr", "en", "de", "es", "it"];

export async function generateLetter(req: LetterRequest): Promise<string> {
  const lang: Lang = req.lang && LETTER_LANGS.includes(req.lang) ? req.lang : "fr";
  if (!hasAnthropicKey()) return templateLetter(req, lang);
  try {
    const client = new Anthropic();
    const intent = ACTION_INTENT[lang][req.action] ?? ACTION_INTENT[lang].renegotiate;
    const sourcesBlock = buildSourcesBlock(req, lang);
    const prompt =
      lang !== "fr"
        ? `Write the letter for this case:
- Provider / service: ${req.merchant}
- Goal: ${intent}${req.alternative ? ` (option considered: ${req.alternative})` : ""}
- Target saving (indicative, not to be framed as a demand): about €${Math.round(
            req.savingMonthly,
          )}/month, i.e. €${Math.round(req.savingAnnual)}/year.${sourcesBlock}

Adapt the tone: a cancellation is firm but courteous; a renegotiation or
consolidation opens a dialogue and asks for a proposal. If market prices are
provided, cite them factually (name + price + date) without aggressiveness.`
        : `Rédige le courrier pour ce cas :
- Fournisseur / service : ${req.merchant}
- Objectif : ${intent}${req.alternative ? ` (piste envisagée : ${req.alternative})` : ""}
- Économie visée (indicative, à ne pas présenter comme une exigence) : environ ${Math.round(
            req.savingMonthly,
          )} €/mois, soit ${Math.round(req.savingAnnual)} €/an.${sourcesBlock}

Adapte le ton : une résiliation est ferme mais courtoise ; une renégociation ou
consolidation ouvre le dialogue et demande une proposition. Si des prix du marché
sont fournis, cite-les factuellement (nom + tarif + date) sans agressivité.`;

    const response = (await client.messages.create({
      model: MODEL,
      max_tokens: 1200,
      system: [{ type: "text", text: SYSTEM[lang], cache_control: { type: "ephemeral" } }],
      messages: [{ role: "user", content: prompt }],
    })) as Anthropic.Message;

    const text = response.content.find((b) => b.type === "text");
    if (text && text.type === "text" && text.text.trim()) return text.text.trim();
    return templateLetter(req, lang);
  } catch (err) {
    console.error("Génération lettre Claude échouée, fallback gabarit :", err);
    return templateLetter(req, lang);
  }
}

function buildSourcesBlock(req: LetterRequest, lang: Lang): string {
  if (!req.sources || req.sources.length === 0) return "";
  const rows = req.sources
    .map((s) =>
      lang === "fr"
        ? `- ${s.name} : ${s.price}${s.date ? ` (relevé ${s.date})` : ""}`
        : `- ${s.name}: ${s.price}${s.date ? ` (checked ${s.date})` : ""}`,
    )
    .join("\n");
  return lang === "fr"
    ? `\n\nPrix du marché sourcés (à citer factuellement pour appuyer la demande, avec la date) :\n${rows}`
    : `\n\nSourced market prices (cite factually to support the request, with the date):\n${rows}`;
}

// --- Gabarit déterministe (sans clé Anthropic) -----------------------------
function templateLetter(req: LetterRequest, lang: Lang): string {
  const isCancel = req.action === "cancel";
  // fr → gabarit FR ; en/de/es/it → gabarit EN (base neutre, à relire par l'utilisateur).
  if (lang !== "fr") {
    const subject = isCancel
      ? `Cancellation of my ${req.merchant} subscription`
      : `Review of my ${req.merchant} contract`;
    const body = isCancel
      ? `I am writing to cancel my ${req.merchant} subscription, tied to account [account number / email].

Please process this cancellation at the earliest possible term, and confirm the effective date as well as the absence of any further charges.`
      : `As a ${req.merchant} customer under account [account number / email], I am reviewing my tools and would like to ${
          ACTION_INTENT.en[req.action] ?? "review my contract"
        }.${req.alternative ? `\n\nOption I am considering: ${req.alternative}.` : ""}

I am comparing market offers at equal usage. Before renewing, could you send me a pricing proposal aligned with your best current offer, detailing what is included?`;
    return `Subject: ${subject}

Hello,

${body}

Looking forward to your reply, best regards.

[First name LAST NAME]
[Company] — [Company ID]
[Email] · [Phone]

— Draft prepared by Argentier. Review it, fill in the [brackets], then send it yourself.`;
  }

  const objet = isCancel
    ? `Résiliation de mon abonnement ${req.merchant}`
    : `Révision de mon contrat ${req.merchant}`;
  const corps = isCancel
    ? `Je vous informe de ma décision de résilier mon abonnement ${req.merchant}, associé au compte [n° de client / email].

Je vous remercie de bien vouloir prendre en compte cette résiliation à la première échéance possible, et de me confirmer la date effective ainsi que l'absence de tout prélèvement ultérieur.`
    : `Client ${req.merchant} sous le compte [n° de client / email], je fais actuellement le point sur mes outils et souhaite ${
        ACTION_INTENT.fr[req.action] ?? "revoir mon contrat"
      }.${req.alternative ? `\n\nPiste envisagée de mon côté : ${req.alternative}.` : ""}

Je compare les offres du marché à usage équivalent. Avant de renouveler, pouvez-vous me faire une proposition tarifaire alignée sur votre meilleure offre actuelle, avec le détail de ce qui est inclus ?`;

  return `Objet : ${objet}

Bonjour,

${corps}

Dans l'attente de votre retour, je vous prie d'agréer mes salutations distinguées.

[Prénom NOM]
[Raison sociale] — [SIRET]
[Email] · [Téléphone]

— Brouillon préparé par Argentier. Relis, complète les [crochets], puis envoie-le toi-même.`;
}
