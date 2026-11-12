import { describe, expect, it } from 'vitest';
import { ibanDigest, maskEmail, maskIban, maskId, normalizeIban, stripSensitive } from '../src/engine/redact.js';

describe('redaction', () => {
  it('masks IBAN to the last 4', () => {
    expect(maskIban('FR76 3000 4000 0500 0000 0000 123')).toBe('•••• 0123');
    expect(maskIban(null)).toBeNull();
  });

  it('normalizes IBAN (no spaces, upper)', () => {
    expect(normalizeIban('de89 3704 0044 0532 0130 00')).toBe('DE89370400440532013000');
  });

  it('IBAN digest is stable and hides the value', () => {
    const d = ibanDigest('FR7630004000050000000000123');
    expect(d).toHaveLength(64);
    expect(d).not.toContain('123');
    expect(ibanDigest('FR76 3000 4000 0500 0000 0000 123')).toBe(d); // whitespace-insensitive
  });

  it('masks object ids and emails', () => {
    expect(maskId('0a1b2c3d-4e5f-6789-abcd-ef0123456789')).toBe('0a1b2c3d…');
    expect(maskEmail('jane.doe@example.com')).toBe('j•••@example.com');
  });

  it('strips URLs/tokens from free text', () => {
    expect(stripSensitive('see https://s3.example.com/abc?token=secret now')).toBe('see [url-redacted] now');
  });
});
