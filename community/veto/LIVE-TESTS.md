# Live Qonto verification

Executed on July 10, 2026 against the author's own live Qonto organization.
Names, identifiers, URLs, and payer details are intentionally omitted.

| Scenario | Observable result | Verdict |
|---|---|---|
| French B2B client missing SIREN | Invoice creation blocked; exact missing field and routing consequence explained | PASS |
| French invoice requested with 15% VAT | Illegal rate refused; legal rates and normal consulting rate proposed | PASS |
| Micro-entrepreneur requested 20% VAT | Organization VAT status questioned; invoice corrected to franchise en base | PASS |
| Draft invoice under franchise en base | Qonto's required `S293B` exemption code discovered after a validation error; draft created with art. 293 B wording | PASS |
| French company lookup: QONTO + 75009 | Official registry returned QONTO, SIREN `819489626`, SIRET `81948962600047`, registered address and VAT number | PASS |
| EU VAT verification: Qonto | VIES SOAP returned a valid result, official name/address and a non-empty consultation reference | PASS |
| Invalid EU VAT response | Parsed as INVALID and kept distinct from transport or member-state availability faults | PASS |
| VIES member-state outage | Parsed as UNAVAILABLE; never reported as an invalid VAT number | PASS |
| Hypothetical invoice 20 days overdue | Level-2 French reminder drafted with explicit interest calculation and €40 indemnity; nothing sent | PASS |
| Full client-book readiness audit | French B2B records classified READY/BLOCKED; network reachability reported separately; no writes performed | PASS |

## Deterministic checks

The deterministic scripts were separately verified for:

- valid and invalid Luhn checksums;
- all five supported French VAT rates and an invalid 15% rate;
- Decimal-based late-interest calculation using an explicit contractual rate.
- active and ambiguous French registry matches;
- valid, invalid, unavailable and malformed VIES SOAP responses;
- local identity match, mismatch and undisclosed-name outcomes;
- country-scoped legal-form normalization across every VIES territory;
- EU country handling including `EL` and `XI`, with `GR` and `GB` rejected.

Automated result: **46 tests passed**. Ruff and BasedPyright completed with
zero lint/type errors.

## Not claimed

- The skill does not keep running after the Claude session ends.
- The French registry establishes legal identity and administrative activity;
  it is not the French e-invoicing routing directory.
- A valid VIES result is point-in-time VAT evidence, not proof of the complete
  tax treatment, transport, solvency or absence of fraud.
- The name comparison is performed locally on identity data returned by VIES;
  it is not an official VIES match verdict.
- A finalized invoice should only be demonstrated with a legitimate customer
  and transaction; the hackathon test invoice remained a removable draft.
