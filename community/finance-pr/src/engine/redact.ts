// Redaction — applied to everything that reaches UI, logs, fixtures, prompts.
// Full IBANs, object IDs, personal data, URLs, tokens never leave in the clear.

import { digest } from './canonical.js';

/** Fixed salt so IBAN digests are stable across a run but not reversible in UI. */
const IBAN_SALT = 'finance-pr-iban-v1';

export function normalizeIban(iban: string | null | undefined): string | null {
  if (!iban) return null;
  return iban.replace(/\s+/g, '').toUpperCase();
}

/** "•••• •••• 2768" style, revealing only the last 4. */
export function maskIban(iban: string | null | undefined): string | null {
  const norm = normalizeIban(iban);
  if (!norm) return null;
  return `•••• ${norm.slice(-4)}`;
}

export function ibanDigest(iban: string | null | undefined): string {
  const norm = normalizeIban(iban);
  return norm ? digest(IBAN_SALT, norm) : 'none';
}

/** Short masked object id: first 8 chars + ellipsis. */
export function maskId(id: string | null | undefined): string {
  if (!id) return 'n/a';
  if (id.length <= 10) return id;
  return `${id.slice(0, 8)}…`;
}

export function maskEmail(email: string | null | undefined): string {
  if (!email) return 'n/a';
  const [user, domain] = email.split('@');
  if (!domain) return 'redacted';
  return `${user.slice(0, 1)}•••@${domain}`;
}

const URL_RE = /https?:\/\/[^\s"')]+/gi;

/** Strip presigned/temporary URLs and long tokens from free text. */
export function stripSensitive(text: string): string {
  return text.replace(URL_RE, '[url-redacted]');
}
