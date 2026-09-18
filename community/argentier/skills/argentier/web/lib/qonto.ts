// ---------------------------------------------------------------------------
// Client Qonto — LECTURE SEULE. N'appelle QUE des endpoints GET.
// Aucun tool d'écriture, aucun mouvement d'argent. (cf. règle read-only.)
//
// Auth : clé API Qonto au format `login:secret_key` dans l'en-tête Authorization
// (Paramètres → Intégrations → API). L'OAuth natif viendra en V1 (PRD §5.1).
// ---------------------------------------------------------------------------

import type { Tx } from "./types";

const QONTO_BASE = "https://thirdparty.qonto.com/v2";

interface RawTx {
  transaction_id?: string;
  id?: string;
  amount?: number;
  amount_cents?: number;
  currency?: string;
  local_amount?: number;
  local_currency?: string;
  side?: "debit" | "credit";
  operation_type?: string;
  settled_at?: string;
  emitted_at?: string;
  label?: string;
  clean_counterparty_name?: string;
  reference?: string;
  attachment_required?: boolean;
  attachment_ids?: string[];
}

export interface QontoConfig {
  login: string;
  secretKey: string;
  iban?: string;
}

export function readQontoConfig(): QontoConfig | null {
  const login = process.env.QONTO_LOGIN;
  const secretKey = process.env.QONTO_SECRET_KEY;
  if (!login || !secretKey) return null;
  return { login, secretKey, iban: process.env.QONTO_IBAN };
}

function authHeaders(cfg: QontoConfig): HeadersInit {
  return {
    Authorization: `${cfg.login}:${cfg.secretKey}`,
    "Content-Type": "application/json",
  };
}

async function qontoGet<T>(cfg: QontoConfig, path: string): Promise<T> {
  const res = await fetch(`${QONTO_BASE}${path}`, {
    method: "GET",
    headers: authHeaders(cfg),
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Qonto ${res.status} sur ${path} : ${body.slice(0, 200)}`);
  }
  return (await res.json()) as T;
}

/** Compte + solde (get_organization). */
export async function getOrganization(cfg: QontoConfig): Promise<{
  name: string;
  balance: number;
  iban?: string;
}> {
  const data = await qontoGet<{
    organization?: {
      legal_name?: string;
      name?: string;
      bank_accounts?: Array<{ iban?: string; balance?: number; balance_cents?: number }>;
    };
  }>(cfg, "/organization");

  const org = data.organization ?? {};
  const accounts = org.bank_accounts ?? [];
  const chosen =
    (cfg.iban && accounts.find((a) => a.iban === cfg.iban)) || accounts[0] || {};
  const balance =
    chosen.balance != null
      ? chosen.balance
      : chosen.balance_cents != null
        ? chosen.balance_cents / 100
        : 0;

  return {
    name: org.legal_name || org.name || "Mon entreprise",
    balance,
    iban: chosen.iban ?? cfg.iban,
  };
}

function isFxFee(raw: RawTx): boolean {
  return (
    raw.operation_type === "qonto_fee" &&
    String(raw.reference ?? "").toLowerCase().includes("fx")
  );
}

function normalize(raw: RawTx): Tx {
  const amount =
    raw.amount != null
      ? Math.abs(raw.amount)
      : raw.amount_cents != null
        ? Math.abs(raw.amount_cents) / 100
        : 0;
  const rawDate = raw.settled_at || raw.emitted_at || "";
  return {
    id: raw.transaction_id || raw.id || `${raw.label}-${rawDate}`,
    merchant: (raw.clean_counterparty_name || raw.label || "inconnu").trim(),
    amount,
    localCurrency: raw.local_currency || raw.currency || "EUR",
    isFx: isFxFee(raw) || (!!raw.local_currency && raw.local_currency !== "EUR"),
    side: raw.side === "credit" ? "credit" : "debit",
    operationType: raw.operation_type || "unknown",
    date: rawDate.slice(0, 10),
    attachmentRequired: !!raw.attachment_required,
    hasAttachment: (raw.attachment_ids?.length ?? 0) > 0,
  };
}

/** list_transactions paginé sur une fenêtre glissante. Filtre `settled_at`. */
export async function listTransactions(
  cfg: QontoConfig,
  windowDays: number,
): Promise<Tx[]> {
  const iban = cfg.iban;
  const from = new Date(Date.now() - windowDays * 86_400_000).toISOString();

  const all: Tx[] = [];
  let page = 1;
  const maxPages = 20; // garde-fou : 20 × 100 = 2000 transactions max

  while (page <= maxPages) {
    const params = new URLSearchParams({
      sort_by: "settled_at:desc",
      per_page: "100",
      current_page: String(page),
      settled_at_from: from,
    });
    if (iban) params.set("iban", iban);

    const data = await qontoGet<{
      transactions?: RawTx[];
      meta?: { total_pages?: number; next_page?: number | null };
    }>(cfg, `/transactions?${params.toString()}`);

    const txs = data.transactions ?? [];
    all.push(...txs.map(normalize));

    const next = data.meta?.next_page;
    if (!next || txs.length === 0) break;
    page = next;
  }

  return all;
}
