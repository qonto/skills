from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from typing import NotRequired, TypedDict, assert_never
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_URL = "https://recherche-entreprises.api.gouv.fr/search"


class RegisteredOffice(TypedDict):
    siret: str
    adresse: str
    code_postal: str


class RegistryCompany(TypedDict):
    siren: str
    nom_raison_sociale: str
    etat_administratif: str
    siege: RegisteredOffice
    tva: NotRequired[list[str] | None]


class RegistryResponse(TypedDict):
    results: list[RegistryCompany]


@dataclass(frozen=True, slots=True)
class CompanyMatch:
    legal_name: str
    siren: str
    siret: str
    address: str
    postcode: str
    vat_number: str | None


@dataclass(frozen=True, slots=True)
class NoMatch:
    pass


@dataclass(frozen=True, slots=True)
class AmbiguousMatch:
    candidates: int


RegistryMatch = CompanyMatch | NoMatch | AmbiguousMatch


def parse_search_response(
    payload: RegistryResponse,
    postcode: str | None = None,
    name: str | None = None,
) -> RegistryMatch:
    candidates = [
        company
        for company in payload["results"]
        if company["etat_administratif"] == "A"
        and (postcode is None or company["siege"]["code_postal"] == postcode)
    ]
    if not candidates:
        return NoMatch()
    if name is not None:
        exact = [
            company
            for company in candidates
            if company["nom_raison_sociale"].casefold() == name.casefold()
        ]
        if len(exact) == 1:
            candidates = exact
    if len(candidates) > 1:
        return AmbiguousMatch(len(candidates))

    company = candidates[0]
    office = company["siege"]
    vat_numbers = company.get("tva") or []
    return CompanyMatch(
        legal_name=company["nom_raison_sociale"],
        siren=company["siren"],
        siret=office["siret"],
        address=office["adresse"],
        postcode=office["code_postal"],
        vat_number=vat_numbers[0] if vat_numbers else None,
    )


def search_company(name: str, postcode: str | None = None) -> RegistryMatch:
    query = {"q": name, "per_page": "10"}
    if postcode is not None:
        query["code_postal"] = postcode
    request = Request(
        f"{API_URL}?{urlencode(query)}",
        headers={"Accept": "application/json", "User-Agent": "veto-skill/1.0"},
    )
    try:
        with urlopen(request, timeout=10) as response:
            payload: RegistryResponse = json.load(response)
    except (HTTPError, URLError, TimeoutError) as error:
        raise RegistryLookupError(str(error)) from error
    return parse_search_response(payload, postcode, name)


class RegistryLookupError(RuntimeError):
    pass


def main() -> int:
    if len(sys.argv) not in {2, 3}:
        print("Usage: registry_fr.py <company name> [postcode]")
        return 2
    result = search_company(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)
    match result:
        case CompanyMatch():
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
            return 0
        case NoMatch():
            print("NO_MATCH: no active company matched the supplied name and postcode")
            return 1
        case AmbiguousMatch(candidates=count):
            print(f"REVIEW: {count} active companies matched; refine name or postcode")
            return 1
        case unreachable:
            assert_never(unreachable)


if __name__ == "__main__":
    sys.exit(main())
