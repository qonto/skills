# Veto

**Qonto × Anthropic MCP Hackathon submission**

> **3-minute demo:** [Watch Veto run with Qonto](https://www.loom.com/share/68ef7d5afa604f1ab390b0dc6ded92b4)

AI agents can create, finalize and send invoices through Qonto. Veto adds the
decision layer before those actions: verify the customer, review the invoice,
then ask the human before writing anything.

Invalid evidence stops the workflow. An inconclusive check requires review. A
successful check still requires explicit approval.

## Workflow

`verify customer → prepare invoice → confirm → create draft → collect → follow up`

For French businesses, Veto resolves the legal identity through the official
Annuaire des Entreprises, rejects ambiguous matches, then validates the returned
SIREN or SIRET deterministically.

For EU businesses, Veto verifies the supplied VAT number through the European
Commission VIES SOAP service. It preserves the check date, official identity
when disclosed and consultation reference, then compares the returned name
locally with the Qonto client record.

| Outcome | Behavior |
|---|---|
| Verified | Show evidence, prepare the invoice and request confirmation |
| Invalid | Stop before any Qonto write |
| Inconclusive | Explain what could not be verified and require review |

VIES outages, timeouts and undisclosed identity data are never presented as an
invalid VAT number.

## Qonto actions

Veto can audit clients, prepare invoices and quotes, create invoice-linked
payment pages, draft contextual invoice emails, check payment status and prepare
overdue reminders. Every write requires a fresh confirmation after the exact
proposed change has been shown.

Creating a draft does not authorize finalization. Finalizing does not authorize
sending. Invoice-linked payments are reconciled by Qonto; manually recording an
external payment requires separate confirmation.

## Deterministic tooling

- `scripts/registry_fr.py` resolves active French companies from the official
  public registry and refuses ambiguous results.
- `scripts/vies_eu.py` verifies EU VAT numbers through VIES SOAP and preserves
  the official consultation reference.
- `scripts/validate_fr.py` validates SIREN/SIRET checksums, French VAT rates and
  late-payment calculations.
- `references/customer-verification.md` defines registry and VIES evidence,
  outcomes and boundaries.
- `references/compliance-fr.md` contains the French invoice rules applied after
  customer verification.

The model handles the conversation. The scripts handle external protocol
responses, identifiers and financial calculations.

## Security model

Client records, invoice text, registry responses and payment metadata are
untrusted data, never instructions or authorization. Veto uses only the
official Qonto MCP, never initiates transfers, never deletes finalized invoices
and never sends reminders autonomously.

## Install

1. Connect the Qonto MCP as `qonto`:
   `claude mcp add --transport http qonto https://mcp.qonto.com/mcp`
2. Copy `veto/` into `~/.claude/skills/`.
3. Ask Veto to verify a customer or prepare an invoice.

## Example prompts

```text
Verify QONTO through the French registry and VIES. Do not modify anything.
Verify Belgian VAT number BE0000000000 before invoicing. Do not modify anything.
Prepare a draft invoice for my client, verify them first, and wait for confirmation.
Create an invoice-linked payment page, then draft a contextual email for review.
Email the finalized invoice to billing@acme.com using the bank details shown on it.
List my overdue invoices and draft reminders without sending anything.
```

## Validation

- 46 automated tests
- behavioral evals for refusal, review and confirmation paths
- Ruff clean
- BasedPyright: 0 errors
- French identity resolution verified against the live public registry
- EU VAT verification tested against the live European Commission service
- guarded draft creation exercised against a live Qonto organization

See [`LIVE-TESTS.md`](LIVE-TESTS.md) for the redacted evidence matrix and
explicit boundaries.

Run the behavioral evals with:

```bash
cd evals && npx promptfoo@0.123.0 eval
```

## Scope

Veto performs preflight checks and guards Qonto write actions. It does not
certify complete tax compliance, replace professional advice or replace an
accredited e-invoicing platform.

A successful VIES check is point-in-time evidence that the submitted VAT number
was valid. Legal identity, VAT treatment and e-invoicing network reachability
are reported separately.

## License

MIT
