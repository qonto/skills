// Shared test builders (not a test file).
import type { Evidence, SupplierInvoiceEvidence, SupplierHistoryItem, UserRequest } from '../src/engine/types.js';

export const IBAN_A = 'FR7630004000050000000000123';
export const IBAN_B = 'DE89370400440532013000';

export function makeInvoice(p: Partial<SupplierInvoiceEvidence> = {}): SupplierInvoiceEvidence {
  return {
    object_type: 'supplier_invoice',
    id: p.id ?? 'inv-1',
    invoice_number: p.invoice_number ?? 'INV-1',
    supplier_name: p.supplier_name ?? 'Acme',
    supplier_id: p.supplier_id ?? 'sup-1',
    iban: p.iban ?? IBAN_A,
    amount: p.amount ?? { value: '1000.00', currency: 'EUR' },
    status: p.status ?? 'to_review',
    due_date: p.due_date ?? '2026-08-01',
    issue_date: p.issue_date ?? '2026-07-01',
    has_duplicates: p.has_duplicates ?? false,
    matched_transaction_ids: p.matched_transaction_ids ?? [],
    available_actions: p.available_actions ?? { pay: true },
    attachment_text: p.attachment_text ?? 'Standard invoice. Net 30.',
    updated_at: p.updated_at ?? '2026-07-01T00:00:00.000Z',
  };
}

export function hist(value: string, iban: string | null, num = 'H', day = '2026-05-01'): SupplierHistoryItem {
  return { invoice_number: num, amount: { value, currency: 'EUR' }, iban, issue_date: day, status: 'paid' };
}

export function makeEvidence(p: Partial<Evidence> = {}): Evidence {
  const invoice = p.invoice ?? makeInvoice();
  return {
    data_mode: p.data_mode ?? 'synthetic',
    organization: p.organization ?? { id: 'org-123456789', name: 'Test', legal_country: 'FR' },
    membership: p.membership ?? { id: 'mem-123456789', role: 'owner' },
    invoice,
    supplier_history: p.supplier_history ?? [],
    known_supplier_ibans: p.known_supplier_ibans ?? [invoice.iban ?? IBAN_A],
    observed_at: p.observed_at ?? '2026-07-12T08:00:00.000Z',
    unavailable_fields: p.unavailable_fields ?? [],
  };
}

export const chat = (text: string): UserRequest => ({ text, source: 'user_chat', message_id: 'm1' });
export const prepareRequest = chat('Prepare this invoice for payment review.');
