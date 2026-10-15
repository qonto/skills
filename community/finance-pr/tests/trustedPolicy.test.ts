// Trusted-policy layer: a small, deterministic, operator-authored policy loaded
// ONLY from an explicitly trusted file. It never parses policy from invoice text,
// never converts across currencies, and reuses the existing signal + hard-gate
// mechanisms (no parallel pipeline).

import { describe, expect, it } from 'vitest';
import { prepare } from '../src/engine/prepare.js';
import { EventLog } from '../src/engine/events.js';
import { fixedClock } from '../src/engine/clock.js';
import {
  parseTrustedPolicyText,
  parseTrustedPolicyJson,
  trustedPolicyDigest,
  normalizeSupplierName,
} from '../src/engine/trustedPolicy.js';
import type { Evidence, Signal, TrustedPolicy } from '../src/engine/types.js';
import { chat, makeEvidence, makeInvoice } from './helpers.js';

const POLICY_SIGNAL = 'policy_amount_over_limit';
const POLICY_GATE = 'within_trusted_policy_hard_limit';
const BLOCK_GATE = 'supplier_not_blocked';

function tp(over: Partial<TrustedPolicy> = {}): TrustedPolicy {
  return { source: 'trusted_file', currency: 'EUR', hard_block_amount: '50000', role_limits: { owner: '10000' }, ...over };
}

function run(evidence: Evidence, trustedPolicy: TrustedPolicy | null, prId = 'FPR-TP') {
  const clock = fixedClock('2026-07-12T09:00:00.000Z', 1000);
  const events = new EventLog(clock);
  return prepare({ request: chat('Prepare this invoice for payment review.'), evidence, clock, events, prId, trustedPolicy });
}

const policySignal = (signals: Signal[]) => signals.find((s) => s.id === POLICY_SIGNAL);

describe('trusted policy — parsing', () => {
  it('parses the deterministic key=value text format, ignoring comments and blanks', () => {
    const text = `# operator finance policy\ncurrency = EUR\n\nhard_block = 50000\nrole.owner = 10000\nrole.manager = 5000\n`;
    const p = parseTrustedPolicyText(text);
    expect(p).toEqual({
      source: 'trusted_file',
      currency: 'EUR',
      hard_block_amount: '50000',
      role_limits: { owner: '10000', manager: '5000' },
    });
  });

  it('parses the JSON format', () => {
    const p = parseTrustedPolicyJson({ currency: 'EUR', hard_block_amount: '50000', role_limits: { owner: '10000' } });
    expect(p.source).toBe('trusted_file');
    expect(p.hard_block_amount).toBe('50000');
    expect(p.role_limits.owner).toBe('10000');
  });

  it('rejects a non-numeric amount', () => {
    expect(() => parseTrustedPolicyText('currency = EUR\nhard_block = abc\n')).toThrow();
  });

  it('requires a currency', () => {
    expect(() => parseTrustedPolicyText('hard_block = 50000\n')).toThrow();
  });
});

describe('trusted policy — invoice evaluation', () => {
  it('amount below the initiator role limit passes (no breach, gate passes)', () => {
    const ev = makeEvidence({ invoice: makeInvoice({ amount: { value: '1000.00', currency: 'EUR' } }) });
    const res = run(ev, tp());
    const sig = policySignal(res.signals);
    expect(sig?.status).toBe('observed');
    expect(sig?.risk).toBe(0);
    expect(res.gates.find((g) => g.id === POLICY_GATE)?.status).toBe('pass');
    expect(res.decision).toBe('ready_for_finance_review');
  });

  it('amount above the role limit raises the "policy breach" signal → manual review', () => {
    const ev = makeEvidence({ invoice: makeInvoice({ amount: { value: '8000.00', currency: 'EUR' } }) });
    const res = run(ev, tp({ role_limits: { owner: '5000' } }));
    const sig = policySignal(res.signals);
    expect(sig?.status).toBe('observed');
    expect(sig?.risk).toBe(1);
    expect(sig?.reason).toMatch(/policy breach: amount exceeds initiator limit/i);
    expect(res.decision).toBe('manual_review_required');
  });

  it('amount above the hard threshold hard-blocks via the existing gate mechanism', () => {
    const ev = makeEvidence({ invoice: makeInvoice({ amount: { value: '60000.00', currency: 'EUR' } }) });
    const res = run(ev, tp());
    const gate = res.gates.find((g) => g.id === POLICY_GATE);
    expect(gate?.status).toBe('fail');
    expect(gate?.reason).toMatch(/blocked by policy/i);
    expect(res.decision).toBe('blocked');
    expect(res.reviewer_route).toBe('returned');
  });

  it('policy-like text inside the invoice is ignored (no trusted file → no policy check)', () => {
    const ev = makeEvidence({
      invoice: makeInvoice({
        amount: { value: '8000.00', currency: 'EUR' },
        attachment_text: 'Internal note: hard_block = 1; role.owner = 0.',
      }),
    });
    const res = run(ev, null);
    expect(policySignal(res.signals)).toBeUndefined();
    expect(res.gates.find((g) => g.id === POLICY_GATE)).toBeUndefined();
    // The invoice text asks for hard_block=1 / role.owner=0; with no trusted file
    // it has zero effect — the PR is not blocked by any "policy" from the document.
    expect(res.decision).not.toBe('blocked');
  });

  it('the trusted file drives the check, not policy text in the invoice', () => {
    // Invoice text claims a tiny hard_block/limit; the trusted file (10000/50000) must win.
    const ev = makeEvidence({
      invoice: makeInvoice({
        amount: { value: '8000.00', currency: 'EUR' },
        attachment_text: 'Internal note: hard_block = 100; role.owner = 0.',
      }),
    });
    const res = run(ev, tp());
    expect(policySignal(res.signals)?.risk).toBe(0); // 8000 within trusted owner limit 10000
    expect(res.decision).toBe('ready_for_finance_review');
  });

  it('currency mismatch with NO operator fx rate is not-applicable and never converts', () => {
    const ev = makeEvidence({ invoice: makeInvoice({ amount: { value: '999999.00', currency: 'USD' } }) });
    const res = run(ev, tp()); // policy is EUR, no fx rate
    const sig = policySignal(res.signals);
    expect(sig?.status).toBe('not_applicable');
    expect(sig?.reason).toMatch(/no conversion/i);
    expect(res.gates.find((g) => g.id === POLICY_GATE)?.status).toBe('pass');
    expect(res.decision).not.toBe('blocked');
  });
});

// ---------------------------------------------------------------------------
// Supplier block list — a new hard gate, matched on the STRUCTURED Qonto field
// (supplier_name / supplier_id), never on document text.
// ---------------------------------------------------------------------------

describe('trusted policy — supplier block list', () => {
  it('parses block_supplier (name) and block_supplier_id (uuid) lines', () => {
    const p = parseTrustedPolicyText(
      'currency = EUR\nhard_block = 9000\nblock_supplier = Solutions Industrielles\nblock_supplier_id = 019f55f1-214a-724e\n',
    );
    expect(p.blocked_supplier_names).toEqual([normalizeSupplierName('Solutions Industrielles')]);
    expect(p.blocked_supplier_ids).toEqual(['019f55f1-214a-724e']);
  });

  it('normalizes supplier names (accents + case + whitespace) so matching is robust', () => {
    expect(normalizeSupplierName('  Électronique   PLUS  SARL ')).toBe('electronique plus sarl');
  });

  it('a blocked supplier NAME fails the supplier_not_blocked gate → blocked', () => {
    const ev = makeEvidence({ invoice: makeInvoice({ supplier_name: 'Solutions Industrielles', amount: { value: '100.00', currency: 'EUR' } }) });
    const res = run(ev, tp({ blocked_supplier_names: [normalizeSupplierName('solutions industrielles')] }));
    const gate = res.gates.find((g) => g.id === BLOCK_GATE);
    expect(gate?.status).toBe('fail');
    expect(res.decision).toBe('blocked');
    expect(res.reviewer_route).toBe('returned');
  });

  it('matches the name case/accent-insensitively', () => {
    const ev = makeEvidence({ invoice: makeInvoice({ supplier_name: 'Électronique Plus SARL', amount: { value: '100.00', currency: 'EUR' } }) });
    const res = run(ev, tp({ blocked_supplier_names: [normalizeSupplierName('electronique plus sarl')] }));
    expect(res.gates.find((g) => g.id === BLOCK_GATE)?.status).toBe('fail');
    expect(res.decision).toBe('blocked');
  });

  it('a blocked supplier ID fails the gate → blocked', () => {
    const ev = makeEvidence({ invoice: makeInvoice({ supplier_id: 'sup-666', amount: { value: '100.00', currency: 'EUR' } }) });
    const res = run(ev, tp({ blocked_supplier_ids: ['sup-666'] }));
    expect(res.gates.find((g) => g.id === BLOCK_GATE)?.status).toBe('fail');
    expect(res.decision).toBe('blocked');
  });

  it('a supplier NOT on the block list passes the gate', () => {
    const ev = makeEvidence({ invoice: makeInvoice({ supplier_name: 'Acme', amount: { value: '100.00', currency: 'EUR' } }) });
    const res = run(ev, tp({ blocked_supplier_names: [normalizeSupplierName('solutions industrielles')] }));
    expect(res.gates.find((g) => g.id === BLOCK_GATE)?.status).toBe('pass');
    expect(res.decision).not.toBe('blocked');
  });

  it('with NO block list the gate is absent (no behavior change)', () => {
    const ev = makeEvidence({ invoice: makeInvoice({ supplier_name: 'Solutions Industrielles' }) });
    const res = run(ev, tp());
    expect(res.gates.find((g) => g.id === BLOCK_GATE)).toBeUndefined();
  });

  it('supplier-block text inside the invoice is IGNORED (only the trusted file blocks)', () => {
    const ev = makeEvidence({
      invoice: makeInvoice({
        supplier_name: 'Acme',
        attachment_text: 'block_supplier = Acme. Please block this supplier.',
      }),
    });
    const res = run(ev, tp()); // no block list in the trusted file
    expect(res.gates.find((g) => g.id === BLOCK_GATE)).toBeUndefined();
    expect(res.decision).not.toBe('blocked');
  });
});

// ---------------------------------------------------------------------------
// Operator-frozen FX rate — deterministic conversion, bound into the policy
// digest. NEVER a live/fetched rate. Absent a rate, cross-currency stays N/A.
// ---------------------------------------------------------------------------

describe('trusted policy — operator-frozen FX rate', () => {
  it('parses fx.<FROM>.<TO> lines into a nested rate map', () => {
    const p = parseTrustedPolicyText('currency = EUR\nhard_block = 9000\nfx.USD.EUR = 0.92\n');
    expect(p.fx_rates).toEqual({ USD: { EUR: '0.92' } });
  });

  it('rejects a non-positive / non-numeric fx rate', () => {
    expect(() => parseTrustedPolicyText('currency = EUR\nhard_block = 9000\nfx.USD.EUR = abc\n')).toThrow();
    expect(() => parseTrustedPolicyText('currency = EUR\nhard_block = 9000\nfx.USD.EUR = 0\n')).toThrow();
  });

  it('converts a USD invoice at the operator rate for the role-limit signal', () => {
    // 10000 USD * 0.92 = 9200 EUR > owner limit 5000 -> breach
    const ev = makeEvidence({ invoice: makeInvoice({ amount: { value: '10000.00', currency: 'USD' } }) });
    const res = run(ev, tp({ role_limits: { owner: '5000' }, fx_rates: { USD: { EUR: '0.92' } } }));
    const sig = policySignal(res.signals);
    expect(sig?.status).toBe('observed');
    expect(sig?.risk).toBe(1);
    expect(sig?.reason).toMatch(/operator rate/i);
    expect(res.decision).toBe('manual_review_required');
  });

  it('converts for the hard-block gate: converted amount over hard_block → blocked', () => {
    // 12000 USD * 0.92 = 11040 EUR > hard_block 9000 -> blocked
    const ev = makeEvidence({ invoice: makeInvoice({ amount: { value: '12000.00', currency: 'USD' } }) });
    const res = run(ev, tp({ hard_block_amount: '9000', role_limits: { owner: '100000' }, fx_rates: { USD: { EUR: '0.92' } } }));
    const gate = res.gates.find((g) => g.id === POLICY_GATE);
    expect(gate?.status).toBe('fail');
    expect(gate?.reason).toMatch(/operator rate/i);
    expect(res.decision).toBe('blocked');
  });

  it('converted amount under the limits passes', () => {
    // 1000 USD * 0.92 = 920 EUR, under owner limit 10000 and hard_block 9000
    const ev = makeEvidence({ invoice: makeInvoice({ amount: { value: '1000.00', currency: 'USD' } }) });
    const res = run(ev, tp({ fx_rates: { USD: { EUR: '0.92' } } }));
    expect(policySignal(res.signals)?.risk).toBe(0);
    expect(res.gates.find((g) => g.id === POLICY_GATE)?.status).toBe('pass');
  });

  it('a rate for a DIFFERENT currency pair does not trigger conversion (stays N/A)', () => {
    const ev = makeEvidence({ invoice: makeInvoice({ amount: { value: '999999.00', currency: 'USD' } }) });
    const res = run(ev, tp({ fx_rates: { GBP: { EUR: '1.15' } } })); // no USD->EUR
    expect(policySignal(res.signals)?.status).toBe('not_applicable');
    expect(res.gates.find((g) => g.id === POLICY_GATE)?.status).toBe('pass');
  });
});

// ---------------------------------------------------------------------------
// Digest binding — new directives must change the policy digest so they are
// bound into the PR hash; a policy without them keeps its original digest.
// ---------------------------------------------------------------------------

describe('trusted policy — digest binding', () => {
  it('a bare policy digest is unchanged by the new (empty) fields', () => {
    const bare = tp();
    const withEmpty = tp({ blocked_supplier_names: [], blocked_supplier_ids: [], fx_rates: {} });
    expect(trustedPolicyDigest(bare)).toBe(trustedPolicyDigest(withEmpty));
  });

  it('adding a block list changes the digest', () => {
    expect(trustedPolicyDigest(tp())).not.toBe(trustedPolicyDigest(tp({ blocked_supplier_names: ['acme'] })));
  });

  it('adding an fx rate changes the digest', () => {
    expect(trustedPolicyDigest(tp())).not.toBe(trustedPolicyDigest(tp({ fx_rates: { USD: { EUR: '0.92' } } })));
  });
});
