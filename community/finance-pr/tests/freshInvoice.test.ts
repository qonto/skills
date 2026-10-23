import { describe, expect, it } from 'vitest';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { loadFreshInvoice } from '../src/node/freshInvoice.js';

describe('Act fresh input', () => {
  it('rejects absent fresh input instead of using cached observation', () => {
    expect(() => loadFreshInvoice(undefined)).toThrow('act requires --fresh <rawInvoice.json> from a new Qonto read.');
  });

  it('maps the explicitly supplied fresh Qonto invoice', () => {
    const dir = mkdtempSync(join(tmpdir(), 'finance-pr-fresh-'));
    try {
      const path = join(dir, 'invoice.json');
      writeFileSync(path, JSON.stringify({ supplier_invoice: { id: 'inv-fresh', total_amount: { value: '1200.00', currency: 'EUR' }, matched_transactions: [{ id: 'payment-1' }] } }));
      const fresh = loadFreshInvoice(path);
      expect(fresh.id).toBe('inv-fresh');
      expect(fresh.matched_transaction_ids).toEqual(['payment-1']);
    } finally {
      rmSync(dir, { recursive: true });
    }
  });
});
