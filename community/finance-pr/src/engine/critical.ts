// The "critical state" is the set of fields that must never change silently
// between Prepare and Act: amount, currency, IBAN, supplier, status. We bind it
// as a salted digest (kept inside the hashed body) plus a masked display copy.

import { digest } from './canonical.js';
import { ibanDigest, maskIban, normalizeIban } from './redact.js';
import type { FinancePrBody, SupplierInvoiceEvidence } from './types.js';

export function criticalStateDigest(inv: SupplierInvoiceEvidence): string {
  return digest(
    'critical-v1',
    inv.amount.value,
    inv.amount.currency,
    ibanDigest(inv.iban),
    inv.supplier_name,
    inv.supplier_id,
    inv.status,
  );
}

export function criticalStateDisplay(inv: SupplierInvoiceEvidence): FinancePrBody['critical_state_display'] {
  return {
    amount: inv.amount,
    iban_masked: maskIban(inv.iban),
    supplier_name: inv.supplier_name,
    status: inv.status,
  };
}

/** Field-level comparison so Act can report exactly which critical field drifted. */
export function criticalFieldDiffs(body: FinancePrBody, fresh: SupplierInvoiceEvidence): string[] {
  const diffs: string[] = [];
  const d = body.critical_state_display;
  if (fresh.amount.value !== d.amount.value) diffs.push(`amount ${d.amount.value} → ${fresh.amount.value}`);
  if (fresh.amount.currency !== d.amount.currency) diffs.push(`currency ${d.amount.currency} → ${fresh.amount.currency}`);
  if (normalizeIban(fresh.iban) !== undefined && maskIban(fresh.iban) !== d.iban_masked) {
    diffs.push(`IBAN ${d.iban_masked ?? 'none'} → ${maskIban(fresh.iban) ?? 'none'}`);
  }
  if (fresh.supplier_name !== d.supplier_name) diffs.push(`supplier ${d.supplier_name} → ${fresh.supplier_name}`);
  if (fresh.status !== d.status) diffs.push(`status ${d.status} → ${fresh.status}`);
  return diffs;
}
