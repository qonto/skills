from decimal import Decimal

import pytest

from scripts.validate_fr import calculate_penalty, check_siren, check_vat
from scripts.registry_fr import AmbiguousMatch, CompanyMatch, RegistryResponse
from scripts.registry_fr import parse_search_response


def test_check_siren_accepts_valid_number() -> None:
    result = check_siren("819489626")
    assert result.valid is True
    assert result.kind == "SIREN"


def test_check_siren_rejects_invalid_checksum() -> None:
    result = check_siren("819489627")
    assert result.valid is False
    assert "checksum" in result.message


@pytest.mark.parametrize("rate", ["20%", "10%", "5.5%", "2.1%", "0%"])
def test_check_vat_accepts_legal_percentage(rate: str) -> None:
    result = check_vat(rate)
    assert result.valid is True


@pytest.mark.parametrize("rate", ["0.20", "0.10", "0.055", "0.021", "0"])
def test_check_vat_accepts_legal_decimal(rate: str) -> None:
    result = check_vat(rate)
    assert result.valid is True


def test_check_vat_message_uses_plain_decimal_notation() -> None:
    result = check_vat("20%")
    assert "E" not in result.message
    assert "20%" in result.message


def test_check_vat_rejects_illegal_percentage() -> None:
    result = check_vat("15%")
    assert result.valid is False


@pytest.mark.parametrize("rate", ["NaN", "Infinity", "-20%"])
def test_check_vat_rejects_non_finite_or_negative(rate: str) -> None:
    result = check_vat(rate)
    assert result.valid is False


def test_calculate_penalty_uses_explicit_contract_rate() -> None:
    result = calculate_penalty(Decimal("1200.00"), 20, Decimal("12.15"))
    assert result.interest == Decimal("7.99")
    assert result.fixed_indemnity == Decimal("40.00")
    assert result.total == Decimal("47.99")


def test_calculate_penalty_rejects_negative_days() -> None:
    with pytest.raises(ValueError, match="days late"):
        _ = calculate_penalty(Decimal("1200.00"), -5, Decimal("12.15"))


def test_calculate_penalty_rejects_non_positive_amount() -> None:
    with pytest.raises(ValueError, match="amount must be positive"):
        _ = calculate_penalty(Decimal("0"), 20, Decimal("12.15"))


def test_registry_selects_only_active_exact_postcode_match() -> None:
    payload: RegistryResponse = {
        "results": [
            {
                "siren": "819489626",
                "nom_raison_sociale": "QONTO",
                "etat_administratif": "A",
                "siege": {
                    "siret": "81948962600047",
                    "adresse": "18 RUE DE NAVARIN 75009 PARIS",
                    "code_postal": "75009",
                },
                "tva": ["FR10819489626"],
            },
            {
                "siren": "981621840",
                "nom_raison_sociale": "QONTO COM",
                "etat_administratif": "C",
                "siege": {
                    "siret": "98162184000017",
                    "adresse": "16 RUE DE NAVARIN 75009 PARIS",
                    "code_postal": "75009",
                },
                "tva": None,
            },
        ]
    }

    result = parse_search_response(payload, "75009")

    assert result == CompanyMatch(
        legal_name="QONTO",
        siren="819489626",
        siret="81948962600047",
        address="18 RUE DE NAVARIN 75009 PARIS",
        postcode="75009",
        vat_number="FR10819489626",
    )


def test_registry_requires_review_when_multiple_active_matches_remain() -> None:
    payload: RegistryResponse = {
        "results": [
            {
                "siren": "819489626",
                "nom_raison_sociale": "QONTO",
                "etat_administratif": "A",
                "siege": {
                    "siret": "81948962600047",
                    "adresse": "18 RUE DE NAVARIN 75009 PARIS",
                    "code_postal": "75009",
                },
                "tva": ["FR10819489626"],
            },
            {
                "siren": "880118765",
                "nom_raison_sociale": "QONTO SERVICES SA",
                "etat_administratif": "A",
                "siege": {
                    "siret": "88011876500028",
                    "adresse": "18 RUE DE NAVARIN 75009 PARIS",
                    "code_postal": "75009",
                },
                "tva": ["FR11880118765"],
            },
        ]
    }

    result = parse_search_response(payload, "75009")

    assert result == AmbiguousMatch(candidates=2)
