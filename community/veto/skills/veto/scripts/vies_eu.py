from __future__ import annotations

import http.client
import json
import sys
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Final, assert_never

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.legal_forms_eu import LEGAL_FORMS_BY_COUNTRY

VIES_HOST: Final = "ec.europa.eu"
VIES_PATH: Final = "/taxation_customs/vies/services/checkVatService"
SOAP_NAMESPACE: Final = "urn:ec.europa.eu:taxud:vies:services:checkVat:types"
SUPPORTED_COUNTRIES: Final = frozenset(
    "AT BE BG CY CZ DE DK EE EL ES FI FR HR HU IE IT LT LU LV MT NL PL PT RO SE SI SK XI".split()
)


class IdentityMatch(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    NOT_PROCESSED = "NOT_PROCESSED"


@dataclass(frozen=True, slots=True)
class ValidVat:
    country_code: str
    vat_number: str
    request_date: str
    official_name: str | None
    official_address: str | None
    request_identifier: str
    name_match: IdentityMatch


@dataclass(frozen=True, slots=True)
class InvalidVat:
    country_code: str
    vat_number: str
    request_date: str
    request_identifier: str


@dataclass(frozen=True, slots=True)
class Unavailable:
    reason: str


VatResult = ValidVat | InvalidVat | Unavailable


@dataclass(frozen=True, slots=True)
class VatCheckRequest:
    country_code: str
    vat_number: str
    requester_country_code: str | None
    requester_vat_number: str | None
    claimed_name: str


class UnsupportedCountryError(ValueError):
    def __init__(self, country_code: str) -> None:
        super().__init__(f"{country_code!r} is not supported by VIES")


class VatCountryMismatchError(ValueError):
    def __init__(self, expected: str, actual: str) -> None:
        super().__init__(f"VAT prefix {actual!r} does not match country {expected!r}")


def parse_country_code(value: str) -> str:
    country_code = value.strip().upper()
    if country_code not in SUPPORTED_COUNTRIES:
        raise UnsupportedCountryError(country_code)
    return country_code


def parse_vat_number(country_code: str, value: str) -> str:
    country = parse_country_code(country_code)
    compact = "".join(character for character in value.upper() if character.isalnum())
    if compact.startswith(country):
        return compact[len(country) :]
    prefix = compact[:2]
    if prefix in SUPPORTED_COUNTRIES:
        raise VatCountryMismatchError(country, prefix)
    return compact


def _text(root: ET.Element, local_name: str) -> str | None:
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] == local_name:
            value = element.text
            return value.strip() if value and value.strip() else None
    return None


def _normalize_name(value: str, country_code: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    tokens = (
        "".join(
            character if character.isalnum() else " " for character in without_marks
        )
        .casefold()
        .split()
    )
    for legal_form in LEGAL_FORMS_BY_COUNTRY[country_code]:
        size = len(legal_form)
        if len(tokens) > size and tuple(tokens[:size]) == legal_form:
            return "".join(tokens[size:])
        if len(tokens) > size and tuple(tokens[-size:]) == legal_form:
            return "".join(tokens[:-size])
    return "".join(tokens)


def parse_soap_response(xml: str, claimed_name: str) -> VatResult:
    if "<!DOCTYPE" in xml.upper() or "<!ENTITY" in xml.upper():
        return Unavailable("UNSAFE_XML")
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return Unavailable("MALFORMED_RESPONSE")

    fault = _text(root, "faultstring")
    if fault is not None:
        return Unavailable(fault)

    country_code = _text(root, "countryCode")
    vat_number = _text(root, "vatNumber")
    request_date = _text(root, "requestDate")
    valid = _text(root, "valid")
    request_identifier = _text(root, "requestIdentifier") or ""
    if country_code is None or vat_number is None or request_date is None:
        return Unavailable("MALFORMED_RESPONSE")
    if valid == "false":
        return InvalidVat(country_code, vat_number, request_date, request_identifier)
    if valid != "true":
        return Unavailable("MALFORMED_RESPONSE")

    official_name = _text(root, "traderName") or _text(root, "name")
    official_address = _text(root, "traderAddress") or _text(root, "address")
    if official_name is None or not claimed_name.strip():
        name_match = IdentityMatch.NOT_PROCESSED
    elif _normalize_name(official_name, country_code) == _normalize_name(
        claimed_name, country_code
    ):
        name_match = IdentityMatch.MATCH
    else:
        name_match = IdentityMatch.MISMATCH
    return ValidVat(
        country_code,
        vat_number,
        request_date,
        official_name,
        official_address,
        request_identifier,
        name_match,
    )


def build_soap_request(request: VatCheckRequest) -> bytes:
    envelope = ET.Element("{http://schemas.xmlsoap.org/soap/envelope/}Envelope")
    body = ET.SubElement(envelope, "{http://schemas.xmlsoap.org/soap/envelope/}Body")
    operation = (
        "checkVatApprox"
        if request.requester_country_code is not None
        and request.requester_vat_number is not None
        else "checkVat"
    )
    check = ET.SubElement(body, f"{{{SOAP_NAMESPACE}}}{operation}")
    values = [
        ("countryCode", request.country_code),
        ("vatNumber", request.vat_number),
    ]
    if (
        request.requester_country_code is not None
        and request.requester_vat_number is not None
    ):
        values.extend(
            (
                ("traderName", request.claimed_name),
                ("requesterCountryCode", request.requester_country_code),
                ("requesterVatNumber", request.requester_vat_number),
            )
        )
    for key, value in values:
        ET.SubElement(check, f"{{{SOAP_NAMESPACE}}}{key}").text = value
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


def check_vat(request: VatCheckRequest) -> VatResult:
    country = parse_country_code(request.country_code)
    requester_country = (
        parse_country_code(request.requester_country_code)
        if request.requester_country_code is not None
        else None
    )
    requester_vat = (
        parse_vat_number(requester_country, request.requester_vat_number)
        if requester_country is not None and request.requester_vat_number is not None
        else None
    )
    normalized = VatCheckRequest(
        country,
        parse_vat_number(country, request.vat_number),
        requester_country,
        requester_vat,
        request.claimed_name.strip(),
    )
    connection = http.client.HTTPSConnection(VIES_HOST, timeout=15)
    try:
        connection.request(
            "POST",
            VIES_PATH,
            body=build_soap_request(normalized),
            headers={
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": '""',
                "User-Agent": "veto-skill/1.0",
            },
        )
        response = connection.getresponse()
        payload = response.read(1_000_001)
    except (OSError, TimeoutError, http.client.HTTPException) as error:
        return Unavailable(type(error).__name__)
    finally:
        connection.close()
    if len(payload) > 1_000_000:
        return Unavailable("RESPONSE_TOO_LARGE")
    return parse_soap_response(
        payload.decode("utf-8", errors="strict"), normalized.claimed_name
    )


def main() -> int:
    match sys.argv[1:]:
        case [country, vat]:
            request = VatCheckRequest(country, vat, None, None, "")
        case [country, vat, name]:
            request = VatCheckRequest(country, vat, None, None, name)
        case [country, vat, requester_country, requester_vat]:
            request = VatCheckRequest(
                country, vat, requester_country, requester_vat, ""
            )
        case [country, vat, requester_country, requester_vat, name]:
            request = VatCheckRequest(
                country, vat, requester_country, requester_vat, name
            )
        case _:
            print(
                "Usage: vies_eu.py <country> <vat> [name] OR vies_eu.py "
                "<country> <vat> <requester_country> <requester_vat> [name]"
            )
            return 2
    result = check_vat(request)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    match result:
        case ValidVat():
            return 0
        case InvalidVat() | Unavailable():
            return 1
        case unreachable:
            assert_never(unreachable)


if __name__ == "__main__":
    sys.exit(main())
