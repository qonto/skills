// Canonical JSON + SHA-256 + short fingerprint.
// Canonicalization = deterministic key ordering so the same logical body always
// hashes identically across Node, browser, and tests.

import { sha256 } from 'js-sha256';

/** Deterministic JSON: object keys sorted recursively, arrays preserved. */
export function canonicalize(value: unknown): string {
  return JSON.stringify(sortValue(value));
}

function sortValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(sortValue);
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {};
    for (const key of Object.keys(value as Record<string, unknown>).sort()) {
      out[key] = sortValue((value as Record<string, unknown>)[key]);
    }
    return out;
  }
  return value;
}

export function hashBody(value: unknown): string {
  return sha256(canonicalize(value));
}

/** Short, human-verifiable fingerprint from a full hash, e.g. "7C91-A2B4". */
export function fingerprintFromHash(hash: string): string {
  const head = hash.slice(0, 8).toUpperCase();
  return `${head.slice(0, 4)}-${head.slice(4, 8)}`;
}

export function digest(...parts: string[]): string {
  return sha256(parts.join('\0'));
}
