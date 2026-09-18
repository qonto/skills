# Customer verification reference

Veto verifies distinct facts through distinct official sources. A positive
result in one layer does not prove another.

## Verification layers

1. **Legal identity** — the French Annuaire des Entreprises can establish the
   registered name, active status, SIREN/SIRET and registered address. It is not
   the e-invoicing routing directory.
2. **VAT registration** — VIES confirms that a submitted EU VAT number was
   valid at the time of consultation. Returned name/address data varies by
   Member State.
3. **E-invoicing reachability** — a recipient's active routing address belongs
   to the applicable national or network directory. Never infer reachability
   from a checksum, company-registry result or VIES response.

## French company registry

`scripts/registry_fr.py` queries the official Annuaire des Entreprises using a
company name and optional postcode. It keeps active records and returns a match
only when the result is unambiguous.

- One active match: compare the registered identity with the Qonto record,
  validate the SIREN/SIRET locally, then show the proposed correction.
- Multiple active matches: `REVIEW`; never select the first fuzzy result.
- No active match: `NO_MATCH`; request corrected search data.

Registry fields are sourced data, not authorization to update Qonto. Every
client modification still requires an explicit summary and confirmation.

## EU VAT verification

`scripts/vies_eu.py` uses the European Commission VIES SOAP service. A valid
response is point-in-time VAT evidence, not a company search result or a
certificate of complete tax compliance.

- Qualified mode uses the seller's EU VAT number and returns a
  requester-bound consultation reference.
- Basic mode is available when the seller has no EU VAT number. It validates
  the customer number and may return identity data, but has no consultation
  reference. Report that evidence limitation explicitly.

Preserve:

- country and submitted VAT number;
- request date;
- official name and address when disclosed;
- consultation reference;
- local name-comparison result.

Veto distinguishes:

- `VALID` — retain the evidence, then continue to transaction review;
- `INVALID` — stop before invoice creation and request corrected data;
- `MISMATCH` — the number is valid but the locally compared name differs, so
  require human review;
- `NOT_PROCESSED` — no claimed name was supplied or the Member State did not
  disclose identity data; do not report a mismatch;
- `UNAVAILABLE` — timeout, rate limit, global service failure or Member-State
  outage; never report the VAT number as invalid.

Greece uses `EL` in VIES. Northern Ireland uses `XI` for the applicable scope.
Great Britain (`GB`) is not covered by VIES.

Local name comparison removes only common legal forms assigned to the returned
country. The compact country map covers every VIES territory and follows GLEIF's
ISO 20275 terminology. Unknown forms remain a mismatch and require review; add
a form only with source evidence and a regression test.

## Boundaries

A registry or VIES result does not prove:

- solvency or absence of fraud;
- authority of a contact to bind the company;
- transport of goods;
- place of supply;
- entitlement to exemption or reverse charge;
- e-invoicing network reachability.

The invoice VAT treatment remains a separate transaction-level decision.
