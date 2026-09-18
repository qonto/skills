// Read-only mapping from raw Qonto MCP JSON into typed engine Evidence.
// The Skill fetches the JSON via MCP (read-only) and hands it to the CLI; this
// module NEVER calls Qonto and NEVER mutates anything.

import { normalizeIban } from '../engine/redact.js';
import type { Evidence, SupplierHistoryItem, SupplierInvoiceEvidence } from '../engine/types.js';

/* eslint-disable @typescript-eslint/no-explicit-any */
type Json = any;

export interface QontoBundle {
  organization: Json; // get_organization result
  membership?: Json; // get_authenticated_membership result
  supplier_invoice: Json; // get_supplier_invoice result (or a list element)
  supplier_invoices?: Json; // list_supplier_invoices result (for history)
  observed_at?: string;
}

function unwrap(v: Json, key: string): Json {
  return v && typeof v === 'object' && key in v ? v[key] : v;
}

export function invoiceFromQonto(raw: Json): SupplierInvoiceEvidence {
  const inv = unwrap(raw, 'supplier_invoice');
  const amount = inv.total_amount ?? inv.payable_amount ?? { value: '0', currency: 'EUR' };
  return {
    object_type: 'supplier_invoice',
    id: inv.id,
    invoice_number: inv.invoice_number ?? '(none)',
    supplier_name: inv.supplier_name ?? inv.issuer_name ?? '(unknown)',
    supplier_id: inv.supplier_id ?? '(unknown)',
    iban: normalizeIban(inv.iban ?? null),
    amount: { value: String(amount.value), currency: amount.currency },
    status: inv.status ?? 'to_review',
    due_date: inv.due_date ?? null,
    issue_date: inv.issue_date ?? null,
    has_duplicates: Boolean(inv.has_duplicates),
    matched_transaction_ids: Array.isArray(inv.matched_transactions) ? inv.matched_transactions.map((m: Json) => m.id ?? String(m)) : [],
    available_actions: {
      pay: Boolean(inv.available_actions?.pay),
      reasons: inv.available_actions?.reasons,
    },
    attachment_text: null, // never OCR'd here; treated as unavailable optional evidence
    updated_at: inv.updated_at ?? null,
  };
}

export function evidenceFromQonto(bundle: QontoBundle): Evidence {
  const org = unwrap(bundle.organization, 'organization');
  const mem = bundle.membership ? unwrap(bundle.membership, 'membership') : { id: '(unknown)', role: '(unknown)' };
  const invoice = invoiceFromQonto(bundle.supplier_invoice);

  const list: Json[] = bundle.supplier_invoices ? unwrap(bundle.supplier_invoices, 'supplier_invoices') ?? [] : [];
  const history: SupplierHistoryItem[] = list
    .filter((h) => h.id !== invoice.id && (h.supplier_id === invoice.supplier_id || h.supplier_name === invoice.supplier_name))
    .map((h) => {
      const amt = h.total_amount ?? h.payable_amount ?? { value: '0', currency: 'EUR' };
      return {
        invoice_number: h.invoice_number ?? '(none)',
        amount: { value: String(amt.value), currency: amt.currency },
        iban: normalizeIban(h.iban ?? null),
        issue_date: h.issue_date ?? null,
        status: h.status ?? 'to_review',
      };
    });

  const knownIbans = Array.from(new Set(history.map((h) => h.iban).filter((x): x is string => Boolean(x))));

  return {
    data_mode: 'qonto_sandbox',
    organization: { id: org.id, name: org.legal_name ?? org.name ?? '(org)', legal_country: org.legal_country ?? 'FR' },
    membership: { id: mem.id, role: mem.role ?? '(unknown)' },
    invoice,
    supplier_history: history,
    known_supplier_ibans: knownIbans,
    observed_at: bundle.observed_at ?? new Date().toISOString(),
    unavailable_fields: [
      'attachment_text (document not OCR-extracted in this MVP)',
      ...(knownIbans.length === 0 ? ['known supplier IBAN history (none returned by sandbox)'] : []),
    ],
  };
}
