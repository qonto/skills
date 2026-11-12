// Trusted policy — pure parsing + digest (no filesystem, no LLM, no NL).
// The node layer reads the file bytes and hands them here; this module only ever
// parses a small deterministic structure. Natural language is NEVER interpreted
// here: the Skill compiles operator prose into these typed directives (which the
// operator ratifies) BEFORE the bytes reach this parser. Any line outside the
// grammar throws. Two accepted shapes:
//   - `.txt`  key = value lines (comments with '#', blank lines ignored):
//         currency          = EUR
//         hard_block        = 50000
//         role.owner        = 10000
//         block_supplier    = Solutions Industrielles   (repeatable)
//         block_supplier_id = 019f55f1-214a-...          (repeatable)
//         fx.USD.EUR        = 0.92    (operator-FROZEN rate, never a live rate)
//   - `.json` { currency, hard_block_amount, role_limits,
//               blocked_supplier_names?, blocked_supplier_ids?, fx_rates? }
// Both must be an EXPLICITLY trusted operator source. Never parse invoice text.

import { digest } from './canonical.js';
import type { TrustedPolicy } from './types.js';

const DECIMAL = /^\d+(\.\d+)?$/;

function requireAmount(field: string, value: unknown): string {
  const s = String(value).trim();
  if (!DECIMAL.test(s)) throw new Error(`Trusted policy: ${field} must be a non-negative decimal amount, got "${s}".`);
  return s;
}

/** An FX rate must be a strictly-positive decimal (0 and negatives are rejected). */
function requireRate(field: string, value: unknown): string {
  const s = String(value).trim();
  if (!DECIMAL.test(s) || Number.parseFloat(s) <= 0) {
    throw new Error(`Trusted policy: ${field} must be a positive decimal rate, got "${s}".`);
  }
  return s;
}

/** Normalize a supplier name for robust structured-field matching: strip accents,
 * lowercase, collapse whitespace. Names are compared normalized; ids are exact. */
export function normalizeSupplierName(name: string): string {
  return name
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, ' ');
}

interface RawDirectives {
  currency: string;
  hardBlock: unknown;
  roleLimits: Record<string, unknown>;
  blockedNames: string[];
  blockedIds: string[];
  fxRates: Record<string, Record<string, string>>;
}

function finalize(raw: RawDirectives): TrustedPolicy {
  const cur = raw.currency.trim().toUpperCase();
  if (!cur) throw new Error('Trusted policy: a currency is required.');
  const role_limits: Record<string, string> = {};
  for (const [role, v] of Object.entries(raw.roleLimits)) {
    role_limits[role.trim()] = requireAmount(`role_limits.${role}`, v);
  }
  const tp: TrustedPolicy = {
    source: 'trusted_file',
    currency: cur,
    hard_block_amount: requireAmount('hard_block_amount', raw.hardBlock),
    role_limits,
  };
  // Omit the extension fields when empty so a bare policy's digest is unchanged.
  const names = [...new Set(raw.blockedNames.filter(Boolean))];
  const ids = [...new Set(raw.blockedIds.filter(Boolean))];
  if (names.length) tp.blocked_supplier_names = names;
  if (ids.length) tp.blocked_supplier_ids = ids;
  if (Object.keys(raw.fxRates).length) tp.fx_rates = raw.fxRates;
  return tp;
}

/** Parse the deterministic `key = value` text format. */
export function parseTrustedPolicyText(text: string): TrustedPolicy {
  const raw: RawDirectives = {
    currency: '',
    hardBlock: undefined,
    roleLimits: {},
    blockedNames: [],
    blockedIds: [],
    fxRates: {},
  };
  let sawHardBlock = false;

  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;
    const eq = line.indexOf('=');
    if (eq < 0) throw new Error(`Trusted policy: cannot parse line "${line}" (expected key = value).`);
    const key = line.slice(0, eq).trim().toLowerCase();
    const value = line.slice(eq + 1).trim();
    if (key === 'currency') raw.currency = value;
    else if (key === 'hard_block' || key === 'hard_block_amount') {
      raw.hardBlock = value;
      sawHardBlock = true;
    } else if (key.startsWith('role.')) raw.roleLimits[key.slice('role.'.length)] = value;
    else if (key === 'block_supplier') raw.blockedNames.push(normalizeSupplierName(value));
    else if (key === 'block_supplier_id') raw.blockedIds.push(value);
    else if (key.startsWith('fx.')) {
      // fx.<FROM>.<TO> = <rate>  — currencies uppercased; rate validated positive.
      const parts = key.slice('fx.'.length).split('.');
      if (parts.length !== 2 || !parts[0] || !parts[1]) {
        throw new Error(`Trusted policy: fx rate key must be "fx.<FROM>.<TO>", got "${key}".`);
      }
      const from = parts[0].toUpperCase();
      const to = parts[1].toUpperCase();
      (raw.fxRates[from] ??= {})[to] = requireRate(`fx.${from}.${to}`, value);
    } else throw new Error(`Trusted policy: unknown key "${key}".`);
  }
  if (!sawHardBlock) throw new Error('Trusted policy: hard_block is required.');
  return finalize(raw);
}

/** Parse the JSON object form. */
export function parseTrustedPolicyJson(obj: unknown): TrustedPolicy {
  if (!obj || typeof obj !== 'object') throw new Error('Trusted policy: expected a JSON object.');
  const o = obj as Record<string, unknown>;
  if (typeof o.currency !== 'string') throw new Error('Trusted policy: a currency string is required.');
  if (o.hard_block_amount === undefined) throw new Error('Trusted policy: hard_block_amount is required.');
  const roles = (o.role_limits && typeof o.role_limits === 'object' ? o.role_limits : {}) as Record<string, unknown>;

  const blockedNames = Array.isArray(o.blocked_supplier_names)
    ? o.blocked_supplier_names.map((n) => normalizeSupplierName(String(n)))
    : [];
  const blockedIds = Array.isArray(o.blocked_supplier_ids) ? o.blocked_supplier_ids.map((i) => String(i).trim()) : [];

  const fxRates: Record<string, Record<string, string>> = {};
  if (o.fx_rates && typeof o.fx_rates === 'object') {
    for (const [from, tos] of Object.entries(o.fx_rates as Record<string, unknown>)) {
      if (!tos || typeof tos !== 'object') continue;
      for (const [to, rate] of Object.entries(tos as Record<string, unknown>)) {
        (fxRates[from.toUpperCase()] ??= {})[to.toUpperCase()] = requireRate(`fx_rates.${from}.${to}`, rate);
      }
    }
  }

  return finalize({
    currency: o.currency,
    hardBlock: o.hard_block_amount,
    roleLimits: roles,
    blockedNames,
    blockedIds,
    fxRates,
  });
}

// --- evaluation helpers (pure) ----------------------------------------------

/** Is this supplier on the operator block list? Matches the STRUCTURED Qonto
 * fields only (normalized name or exact id) — never document text. */
export function supplierBlock(
  tp: TrustedPolicy,
  supplierName: string,
  supplierId: string,
): { blocked: boolean; by?: 'name' | 'id' } {
  const ids = tp.blocked_supplier_ids ?? [];
  if (supplierId && ids.includes(supplierId)) return { blocked: true, by: 'id' };
  const names = tp.blocked_supplier_names ?? [];
  if (names.includes(normalizeSupplierName(supplierName))) return { blocked: true, by: 'name' };
  return { blocked: false };
}

/** True when the policy declares any supplier block. */
export function hasSupplierBlockList(tp: TrustedPolicy): boolean {
  return Boolean((tp.blocked_supplier_ids?.length ?? 0) + (tp.blocked_supplier_names?.length ?? 0));
}

/** The operator-frozen rate to convert `from` -> `to`, or null if none declared. */
export function fxRate(tp: TrustedPolicy, from: string, to: string): string | null {
  return tp.fx_rates?.[from]?.[to] ?? null;
}

/** Stable digest binding the exact policy used, for the hashed PR body / audit.
 * Extension segments are appended only when present, so a bare policy's digest is
 * identical to the pre-extension version. */
export function trustedPolicyDigest(tp: TrustedPolicy): string {
  const roles = Object.keys(tp.role_limits)
    .sort()
    .map((k) => `${k}:${tp.role_limits[k]}`)
    .join(',');
  const parts = ['trusted_policy', tp.source, tp.currency, tp.hard_block_amount, roles];
  if (tp.blocked_supplier_names?.length) parts.push('blocked_names:' + [...tp.blocked_supplier_names].sort().join(','));
  if (tp.blocked_supplier_ids?.length) parts.push('blocked_ids:' + [...tp.blocked_supplier_ids].sort().join(','));
  if (tp.fx_rates && Object.keys(tp.fx_rates).length) {
    const fx = Object.keys(tp.fx_rates)
      .sort()
      .map((from) =>
        Object.keys(tp.fx_rates![from])
          .sort()
          .map((to) => `${from}>${to}:${tp.fx_rates![from][to]}`)
          .join(','),
      )
      .join(',');
    parts.push('fx:' + fx);
  }
  return digest(...parts);
}
