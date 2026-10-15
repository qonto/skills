import { describe, expect, it } from 'vitest';
import { sha256 } from 'js-sha256';
import { canonicalize, fingerprintFromHash, hashBody } from '../src/engine/canonical.js';

describe('canonical json + hashing', () => {
  it('sha256 matches a known vector (library sanity)', () => {
    expect(sha256('abc')).toBe('ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');
  });

  it('is independent of key insertion order', () => {
    const a = { b: 1, a: 2, nested: { y: 1, x: 2 } };
    const b = { a: 2, nested: { x: 2, y: 1 }, b: 1 };
    expect(canonicalize(a)).toBe(canonicalize(b));
    expect(hashBody(a)).toBe(hashBody(b));
  });

  it('preserves array order (arrays are significant)', () => {
    expect(canonicalize([1, 2, 3])).not.toBe(canonicalize([3, 2, 1]));
  });

  it('any change to the body changes the hash', () => {
    const base = { amount: '100.00', iban: 'x' };
    expect(hashBody(base)).not.toBe(hashBody({ ...base, amount: '100.01' }));
  });

  it('fingerprint is a grouped 8-hex code', () => {
    const fp = fingerprintFromHash('7c91a2b4deadbeef');
    expect(fp).toBe('7C91-A2B4');
    expect(fp).toMatch(/^[0-9A-F]{4}-[0-9A-F]{4}$/);
  });
});
