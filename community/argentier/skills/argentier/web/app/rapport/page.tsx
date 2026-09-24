"use client";

/**
 * /rapport — version imprimable du plan d'action (→ PDF via « Imprimer »).
 * Bilingue : lit ?lang=fr|en (transmis par le lien) ou localStorage.
 */

import React, { useEffect, useMemo, useState } from "react";
import type { AnalyzeResult, Lang, Localized } from "@/lib/types";
import { eur as eurFmt, LANGS, natureLabel, riskLabel } from "@/lib/i18n";

const DICT = {
  fr: {
    print: "Imprimer / Enregistrer en PDF",
    title: "Argentier — Plan d'action",
    heroCap: (m: string) => `récupérables / an (${m}/mois)`,
    kOut: "Sorties du mois",
    kRunrate: "Run-rate pilotable",
    kScore: "Score de santé",
    kRunway: "Trésorerie",
    months: (n: number) => `${n} mois`,
    byNature: "Répartition par nature (mois observé)",
    plan: "Plan d'économies — leviers retenus",
    hLever: "Levier",
    hAction: "Action",
    hPerMonth: "€ / mois",
    hRisk: "Risque",
    total: "Total leviers retenus",
    perMonth: "/ mois",
    flags: "Points de vigilance (score)",
    foot: "Argentier prépare, tu décides. Aucune action bancaire n'a été déclenchée. Conseils fiscaux à valider avec ton comptable. Données traitées en Europe.",
    loading: "Chargement du rapport…",
  },
  en: {
    print: "Print / Save as PDF",
    title: "Argentier — Action plan",
    heroCap: (m: string) => `recoverable / yr (${m}/mo)`,
    kOut: "Monthly outflows",
    kRunrate: "Controllable run-rate",
    kScore: "Health score",
    kRunway: "Runway",
    months: (n: number) => `${n} months`,
    byNature: "Breakdown by nature (observed month)",
    plan: "Savings plan — selected levers",
    hLever: "Lever",
    hAction: "Action",
    hPerMonth: "€ / mo",
    hRisk: "Risk",
    total: "Total selected levers",
    perMonth: "/ mo",
    flags: "Red flags (score)",
    foot: "Argentier prepares, you decide. No banking action was triggered. Tax advice to be confirmed with your accountant. Data processed in Europe.",
    loading: "Loading report…",
  },
  de: {
    print: "Drucken / Als PDF speichern",
    title: "Argentier — Aktionsplan",
    heroCap: (m: string) => `pro Jahr zurückholbar (${m}/Monat)`,
    kOut: "Ausgaben des Monats",
    kRunrate: "Steuerbare Run-Rate",
    kScore: "Gesundheitsscore",
    kRunway: "Liquidität",
    months: (n: number) => `${n} Monate`,
    byNature: "Aufschlüsselung nach Art (beobachteter Monat)",
    plan: "Sparplan — ausgewählte Hebel",
    hLever: "Hebel",
    hAction: "Aktion",
    hPerMonth: "€ / Monat",
    hRisk: "Risiko",
    total: "Summe ausgewählter Hebel",
    perMonth: "/ Monat",
    flags: "Aufmerksamkeitspunkte (Score)",
    foot: "Argentier bereitet vor, du entscheidest. Es wurde keine Bankaktion ausgelöst. Steuerhinweise mit deinem Steuerberater abstimmen. Daten werden in Europa verarbeitet.",
    loading: "Bericht wird geladen…",
  },
  es: {
    print: "Imprimir / Guardar como PDF",
    title: "Argentier — Plan de acción",
    heroCap: (m: string) => `recuperables / año (${m}/mes)`,
    kOut: "Salidas del mes",
    kRunrate: "Run-rate controlable",
    kScore: "Puntuación de salud",
    kRunway: "Liquidez",
    months: (n: number) => `${n} meses`,
    byNature: "Desglose por naturaleza (mes observado)",
    plan: "Plan de ahorro — palancas seleccionadas",
    hLever: "Palanca",
    hAction: "Acción",
    hPerMonth: "€ / mes",
    hRisk: "Riesgo",
    total: "Total de palancas seleccionadas",
    perMonth: "/ mes",
    flags: "Puntos de vigilancia (score)",
    foot: "Argentier prepara, tú decides. No se ha activado ninguna acción bancaria. Consejos fiscales a validar con tu asesor. Datos procesados en Europa.",
    loading: "Cargando el informe…",
  },
  it: {
    print: "Stampa / Salva come PDF",
    title: "Argentier — Piano d'azione",
    heroCap: (m: string) => `recuperabili / anno (${m}/mese)`,
    kOut: "Uscite del mese",
    kRunrate: "Run-rate gestibile",
    kScore: "Punteggio di salute",
    kRunway: "Liquidità",
    months: (n: number) => `${n} mesi`,
    byNature: "Ripartizione per natura (mese osservato)",
    plan: "Piano di risparmio — leve selezionate",
    hLever: "Leva",
    hAction: "Azione",
    hPerMonth: "€ / mese",
    hRisk: "Rischio",
    total: "Totale leve selezionate",
    perMonth: "/ mese",
    flags: "Punti di attenzione (score)",
    foot: "Argentier prepara, tu decidi. Nessuna azione bancaria è stata avviata. Consigli fiscali da validare con il tuo commercialista. Dati trattati in Europa.",
    loading: "Caricamento del report…",
  },
};

export default function Rapport() {
  const [lang, setLang] = useState<Lang>("fr");
  const [data, setData] = useState<AnalyzeResult | null>(null);

  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get("lang");
    const saved = window.localStorage.getItem("argentier-lang");
    const isLang = (v: string | null): v is Lang => !!v && (LANGS as string[]).includes(v);
    const chosen: Lang = isLang(q) ? q : isLang(saved) ? saved : "fr";
    setLang(chosen);
    fetch("/api/analyze")
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData(null));
  }, []);

  const t = DICT[lang];
  const eur = (n: number) => eurFmt(n, lang);
  // de/es/it retombent sur l'anglais pour les Localized (fr/en only).
  const loc = (x: Localized) => x[lang as "fr" | "en"] ?? x.en;
  const active = useMemo(() => (data ? data.levers.filter((l) => l.active) : []), [data]);
  const monthly = active.reduce((s, l) => s + l.saving, 0);
  const annual = monthly * 12;

  if (!data) {
    return (
      <div className="rap-root">
        <style>{CSS}</style>
        <p className="rap-loading">{t.loading}</p>
      </div>
    );
  }

  return (
    <div className="rap-root">
      <style>{CSS}</style>

      <div className="rap-toolbar">
        <button className="rap-print" onClick={() => window.print()}>
          {t.print}
        </button>
      </div>

      <header className="rap-head">
        <div>
          <h1 className="rap-brand">{t.title}</h1>
          <p className="rap-sub">
            {data.account.name} · {data.account.bank} · {loc(data.window.label)}
          </p>
        </div>
        <div className="rap-hero">
          <span className="rap-hero-num">{eur(annual)}</span>
          <span className="rap-hero-cap">{t.heroCap(eur(monthly))}</span>
        </div>
      </header>

      <section className="rap-kpis">
        <Kpi label={t.kOut} value={eur(data.totals.out)} />
        <Kpi label={t.kRunrate} value={eur(data.totals.runRate) + "/m"} />
        <Kpi label={t.kScore} value={`${data.score.value}/100`} />
        <Kpi label={t.kRunway} value={t.months(data.runway.months)} />
      </section>

      <h2 className="rap-h2">{t.byNature}</h2>
      <table className="rap-table">
        <tbody>
          {data.natures.map((n) => (
            <tr key={n.key}>
              <td>{natureLabel(n.key, lang)}</td>
              <td className="rap-num">{eur(n.amount)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2 className="rap-h2">{t.plan}</h2>
      <table className="rap-table">
        <thead>
          <tr>
            <th>{t.hLever}</th>
            <th>{t.hAction}</th>
            <th className="rap-num">{t.hPerMonth}</th>
            <th>{t.hRisk}</th>
          </tr>
        </thead>
        <tbody>
          {[...data.levers]
            .sort((a, b) => Number(b.active) - Number(a.active) || b.saving - a.saving)
            .map((l) => (
              <tr key={l.id} className={l.active ? "" : "rap-off"}>
                <td>{l.label}</td>
                <td>{l.to}</td>
                <td className="rap-num">{l.saving} €</td>
                <td>{riskLabel(l.risk, lang)}</td>
              </tr>
            ))}
        </tbody>
        <tfoot>
          <tr>
            <td colSpan={2}>{t.total}</td>
            <td className="rap-num">{eur(monthly)}</td>
            <td>{t.perMonth}</td>
          </tr>
        </tfoot>
      </table>

      {data.score.drivers.length > 0 && (
        <>
          <h2 className="rap-h2">{t.flags}</h2>
          <ul className="rap-list">
            {data.score.drivers.map((d, i) => (
              <li key={i}>{loc(d)}</li>
            ))}
          </ul>
        </>
      )}

      <footer className="rap-foot">{t.foot}</footer>
    </div>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="rap-kpi">
      <span className="rap-kpi-label">{label}</span>
      <span className="rap-kpi-val">{value}</span>
    </div>
  );
}

const CSS = `
.rap-root{
  --ink:#17140F; --ink2:#5B554C; --line:#E4E0D6; --vert:#2F6F5B; --paper:#fff;
  max-width:800px;margin:0 auto;padding:32px 28px 60px;color:var(--ink);
  font-family:'Inter',system-ui,sans-serif;line-height:1.5;background:var(--paper);
}
.rap-loading{color:var(--ink2);text-align:center;padding:80px 0;}
.rap-toolbar{display:flex;justify-content:flex-end;margin-bottom:18px;}
.rap-print{background:var(--ink);color:#fff;border:0;border-radius:9px;padding:10px 16px;
  font-size:13px;font-weight:500;cursor:pointer;font-family:inherit;}
.rap-print:hover{opacity:.9;}

.rap-head{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;
  padding-bottom:16px;border-bottom:2px solid var(--ink);margin-bottom:20px;}
.rap-brand{font-size:22px;margin:0 0 4px;font-weight:700;letter-spacing:-.01em;}
.rap-sub{font-size:12px;color:var(--ink2);margin:0;}
.rap-hero{text-align:right;}
.rap-hero-num{display:block;font-family:'JetBrains Mono',ui-monospace,monospace;font-variant-numeric:tabular-nums;
  font-size:30px;font-weight:600;color:var(--vert);line-height:1;letter-spacing:-.02em;}
.rap-hero-cap{font-size:11px;color:var(--ink2);}

.rap-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:24px;}
.rap-kpi{border:1px solid var(--line);border-radius:10px;padding:12px 14px;}
.rap-kpi-label{display:block;font-size:11px;color:var(--ink2);margin-bottom:5px;}
.rap-kpi-val{font-family:'JetBrains Mono',ui-monospace,monospace;font-weight:600;font-size:16px;}

.rap-h2{font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--ink2);
  margin:24px 0 10px;font-weight:700;}
.rap-table{width:100%;border-collapse:collapse;font-size:13px;}
.rap-table th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.04em;
  color:var(--ink2);font-weight:700;padding:6px 8px;border-bottom:1px solid var(--ink);}
.rap-table td{padding:7px 8px;border-bottom:1px solid var(--line);}
.rap-num{text-align:right;font-family:'JetBrains Mono',ui-monospace,monospace;font-variant-numeric:tabular-nums;}
.rap-off{color:var(--ink2);}
.rap-off td{text-decoration:line-through;text-decoration-color:var(--line);}
.rap-table tfoot td{font-weight:700;border-top:2px solid var(--ink);border-bottom:0;padding-top:9px;}
.rap-list{font-size:13px;color:var(--ink2);padding-left:18px;margin:0;}
.rap-list li{margin-bottom:4px;}
.rap-foot{font-size:11px;color:var(--ink2);margin-top:28px;padding-top:14px;border-top:1px solid var(--line);}

@media print{
  .rap-toolbar{display:none;}
  .rap-root{padding:0;max-width:none;}
  @page{margin:16mm;}
}
@media(max-width:640px){.rap-kpis{grid-template-columns:repeat(2,1fr);}.rap-head{flex-direction:column;}.rap-hero{text-align:left;}}
`;
