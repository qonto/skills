from __future__ import annotations

import sys
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from enum import Enum
from typing import Literal

IdentifierKind = Literal["SIREN", "SIRET"]

LEGAL_VAT_RATES = frozenset(
    {Decimal("20"), Decimal("10"), Decimal("5.5"), Decimal("2.1"), Decimal("0")}
)
FIXED_RECOVERY_INDEMNITY = Decimal("40.00")
MONEY_QUANTUM = Decimal("0.01")
DAYS_PER_YEAR = Decimal("365")
USAGE = "Usage: validate_fr.py <siren N | vat RATE | penalty AMOUNT DAYS RATE>"


class PenaltyInputError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ValidationResult:
    valid: bool
    message: str
    kind: IdentifierKind | None = None


@dataclass(frozen=True, slots=True)
class PenaltyResult:
    interest: Decimal
    fixed_indemnity: Decimal
    total: Decimal


class Command(str, Enum):
    SIREN = "siren"
    VAT = "vat"
    PENALTY = "penalty"


def luhn_valid(digits: str) -> bool:
    total = 0
    for index, character in enumerate(reversed(digits)):
        value = int(character)
        if index % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def check_siren(value: str) -> ValidationResult:
    normalized = value.replace(" ", "")
    if not normalized.isdigit():
        return ValidationResult(False, "SIREN/SIRET must contain digits only")

    length = len(normalized)
    if length == 9:
        kind: IdentifierKind = "SIREN"
    elif length == 14:
        kind = "SIRET"
    else:
        return ValidationResult(
            False, f"Expected 9 digits (SIREN) or 14 digits (SIRET), got {length}"
        )

    if normalized[:9] != "356000000" and not luhn_valid(normalized):
        return ValidationResult(
            False,
            f"{kind} {normalized} fails the Luhn checksum; check for a typo",
            kind,
        )
    return ValidationResult(True, f"{kind} {normalized} is structurally valid", kind)


def check_vat(rate: str) -> ValidationResult:
    raw = rate.strip()
    is_percentage = raw.endswith("%")
    number = raw[:-1].strip() if is_percentage else raw
    try:
        parsed = Decimal(number)
    except InvalidOperation:
        return ValidationResult(False, f"VAT rate '{rate}' is not numeric")
    if not parsed.is_finite():
        return ValidationResult(False, f"VAT rate '{rate}' must be a finite number")

    percentage = parsed if (is_percentage or parsed > 1) else parsed * 100
    if percentage < 0:
        return ValidationResult(False, f"VAT rate '{rate}' cannot be negative")
    shown = f"{percentage.normalize():f}"
    if percentage in LEGAL_VAT_RATES:
        return ValidationResult(True, f"{shown}% is a legal French VAT rate")
    legal = "use 20%, 10%, 5.5%, 2.1%, or 0% with an exemption code"
    return ValidationResult(False, f"{shown}% is not legal in France; {legal}")


def calculate_penalty(
    amount_ttc: Decimal,
    days_late: int,
    annual_rate_percent: Decimal,
) -> PenaltyResult:
    if not amount_ttc.is_finite() or not annual_rate_percent.is_finite():
        raise PenaltyInputError("amount and annual rate must be finite numbers")
    if amount_ttc <= 0:
        raise PenaltyInputError("amount must be positive")
    if days_late <= 0:
        raise PenaltyInputError("days late must be a positive number of days")
    if annual_rate_percent < 0:
        raise PenaltyInputError("annual rate cannot be negative")

    interest = (
        amount_ttc
        * (annual_rate_percent / Decimal("100"))
        * Decimal(days_late)
        / DAYS_PER_YEAR
    ).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
    total = interest + FIXED_RECOVERY_INDEMNITY
    return PenaltyResult(interest, FIXED_RECOVERY_INDEMNITY, total)


def _run_siren(arg: str) -> int:
    result = check_siren(arg)
    print(("OK: " if result.valid else "FAIL: ") + result.message)
    return 0 if result.valid else 1


def _run_vat(arg: str) -> int:
    result = check_vat(arg)
    print(("OK: " if result.valid else "FAIL: ") + result.message)
    return 0 if result.valid else 1


def _run_penalty(args: list[str]) -> int:
    if len(args) != 3:
        print("Usage: penalty <amount_ttc> <days_late> <annual_rate_percent>")
        return 2
    try:
        penalty = calculate_penalty(Decimal(args[0]), int(args[1]), Decimal(args[2]))
    except (InvalidOperation, ValueError) as error:
        print(f"Invalid penalty input: {error}")
        return 2
    print(
        "\n".join(
            (
                f"Interest: {penalty.interest:.2f} EUR",
                f"Fixed recovery indemnity: {penalty.fixed_indemnity:.2f} EUR",
                f"Total claimable: {penalty.total:.2f} EUR",
            )
        )
    )
    return 0


def main() -> int:
    if len(sys.argv) < 3:
        print(USAGE)
        return 2

    name = sys.argv[1]
    if name == Command.SIREN.value:
        return _run_siren(sys.argv[2])
    if name == Command.VAT.value:
        return _run_vat(sys.argv[2])
    if name == Command.PENALTY.value:
        return _run_penalty(sys.argv[2:])
    print(f"Unknown command '{name}'")
    return 2


if __name__ == "__main__":
    sys.exit(main())
