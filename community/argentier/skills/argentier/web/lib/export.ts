// ---------------------------------------------------------------------------
// Export du plan d'action en CSV (ouvrable dans Excel). Fonction pure —
// utilisable côté client comme côté serveur. Séparateur « ; » pour Excel FR.
// ---------------------------------------------------------------------------

import type { AnalyzeResult, Lever, Risk } from "./types";

const RISK_LABEL: Record<Risk, string> = {
  safe: "sans risque",
  med: "à valider",
  hard: "projet",
};

function cell(v: string | number): string {
  const s = String(v);
  // Échappe les guillemets / séparateurs / retours ligne.
  return /[";\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

export function buildPlanCsv(data: AnalyzeResult, levers: Lever[]): string {
  const active = levers.filter((l) => l.active);
  const monthly = active.reduce((s, l) => s + l.saving, 0);
  const annual = monthly * 12;

  const lines: string[] = [];
  lines.push(cell(`Plan d'action Argentier — ${data.account.name} — ${data.window.label}`));
  lines.push([cell("Run-rate pilotable"), cell(`${data.totals.runRate} €/mois`)].join(";"));
  lines.push(
    [cell("Économie active"), cell(`${monthly} €/mois`), cell(`${annual} €/an`)].join(";"),
  );
  lines.push("");
  lines.push(
    ["Levier", "Action / alternative", "Économie €/mois", "Risque", "Statut"]
      .map(cell)
      .join(";"),
  );
  for (const l of levers) {
    lines.push(
      [
        cell(l.label),
        cell(l.to),
        cell(l.saving),
        cell(RISK_LABEL[l.risk]),
        cell(l.active ? "retenu" : "écarté"),
      ].join(";"),
    );
  }
  // BOM pour qu'Excel lise l'UTF-8 (accents).
  return "﻿" + lines.join("\r\n");
}

export function planFilename(data: AnalyzeResult): string {
  const slug = data.account.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
  return `plan-argentier-${slug || "compte"}.csv`;
}
