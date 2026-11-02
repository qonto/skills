import { readFileSync } from 'node:fs';
import { invoiceFromQonto } from './qontoAdapter.js';
import type { SupplierInvoiceEvidence } from '../engine/types.js';

/** Load only an explicit fresh read; never substitute cached evidence. */
export function loadFreshInvoice(path: string | undefined): SupplierInvoiceEvidence {
  if (!path) throw new Error('act requires --fresh <rawInvoice.json> from a new Qonto read.');
  return invoiceFromQonto(JSON.parse(readFileSync(path, 'utf8')));
}
