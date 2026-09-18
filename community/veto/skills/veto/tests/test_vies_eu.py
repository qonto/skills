import pytest

from scripts.vies_eu import (
    IdentityMatch,
    InvalidVat,
    LEGAL_FORMS_BY_COUNTRY,
    SUPPORTED_COUNTRIES,
    Unavailable,
    ValidVat,
    VatCheckRequest,
    build_soap_request,
    parse_country_code,
    parse_soap_response,
    parse_vat_number,
)

VALID_SOAP = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <checkVatApproxResponse xmlns="urn:ec.europa.eu:taxud:vies:services:checkVat:types">
      <countryCode>BE</countryCode>
      <vatNumber>0671495129</vatNumber>
      <requestDate>2026-07-13</requestDate>
      <valid>true</valid>
      <traderName>EXAMPLE SRL</traderName>
      <traderAddress>RUE DE LA LOI 1 1000 BRUXELLES</traderAddress>
      <requestIdentifier>WAPIAAAATEST1234</requestIdentifier>
    </checkVatApproxResponse>
  </soap:Body>
</soap:Envelope>"""

INVALID_SOAP = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <checkVatApproxResponse xmlns="urn:ec.europa.eu:taxud:vies:services:checkVat:types">
      <countryCode>BE</countryCode>
      <vatNumber>0000000000</vatNumber>
      <requestDate>2026-07-13</requestDate>
      <valid>false</valid>
      <requestIdentifier>WAPIAAAATEST9999</requestIdentifier>
    </checkVatApproxResponse>
  </soap:Body>
</soap:Envelope>"""

FAULT_SOAP = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <soap:Fault>
      <faultcode>soap:Server</faultcode>
      <faultstring>MS_UNAVAILABLE</faultstring>
    </soap:Fault>
  </soap:Body>
</soap:Envelope>"""

BASIC_SOAP = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <checkVatResponse xmlns="urn:ec.europa.eu:taxud:vies:services:checkVat:types">
      <countryCode>FR</countryCode>
      <vatNumber>10819489626</vatNumber>
      <requestDate>2026-07-13</requestDate>
      <valid>true</valid>
      <name>SAS Qonto</name>
      <address>18 RUE DE NAVARIN 75009 PARIS</address>
    </checkVatResponse>
  </soap:Body>
</soap:Envelope>"""


def test_parse_valid_response_preserves_consultation_proof() -> None:
    result = parse_soap_response(VALID_SOAP, "Example SRL")

    assert result == ValidVat(
        country_code="BE",
        vat_number="0671495129",
        request_date="2026-07-13",
        official_name="EXAMPLE SRL",
        official_address="RUE DE LA LOI 1 1000 BRUXELLES",
        request_identifier="WAPIAAAATEST1234",
        name_match=IdentityMatch.MATCH,
    )


def test_parse_valid_response_reports_local_name_mismatch() -> None:
    result = parse_soap_response(VALID_SOAP, "Different Company SA")

    assert isinstance(result, ValidVat)
    assert result.name_match is IdentityMatch.MISMATCH


def test_parse_valid_response_ignores_legal_form_tokens() -> None:
    result = parse_soap_response(VALID_SOAP, "Example")

    assert isinstance(result, ValidVat)
    assert result.name_match is IdentityMatch.MATCH


def test_parse_valid_response_keeps_substantive_name_difference() -> None:
    result = parse_soap_response(VALID_SOAP, "Example Services")

    assert isinstance(result, ValidVat)
    assert result.name_match is IdentityMatch.MISMATCH


def test_parse_valid_response_handles_identity_not_returned() -> None:
    soap = VALID_SOAP.replace("<traderName>EXAMPLE SRL</traderName>", "")

    result = parse_soap_response(soap, "Example SRL")

    assert isinstance(result, ValidVat)
    assert result.name_match is IdentityMatch.NOT_PROCESSED


def test_parse_valid_response_without_claimed_name_skips_identity_match() -> None:
    result = parse_soap_response(VALID_SOAP, "")

    assert isinstance(result, ValidVat)
    assert result.name_match is IdentityMatch.NOT_PROCESSED


def test_parse_invalid_response_is_not_an_outage() -> None:
    result = parse_soap_response(INVALID_SOAP, "Example SRL")

    assert result == InvalidVat(
        country_code="BE",
        vat_number="0000000000",
        request_date="2026-07-13",
        request_identifier="WAPIAAAATEST9999",
    )


def test_parse_fault_returns_unavailable_instead_of_invalid() -> None:
    result = parse_soap_response(FAULT_SOAP, "Example SRL")

    assert result == Unavailable(reason="MS_UNAVAILABLE")


def test_basic_check_without_seller_vat_preserves_limited_evidence() -> None:
    result = parse_soap_response(BASIC_SOAP, "SAS Qonto")

    assert isinstance(result, ValidVat)
    assert result.request_identifier == ""
    assert result.name_match is IdentityMatch.MATCH


def test_basic_check_matches_name_without_leading_legal_form() -> None:
    result = parse_soap_response(BASIC_SOAP, "QONTO")

    assert isinstance(result, ValidVat)
    assert result.name_match is IdentityMatch.MATCH


def test_legal_form_normalization_is_country_specific() -> None:
    soap = BASIC_SOAP.replace("<name>SAS Qonto</name>", "<name>SRL Qonto</name>")

    result = parse_soap_response(soap, "QONTO")

    assert isinstance(result, ValidVat)
    assert result.name_match is IdentityMatch.MISMATCH


def test_legal_form_dataset_covers_every_vies_territory() -> None:
    assert LEGAL_FORMS_BY_COUNTRY.keys() == SUPPORTED_COUNTRIES


def test_basic_check_request_omits_empty_requester_fields() -> None:
    request = VatCheckRequest(
        country_code="FR",
        vat_number="10819489626",
        requester_country_code=None,
        requester_vat_number=None,
        claimed_name="SAS Qonto",
    )

    payload = build_soap_request(request).decode()

    assert "checkVatApprox" not in payload
    assert "requesterCountryCode" not in payload
    assert "requesterVatNumber" not in payload
    assert "checkVat" in payload


@pytest.mark.parametrize("country_code", ["FR", "BE", "EL", "XI"])
def test_country_code_accepts_supported_vies_territories(country_code: str) -> None:
    assert parse_country_code(country_code) == country_code


@pytest.mark.parametrize("country_code", ["GR", "GB", "US", ""])
def test_country_code_rejects_unsupported_territories(country_code: str) -> None:
    with pytest.raises(ValueError, match="not supported by VIES"):
        _ = parse_country_code(country_code)


def test_vat_number_accepts_matching_country_prefix() -> None:
    assert parse_vat_number("FR", "FR 10 819 489 626") == "10819489626"


def test_vat_number_preserves_unprefixed_identifier() -> None:
    assert parse_vat_number("FR", "10 819 489 626") == "10819489626"


def test_vat_number_rejects_different_country_prefix() -> None:
    with pytest.raises(ValueError, match="does not match"):
        _ = parse_vat_number("FR", "BE0671495129")
