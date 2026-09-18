from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final


def _forms(*values: str) -> tuple[tuple[str, ...], ...]:
    return tuple(
        sorted(
            (tuple(value.split()) for value in values),
            key=lambda item: (-len(item), item),
        )
    )


LEGAL_FORMS_BY_COUNTRY: Final[Mapping[str, tuple[tuple[str, ...], ...]]] = (
    MappingProxyType(
        {
            "AT": _forms("ag", "eu", "flexkapg", "gmbh", "kg", "og", "ohg"),
            "BE": _forms(
                "asbl",
                "bv",
                "bvba",
                "cv",
                "cvba",
                "nv",
                "sa",
                "sc",
                "sca",
                "scrl",
                "scri",
                "scs",
                "snc",
                "sprl",
                "sprlu",
                "srl",
                "vof",
                "vzw",
            ),
            "BG": _forms("ad", "ead", "eood", "et", "kd", "kda", "ood", "sd"),
            "CY": _forms("ltd", "plc"),
            "CZ": _forms("as", "druzstvo", "ks", "sro", "vos", "se", "sce"),
            "DE": _forms(
                "ag",
                "eg",
                "egbr",
                "ewiv",
                "gbr",
                "ggmbh",
                "gmbh",
                "kg",
                "kgaa",
                "ohg",
                "partg",
                "ug",
                "vvag",
            ),
            "DK": _forms("amba", "aps", "as", "is", "ivs", "ks", "ps", "smba"),
            "EE": _forms("as", "fie", "mtu", "ou", "sa", "tuh"),
            "EL": _forms("ae", "ee", "epe", "ike", "oe", "pc", "sa"),
            "ES": _forms(
                "aeie", "aie", "cb", "sa", "sal", "sc", "sl", "sll", "slp", "slu"
            ),
            "FI": _forms("ab", "abp", "ky", "osk", "oy", "oyj"),
            "FR": _forms(
                "ei",
                "eurl",
                "geie",
                "sa",
                "sarl",
                "sas",
                "sasu",
                "sca",
                "sci",
                "scop",
                "se",
                "selarl",
                "selas",
                "slp",
                "snc",
            ),
            "HR": _forms("dd", "doo", "jdoo", "jtd", "kd"),
            "HU": _forms("bt", "kft", "kkt", "nyrt", "zrt"),
            "IE": _forms("clg", "dac", "icav", "ltd", "plc", "ulc"),
            "IT": _forms("sas", "sc", "snc", "spa", "srl", "srls", "ss"),
            "LT": _forms("ab", "ii", "mb", "uab"),
            "LU": _forms(
                "asbl",
                "geie",
                "gie",
                "sa",
                "sarl",
                "sc",
                "sci",
                "seca",
                "secs",
                "senc",
                "sicaf",
                "sicav",
            ),
            "LV": _forms("as", "ik", "ks", "ps", "sia"),
            "MT": _forms("lp", "ltd", "plc"),
            "NL": _forms("bv", "cv", "eesv", "nv", "vof"),
            "PL": _forms("sa", "sc", "sj", "ska", "sp z oo", "spj", "spk", "spp"),
            "PT": _forms("lda", "sa"),
            "RO": _forms("ii", "pfa", "sa", "sca", "scs", "snc", "srl"),
            "SE": _forms("ab", "ekonomisk forening", "hb", "kb"),
            "SI": _forms("dd", "dno", "doo", "kd", "kdd", "sp"),
            "SK": _forms("as", "ks", "sro", "vos"),
            "XI": _forms("cic", "llp", "lp", "ltd", "plc", "ulc"),
        }
    )
)
