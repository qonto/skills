"use client";

/**
 * Argentier — front d'entrée, bilingue FR / EN.
 * Au montage, il fetch /api/analyze (Qonto → Claude → engine.ts). Tant que la
 * réponse n'arrive pas — ou si l'API échoue — il affiche les données mock.
 * La langue est persistée (localStorage) et transmise à Claude (lettres, benchmark).
 */

import React, { useEffect, useMemo, useState } from "react";
import type { AnalyzeResult, Lang, Lever, Localized, Nature, NatureSlice, Risk } from "@/lib/types";
import { buildPlanCsv, planFilename } from "@/lib/export";
import { MOCK } from "@/lib/mock";
import { detectLang, eur as eurFmt, LANGS, LOCALE, natureLabel, PITCH, riskLabel, tr } from "@/lib/i18n";
import { EUROPE_PATHS, EUROPE_VIEWBOX, EU_CITY_XY } from "@/lib/europeMap";

// Agent conversationnel ElevenLabs (Q&A vocal). Vide = widget Q&A désactivé.
const CONVAI_AGENT_ID = process.env.NEXT_PUBLIC_ELEVENLABS_AGENT_ID;

// Rend un texte avec emphase **...** → <strong>.
function emph(text: string, keyBase: string): React.ReactNode[] {
  return text.split("**").map((seg, i) =>
    i % 2 === 1 ? <strong key={`${keyBase}-${i}`}>{seg}</strong> : <React.Fragment key={`${keyBase}-${i}`}>{seg}</React.Fragment>,
  );
}

// Résout un dictionnaire 5-langues, avec repli propre sur l'anglais.
function pick<T>(lang: Lang, m: Record<Lang, T>): T {
  return m[lang] ?? m.en;
}

// Sélecteur de langue : drapeau + code (persisté dans localStorage).
const LANG_CHOICES: { code: Lang; flag: string; label: string }[] = [
  { code: "fr", flag: "🇫🇷", label: "FR" },
  { code: "en", flag: "🇬🇧", label: "EN" },
  { code: "de", flag: "🇩🇪", label: "DE" },
  { code: "es", flag: "🇪🇸", label: "ES" },
  { code: "it", flag: "🇮🇹", label: "IT" },
];

const RISK_COLOR: Record<Risk, string> = {
  safe: "var(--c-vert)",
  med: "var(--c-amber)",
  hard: "var(--c-clay)",
};

const NATURE_COLOR: Record<Nature, string> = {
  structurel: "var(--c-ink2)",
  ponctuel: "var(--c-amber)",
  perso: "var(--c-line-strong)",
  pilotable: "var(--c-vert)",
};

// Entreprises flottant sur la carte d'Europe (hero du pitch).
// La position (x/y en % du viewBox) vient de EU_CITY_XY, reprojetée avec la
// carte. t = taille (1 petit … 3 grand) ; cfo = la rare entreprise (les 10%)
// qui a un DAF → bulle verte.
type EuCo = { city: string; t: 1 | 2 | 3; cfo?: boolean };
const EU_COMPANIES: EuCo[] = [
  { city: "London", t: 3 },
  { city: "Dublin", t: 1 },
  { city: "Paris", t: 3, cfo: true },
  { city: "Amsterdam", t: 2 },
  { city: "Bruxelles", t: 1 },
  { city: "Berlin", t: 3 },
  { city: "Warszawa", t: 2 },
  { city: "Praha", t: 1 },
  { city: "München", t: 2 },
  { city: "Wien", t: 2 },
  { city: "Zürich", t: 1 },
  { city: "Milano", t: 2 },
  { city: "Roma", t: 2 },
  { city: "Madrid", t: 2 },
  { city: "Barcelona", t: 1, cfo: true },
  { city: "Lisboa", t: 1 },
  { city: "Stockholm", t: 1 },
  { city: "København", t: 1 },
];

// Compteur animé, respecte prefers-reduced-motion. Se relance quand `trigger` change.
function useCountUp(target: number, trigger: unknown, ms = 900) {
  const [val, setVal] = useState(0);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const reduce =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      setVal(target);
      setReady(true);
      return;
    }
    setReady(false);
    let raf = 0;
    const start = performance.now();
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / ms);
      const eased = 1 - Math.pow(1 - p, 3);
      setVal(Math.round(target * eased));
      if (p < 1) raf = requestAnimationFrame(tick);
      else setReady(true);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trigger]);
  return { val, ready };
}

export default function Argentier() {
  const [lang, setLang] = useState<Lang>("fr");
  const [data, setData] = useState<AnalyzeResult>(MOCK);
  const [levers, setLevers] = useState(MOCK.levers);
  const [horizon, setHorizon] = useState(12);
  const [loaded, setLoaded] = useState(false);

  const T = tr(lang);
  const eur = (n: number) => eurFmt(n, lang);
  // Résout un texte 5-langues (repli anglais) ; loc() résout un Localized (fr/en only).
  const L = (m: Record<Lang, string>) => pick(lang, m);
  const loc = (x: Localized) => x[lang as "fr" | "en"] ?? x.en;

  useEffect(() => {
    const saved =
      typeof window !== "undefined" ? window.localStorage.getItem("argentier-lang") : null;
    setLang(saved && (LANGS as string[]).includes(saved) ? (saved as Lang) : detectLang(navigator.language));
  }, []);

  const changeLang = (l: Lang) => {
    setLang(l);
    try {
      window.localStorage.setItem("argentier-lang", l);
    } catch {
      /* stockage indisponible — pas grave */
    }
  };

  // --- Présentation / elevator pitch ---------------------------------------
  const [pitchOpen, setPitchOpen] = useState(false);
  useEffect(() => {
    if (!pitchOpen) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setPitchOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [pitchOpen]);

  // --- Autopilote — démo done-for-you : audit → gate 1-tap → preuve --------
  const [apOpen, setApOpen] = useState(false);
  const [apStep, setApStep] = useState(0); // 0 observe … 3 gate … 6 preuve
  const [apDecision, setApDecision] = useState<"pending" | "approved" | "refused">("pending");
  // Board Trello + liste d'attente (fake-it)
  const [board, setBoard] = useState<Record<string, "todo" | "doing" | "done">>({});
  const [dragId, setDragId] = useState<string | null>(null);
  const [wl, setWl] = useState<string | null>(null);
  const [wlEmail, setWlEmail] = useState("");
  const [wlJoined, setWlJoined] = useState<Record<string, boolean>>({});
  // Liste d'attente « connecter Qonto » (bas de page) → Cloudflare KV.
  const [qEmail, setQEmail] = useState("");
  const [qJoined, setQJoined] = useState(false);
  const submitQonto = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!qEmail.includes("@")) return;
    try {
      await fetch("https://argentier-mcp.bonjour-e83.workers.dev/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: qEmail.trim().toLowerCase(), lang, source: "connect-qonto-demo" }),
      });
    } catch {
      /* réseau — on ne bloque pas */
    }
    setQJoined(true);
  };
  // Voix ElevenLabs (TTS « explique-moi » + widget Q&A conditionnel)
  const [voiceState, setVoiceState] = useState<"idle" | "loading" | "playing">("idle");
  const audioRef = React.useRef<HTMLAudioElement | null>(null);
  const convaiRef = React.useRef<HTMLDivElement | null>(null);
  const startAutopilot = () => {
    setApDecision("pending");
    setApStep(0);
    setApOpen(true);
  };
  useEffect(() => {
    // le gate (3) et la fin (6) ne s'auto-avancent pas
    if (!apOpen || apStep === 3 || apStep >= 6) return;
    const id = setTimeout(() => setApStep((s) => s + 1), apStep === 0 ? 1000 : 1200);
    return () => clearTimeout(id);
  }, [apOpen, apStep]);

  useEffect(() => {
    let alive = true;
    fetch("/api/analyze")
      .then((r) => r.json())
      .then((d: AnalyzeResult) => {
        if (!alive) return;
        setData(d);
        setLevers(d.levers);
        setLoaded(true);
      })
      .catch(() => alive && setLoaded(true));
    return () => {
      alive = false;
    };
  }, []);

  const monthly = useMemo(
    () => levers.filter((l) => l.active).reduce((s, l) => s + l.saving, 0),
    [levers],
  );
  const annual = monthly * 12;
  const optimized = data.totals.runRate - monthly;
  const pct = data.totals.runRate > 0 ? Math.round((monthly / data.totals.runRate) * 100) : 0;

  const { val: heroVal, ready } = useCountUp(annual, loaded);
  const shownAnnual = ready ? annual : heroVal;

  // Levier vedette de l'autopilote : le plus gros gain actif.
  const apLever = useMemo(
    () => [...levers].filter((l) => l.active).sort((a, b) => b.saving - a.saving)[0] ?? levers[0],
    [levers],
  );

  // Texte que la voix lit — dans la langue courante, avec le chiffre du hero.
  const voiceScript = () => {
    const a = eur(annual);
    const s: Record<Lang, string> = {
      fr: `Bienvenue sur Argentier, ton directeur financier autonome. Ton relevé Qonto cache ton vrai run-rate : il mélange abonnements récurrents, charges structurelles et dépenses ponctuelles. Argentier a séparé tes flux et repéré environ ${a} par an récupérables, sans perdre une seule capacité. Plus bas, le simulateur montre chaque levier : tu actives, tu désactives, et tu prépares la lettre de résiliation en un clic. Le bouton Autopilote lance l'audit tout seul, te propose chaque action à approuver, et prouve l'économie trente jours après. Tu approuves, tu envoies : Argentier ne bouge jamais ton argent.`,
      en: `Welcome to Argentier, your autonomous CFO. Your Qonto statement hides your true run-rate: it blends recurring tools, structural costs and one-off spend. Argentier separated your flows and found about ${a} a year you can recover, without losing a single capability. Below, the simulator shows every lever: toggle them, and prepare the cancellation letter in one click. The Autopilot button runs the audit on its own, proposes each action for you to approve, and proves the saving thirty days later. You approve, you send: Argentier never moves your money.`,
      de: `Willkommen bei Argentier, deinem autonomen CFO. Dein Qonto-Auszug verbirgt deine echte Run-Rate: Er wirft laufende Tools, Strukturkosten und Einmalausgaben zusammen. Argentier hat deine Flüsse getrennt und rund ${a} pro Jahr gefunden, die du zurückholen kannst, ohne eine einzige Funktion zu verlieren. Weiter unten zeigt der Simulator jeden Hebel: ein- und ausschalten und das Kündigungsschreiben mit einem Klick vorbereiten. Der Autopilot-Knopf führt die Prüfung selbst durch, schlägt jede Aktion zur Freigabe vor und beweist die Einsparung dreißig Tage später. Du gibst frei, du sendest: Argentier bewegt dein Geld nie.`,
      es: `Bienvenido a Argentier, tu director financiero autónomo. Tu extracto de Qonto oculta tu verdadero run-rate: mezcla herramientas recurrentes, costes estructurales y gastos puntuales. Argentier ha separado tus flujos y ha encontrado unos ${a} al año que puedes recuperar, sin perder ni una sola capacidad. Más abajo, el simulador muestra cada palanca: actívalas y prepara la carta de baja en un clic. El botón Autopiloto ejecuta la auditoría solo, te propone cada acción para aprobar y demuestra el ahorro treinta días después. Tú apruebas, tú envías: Argentier nunca mueve tu dinero.`,
      it: `Benvenuto su Argentier, il tuo CFO autonomo. Il tuo estratto conto Qonto nasconde il vero run-rate: mescola strumenti ricorrenti, costi strutturali e spese una tantum. Argentier ha separato i tuoi flussi e ha trovato circa ${a} all'anno che puoi recuperare, senza perdere una sola funzionalità. Più in basso, il simulatore mostra ogni leva: attivale e prepara la lettera di disdetta con un clic. Il pulsante Autopilota esegue l'audit da solo, ti propone ogni azione da approvare e dimostra il risparmio trenta giorni dopo. Tu approvi, tu invii: Argentier non muove mai i tuoi soldi.`,
    };
    return s[lang] ?? s.en;
  };

  const playVoice = async () => {
    if (voiceState === "playing") {
      audioRef.current?.pause();
      setVoiceState("idle");
      return;
    }
    setVoiceState("loading");
    try {
      const res = await fetch("/api/voice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: voiceScript(), lang }),
      });
      if (!res.ok) throw new Error(String(res.status));
      const url = URL.createObjectURL(await res.blob());
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => {
        setVoiceState("idle");
        URL.revokeObjectURL(url);
      };
      audio.onerror = () => setVoiceState("idle");
      await audio.play();
      setVoiceState("playing");
    } catch {
      setVoiceState("idle");
    }
  };

  // Widget conversationnel ElevenLabs (Q&A vocal) — seulement si un agent public
  // est configuré (NEXT_PUBLIC_ELEVENLABS_AGENT_ID). Suit la langue courante.
  useEffect(() => {
    if (!CONVAI_AGENT_ID || !convaiRef.current) return;
    if (!document.querySelector("script[data-elevenlabs-convai]")) {
      const sc = document.createElement("script");
      sc.src = "https://unpkg.com/@elevenlabs/convai-widget-embed";
      sc.async = true;
      sc.setAttribute("data-elevenlabs-convai", "");
      document.body.appendChild(sc);
    }
    const el = document.createElement("elevenlabs-convai");
    el.setAttribute("agent-id", CONVAI_AGENT_ID);
    el.setAttribute("override-language", lang);
    convaiRef.current.innerHTML = "";
    convaiRef.current.appendChild(el);
  }, [lang]);

  const toggle = (id: string) =>
    setLevers((ls) => ls.map((l) => (l.id === id ? { ...l, active: !l.active } : l)));
  const setAll = (fn: (l: (typeof levers)[number]) => boolean) =>
    setLevers((ls) => ls.map((l) => ({ ...l, active: fn(l) })));

  // --- Export du plan (CSV / Excel) ----------------------------------------
  const exportCsv = () => {
    const csv = buildPlanCsv({ ...data, levers }, levers);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = planFilename(data);
    a.click();
    URL.revokeObjectURL(url);
  };

  // --- Tiroir « lettre prête à envoyer » + benchmark web -------------------
  type LetterSource = { name: string; price: string; date: string; url: string };
  type BenchAlt = { name: string; monthlyPrice: number | null; unit: string; sourceUrl: string; sourceDate: string };
  type BenchResult = {
    verified: boolean;
    note?: string;
    alternatives: BenchAlt[];
    sources: { title: string; url: string; date: string }[];
    bestSaving: number;
    bestAlternative: string | null;
    provider?: "linkup" | "claude";
  };

  const [letterFor, setLetterFor] = useState<Lever | null>(null);
  const [letterText, setLetterText] = useState("");
  const [letterLoading, setLetterLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [bench, setBench] = useState<BenchResult | null>(null);
  const [benchLoading, setBenchLoading] = useState(false);

  const openLetter = async (l: Lever, sources?: LetterSource[]) => {
    setLetterFor(l);
    setLetterText("");
    setCopied(false);
    if (!sources) setBench(null);
    setLetterLoading(true);
    try {
      const res = await fetch("/api/letter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          merchant: l.label,
          action: l.action ?? "renegotiate",
          alternative: l.to,
          savingMonthly: l.saving,
          savingAnnual: l.saving * 12,
          lang,
          sources,
        }),
      });
      const json = await res.json();
      setLetterText(json.letter ?? "…");
    } catch {
      setLetterText(
        L({
          fr: "Erreur réseau — réessaie.",
          en: "Network error — try again.",
          de: "Netzwerkfehler — versuch es erneut.",
          es: "Error de red — inténtalo de nuevo.",
          it: "Errore di rete — riprova.",
        }),
      );
    } finally {
      setLetterLoading(false);
    }
  };

  const runBenchmark = async (l: Lever) => {
    setBenchLoading(true);
    setBench(null);
    try {
      const res = await fetch("/api/benchmark", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ merchant: l.label, category: l.to, monthly: l.monthly ?? 0, lang }),
      });
      setBench(await res.json());
    } catch {
      setBench({ verified: false, note: T.benchNone, alternatives: [], sources: [], bestSaving: 0, bestAlternative: null });
    } finally {
      setBenchLoading(false);
    }
  };

  const regenerateWithPrices = () => {
    if (!letterFor || !bench) return;
    const sources: LetterSource[] = bench.alternatives
      .filter((a) => a.monthlyPrice != null)
      .map((a) => ({
        name: a.name,
        price: `${a.monthlyPrice} €${a.unit || "/mois"}`,
        date: a.sourceDate,
        url: a.sourceUrl,
      }));
    openLetter(letterFor, sources);
  };

  const copyLetter = async () => {
    try {
      await navigator.clipboard.writeText(letterText);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard indisponible */
    }
  };

  const natureTotal = data.natures.reduce((s, n) => s + n.amount, 0) || 1;
  const maxPole = Math.max(1, ...data.poles.map((p) => p.amount));
  const scoreDash = `${data.score.value} ${100 - data.score.value}`;

  return (
    <div className="arg-root">
      <style>{CSS}</style>

      {/* Barre */}
      <header className="arg-top">
        <div className="arg-brand">
          <span className="arg-mark"><ArgLogo /></span>
          <span className="arg-word">Argentier</span>
          <span className="arg-chip">
            {data.account.name} · {data.account.bank}
          </span>
          <span className={"arg-src " + (data.meta?.source === "qonto" ? "live" : "demo")}>
            ● {data.meta?.source === "qonto" ? T.srcLive : T.srcDemo}
            {data.meta?.categorized === "claude" ? ` · ${T.byClaude}` : ""}
          </span>
        </div>
        <div className="arg-top-right">
          <button className="arg-ap-open" onClick={startAutopilot}>
            ⚡ {L({ fr: "Autopilote", en: "Autopilot", de: "Autopilot", es: "Autopiloto", it: "Autopilota" })}
          </button>
          <button className="arg-pitch-open" onClick={() => setPitchOpen(true)}>
            ▶ {T.pitch}
          </button>
          <div className="arg-lang" role="group" aria-label="Language">
            {LANG_CHOICES.map((c) => (
              <button
                key={c.code}
                className={"arg-lang-btn" + (lang === c.code ? " on" : "")}
                onClick={() => changeLang(c.code)}
                aria-pressed={lang === c.code}
              >
                <span className="arg-lang-flag" aria-hidden="true">{c.flag}</span> {c.label}
              </button>
            ))}
          </div>
          <span className="arg-window">{loc(data.window.label)}</span>
        </div>
      </header>

      {/* Hero */}
      <section className="arg-hero">
        <div>
          <p className="arg-eyebrow">{loaded ? T.heroEyebrow : T.analyzing}</p>
          <p className={"arg-figure" + (loaded ? "" : " loading")} aria-live="polite">
            {eur(shownAnnual)}
          </p>
          <p className="arg-sub">{T.heroSub(eur(monthly))}</p>
          <button
            className="arg-cta"
            onClick={() => document.getElementById("plan")?.scrollIntoView({ behavior: "smooth", block: "start" })}
          >
            {T.cta}
          </button>
        </div>

        <div className="arg-hero-side">
          <div className="arg-score">
            <svg viewBox="0 0 36 36" width="84" height="84" aria-hidden="true">
              <circle className="arg-score-bg" cx="18" cy="18" r="15.9155" />
              <circle
                className="arg-score-fg"
                cx="18"
                cy="18"
                r="15.9155"
                strokeDasharray={scoreDash}
                strokeDashoffset="25"
              />
            </svg>
            <div className="arg-score-num">
              <strong>{data.score.value}</strong>
              <span>/100</span>
            </div>
            <p className="arg-score-cap">{T.scoreCap}</p>
          </div>
          <div className="arg-runway">
            <span className="arg-runway-num">
              {T.months(data.runway.months.toLocaleString(LOCALE[lang]))}
            </span>
            <span className="arg-runway-cap">{T.treso(loc(data.runway.note))}</span>
          </div>
        </div>
      </section>

      {/* Barre ledger — natures */}
      <section className="arg-card">
        <div className="arg-card-head">
          <span className="arg-card-title">{T.ledgerTitle}</span>
          <span className="arg-muted arg-mono">{T.thisMonth(eur(data.totals.out))}</span>
        </div>
        <div className="arg-ledger" role="img" aria-label={T.natureAria}>
          {data.natures.map((n) => (
            <div
              key={n.key}
              className="arg-ledger-seg"
              style={{ width: `${(n.amount / natureTotal) * 100}%`, background: NATURE_COLOR[n.key] }}
              title={`${natureLabel(n.key, lang)} ${eur(n.amount)}`}
            />
          ))}
        </div>
        <div className="arg-legend">
          {data.natures.map((n) => (
            <span key={n.key} className="arg-legend-item">
              <i style={{ background: NATURE_COLOR[n.key] }} /> {natureLabel(n.key, lang)}{" "}
              <b className="arg-mono">{eur(n.amount)}</b>
            </span>
          ))}
        </div>
      </section>

      {/* Waterfall — du relevé au vrai run-rate pilotable */}
      <section className="arg-card">
        <div className="arg-card-head">
          <span className="arg-card-title">{L({ fr: "Du relevé au vrai run-rate", en: "From statement to true run-rate", de: "Vom Auszug zur echten Run-Rate", es: "Del extracto al run-rate real", it: "Dall'estratto al vero run-rate" })}</span>
        </div>
        <NatureWaterfall natures={data.natures} out={data.totals.out} lang={lang} fmt={eur} />
      </section>

      {/* Metric cards */}
      <section className="arg-metrics">
        <Metric label={T.mRunrate} value={eur(data.totals.runRate) + "/m"} note={T.mRunrateNote(eur(data.totals.runRate * 12))} />
        <Metric label={T.mActive} value={eur(monthly) + "/m"} accent note={T.mActiveNote(eur(annual))} />
        <Metric label={T.mOptimized} value={eur(optimized) + "/m"} note={T.mOptimizedNote(pct)} />
      </section>

      {/* Levier fiscal — TVA récupérable (justificatifs manquants) */}
      {data.tvaPerdue && (
        <section className="arg-card arg-tva">
          <div className="arg-tva-body">
            <div>
              <p className="arg-tva-kicker">{L({ fr: "Levier fiscal", en: "Tax lever", de: "Steuerhebel", es: "Palanca fiscal", it: "Leva fiscale" })}</p>
              <p className="arg-tva-title">
                {L({
                  fr: `${data.tvaPerdue.transactions} justificatifs manquants → TVA récupérable`,
                  en: `${data.tvaPerdue.transactions} missing receipts → recoverable VAT`,
                  de: `${data.tvaPerdue.transactions} fehlende Belege → erstattungsfähige MwSt.`,
                  es: `${data.tvaPerdue.transactions} justificantes faltantes → IVA recuperable`,
                  it: `${data.tvaPerdue.transactions} giustificativi mancanti → IVA recuperabile`,
                })}
              </p>
              <p className="arg-tva-sub">
                {L({
                  fr: `Sur ${eur(data.tvaPerdue.baseTtcEur)} de dépenses PRO sans pièce jointe. À confirmer avec ton comptable.`,
                  en: `On ${eur(data.tvaPerdue.baseTtcEur)} of PRO spend with no receipt. To confirm with your accountant.`,
                  de: `Auf ${eur(data.tvaPerdue.baseTtcEur)} PRO-Ausgaben ohne Beleg. Mit deinem Steuerberater zu bestätigen.`,
                  es: `Sobre ${eur(data.tvaPerdue.baseTtcEur)} de gasto PRO sin justificante. A confirmar con tu asesor.`,
                  it: `Su ${eur(data.tvaPerdue.baseTtcEur)} di spese PRO senza giustificativo. Da confermare con il tuo commercialista.`,
                })}
              </p>
            </div>
            <p className="arg-tva-num arg-mono">{eur(data.tvaPerdue.tvaRecuperableEur)}</p>
          </div>
        </section>
      )}

      {/* Détail pilotable par pôle */}
      <section className="arg-card">
        <div className="arg-card-head">
          <span className="arg-card-title">{T.polesTitle}</span>
        </div>
        <div className="arg-bars">
          {data.poles.map((p) => (
            <div key={p.label} className="arg-bar-row">
              <span className="arg-bar-label">{p.label}</span>
              <div className="arg-bar-track">
                <div className="arg-bar-fill" style={{ width: `${(p.amount / maxPole) * 100}%` }} />
              </div>
              <span className="arg-bar-val arg-mono">{eur(p.amount)}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Simulateur */}
      <section className="arg-card" id="plan">
        <div className="arg-card-head">
          <span className="arg-card-title">{T.simTitle}</span>
          <span className="arg-muted">{T.simRecovered(pct)}</span>
        </div>

        <div className="arg-sim-read">
          <SimStat label={T.perMonth} value={eur(monthly)} accent />
          <SimStat label={T.perYear} value={eur(annual)} />
          <SimStat label={T.cumul(horizon)} value={eur(monthly * horizon)} />
          <SimStat label={T.optimizedRunrate} value={eur(optimized)} />
        </div>

        <div className="arg-horizon">
          <label htmlFor="hz">{T.horizon}</label>
          <input
            id="hz"
            type="range"
            min={1}
            max={36}
            value={horizon}
            onChange={(e) => setHorizon(parseInt(e.target.value, 10))}
          />
          <span className="arg-mono">{T.hMonths(horizon)}</span>
        </div>

        <div className="arg-progress">
          <div style={{ width: `${pct}%` }} />
        </div>

        <div className="arg-levers">
          {levers.map((l) => (
            <div key={l.id} className={"arg-lever" + (l.active ? " on" : "")}>
              <button className="arg-lever-toggle" onClick={() => toggle(l.id)} aria-pressed={l.active}>
                <span className="arg-check" aria-hidden="true">
                  {l.active ? "✓" : ""}
                </span>
                <span className="arg-lever-txt">
                  {l.label} <span className="arg-muted">→ {l.to}</span>
                  {l.hausse && (
                    <span
                      className="arg-hausse"
                      title={L({
                        fr: `Hausse silencieuse : ${eur(l.hausse.avantEur)} → ${eur(l.hausse.apresEur)}`,
                        en: `Silent hike: ${eur(l.hausse.avantEur)} → ${eur(l.hausse.apresEur)}`,
                        de: `Stille Erhöhung: ${eur(l.hausse.avantEur)} → ${eur(l.hausse.apresEur)}`,
                        es: `Subida silenciosa: ${eur(l.hausse.avantEur)} → ${eur(l.hausse.apresEur)}`,
                        it: `Aumento silenzioso: ${eur(l.hausse.avantEur)} → ${eur(l.hausse.apresEur)}`,
                      })}
                    >
                      ▲ +{l.hausse.pct}%
                    </span>
                  )}
                </span>
                <span className="arg-risk" style={{ color: RISK_COLOR[l.risk] }}>
                  {riskLabel(l.risk, lang)}
                </span>
                <span className="arg-lever-save arg-mono">{l.saving} €</span>
              </button>
              <select
                className="arg-lever-status"
                value={board[l.id] ?? "todo"}
                onChange={(e) =>
                  setBoard((b) => ({ ...b, [l.id]: e.target.value as "todo" | "doing" | "done" }))
                }
                aria-label={L({ fr: "Statut du suivi", en: "Tracking status", de: "Status", es: "Estado", it: "Stato" })}
                title={L({ fr: "Statut du suivi", en: "Tracking status", de: "Status", es: "Estado", it: "Stato" })}
              >
                <option value="todo">{L({ fr: "À traiter", en: "To do", de: "Zu erledigen", es: "Por hacer", it: "Da fare" })}</option>
                <option value="doing">{L({ fr: "En cours", en: "In progress", de: "In Arbeit", es: "En curso", it: "In corso" })}</option>
                <option value="done">{L({ fr: "Résilié / réduit", en: "Cancelled / reduced", de: "Gekündigt / reduziert", es: "Cancelado / reducido", it: "Disdetto / ridotto" })}</option>
              </select>
              <button
                className="arg-lever-letter"
                onClick={() => openLetter(l)}
                title={T.letterFor(l.label)}
                aria-label={T.letterFor(l.label)}
              >
                ✎
              </button>
            </div>
          ))}
        </div>

        <div className="arg-actions">
          <button className="arg-btn" onClick={() => setAll((l) => l.risk === "safe")}>
            {T.quickWins}
          </button>
          <button className="arg-btn" onClick={() => setAll(() => true)}>
            {T.enableAll}
          </button>
          <button className="arg-btn" onClick={() => setAll(() => false)}>
            {T.disableAll}
          </button>
          <a className="arg-btn" href={`/rapport?lang=${lang}`} target="_blank" rel="noopener">
            {T.printable}
          </a>
          <button className="arg-btn arg-btn-ghost" onClick={exportCsv}>
            {T.exportCsv}
          </button>
        </div>
        <p className="arg-hint">{T.leverHint}</p>
      </section>

      {/* Anomalies */}
      <section className="arg-card">
        <div className="arg-card-head">
          <span className="arg-card-title">{T.anomTitle}</span>
        </div>
        <ul className="arg-flux">
          {data.flux.map((f, i) => (
            <li key={i} className="arg-flux-row">
              <span className={"arg-dot " + f.tone} aria-hidden="true" />
              <span className="arg-flux-label">{loc(f.label)}</span>
              <span className={"arg-flux-val arg-mono " + f.tone}>{loc(f.value)}</span>
            </li>
          ))}
        </ul>
      </section>

      {/* Suivi — board drag-and-drop des forfaits à traiter */}
      <section className="arg-card">
        <div className="arg-card-head">
          <span className="arg-card-title">{L({ fr: "Suivi des résiliations", en: "Cancellation tracker", de: "Kündigungs-Tracker", es: "Seguimiento de cancelaciones", it: "Monitoraggio disdette" })}</span>
          <span className="arg-muted">{L({ fr: "glisse-dépose les forfaits", en: "drag & drop the plans", de: "Tarife per Drag & Drop verschieben", es: "arrastra y suelta los planes", it: "trascina e rilascia i piani" })}</span>
        </div>
        <div className="arg-board">
          {(
            [
              ["todo", L({ fr: "À traiter", en: "To do", de: "Zu erledigen", es: "Por hacer", it: "Da fare" })],
              ["doing", L({ fr: "En cours", en: "In progress", de: "In Arbeit", es: "En curso", it: "In corso" })],
              ["done", L({ fr: "Résilié / réduit", en: "Cancelled / reduced", de: "Gekündigt / reduziert", es: "Cancelado / reducido", it: "Disdetto / ridotto" })],
            ] as const
          ).map(([col, title]) => (
            <div
              key={col}
              className={"arg-col" + (dragId ? " drop" : "")}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => {
                if (dragId) {
                  setBoard((b) => ({ ...b, [dragId]: col }));
                  setDragId(null);
                }
              }}
            >
              <div className="arg-col-head">
                {title} <b>{levers.filter((l) => (board[l.id] ?? "todo") === col).length}</b>
              </div>
              {levers
                .filter((l) => (board[l.id] ?? "todo") === col)
                .map((l) => (
                  <div
                    key={l.id}
                    className="arg-tile"
                    draggable
                    onDragStart={() => setDragId(l.id)}
                    onDragEnd={() => setDragId(null)}
                  >
                    <span className="arg-tile-name">{l.label}</span>
                    <span className="arg-tile-right">
                      <span className="arg-tile-save arg-mono">−{l.saving} €</span>
                      <button
                        className="arg-tile-letter"
                        draggable={false}
                        onMouseDown={(e) => e.stopPropagation()}
                        onClick={(e) => {
                          e.stopPropagation();
                          openLetter(l);
                        }}
                        title={T.letterFor(l.label)}
                        aria-label={T.letterFor(l.label)}
                      >
                        ✎
                      </button>
                    </span>
                  </div>
                ))}
            </div>
          ))}
        </div>
      </section>

      {/* Journal d'audit MCP — preuve du Zéro-PII */}
      <section className="arg-card">
        <div className="arg-card-head">
          <span className="arg-card-title">{L({ fr: "Journal d'audit MCP", en: "MCP audit log", de: "MCP-Audit-Protokoll", es: "Registro de auditoría MCP", it: "Registro di audit MCP" })}</span>
          <span className="arg-src live">● {L({ fr: "Zéro PII prouvé", en: "Zero PII proven", de: "Null PII bewiesen", es: "Cero PII probado", it: "Zero PII dimostrato" })}</span>
        </div>
        <ul className="arg-audit">
          {[
            { t: "mcp__qonto__get_organization", out: L({ fr: "aucune donnée émise (lecture)", en: "no data sent (read)", de: "keine Daten gesendet (Lesen)", es: "ningún dato enviado (lectura)", it: "nessun dato inviato (lettura)" }), tone: "in" },
            { t: "mcp__qonto__list_transactions", out: L({ fr: "reste dans la machine", en: "stays in the machine", de: "bleibt in der Maschine", es: "se queda en la máquina", it: "resta nella macchina" }), tone: "in" },
            {
              t: "mcp__linkup__linkup-search",
              out: L({ fr: "sorti : « Figma · design » (marchand + catégorie)", en: "sent: “Figma · design” (merchant + category)", de: "gesendet: „Figma · Design“ (Händler + Kategorie)", es: "enviado: «Figma · design» (comercio + categoría)", it: "inviato: «Figma · design» (esercente + categoria)" }),
              tone: "out",
            },
          ].map((r, i) => (
            <li key={i} className="arg-audit-row">
              <code className="arg-audit-tool">{r.t}</code>
              <span className={"arg-audit-out " + r.tone}>
                {r.tone === "out" ? "↗" : "•"} {r.out}
              </span>
            </li>
          ))}
        </ul>
        <p className="arg-hint">
          {L({
            fr: "Aucun IBAN, transaction_id ni donnée perso ne sort. Seuls marchand + catégorie partent vers le web (règle 3).",
            en: "No IBAN, transaction_id or personal data leaves. Only merchant + category go to the web (rule 3).",
            de: "Keine IBAN, keine transaction_id, keine persönlichen Daten verlassen das System. Nur Händler + Kategorie gehen ins Web (Regel 3).",
            es: "No sale ningún IBAN, transaction_id ni dato personal. Solo comercio + categoría van a la web (regla 3).",
            it: "Nessun IBAN, transaction_id o dato personale esce. Solo esercente + categoria vanno sul web (regola 3).",
          })}
        </p>
      </section>

      {/* Bientôt — fake-it grisé + liste d'attente */}
      <section className="arg-card">
        <div className="arg-card-head">
          <span className="arg-card-title">{L({ fr: "Bientôt", en: "Coming soon", de: "Demnächst", es: "Próximamente", it: "Prossimamente" })}</span>
          <span className="arg-muted">{L({ fr: "rejoins la liste d'attente", en: "join the waitlist", de: "trag dich in die Warteliste ein", es: "únete a la lista de espera", it: "iscriviti alla lista d'attesa" })}</span>
        </div>
        <div className="arg-soon">
          {(
            [
              [
                "affacturage",
                L({ fr: "Simulation affacturage", en: "Factoring simulation", de: "Factoring-Simulation", es: "Simulación de factoring", it: "Simulazione factoring" }),
                L({ fr: "Combien débloquer en cédant tes factures clients.", en: "How much to unlock by selling your client invoices.", de: "Wie viel du durch den Verkauf deiner Kundenrechnungen freisetzt.", es: "Cuánto liberar cediendo tus facturas de clientes.", it: "Quanto liberare cedendo le tue fatture clienti." }),
              ],
              [
                "balance",
                L({ fr: "Balance âgée", en: "Aged balance", de: "Altersstruktur der Forderungen", es: "Balance por antigüedad", it: "Scadenzario crediti" }),
                L({ fr: "Tes créances clients par ancienneté (30 / 60 / 90 j).", en: "Your receivables by age (30 / 60 / 90 days).", de: "Deine Forderungen nach Alter (30 / 60 / 90 Tage).", es: "Tus cuentas por cobrar por antigüedad (30 / 60 / 90 días).", it: "I tuoi crediti per anzianità (30 / 60 / 90 giorni)." }),
              ],
            ] as const
          ).map(([key, title, desc]) => (
            <div key={key} className="arg-soon-tile">
              <span className="arg-soon-lock" aria-hidden="true">🔒</span>
              <p className="arg-soon-title">{title}</p>
              <p className="arg-soon-desc">{desc}</p>
              <button className="arg-soon-btn" onClick={() => { setWl(key); setWlEmail(""); }}>
                {wlJoined[key]
                  ? L({ fr: "✓ Inscrit", en: "✓ Joined", de: "✓ Eingetragen", es: "✓ Inscrito", it: "✓ Iscritto" })
                  : L({ fr: "Rejoindre la liste d'attente", en: "Join the waitlist", de: "Zur Warteliste", es: "Unirse a la lista de espera", it: "Iscriviti alla lista d'attesa" })}
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Connecter son vrai compte Qonto — liste d'attente (email → Cloudflare KV) */}
      <section className="arg-card arg-qwl">
        <h3 className="arg-qwl-title">
          {L({
            fr: "Branche ton vrai compte Qonto",
            en: "Connect your real Qonto account",
            de: "Verbinde dein echtes Qonto-Konto",
            es: "Conecta tu cuenta Qonto real",
            it: "Collega il tuo vero conto Qonto",
          })}
        </h3>
        {qJoined ? (
          <p className="arg-qwl-done">
            ✓ {L({ fr: "Tu es sur la liste", en: "You're on the list", de: "Du bist auf der Liste", es: "Estás en la lista", it: "Sei nella lista" })}
          </p>
        ) : (
          <>
            <form className="arg-qwl-form" onSubmit={submitQonto}>
              <input
                className="arg-qwl-input"
                type="email"
                required
                placeholder={L({ fr: "ton@email.com", en: "you@email.com", de: "du@email.com", es: "tu@email.com", it: "tua@email.com" })}
                value={qEmail}
                onChange={(e) => setQEmail(e.target.value)}
                aria-label="email"
              />
              <button className="arg-qwl-btn" type="submit">
                {L({
                  fr: "Rejoindre : connecter Qonto",
                  en: "Join: connect Qonto",
                  de: "Beitreten: Qonto verbinden",
                  es: "Unirse: conectar Qonto",
                  it: "Iscriviti: collega Qonto",
                })}
              </button>
            </form>
            <p className="arg-qwl-hint">
              {L({
                fr: "Pour rejoindre la liste d'attente, connecte ton email.",
                en: "To join the waitlist, connect your email.",
                de: "Um der Warteliste beizutreten, gib deine E-Mail an.",
                es: "Para unirte a la lista de espera, conecta tu email.",
                it: "Per iscriverti alla lista d'attesa, collega la tua email.",
              })}
            </p>
          </>
        )}
      </section>

      <footer className="arg-foot">
        {data.meta?.source === "mock"
          ? T.footMock
          : T.footReal(data.meta?.txCount ?? 0, data.meta?.categorized === "claude")}
        {T.footPrivacy}
        <br />
        <b>
          {L({
            fr: "Prototype pour Hackathon Qonto",
            en: "Prototype for Qonto Hackathon",
            de: "Prototyp für den Qonto-Hackathon",
            es: "Prototipo para el Hackathon de Qonto",
            it: "Prototipo per l'Hackathon Qonto",
          })}
        </b>
      </footer>

      {/* Tiroir : lettre prête à envoyer (gate humain) */}
      {letterFor && (
        <div className="arg-drawer-wrap" role="dialog" aria-modal="true" aria-label={letterFor.label}>
          <div className="arg-drawer-backdrop" onClick={() => setLetterFor(null)} />
          <aside className="arg-drawer">
            <div className="arg-drawer-head">
              <div>
                <p className="arg-drawer-eyebrow">{T.drawerEyebrow}</p>
                <h3 className="arg-drawer-title">{letterFor.label}</h3>
              </div>
              <button className="arg-drawer-close" onClick={() => setLetterFor(null)} aria-label={T.close}>
                ✕
              </button>
            </div>

            {letterLoading ? (
              <div className="arg-drawer-loading">{T.drawerLoading}</div>
            ) : (
              <textarea
                className="arg-drawer-text arg-mono"
                value={letterText}
                onChange={(e) => setLetterText(e.target.value)}
                spellCheck={false}
              />
            )}

            <div className="arg-drawer-actions">
              <button className="arg-btn" onClick={() => openLetter(letterFor)} disabled={letterLoading}>
                {T.regenerate}
              </button>
              <button className="arg-btn arg-btn-ghost" onClick={copyLetter} disabled={letterLoading || !letterText}>
                {copied ? T.copied : T.copy}
              </button>
            </div>

            <button
              className="arg-send-reco"
              disabled
              aria-disabled="true"
              title={L({
                fr: "Bientôt : envoi en lettre recommandée en 1 clic",
                en: "Soon: send by registered mail in 1 click",
                de: "Bald: Einschreiben mit einem Klick senden",
                es: "Pronto: enviar por correo certificado en 1 clic",
                it: "Presto: invio con raccomandata in 1 clic",
              })}
            >
              ✉{" "}
              {L({
                fr: "Envoyer en recommandé",
                en: "Send by registered mail",
                de: "Per Einschreiben senden",
                es: "Enviar por correo certificado",
                it: "Invia con raccomandata",
              })}
              <span className="arg-soon-pill">
                {L({ fr: "à venir", en: "soon", de: "bald", es: "pronto", it: "presto" })}
              </span>
            </button>

            {/* Benchmark web — sur accord (règle 3) */}
            <div className="arg-bench">
              <div className="arg-bench-head">
                <span className="arg-bench-title">{T.benchTitle}</span>
                <button className="arg-btn arg-bench-btn" onClick={() => runBenchmark(letterFor)} disabled={benchLoading}>
                  {benchLoading ? "…" : bench ? T.benchRerun : T.benchSource}
                </button>
              </div>

              {benchLoading && <p className="arg-bench-hint">{T.benchSearching}</p>}

              {bench && !benchLoading && (
                <>
                  {bench.bestSaving > 0 && bench.bestAlternative && (
                    <p className="arg-bench-best mono">{T.benchBest(bench.bestSaving, bench.bestAlternative)}</p>
                  )}
                  {bench.alternatives.length > 0 ? (
                    <ul className="arg-bench-list">
                      {bench.alternatives.map((a, i) => (
                        <li key={i}>
                          <span className="arg-bench-alt">{a.name}</span>
                          {a.monthlyPrice != null && (
                            <span className="mono arg-bench-price">
                              {a.monthlyPrice} €{a.unit}
                            </span>
                          )}
                          {a.sourceUrl && (
                            <a href={a.sourceUrl} target="_blank" rel="noopener" className="arg-bench-src">
                              {T.benchSourceLink(a.sourceDate)}
                            </a>
                          )}
                        </li>
                      ))}
                    </ul>
                  ) : bench.sources.length > 0 ? (
                    <>
                      <p className="arg-bench-hint">{T.benchNoAlt}</p>
                      <ul className="arg-bench-list">
                        {bench.sources.slice(0, 4).map((s, i) => (
                          <li key={i}>
                            <span className="arg-bench-alt">{s.title}</span>
                            <a href={s.url} target="_blank" rel="noopener" className="arg-bench-src">
                              {T.benchSourceLink(s.date)}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </>
                  ) : (
                    <p className="arg-bench-hint">{bench.note ?? T.benchNone}</p>
                  )}
                  {bench.alternatives.some((a) => a.monthlyPrice != null) && (
                    <button className="arg-btn arg-bench-inject" onClick={regenerateWithPrices}>
                      {T.benchInject}
                    </button>
                  )}
                  {bench.provider && <p className="arg-bench-via">{T.benchVia(bench.provider)}</p>}
                </>
              )}
            </div>

            <p className="arg-drawer-note">{T.drawerNote}</p>
          </aside>
        </div>
      )}

      {/* Présentation — elevator pitch bilingue */}
      {pitchOpen && (
        <div className="arg-pitch" role="dialog" aria-modal="true" aria-label={T.pitchKicker}>
          <div className="arg-pitch-bar">
            <span className="arg-pitch-brand">
              <span className="arg-mark"><ArgLogo /></span> Argentier
            </span>
            <div className="arg-pitch-controls">
              <div className="arg-lang" role="group" aria-label="Language">
                {LANG_CHOICES.map((c) => (
                  <button
                    key={c.code}
                    className={"arg-lang-btn" + (lang === c.code ? " on" : "")}
                    onClick={() => changeLang(c.code)}
                    aria-pressed={lang === c.code}
                  >
                    <span className="arg-lang-flag" aria-hidden="true">{c.flag}</span> {c.label}
                  </button>
                ))}
              </div>
              <button className="arg-drawer-close" onClick={() => setPitchOpen(false)} aria-label={T.close}>
                ✕
              </button>
            </div>
          </div>

          <div className="arg-pitch-scroll">
            <div className="arg-pitch-inner">
              <p className="arg-pitch-kicker">{T.pitchKicker}</p>

              <div className="arg-eu" aria-hidden="true">
                <svg
                  className="arg-eu-map"
                  viewBox={EUROPE_VIEWBOX}
                  preserveAspectRatio="xMidYMid meet"
                  dangerouslySetInnerHTML={{ __html: EUROPE_PATHS }}
                />

                {EU_COMPANIES.map((c, i) => (
                  <span
                    key={c.city}
                    className={"arg-eu-co t" + c.t + (c.cfo ? " cfo" : "")}
                    style={{
                      left: EU_CITY_XY[c.city][0] + "%",
                      top: EU_CITY_XY[c.city][1] + "%",
                      animationDelay: (i % 6) * -0.9 + "s",
                      animationDuration: 3.6 + (i % 5) * 0.45 + "s",
                    }}
                  >
                    <b className="arg-eu-dot">{c.cfo ? "★" : "▪"}</b>
                    <em className="arg-eu-city">{c.city}</em>
                  </span>
                ))}

                <div className="arg-eu-title">
                  <span className="arg-pitch-num">{PITCH[lang].hookNum}</span>
                  <span className="arg-pitch-hookcap">{PITCH[lang].hookCap}</span>
                </div>
              </div>
              {PITCH[lang].paras.map((p, i) => (
                <p key={i} className="arg-pitch-para">
                  {emph(p, `p${i}`)}
                </p>
              ))}
              <p className="arg-pitch-tagline">{PITCH[lang].tagline}</p>

              {/* Architecture — bilingue FR/EN (suit le sélecteur du pitch) */}
              <section className="arg-arch">
                <p className="arg-arch-kicker">Architecture</p>
                <h3 className="arg-arch-title">
                  {L({
                    fr: "Un cerveau, coupé en deux — volontairement.",
                    en: "One brain, split in two — on purpose.",
                    de: "Ein Gehirn, bewusst zweigeteilt.",
                    es: "Un cerebro, dividido en dos — a propósito.",
                    it: "Un cervello, diviso in due — di proposito.",
                  })}
                </h3>
                <p className="arg-arch-lede">
                  {emph(
                    L({
                      fr: "Argentier est un **Skill Claude Code** branché sur des **serveurs MCP** en direct. Le LLM orchestre et met en mots ; un moteur déterministe fait chaque euro. Le modèle ne touche jamais au calcul — c'est ce qui rend chaque chiffre auditable.",
                      en: "Argentier is a **Claude Code Skill** wired to live **MCP servers**. The LLM orchestrates and explains; a deterministic engine does every euro. The model never touches the math — that's what makes every figure auditable.",
                      de: "Argentier ist ein **Claude Code Skill**, der live an **MCP-Server** angebunden ist. Das LLM orchestriert und formuliert; eine deterministische Engine macht jeden Euro. Das Modell rührt die Berechnung nie an — das macht jede Zahl prüfbar.",
                      es: "Argentier es un **Skill de Claude Code** conectado en directo a **servidores MCP**. El LLM orquesta y pone en palabras; un motor determinista hace cada euro. El modelo nunca toca el cálculo — eso es lo que hace auditable cada cifra.",
                      it: "Argentier è uno **Skill di Claude Code** collegato in diretta a **server MCP**. L'LLM orchestra e mette in parole; un motore deterministico fa ogni euro. Il modello non tocca mai il calcolo — è ciò che rende verificabile ogni cifra.",
                    }),
                    "arch-lede",
                  )}
                </p>

                <div className="arg-arch-flow" aria-label="pipeline">
                  {pick(lang, {
                    fr: ["Observe", "Analyse", "Benchmark", "Recommande", "Gate", "Ledger", "Vérifie"],
                    en: ["Observe", "Analyse", "Benchmark", "Recommend", "Gate", "Ledger", "Verify"],
                    de: ["Beobachten", "Analysieren", "Benchmark", "Empfehlen", "Gate", "Ledger", "Prüfen"],
                    es: ["Observar", "Analizar", "Benchmark", "Recomendar", "Gate", "Ledger", "Verificar"],
                    it: ["Osservare", "Analizzare", "Benchmark", "Raccomandare", "Gate", "Ledger", "Verificare"],
                  }).map((s, i) => (
                    <span key={i} className="arg-arch-step">
                      <b>{String(i + 1).padStart(2, "0")}</b>
                      {s}
                    </span>
                  ))}
                </div>

                <div className="arg-arch-grid">
                  <div className="arg-arch-card">
                    <div className="arg-arch-head">
                      <i className="lock" /> Qonto MCP{" "}
                      <span className="arg-arch-tag green">{L({ fr: "lecture seule", en: "read-only", de: "schreibgeschützt", es: "solo lectura", it: "sola lettura" })}</span>
                    </div>
                    <p className="arg-arch-desc">{L({ fr: "Lit le compte réel, en direct.", en: "Reads the real account, live.", de: "Liest das echte Konto, live.", es: "Lee la cuenta real, en directo.", it: "Legge il conto reale, in diretta." })}</p>
                    <code className="arg-arch-tools">get_organization · list_transactions · list_labels · list_transaction_attachments</code>
                    <p className="arg-arch-foot">
                      {emph(
                        L({
                          fr: "Tout tool d'écriture / virement / carte est **dur-bloqué** (deny > allow). Il ne peut pas bouger d'argent.",
                          en: "Every write / transfer / card tool is **hard-denied** (deny > allow). It cannot move money.",
                          de: "Jedes Schreib-/Überweisungs-/Kartentool ist **hart gesperrt** (deny > allow). Es kann kein Geld bewegen.",
                          es: "Toda herramienta de escritura / transferencia / tarjeta está **bloqueada en duro** (deny > allow). No puede mover dinero.",
                          it: "Ogni tool di scrittura / bonifico / carta è **bloccato in modo rigido** (deny > allow). Non può muovere denaro.",
                        }),
                        "arch-foot-1",
                      )}
                    </p>
                  </div>

                  <div className="arg-arch-card">
                    <div className="arg-arch-head">
                      <i className="calc" /> Argentier{" "}
                      <span className="arg-arch-tag ink">{L({ fr: "déterministe", en: "deterministic", de: "deterministisch", es: "determinista", it: "deterministico" })}</span>
                    </div>
                    <p className="arg-arch-desc">{L({ fr: "Fait chaque euro. Jamais le modèle.", en: "Does every euro. Never the model.", de: "Macht jeden Euro. Nie das Modell.", es: "Hace cada euro. Nunca el modelo.", it: "Fa ogni euro. Mai il modello." })}</p>
                    <code className="arg-arch-tools">recurrence · ×12 annualization · duplicates · FX fees · PRO / PERSO / TO&#8209;CLARIFY</code>
                    <p className="arg-arch-foot">
                      {emph(
                        L({
                          fr: "Mêmes règles portées dans **engine.ts** pour le dashboard web.",
                          en: "Same rules ported to **engine.ts** for the web dashboard.",
                          de: "Dieselben Regeln in **engine.ts** für das Web-Dashboard portiert.",
                          es: "Las mismas reglas portadas a **engine.ts** para el panel web.",
                          it: "Le stesse regole portate in **engine.ts** per la dashboard web.",
                        }),
                        "arch-foot-2",
                      )}
                    </p>
                  </div>

                  <div className="arg-arch-card">
                    <div className="arg-arch-head">
                      <i className="src" /> Linkup MCP{" "}
                      <span className="arg-arch-tag amber">{L({ fr: "sourcé + daté", en: "sourced + dated", de: "belegt + datiert", es: "con fuente y fecha", it: "con fonte e data" })}</span>
                    </div>
                    <p className="arg-arch-desc">{L({ fr: "Benchmarke les prix sur le web vivant.", en: "Benchmarks prices on the live web.", de: "Vergleicht Preise im lebendigen Web.", es: "Compara precios en la web viva.", it: "Confronta i prezzi sul web vivo." })}</p>
                    <code className="arg-arch-tools">linkup-search</code>
                    <p className="arg-arch-foot">
                      {emph(
                        L({
                          fr: "Seuls le marchand + la catégorie sortent. Chaque prix porte une **source (URL + date)**, sinon il est écarté.",
                          en: "Only merchant + category leave the machine. Every price carries a **source URL + date**, or it's dropped.",
                          de: "Nur Händler + Kategorie verlassen das System. Jeder Preis trägt eine **Quelle (URL + Datum)**, sonst wird er verworfen.",
                          es: "Solo salen el comercio + la categoría. Cada precio lleva una **fuente (URL + fecha)**, o se descarta.",
                          it: "Escono solo esercente + categoria. Ogni prezzo porta una **fonte (URL + data)**, altrimenti viene scartato.",
                        }),
                        "arch-foot-3",
                      )}
                    </p>
                  </div>
                </div>

                <div className="arg-arch-rails">
                  {pick(lang, {
                    fr: ["Qonto read-only", "Le moteur calcule, pas le LLM", "Zéro PII vers le web", "Prix = source + date"],
                    en: ["Read-only Qonto", "Engine computes, not the LLM", "Zero PII to the web", "Price = source + date"],
                    de: ["Qonto schreibgeschützt", "Die Engine rechnet, nicht das LLM", "Null PII ins Web", "Preis = Quelle + Datum"],
                    es: ["Qonto solo lectura", "El motor calcula, no el LLM", "Cero PII hacia la web", "Precio = fuente + fecha"],
                    it: ["Qonto sola lettura", "Il motore calcola, non l'LLM", "Zero PII verso il web", "Prezzo = fonte + data"],
                  }).map((r, i) => (
                    <span key={i} className="arg-arch-rail">
                      <b>{i + 1}</b>
                      {r}
                    </span>
                  ))}
                </div>

                <p className="arg-arch-close">
                  {L({
                    fr: "Nativement MCP. Read-only par construction. Humain dans la boucle par design.",
                    en: "MCP-native. Read-only by construction. Human-in-the-loop by design.",
                    de: "MCP-nativ. Schreibgeschützt per Konstruktion. Mensch in der Schleife per Design.",
                    es: "Nativo MCP. Solo lectura por construcción. Humano en el bucle por diseño.",
                    it: "Nativo MCP. Sola lettura per costruzione. Umano nel ciclo per design.",
                  })}
                </p>
              </section>
            </div>
          </div>
        </div>
      )}

      {/* Autopilote — démo done-for-you : audit → gate 1-tap → preuve */}
      {apOpen && apLever && (
        <div className="arg-ap" role="dialog" aria-modal="true" aria-label="Autopilote">
          <div className="arg-ap-bar">
            <span className="arg-ap-brand">
              <span className="arg-mark"><ArgLogo /></span>
              {L({ fr: "Autopilote", en: "Autopilot", de: "Autopilot", es: "Autopiloto", it: "Autopilota" })}
              <span className="arg-ap-badge">done-for-you</span>
            </span>
            <button className="arg-drawer-close" onClick={() => setApOpen(false)} aria-label={T.close}>✕</button>
          </div>

          <div className="arg-ap-body">
            <ol className="arg-ap-steps">
              {pick(lang, {
                fr: ["Observe (Qonto 90 j)", "Analyse (engine.py)", "Benchmark (Linkup)", "Décision — ton accord", "Prépare le livrable", "Ledger", "Preuve J+30"],
                en: ["Observe (Qonto 90d)", "Analyse (engine.py)", "Benchmark (Linkup)", "Decision — your call", "Prepare deliverable", "Ledger", "Proof D+30"],
                de: ["Beobachten (Qonto 90 T)", "Analyse (engine.py)", "Benchmark (Linkup)", "Entscheidung — deine Freigabe", "Unterlage vorbereiten", "Ledger", "Nachweis T+30"],
                es: ["Observar (Qonto 90 d)", "Análisis (engine.py)", "Benchmark (Linkup)", "Decisión — tu aprobación", "Preparar el documento", "Ledger", "Prueba D+30"],
                it: ["Osservare (Qonto 90 g)", "Analisi (engine.py)", "Benchmark (Linkup)", "Decisione — il tuo ok", "Prepara il documento", "Ledger", "Prova G+30"],
              }).map((label, i) => {
                const state = i < apStep ? "done" : i === apStep ? "cur" : "todo";
                return (
                  <li key={i} className={"arg-ap-step " + state}>
                    <span className="arg-ap-num">{i < apStep ? "✓" : i + 1}</span>
                    {label}
                  </li>
                );
              })}
            </ol>

            <div className="arg-ap-panel">
              {apStep <= 2 && (
                <div className="arg-ap-run">
                  <div className="arg-ap-spin" />
                  <p className="arg-ap-runlabel">
                    {apStep === 0 && L({ fr: "Lecture du compte, en lecture seule…", en: "Reading the account, read-only…", de: "Konto wird gelesen, schreibgeschützt…", es: "Leyendo la cuenta, en solo lectura…", it: "Lettura del conto, in sola lettura…" })}
                    {apStep === 1 && L({ fr: "Le moteur calcule chaque euro…", en: "The engine computes every euro…", de: "Die Engine berechnet jeden Euro…", es: "El motor calcula cada euro…", it: "Il motore calcola ogni euro…" })}
                    {apStep === 2 && L({ fr: "Benchmark web, sourcé + daté…", en: "Web benchmark, sourced + dated…", de: "Web-Benchmark, belegt + datiert…", es: "Benchmark web, con fuente y fecha…", it: "Benchmark web, con fonte e data…" })}
                  </p>
                  <code className="arg-ap-tool">
                    {apStep === 0 && "mcp__qonto__list_transactions · settled_at_from=−90d"}
                    {apStep === 1 && "python3 engine.py data/flows-*.json --json"}
                    {apStep === 2 && `mcp__linkup__linkup-search · "${apLever.label}"`}
                  </code>
                </div>
              )}

              {apStep === 3 && (
                <div className="arg-ap-gate">
                  <p className="arg-ap-gate-kicker">{L({ fr: "1 décision · 1 tap", en: "1 decision · 1 tap", de: "1 Entscheidung · 1 Tipp", es: "1 decisión · 1 toque", it: "1 decisione · 1 tap" })}</p>
                  <div className="arg-ap-card">
                    <div className="arg-ap-card-head">
                      <b>{apLever.label}</b>
                      <span className="arg-ap-card-tag">{apLever.action ?? "renegotiate"}</span>
                    </div>
                    <p className="arg-ap-card-line">
                      {L({ fr: "Économie", en: "Saving", de: "Einsparung", es: "Ahorro", it: "Risparmio" })} · <b className="arg-mono">{eur(apLever.saving)}{L({ fr: "/mois", en: "/mo", de: "/Monat", es: "/mes", it: "/mese" })}</b> →{" "}
                      <b className="arg-mono">{eur(apLever.saving * 12)}/{L({ fr: "an", en: "yr", de: "Jahr", es: "año", it: "anno" })}</b>
                    </p>
                    <p className="arg-ap-card-line">{L({ fr: "Action", en: "Action", de: "Aktion", es: "Acción", it: "Azione" })} · {apLever.to}</p>
                    <p className="arg-ap-card-src">
                      {L({ fr: "Économie calculée par engine.py · prix sourcé + daté (Linkup)", en: "Saving computed by engine.py · price sourced + dated (Linkup)", de: "Einsparung von engine.py berechnet · Preis belegt + datiert (Linkup)", es: "Ahorro calculado por engine.py · precio con fuente y fecha (Linkup)", it: "Risparmio calcolato da engine.py · prezzo con fonte e data (Linkup)" })}
                    </p>
                  </div>
                  <div className="arg-ap-actions">
                    <button
                      className="arg-ap-approve"
                      onClick={() => {
                        setApDecision("approved");
                        setApStep(4);
                        setBoard((b) => ({ ...b, [apLever.id]: "doing" }));
                      }}
                    >
                      ✓ {L({ fr: "Approuver", en: "Approve", de: "Freigeben", es: "Aprobar", it: "Approva" })}
                    </button>
                    <button className="arg-ap-refuse" onClick={() => { setApDecision("refused"); setApStep(6); }}>
                      ✕ {L({ fr: "Refuser", en: "Refuse", de: "Ablehnen", es: "Rechazar", it: "Rifiuta" })}
                    </button>
                  </div>
                  <p className="arg-ap-gate-foot">
                    {L({ fr: "Argentier prépare — c'est toi qui envoies. Il ne bouge jamais d'argent.", en: "Argentier prepares — you send. It never moves money.", de: "Argentier bereitet vor — du sendest. Es bewegt nie Geld.", es: "Argentier prepara — tú envías. Nunca mueve dinero.", it: "Argentier prepara — sei tu a inviare. Non muove mai denaro." })}
                  </p>
                </div>
              )}

              {(apStep === 4 || apStep === 5) && (
                <div className="arg-ap-run">
                  <div className="arg-ap-spin" />
                  <p className="arg-ap-runlabel">
                    {apStep === 4
                      ? L({ fr: "Lettre écrite dans drafts/ — « PRÊT — À ENVOYER PAR TOI »", en: "Letter written to drafts/ — “READY — TO BE SENT BY YOU”", de: "Schreiben in drafts/ erstellt — „BEREIT — VON DIR ZU SENDEN“", es: "Carta escrita en drafts/ — «LISTO — PARA QUE LO ENVÍES TÚ»", it: "Lettera scritta in drafts/ — «PRONTO — DA INVIARE TU»" })
                      : L({ fr: "Décision tracée au ledger (statut : en attente)…", en: "Decision written to the ledger (status: pending)…", de: "Entscheidung im Ledger erfasst (Status: ausstehend)…", es: "Decisión registrada en el ledger (estado: pendiente)…", it: "Decisione registrata nel ledger (stato: in attesa)…" })}
                  </p>
                </div>
              )}

              {apStep === 6 && apDecision === "approved" && (
                <div className="arg-ap-proof">
                  <p className="arg-ap-proof-badge">✓ {L({ fr: "Prouvé — J+30", en: "Proven — D+30", de: "Bewiesen — T+30", es: "Probado — D+30", it: "Dimostrato — G+30" })}</p>
                  <p className="arg-ap-proof-num arg-mono">−{eur(apLever.saving * 12)}<span>/{L({ fr: "an", en: "yr", de: "Jahr", es: "año", it: "anno" })}</span></p>
                  <p className="arg-ap-proof-sub">
                    {L({ fr: "La charge a bien baissé. Ledger : pending → proven.", en: "The charge dropped. Ledger: pending → proven.", de: "Die Kosten sind tatsächlich gesunken. Ledger: pending → proven.", es: "El gasto bajó de verdad. Ledger: pending → proven.", it: "Il costo è davvero sceso. Ledger: pending → proven." })}
                  </p>
                  <div className="arg-ap-roi">
                    <span>{L({ fr: "Argentier a prouvé", en: "Argentier proved", de: "Argentier hat bewiesen", es: "Argentier probó", it: "Argentier ha dimostrato" })} <b className="arg-mono">{eur(apLever.saving * 12)}</b></span>
                    <span className="arg-ap-roi-arrow">→</span>
                    <span>{L({ fr: "ta commande (5%)", en: "your fee (5%)", de: "deine Provision (5 %)", es: "tu comisión (5 %)", it: "la tua commissione (5%)" })} <b className="arg-mono">{eur(Math.round(apLever.saving * 12 * 0.05))}</b></span>
                  </div>
                  <p className="arg-ap-proof-model">{L({ fr: "Pas d'économie, pas de coût.", en: "No savings, no cost.", de: "Keine Einsparung, keine Kosten.", es: "Sin ahorro, sin coste.", it: "Nessun risparmio, nessun costo." })}</p>
                  <button className="arg-ap-again" onClick={startAutopilot}>↻ {L({ fr: "Rejouer", en: "Replay", de: "Erneut abspielen", es: "Repetir", it: "Rigioca" })}</button>
                </div>
              )}

              {apStep === 6 && apDecision === "refused" && (
                <div className="arg-ap-proof refused">
                  <p className="arg-ap-proof-badge">{L({ fr: "Noté", en: "Noted", de: "Notiert", es: "Anotado", it: "Annotato" })}</p>
                  <p className="arg-ap-proof-sub">
                    {L({
                      fr: `« ${apLever.label} » ajouté à profile.json (refus_passes). Jamais re-proposé.`,
                      en: `“${apLever.label}” added to profile.json (past refusals). Never proposed again.`,
                      de: `„${apLever.label}“ zu profile.json hinzugefügt (frühere Ablehnungen). Wird nie wieder vorgeschlagen.`,
                      es: `«${apLever.label}» añadido a profile.json (rechazos anteriores). Nunca se vuelve a proponer.`,
                      it: `«${apLever.label}» aggiunto a profile.json (rifiuti precedenti). Mai più proposto.`,
                    })}
                  </p>
                  <button className="arg-ap-again" onClick={startAutopilot}>↻ {L({ fr: "Rejouer", en: "Replay", de: "Erneut abspielen", es: "Repetir", it: "Rigioca" })}</button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Liste d'attente (fake-it) */}
      {wl && (
        <div className="arg-wl" role="dialog" aria-modal="true" onClick={() => setWl(null)}>
          <div className="arg-wl-box" onClick={(e) => e.stopPropagation()}>
            <p className="arg-wl-title">{L({ fr: "Liste d'attente", en: "Waitlist", de: "Warteliste", es: "Lista de espera", it: "Lista d'attesa" })}</p>
            <p className="arg-wl-sub">{L({ fr: "On te prévient dès l'ouverture.", en: "We'll ping you at launch.", de: "Wir melden uns zum Start.", es: "Te avisamos en el lanzamiento.", it: "Ti avvisiamo al lancio." })}</p>
            {wlJoined[wl] ? (
              <p className="arg-wl-done">✓ {L({ fr: "Tu es sur la liste.", en: "You're on the list.", de: "Du bist auf der Liste.", es: "Estás en la lista.", it: "Sei nella lista." })}</p>
            ) : (
              <form
                className="arg-wl-form"
                onSubmit={(e) => {
                  e.preventDefault();
                  if (wlEmail.includes("@")) setWlJoined((j) => ({ ...j, [wl]: true }));
                }}
              >
                <input
                  className="arg-wl-input"
                  type="email"
                  required
                  placeholder="email@exemple.com"
                  value={wlEmail}
                  onChange={(e) => setWlEmail(e.target.value)}
                />
                <button className="arg-wl-submit" type="submit">
                  {L({ fr: "Rejoindre", en: "Join", de: "Beitreten", es: "Unirse", it: "Iscriviti" })}
                </button>
              </form>
            )}
            <button className="arg-wl-close" onClick={() => setWl(null)}>
              {L({ fr: "Fermer", en: "Close", de: "Schließen", es: "Cerrar", it: "Chiudi" })}
            </button>
          </div>
        </div>
      )}

      {/* Voix ElevenLabs — explique la page (TTS) + Q&A vocal si agent configuré */}
      <div className="arg-voice">
        {CONVAI_AGENT_ID && <div ref={convaiRef} className="arg-voice-convai" />}
        <button
          className={"arg-voice-btn" + (voiceState !== "idle" ? " on" : "")}
          onClick={playVoice}
          disabled={voiceState === "loading"}
          aria-label={L({ fr: "Écouter l'explication", en: "Listen to the explanation", de: "Erklärung anhören", es: "Escuchar la explicación", it: "Ascolta la spiegazione" })}
        >
          <span className="arg-voice-ico">{voiceState === "loading" ? "…" : voiceState === "playing" ? "⏹" : "🔊"}</span>
          <span className="arg-voice-txt">
            {voiceState === "playing"
              ? L({ fr: "Stop", en: "Stop", de: "Stopp", es: "Parar", it: "Ferma" })
              : L({ fr: "Explique-moi", en: "Explain this", de: "Erklär mir", es: "Explícame", it: "Spiegami" })}
          </span>
        </button>
      </div>
    </div>
  );
}

// Marque Argentier : chevron « A » + barres ascendantes (le run-rate qui monte).
function ArgLogo() {
  return (
    <svg className="arg-logo" viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <path
        d="M5.5 25.5 L16 5.5 L26.5 25.5"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      <rect x="12" y="19.5" width="2.3" height="6" rx="0.7" className="arg-logo-bar" />
      <rect x="15.4" y="16.5" width="2.3" height="9" rx="0.7" className="arg-logo-bar" />
      <rect x="18.8" y="13.5" width="2.3" height="12" rx="0.7" className="arg-logo-bar" />
    </svg>
  );
}

// Waterfall : du total des sorties au vrai run-rate pilotable (le relevé « ment »).
function NatureWaterfall({
  natures,
  out,
  lang,
  fmt,
}: {
  natures: NatureSlice[];
  out: number;
  lang: Lang;
  fmt: (n: number) => string;
}) {
  const by = (k: Nature) => natures.find((n) => n.key === k)?.amount ?? 0;
  const perso = by("perso");
  const ponctuel = by("ponctuel");
  const structurel = by("structurel");
  const pilotable = by("pilotable");
  const max = Math.max(out, 1);
  const W = 560;
  const top = 24;
  const bottom = 196;
  const colW = 78;
  const gap = (W - 5 * colW) / 6;
  const y = (v: number) => bottom - (v / max) * (bottom - top);
  const xAt = (i: number) => gap + i * (colW + gap);
  const bars = [
    { fill: "var(--c-ink)", label: pick(lang, { fr: "Total", en: "Total", de: "Gesamt", es: "Total", it: "Totale" }), hi: out, lo: 0, val: out },
    { fill: "var(--c-line-strong)", label: pick(lang, { fr: "− Perso", en: "− Personal", de: "− Privat", es: "− Personal", it: "− Personale" }), hi: out, lo: out - perso, val: perso },
    { fill: "var(--c-amber)", label: pick(lang, { fr: "− Ponctuel", en: "− One-off", de: "− Einmalig", es: "− Puntual", it: "− Una tantum" }), hi: out - perso, lo: out - perso - ponctuel, val: ponctuel },
    { fill: "var(--c-ink2)", label: pick(lang, { fr: "− Structurel", en: "− Structural", de: "− Strukturell", es: "− Estructural", it: "− Strutturale" }), hi: out - perso - ponctuel, lo: pilotable, val: structurel },
    { fill: "var(--c-vert)", label: pick(lang, { fr: "Pilotable", en: "Controllable", de: "Steuerbar", es: "Controlable", it: "Gestibile" }), hi: pilotable, lo: 0, val: pilotable },
  ];
  const running = [out, out - perso, out - perso - ponctuel, pilotable];
  return (
    <svg
      className="arg-wf"
      viewBox={`0 0 ${W} 236`}
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label={pick(lang, { fr: "Cascade : du total au run-rate pilotable", en: "Waterfall: from total to controllable run-rate", de: "Wasserfall: vom Gesamtbetrag zur steuerbaren Run-Rate", es: "Cascada: del total al run-rate controlable", it: "Cascata: dal totale al run-rate gestibile" })}
    >
      {running.map((lvl, i) => (
        <line key={"l" + i} className="arg-wf-link" x1={xAt(i) + colW} y1={y(lvl)} x2={xAt(i + 1)} y2={y(lvl)} />
      ))}
      {bars.map((b, i) => {
        const x = xAt(i);
        const yt = y(b.hi);
        const h = Math.max(2, y(b.lo) - y(b.hi));
        return (
          <g key={i}>
            <rect x={x} y={yt} width={colW} height={h} rx="3" fill={b.fill} />
            <text className="arg-wf-val" x={x + colW / 2} y={yt - 7} textAnchor="middle">
              {fmt(b.val)}
            </text>
            <text className="arg-wf-cat" x={x + colW / 2} y={218} textAnchor="middle">
              {b.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function Metric({ label, value, note, accent }: { label: string; value: string; note?: string; accent?: boolean }) {
  return (
    <div className="arg-metric">
      <p className="arg-metric-label">{label}</p>
      <p className={"arg-metric-val arg-mono" + (accent ? " accent" : "")}>{value}</p>
      {note && <p className="arg-metric-note">{note}</p>}
    </div>
  );
}

function SimStat({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="arg-simstat">
      <p className={"arg-simstat-val arg-mono" + (accent ? " accent" : "")}>{value}</p>
      <p className="arg-simstat-label">{label}</p>
    </div>
  );
}

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;600&display=swap');

.arg-root{
  --c-paper:#FAFAF7; --c-ink:#17140F; --c-ink2:#5B554C;
  --c-line:#E4E0D6; --c-line-strong:#B8B2A5;
  --c-vert:#2F6F5B; --c-vert-soft:#E7F0EC; --c-amber:#B9812B; --c-clay:#A9432B;
  --r:14px;
  max-width:860px; margin:0 auto; padding:28px 20px 48px;
  background:var(--c-paper); color:var(--c-ink);
  font-family:'Inter',system-ui,sans-serif; line-height:1.5;
  -webkit-font-smoothing:antialiased;
}
.arg-root *{box-sizing:border-box;}
.arg-mono{font-family:'JetBrains Mono',ui-monospace,monospace; font-variant-numeric:tabular-nums;}

.arg-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:22px;gap:12px;flex-wrap:wrap;}
.arg-brand{display:flex;align-items:center;gap:10px;}
.arg-mark{width:30px;height:30px;border-radius:8px;background:var(--c-ink);color:var(--c-paper);
  display:flex;align-items:center;justify-content:center;font-family:'Space Grotesk';font-size:18px;flex:none;}
.arg-logo{width:66%;height:66%;display:block;}
.arg-logo-bar{fill:var(--c-amber);}
.arg-word{font-family:'Space Grotesk';font-weight:600;font-size:18px;letter-spacing:-.01em;}
.arg-chip{font-size:11px;color:var(--c-ink2);border:1px solid var(--c-line);border-radius:99px;padding:3px 10px;}
.arg-src{font-size:11px;font-weight:700;padding:3px 9px;border-radius:99px;white-space:nowrap;letter-spacing:.01em;}
.arg-src.live{background:var(--c-vert-soft);color:var(--c-vert);border:1px solid color-mix(in srgb,var(--c-vert) 32%,transparent);}
.arg-src.demo{background:color-mix(in srgb,var(--c-amber) 13%,transparent);color:var(--c-amber);border:1px solid color-mix(in srgb,var(--c-amber) 30%,transparent);}
.arg-top-right{display:flex;align-items:center;justify-content:flex-end;gap:12px;flex-wrap:wrap;}
.arg-window{font-size:12px;color:var(--c-ink2);}
.arg-figure.loading{opacity:.5;animation:argPulse 1s ease-in-out infinite;}
@keyframes argPulse{0%,100%{opacity:.4}50%{opacity:.72}}
@media(prefers-reduced-motion:reduce){.arg-figure.loading{animation:none;opacity:1;}}
.arg-lang{display:inline-flex;flex-wrap:wrap;border:1px solid var(--c-line);border-radius:8px;overflow:hidden;}
.arg-lang-btn{display:inline-flex;align-items:center;gap:3px;border:0;background:#fff;color:var(--c-ink2);
  font-family:inherit;font-size:11px;font-weight:600;padding:4px 8px;cursor:pointer;transition:background .1s,color .1s;
  border-left:1px solid var(--c-line);}
.arg-lang-btn:first-child{border-left:0;}
.arg-lang-flag{font-size:11px;line-height:1;}
.arg-lang-btn.on{background:var(--c-ink);color:var(--c-paper);}
.arg-lang-btn:not(.on):hover{background:var(--c-vert-soft);}
.arg-pitch-open{border:1px solid var(--c-vert);background:var(--c-vert);color:#fff;border-radius:8px;
  font-family:inherit;font-size:12px;font-weight:600;padding:5px 12px;cursor:pointer;transition:transform .08s ease,opacity .1s;}
.arg-pitch-open:hover{transform:translateY(-1px);opacity:.94;}

/* Présentation plein écran */
.arg-pitch{position:fixed;inset:0;z-index:60;background:var(--c-paper);display:flex;flex-direction:column;
  animation:argFade .25s ease;}
@keyframes argFade{from{opacity:0}to{opacity:1}}
.arg-pitch-bar{display:flex;align-items:center;justify-content:space-between;gap:12px;
  padding:16px 22px;border-bottom:1px solid var(--c-line);flex:none;}
.arg-pitch-brand{display:flex;align-items:center;gap:9px;font-family:'Space Grotesk';font-weight:600;font-size:17px;}
.arg-pitch-controls{display:flex;align-items:center;gap:12px;}
.arg-pitch-scroll{flex:1;overflow:auto;}
.arg-pitch-inner{max-width:760px;margin:0 auto;padding:min(9vh,72px) 24px 96px;}
.arg-pitch-kicker{font-size:12px;text-transform:uppercase;letter-spacing:.16em;color:var(--c-vert);
  font-weight:700;margin:0 0 22px;}
/* Hero : carte d'Europe + entreprises flottantes */
.arg-eu{position:relative;width:100%;aspect-ratio:1000/626;max-height:60vh;margin:0 0 34px;
  padding-bottom:22px;border-bottom:1px solid var(--c-line);isolation:isolate;}
.arg-eu-map{position:absolute;inset:0;width:100%;height:100%;z-index:0;}
.arg-eu-map path{fill:color-mix(in srgb,var(--c-vert) 15%,transparent);
  stroke:color-mix(in srgb,var(--c-vert) 42%,transparent);stroke-width:1;
  stroke-linejoin:round;vector-effect:non-scaling-stroke;}
.arg-eu-co{position:absolute;z-index:1;transform:translate(-50%,-50%);
  display:flex;flex-direction:column;align-items:center;gap:2px;
  animation:argFloat 4s ease-in-out infinite;will-change:transform;pointer-events:none;}
.arg-eu-dot{display:flex;align-items:center;justify-content:center;border-radius:50%;
  background:#fff;color:var(--c-ink2);border:1px solid var(--c-line-strong);
  box-shadow:0 3px 10px rgba(23,20,15,.10);line-height:1;font-style:normal;}
.arg-eu-co.t1 .arg-eu-dot{width:16px;height:16px;font-size:7px;}
.arg-eu-co.t2 .arg-eu-dot{width:22px;height:22px;font-size:9px;}
.arg-eu-co.t3 .arg-eu-dot{width:30px;height:30px;font-size:12px;}
.arg-eu-co.cfo .arg-eu-dot{background:var(--c-vert);color:#fff;border-color:var(--c-vert);
  box-shadow:0 4px 14px color-mix(in srgb,var(--c-vert) 45%,transparent);}
.arg-eu-city{font-style:normal;font-size:9.5px;font-weight:600;color:var(--c-ink2);
  letter-spacing:.01em;white-space:nowrap;opacity:.68;
  text-shadow:0 1px 3px var(--c-paper),0 0 3px var(--c-paper);}
.arg-eu-co.cfo .arg-eu-city{color:var(--c-vert);opacity:1;}
.arg-eu-co.t1 .arg-eu-city{font-size:8px;opacity:.5;}
@keyframes argFloat{0%,100%{transform:translate(-50%,-50%)}50%{transform:translate(-50%,calc(-50% - 8px))}}

.arg-eu-title{position:absolute;left:2px;top:6px;z-index:2;max-width:min(64%,420px);
  display:flex;flex-direction:column;gap:2px;}
.arg-pitch-num{font-family:'JetBrains Mono',ui-monospace,monospace;font-weight:600;
  font-size:clamp(64px,13vw,120px);line-height:.86;color:var(--c-vert);letter-spacing:-.03em;
  text-shadow:0 2px 20px var(--c-paper),0 0 8px var(--c-paper);}
.arg-pitch-hookcap{font-family:'Space Grotesk';font-weight:600;font-size:clamp(18px,3vw,28px);
  color:var(--c-ink);max-width:340px;letter-spacing:-.01em;line-height:1.12;
  text-shadow:0 1px 10px var(--c-paper),0 0 6px var(--c-paper);}
@media(prefers-reduced-motion:reduce){.arg-eu-co{animation:none;}}
@media(max-width:560px){.arg-eu-city{display:none;}
  .arg-eu-co.cfo .arg-eu-city{display:block;}
  .arg-eu-co.t1 .arg-eu-dot{width:12px;height:12px;}}
.arg-pitch-para{font-size:clamp(17px,2.1vw,21px);line-height:1.62;color:var(--c-ink2);margin:0 0 22px;text-wrap:pretty;}
.arg-pitch-para strong{color:var(--c-ink);font-weight:600;}
.arg-pitch-tagline{font-family:'Space Grotesk';font-weight:600;font-size:clamp(24px,4.2vw,38px);
  line-height:1.15;color:var(--c-vert);letter-spacing:-.02em;margin:14px 0 0;text-wrap:balance;
  padding-top:26px;border-top:2px solid var(--c-ink);}
@media(prefers-reduced-motion:reduce){.arg-pitch{animation:none;}}

/* Architecture (bas du pitch deck) */
.arg-arch{margin-top:64px;padding-top:34px;border-top:1px solid var(--c-line);}
.arg-arch-kicker{font-size:12px;text-transform:uppercase;letter-spacing:.16em;color:var(--c-vert);
  font-weight:700;margin:0 0 12px;}
.arg-arch-title{font-family:'Space Grotesk';font-weight:600;font-size:clamp(24px,3.6vw,34px);
  letter-spacing:-.02em;line-height:1.1;color:var(--c-ink);margin:0 0 14px;}
.arg-arch-lede{font-size:clamp(15px,1.7vw,18px);line-height:1.6;color:var(--c-ink2);margin:0 0 26px;
  max-width:620px;text-wrap:pretty;}
.arg-arch-lede strong{color:var(--c-ink);font-weight:600;}

.arg-arch-flow{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 28px;}
.arg-arch-step{display:inline-flex;align-items:center;gap:7px;padding:7px 13px 7px 9px;
  border:1px solid var(--c-line);border-radius:99px;background:#fff;
  font-size:12px;font-weight:600;letter-spacing:.02em;color:var(--c-ink);text-transform:uppercase;}
.arg-arch-step b{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:10px;font-weight:600;
  color:#fff;background:var(--c-vert);border-radius:6px;padding:2px 5px;letter-spacing:0;}
.arg-arch-step:last-child{border-color:color-mix(in srgb,var(--c-vert) 40%,transparent);
  background:var(--c-vert-soft);color:var(--c-vert);}

.arg-arch-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:0 0 26px;}
.arg-arch-card{border:1px solid var(--c-line);border-radius:var(--r);background:#fff;
  padding:18px;display:flex;flex-direction:column;}
.arg-arch-head{display:flex;align-items:center;gap:8px;flex-wrap:wrap;
  font-family:'JetBrains Mono',ui-monospace,monospace;font-weight:600;font-size:14px;color:var(--c-ink);}
.arg-arch-head i{width:11px;height:11px;flex:none;border-radius:3px;}
.arg-arch-head i.lock{background:var(--c-vert);}
.arg-arch-head i.calc{background:var(--c-ink);}
.arg-arch-head i.src{background:var(--c-amber);}
.arg-arch-tag{font-family:'Inter',sans-serif;font-size:10px;font-weight:700;text-transform:uppercase;
  letter-spacing:.04em;padding:2px 7px;border-radius:99px;white-space:nowrap;}
.arg-arch-tag.green{background:var(--c-vert-soft);color:var(--c-vert);}
.arg-arch-tag.ink{background:color-mix(in srgb,var(--c-ink) 8%,transparent);color:var(--c-ink);}
.arg-arch-tag.amber{background:color-mix(in srgb,var(--c-amber) 15%,transparent);color:var(--c-amber);}
.arg-arch-desc{font-size:14px;font-weight:500;color:var(--c-ink);margin:12px 0 10px;line-height:1.4;}
.arg-arch-tools{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:11px;line-height:1.6;
  color:var(--c-ink2);background:var(--c-paper);border:1px solid var(--c-line);border-radius:8px;
  padding:9px 11px;display:block;word-break:break-word;}
.arg-arch-foot{font-size:12px;line-height:1.5;color:var(--c-ink2);margin:11px 0 0;}
.arg-arch-foot b,.arg-arch-foot strong{color:var(--c-ink);font-weight:600;}

.arg-arch-rails{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;
  padding:16px;border:1px solid var(--c-line);border-radius:var(--r);
  background:var(--c-vert-soft);margin:0 0 22px;}
.arg-arch-rail{display:flex;align-items:center;gap:9px;font-size:12.5px;font-weight:600;color:var(--c-ink);}
.arg-arch-rail b{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:11px;color:#fff;
  background:var(--c-vert);width:19px;height:19px;flex:none;border-radius:50%;
  display:flex;align-items:center;justify-content:center;}
.arg-arch-close{font-family:'Space Grotesk';font-weight:600;font-size:clamp(15px,1.9vw,19px);
  color:var(--c-vert);letter-spacing:-.01em;margin:0;text-wrap:balance;}
@media(max-width:720px){.arg-arch-grid{grid-template-columns:1fr;}
  .arg-arch-rails{grid-template-columns:repeat(2,1fr);}}

/* Autopilote — bouton + modale done-for-you */
.arg-ap-open{border:1px solid var(--c-vert);background:linear-gradient(180deg,var(--c-vert),#255a49);color:#fff;
  border-radius:8px;font-family:inherit;font-size:12px;font-weight:600;padding:5px 12px;cursor:pointer;
  box-shadow:0 1px 0 rgba(255,255,255,.15) inset,0 2px 8px color-mix(in srgb,var(--c-vert) 40%,transparent);
  transition:transform .08s ease,opacity .1s;}
.arg-ap-open:hover{transform:translateY(-1px);}
.arg-ap{position:fixed;inset:0;z-index:70;background:var(--c-paper);display:flex;flex-direction:column;animation:argFade .25s ease;}
.arg-ap-bar{display:flex;align-items:center;justify-content:space-between;padding:16px 22px;border-bottom:1px solid var(--c-line);flex:none;}
.arg-ap-brand{display:flex;align-items:center;gap:9px;font-family:'Space Grotesk';font-weight:600;font-size:17px;}
.arg-ap-badge{font-family:'Inter';font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;
  background:var(--c-vert-soft);color:var(--c-vert);padding:3px 8px;border-radius:99px;}
.arg-ap-body{flex:1;overflow:auto;display:grid;grid-template-columns:minmax(220px,300px) 1fr;}
@media(max-width:760px){.arg-ap-body{grid-template-columns:1fr;}}
.arg-ap-steps{list-style:none;margin:0;padding:28px 24px;border-right:1px solid var(--c-line);display:flex;flex-direction:column;gap:6px;}
@media(max-width:760px){.arg-ap-steps{border-right:0;border-bottom:1px solid var(--c-line);flex-direction:row;flex-wrap:wrap;gap:8px 14px;padding:16px;}}
.arg-ap-step{display:flex;align-items:center;gap:10px;font-size:13.5px;color:var(--c-ink2);padding:6px 0;transition:color .2s;}
.arg-ap-num{width:22px;height:22px;flex:none;border-radius:50%;display:flex;align-items:center;justify-content:center;
  font-family:'JetBrains Mono',ui-monospace,monospace;font-size:11px;font-weight:600;border:1px solid var(--c-line-strong);color:var(--c-ink2);background:#fff;}
.arg-ap-step.done{color:var(--c-ink);}
.arg-ap-step.done .arg-ap-num{background:var(--c-vert);border-color:var(--c-vert);color:#fff;}
.arg-ap-step.cur{color:var(--c-ink);font-weight:600;}
.arg-ap-step.cur .arg-ap-num{border-color:var(--c-vert);color:var(--c-vert);box-shadow:0 0 0 3px var(--c-vert-soft);}
.arg-ap-panel{display:flex;align-items:center;justify-content:center;padding:min(6vh,56px) 24px;}
.arg-ap-run{display:flex;flex-direction:column;align-items:center;gap:14px;text-align:center;}
.arg-ap-spin{width:34px;height:34px;border-radius:50%;border:3px solid var(--c-line);border-top-color:var(--c-vert);animation:argSpin .8s linear infinite;}
@keyframes argSpin{to{transform:rotate(360deg);}}
.arg-ap-runlabel{font-family:'Space Grotesk';font-weight:600;font-size:clamp(16px,2.2vw,20px);color:var(--c-ink);margin:0;max-width:460px;text-wrap:balance;}
.arg-ap-tool{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:11.5px;color:var(--c-ink2);background:#fff;border:1px solid var(--c-line);border-radius:8px;padding:8px 12px;}
.arg-ap-gate{display:flex;flex-direction:column;align-items:center;gap:16px;width:100%;max-width:440px;}
.arg-ap-gate-kicker{font-size:11px;text-transform:uppercase;letter-spacing:.14em;color:var(--c-vert);font-weight:700;margin:0;}
.arg-ap-card{width:100%;background:#fff;border:1px solid var(--c-line);border-radius:var(--r);padding:18px;box-shadow:0 6px 24px rgba(23,20,15,.06);}
.arg-ap-card-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px;}
.arg-ap-card-head b{font-family:'Space Grotesk';font-size:18px;}
.arg-ap-card-tag{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;background:color-mix(in srgb,var(--c-amber) 14%,transparent);color:var(--c-amber);padding:3px 8px;border-radius:99px;white-space:nowrap;}
.arg-ap-card-line{font-size:14px;color:var(--c-ink2);margin:4px 0;}
.arg-ap-card-line b{color:var(--c-ink);}
.arg-ap-card-src{font-size:11.5px;color:var(--c-ink2);margin:10px 0 0;padding-top:10px;border-top:1px solid var(--c-line);}
.arg-ap-actions{display:flex;gap:10px;width:100%;}
.arg-ap-approve,.arg-ap-refuse{flex:1;border-radius:10px;font-family:inherit;font-size:15px;font-weight:600;padding:12px;cursor:pointer;transition:transform .08s ease,opacity .1s;}
.arg-ap-approve{border:1px solid var(--c-vert);background:var(--c-vert);color:#fff;}
.arg-ap-refuse{border:1px solid var(--c-line-strong);background:#fff;color:var(--c-ink2);}
.arg-ap-approve:hover,.arg-ap-refuse:hover{transform:translateY(-1px);}
.arg-ap-gate-foot{font-size:12px;color:var(--c-ink2);margin:0;text-align:center;}
.arg-ap-proof{display:flex;flex-direction:column;align-items:center;gap:10px;text-align:center;max-width:480px;}
.arg-ap-proof-badge{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--c-vert);background:var(--c-vert-soft);padding:5px 12px;border-radius:99px;margin:0;}
.arg-ap-proof.refused .arg-ap-proof-badge{color:var(--c-ink2);background:color-mix(in srgb,var(--c-ink) 7%,transparent);}
.arg-ap-proof-num{font-weight:600;font-size:clamp(44px,9vw,76px);line-height:1;color:var(--c-vert);letter-spacing:-.03em;}
.arg-ap-proof-num span{font-size:.4em;color:var(--c-ink2);}
.arg-ap-proof-sub{font-size:15px;color:var(--c-ink2);margin:0;text-wrap:pretty;}
.arg-ap-roi{display:flex;align-items:center;gap:10px;flex-wrap:wrap;justify-content:center;background:#fff;border:1px solid var(--c-line);border-radius:12px;padding:12px 16px;font-size:14px;color:var(--c-ink2);margin-top:6px;}
.arg-ap-roi b{color:var(--c-ink);}
.arg-ap-roi-arrow{color:var(--c-vert);font-weight:700;}
.arg-ap-proof-model{font-family:'Space Grotesk';font-weight:600;font-size:16px;color:var(--c-vert);margin:4px 0 0;}
.arg-ap-again{margin-top:8px;border:1px solid var(--c-line-strong);background:#fff;color:var(--c-ink);border-radius:8px;font-family:inherit;font-size:13px;font-weight:600;padding:8px 16px;cursor:pointer;}
@media(prefers-reduced-motion:reduce){.arg-ap-spin{animation:none;}.arg-ap{animation:none;}}

/* Levier — badge hausse silencieuse */
.arg-hausse{display:inline-flex;align-items:center;gap:2px;font-size:10.5px;font-weight:700;
  color:var(--c-clay);background:color-mix(in srgb,var(--c-clay) 12%,transparent);
  border-radius:99px;padding:1px 7px;margin-left:8px;letter-spacing:.01em;vertical-align:middle;white-space:nowrap;}

/* Carte TVA récupérable (levier fiscal) */
.arg-tva{border-left:3px solid var(--c-amber);}
.arg-tva-body{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;}
.arg-tva-kicker{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--c-amber);font-weight:700;margin:0 0 4px;}
.arg-tva-title{font-family:'Space Grotesk';font-weight:600;font-size:clamp(16px,2vw,19px);color:var(--c-ink);margin:0 0 5px;}
.arg-tva-sub{font-size:12.5px;color:var(--c-ink2);margin:0;max-width:520px;}
.arg-tva-num{font-weight:600;font-size:clamp(26px,4vw,38px);color:var(--c-amber);letter-spacing:-.02em;flex:none;}

/* Waterfall des natures */
.arg-wf{width:100%;height:auto;display:block;margin-top:4px;}
.arg-wf-link{stroke:var(--c-line-strong);stroke-width:1;stroke-dasharray:3 3;}
.arg-wf-val{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:11px;font-weight:600;fill:var(--c-ink);}
.arg-wf-cat{font-family:'Inter',sans-serif;font-size:11px;fill:var(--c-ink2);}

/* Suivi — board drag-and-drop */
.arg-board{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;}
@media(max-width:640px){.arg-board{grid-template-columns:1fr;}}
.arg-col{background:var(--c-paper);border:1px solid var(--c-line);border-radius:12px;padding:10px;min-height:92px;transition:border-color .15s,background .15s;}
.arg-col.drop{border-color:color-mix(in srgb,var(--c-vert) 45%,transparent);background:var(--c-vert-soft);}
.arg-col-head{font-size:12px;font-weight:600;color:var(--c-ink2);text-transform:uppercase;letter-spacing:.04em;margin:2px 4px 10px;display:flex;justify-content:space-between;}
.arg-col-head b{color:var(--c-ink);}
.arg-tile{display:flex;align-items:center;justify-content:space-between;gap:8px;background:#fff;border:1px solid var(--c-line);border-radius:8px;padding:9px 11px;margin-bottom:8px;cursor:grab;box-shadow:0 1px 2px rgba(23,20,15,.04);font-size:13.5px;}
.arg-tile:active{cursor:grabbing;}
.arg-tile-name{font-weight:500;color:var(--c-ink);min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.arg-tile-save{color:var(--c-vert);font-weight:600;font-size:12px;}
.arg-tile-right{display:flex;align-items:center;gap:6px;flex:none;}
.arg-tile-letter{flex:none;width:26px;height:26px;border:1px solid var(--c-line);background:#fff;border-radius:6px;
  color:var(--c-ink2);font-size:13px;line-height:1;cursor:pointer;display:flex;align-items:center;justify-content:center;
  transition:background .12s,color .12s,border-color .12s;}
.arg-tile-letter:hover{background:var(--c-vert-soft);color:var(--c-vert);border-color:color-mix(in srgb,var(--c-vert) 35%,transparent);}

/* Journal d'audit MCP */
.arg-audit{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:0;}
.arg-audit-row{display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:8px 0;border-bottom:1px solid var(--c-line);}
.arg-audit-row:last-child{border-bottom:0;}
.arg-audit-tool{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:11.5px;color:var(--c-ink);background:var(--c-paper);border:1px solid var(--c-line);border-radius:6px;padding:3px 8px;}
.arg-audit-out{font-size:12.5px;color:var(--c-ink2);}
.arg-audit-out.out{color:var(--c-amber);font-weight:500;}

/* Bientôt — fake-it grisé */
.arg-soon{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;}
@media(max-width:640px){.arg-soon{grid-template-columns:1fr;}}
.arg-soon-tile{position:relative;border:1px dashed var(--c-line-strong);border-radius:12px;padding:16px;background:color-mix(in srgb,var(--c-ink) 3%,transparent);}
.arg-soon-lock{position:absolute;top:12px;right:12px;opacity:.5;font-size:14px;}
.arg-soon-title{font-family:'Space Grotesk';font-weight:600;font-size:15px;color:var(--c-ink);margin:0 0 5px;opacity:.78;}
.arg-soon-desc{font-size:12.5px;color:var(--c-ink2);margin:0 0 12px;}
.arg-soon-btn{border:1px solid var(--c-vert);background:#fff;color:var(--c-vert);border-radius:8px;font-family:inherit;font-size:12px;font-weight:600;padding:7px 12px;cursor:pointer;transition:background .12s;}
.arg-soon-btn:hover{background:var(--c-vert-soft);}

/* Liste d'attente */
.arg-wl{position:fixed;inset:0;z-index:80;background:rgba(23,20,15,.42);display:flex;align-items:center;justify-content:center;padding:20px;animation:argFade .2s ease;}
.arg-wl-box{background:var(--c-paper);border:1px solid var(--c-line);border-radius:16px;padding:24px;width:100%;max-width:380px;box-shadow:0 20px 60px rgba(23,20,15,.25);text-align:center;}
.arg-wl-title{font-family:'Space Grotesk';font-weight:600;font-size:20px;color:var(--c-ink);margin:0 0 4px;}
.arg-wl-sub{font-size:13.5px;color:var(--c-ink2);margin:0 0 16px;}
.arg-wl-form{display:flex;gap:8px;}
.arg-wl-input{flex:1;min-width:0;border:1px solid var(--c-line-strong);border-radius:8px;padding:10px 12px;font-family:inherit;font-size:14px;background:#fff;color:var(--c-ink);}
.arg-wl-submit{border:1px solid var(--c-vert);background:var(--c-vert);color:#fff;border-radius:8px;font-family:inherit;font-size:14px;font-weight:600;padding:10px 16px;cursor:pointer;white-space:nowrap;}
.arg-wl-done{font-family:'Space Grotesk';font-weight:600;font-size:16px;color:var(--c-vert);margin:8px 0;}
.arg-wl-close{margin-top:14px;border:0;background:none;color:var(--c-ink2);font-family:inherit;font-size:13px;cursor:pointer;text-decoration:underline;}

/* Voix ElevenLabs — bouton flottant + widget Q&A */
.arg-voice{position:fixed;right:18px;bottom:18px;z-index:75;display:flex;flex-direction:column;align-items:flex-end;gap:10px;}
.arg-voice-btn{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--c-vert);
  background:linear-gradient(180deg,var(--c-vert),#255a49);color:#fff;border-radius:99px;
  font-family:inherit;font-size:13px;font-weight:600;padding:10px 16px;cursor:pointer;
  box-shadow:0 6px 20px color-mix(in srgb,var(--c-vert) 40%,transparent);transition:transform .08s ease,opacity .1s;}
.arg-voice-btn:hover{transform:translateY(-1px);}
.arg-voice-btn:disabled{opacity:.7;cursor:progress;}
.arg-voice-btn.on{background:var(--c-clay);border-color:var(--c-clay);box-shadow:0 6px 20px color-mix(in srgb,var(--c-clay) 40%,transparent);}
.arg-voice-ico{font-size:15px;line-height:1;}
@media(max-width:560px){.arg-voice{right:12px;bottom:12px;}.arg-voice-txt{display:none;}}

.arg-hero{display:flex;justify-content:space-between;align-items:flex-start;gap:24px;
  padding:26px;border:1px solid var(--c-line);border-radius:var(--r);background:#fff;margin-bottom:12px;}
.arg-eyebrow{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--c-ink2);margin:0 0 10px;}
.arg-figure{font-family:'JetBrains Mono';font-variant-numeric:tabular-nums;font-weight:600;
  font-size:clamp(38px,7vw,56px);line-height:1;color:var(--c-vert);margin:0;letter-spacing:-.02em;}
.arg-sub{font-size:14px;color:var(--c-ink2);margin:12px 0 0;}
.arg-cta{margin-top:18px;background:var(--c-ink);color:var(--c-paper);border:0;border-radius:10px;
  padding:11px 18px;font-size:14px;font-weight:500;cursor:pointer;font-family:inherit;transition:transform .08s ease;}
.arg-cta:hover{transform:translateY(-1px);}
.arg-hero-side{display:flex;flex-direction:column;align-items:center;gap:14px;flex:none;}
.arg-score{position:relative;text-align:center;}
.arg-score-bg{fill:none;stroke:var(--c-vert-soft);stroke-width:3;}
.arg-score-fg{fill:none;stroke:var(--c-vert);stroke-width:3;stroke-linecap:round;transform:rotate(-90deg);transform-origin:center;}
.arg-score-num{position:absolute;inset:0;top:30px;display:flex;flex-direction:column;align-items:center;line-height:1;}
.arg-score-num strong{font-family:'JetBrains Mono';font-size:22px;color:var(--c-vert);}
.arg-score-num span{font-size:10px;color:var(--c-ink2);}
.arg-score-cap{font-size:11px;color:var(--c-ink2);margin:6px 0 0;}
.arg-runway{text-align:center;border:1px solid var(--c-line);border-radius:10px;padding:8px 14px;}
.arg-runway-num{display:block;font-family:'JetBrains Mono';font-weight:600;font-size:15px;}
.arg-runway-cap{font-size:10px;color:var(--c-ink2);}

.arg-card{border:1px solid var(--c-line);border-radius:var(--r);background:#fff;padding:18px 20px;margin-bottom:12px;}
.arg-card-head{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:14px;gap:10px;}
.arg-card-title{font-family:'Space Grotesk';font-weight:600;font-size:15px;}
.arg-muted{color:var(--c-ink2);font-size:12px;}

.arg-ledger{display:flex;height:16px;border-radius:6px;overflow:hidden;margin-bottom:10px;}
.arg-ledger-seg{height:100%;}
.arg-legend{display:flex;flex-wrap:wrap;gap:14px;font-size:12px;color:var(--c-ink2);}
.arg-legend-item{display:flex;align-items:center;gap:6px;}
.arg-legend-item i{width:9px;height:9px;border-radius:2px;display:inline-block;}
.arg-legend-item b{color:var(--c-ink);font-weight:600;}

.arg-metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:12px;}
.arg-metric{border:1px solid var(--c-line);border-radius:var(--r);background:#fff;padding:16px 18px;}
.arg-metric-label{font-size:12px;color:var(--c-ink2);margin:0 0 6px;}
.arg-metric-val{font-size:22px;font-weight:600;margin:0;}
.arg-metric-val.accent{color:var(--c-vert);}
.arg-metric-note{font-size:11px;color:var(--c-ink2);margin:5px 0 0;}

.arg-bars{display:flex;flex-direction:column;gap:9px;}
.arg-bar-row{display:grid;grid-template-columns:170px 1fr 64px;align-items:center;gap:12px;}
.arg-bar-label{font-size:12px;color:var(--c-ink2);}
.arg-bar-track{height:9px;background:var(--c-vert-soft);border-radius:5px;overflow:hidden;}
.arg-bar-fill{height:100%;background:var(--c-vert);border-radius:5px;}
.arg-bar-val{font-size:12px;text-align:right;}

.arg-sim-read{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px;}
.arg-simstat-val{font-size:20px;font-weight:600;margin:0;}
.arg-simstat-val.accent{color:var(--c-vert);}
.arg-simstat-label{font-size:11px;color:var(--c-ink2);margin:3px 0 0;}

.arg-horizon{display:flex;align-items:center;gap:12px;margin-bottom:12px;font-size:13px;color:var(--c-ink2);}
.arg-horizon input{flex:1;accent-color:var(--c-vert);}
.arg-progress{height:8px;background:var(--c-line);border-radius:5px;overflow:hidden;margin-bottom:16px;}
.arg-progress>div{height:100%;background:var(--c-vert);transition:width .2s ease;}

.arg-levers{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:8px;}
.arg-lever{display:flex;align-items:stretch;border:1px solid var(--c-line);border-radius:10px;
  background:#fff;overflow:hidden;transition:border-color .1s,background .1s;}
.arg-lever:hover{border-color:var(--c-line-strong);}
.arg-lever.on{border-color:var(--c-vert);background:var(--c-vert-soft);}
.arg-lever-toggle{flex:1;display:flex;align-items:center;gap:10px;padding:10px 12px;border:0;
  background:transparent;cursor:pointer;text-align:left;font-family:inherit;color:inherit;}
.arg-lever-letter{flex:none;width:42px;border:0;border-left:1px solid var(--c-line);background:transparent;
  cursor:pointer;font-size:15px;color:var(--c-ink2);transition:background .1s,color .1s;}
.arg-lever-letter:hover{background:var(--c-vert-soft);color:var(--c-vert);}
.arg-lever.on .arg-lever-letter{border-left-color:color-mix(in srgb,var(--c-vert) 30%,transparent);}
.arg-lever-status{flex:none;align-self:center;border:1px solid var(--c-line);border-radius:7px;background:#fff;
  color:var(--c-ink2);font-family:inherit;font-size:11.5px;font-weight:500;padding:5px 6px;margin:0 2px;cursor:pointer;max-width:130px;}
.arg-lever-status:hover{border-color:var(--c-line-strong);}
.arg-lever-status:focus-visible{outline:2px solid var(--c-vert);outline-offset:1px;}
.arg-check{width:18px;height:18px;border-radius:5px;border:1.5px solid var(--c-line-strong);
  display:flex;align-items:center;justify-content:center;font-size:12px;color:#fff;flex:none;}
.arg-lever.on .arg-check{background:var(--c-vert);border-color:var(--c-vert);}
.arg-lever-txt{flex:1;font-size:13px;}
.arg-risk{font-size:11px;white-space:nowrap;}
.arg-lever-save{font-size:13px;font-weight:600;min-width:46px;text-align:right;}

.arg-hint{font-size:11px;color:var(--c-ink2);margin:12px 0 0;}

/* Tiroir lettre */
.arg-drawer-wrap{position:fixed;inset:0;z-index:50;display:flex;justify-content:flex-end;}
.arg-drawer-backdrop{position:absolute;inset:0;background:rgba(23,20,15,.32);}
.arg-drawer{position:relative;width:min(520px,100%);height:100%;background:var(--c-paper);
  border-left:1px solid var(--c-line);box-shadow:-8px 0 30px rgba(23,20,15,.12);
  display:flex;flex-direction:column;padding:22px 22px 18px;overflow:auto;}
.arg-drawer-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:14px;}
.arg-drawer-eyebrow{font-size:10px;text-transform:uppercase;letter-spacing:.09em;font-weight:700;
  color:var(--c-vert);margin:0 0 4px;}
.arg-drawer-title{font-family:'Space Grotesk';font-weight:600;font-size:20px;margin:0;letter-spacing:-.01em;}
.arg-drawer-close{border:1px solid var(--c-line);background:#fff;border-radius:8px;width:32px;height:32px;
  cursor:pointer;font-size:14px;color:var(--c-ink2);flex:none;}
.arg-drawer-close:hover{border-color:var(--c-line-strong);}
.arg-drawer-loading{flex:1;display:flex;align-items:center;justify-content:center;color:var(--c-ink2);
  font-size:14px;border:1px dashed var(--c-line);border-radius:10px;margin-bottom:12px;min-height:220px;}
.arg-drawer-text{flex:1;min-height:340px;width:100%;resize:vertical;border:1px solid var(--c-line);
  border-radius:10px;padding:14px;font-size:12.5px;line-height:1.6;color:var(--c-ink);background:#fff;
  margin-bottom:12px;white-space:pre-wrap;}
.arg-drawer-text:focus{outline:2px solid var(--c-vert);outline-offset:1px;}
.arg-drawer-actions{display:flex;gap:8px;}
.arg-drawer-actions .arg-btn{flex:1;text-align:center;}
.arg-drawer-note{font-size:11px;color:var(--c-ink2);margin:10px 0 0;text-align:center;}
.arg-send-reco{width:100%;margin-top:10px;display:flex;align-items:center;justify-content:center;gap:8px;
  border:1px solid var(--c-line);background:color-mix(in srgb,var(--c-ink) 4%,transparent);color:var(--c-ink2);
  border-radius:10px;font-family:inherit;font-size:14px;font-weight:600;padding:11px;cursor:not-allowed;opacity:.75;}
.arg-soon-pill{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;
  background:color-mix(in srgb,var(--c-amber) 16%,transparent);color:var(--c-amber);padding:2px 7px;border-radius:99px;}

.arg-bench{margin-top:16px;padding-top:14px;border-top:1px solid var(--c-line);}
.arg-bench-head{display:flex;align-items:center;justify-content:space-between;gap:10px;}
.arg-bench-title{font-family:'Space Grotesk';font-weight:600;font-size:13px;}
.arg-bench-btn{font-size:12px;padding:6px 11px;}
.arg-bench-hint{font-size:12px;color:var(--c-ink2);margin:10px 0 0;}
.arg-bench-best{font-size:12px;font-weight:600;color:var(--c-vert);margin:10px 0 0;}
.arg-bench-via{font-size:10.5px;color:var(--c-ink2);margin:10px 0 0;text-align:right;font-style:italic;}
.arg-bench-list{list-style:none;margin:10px 0 0;padding:0;display:flex;flex-direction:column;gap:7px;}
.arg-bench-list li{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;font-size:12.5px;
  padding-bottom:7px;border-bottom:1px solid var(--c-line);}
.arg-bench-alt{font-weight:600;}
.arg-bench-price{color:var(--c-vert);}
.arg-bench-src{font-size:11px;color:var(--c-ink2);text-decoration:underline;margin-left:auto;}
.arg-bench-src:hover{color:var(--c-vert);}
.arg-bench-inject{width:100%;margin-top:12px;font-size:12.5px;}
@media(max-width:680px){.arg-drawer{width:100%;}}

.arg-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px;}
.arg-btn{border:1px solid var(--c-line);background:#fff;border-radius:9px;padding:8px 14px;
  font-size:13px;cursor:pointer;font-family:inherit;color:var(--c-ink);transition:border-color .1s;text-decoration:none;display:inline-block;}
.arg-btn:hover{border-color:var(--c-line-strong);}
.arg-btn-ghost{margin-left:auto;background:var(--c-ink);color:var(--c-paper);border-color:var(--c-ink);}

.arg-flux{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;}
.arg-flux-row{display:flex;align-items:center;gap:10px;padding:9px 0;border-top:1px solid var(--c-line);}
.arg-flux-row:first-child{border-top:0;}
.arg-dot{width:8px;height:8px;border-radius:99px;flex:none;background:var(--c-ink2);}
.arg-dot.amber{background:var(--c-amber);} .arg-dot.danger{background:var(--c-clay);} .arg-dot.neutral{background:var(--c-line-strong);}
.arg-flux-label{flex:1;font-size:13px;}
.arg-flux-val{font-size:13px;font-weight:600;}
.arg-flux-val.danger{color:var(--c-clay);} .arg-flux-val.amber{color:var(--c-amber);}

.arg-foot{font-size:11px;color:var(--c-ink2);text-align:center;margin-top:20px;}
.arg-qwl{text-align:center;}
.arg-qwl-title{font-family:'Space Grotesk';font-weight:600;font-size:clamp(20px,3vw,28px);color:var(--c-ink);margin:0 0 18px;letter-spacing:-.01em;}
.arg-qwl-form{display:flex;gap:10px;max-width:520px;margin:0 auto;flex-wrap:wrap;justify-content:center;}
.arg-qwl-input{flex:1;min-width:220px;border:1px solid var(--c-line-strong);background:#fff;color:var(--c-ink);border-radius:99px;font-family:inherit;font-size:15px;padding:14px 20px;outline:none;transition:border-color .12s;}
.arg-qwl-input::placeholder{color:var(--c-ink2);}
.arg-qwl-input:focus{border-color:var(--c-vert);}
.arg-qwl-btn{border:1px solid var(--c-vert);background:var(--c-vert);color:#fff;border-radius:99px;font-family:inherit;font-size:15px;font-weight:600;padding:14px 22px;cursor:pointer;white-space:nowrap;transition:transform .08s ease;}
.arg-qwl-btn:hover{transform:translateY(-1px);}
.arg-qwl-hint{font-size:12.5px;color:var(--c-ink2);margin:12px 0 0;}
.arg-qwl-done{font-family:'Space Grotesk';font-weight:600;font-size:18px;color:var(--c-vert);margin:0;}

.arg-lever-toggle:focus-visible,.arg-lever-letter:focus-visible,.arg-btn:focus-visible,.arg-cta:focus-visible,.arg-lang-btn:focus-visible,.arg-horizon input:focus-visible{
  outline:2px solid var(--c-vert);outline-offset:2px;}

@media(max-width:680px){
  .arg-hero{flex-direction:column;} .arg-hero-side{flex-direction:row;align-self:stretch;justify-content:space-between;}
  .arg-metrics{grid-template-columns:1fr;} .arg-sim-read{grid-template-columns:repeat(2,1fr);}
  .arg-bar-row{grid-template-columns:120px 1fr 58px;}
}
@media(prefers-reduced-motion:reduce){.arg-cta,.arg-progress>div{transition:none;}}
`;
