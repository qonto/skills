"""COSigna chain verifier.  # v0.1 S2-3

Pure function. Walks the chain, asserts integrity, returns a Verdict. This Python
implementation is the reference; the S4/S5 browser verifier is a JS port that MUST
produce identical verdicts on identical input (same canonical hashing).

Checks, in order:
  1. structural schema (>=2 blocks, every block tagged cosigna.chain/1)
  2. first block is OPEN, last is CLOSE
  3. CLOSE signer == OPEN signer  (loop closed by the initiator)
  4. every block carries the same doc_hash
  5. every block after OPEN: prev == hash(previous block)        (chain integrity)
  6. every block after OPEN: prev_legit is true                  (human attestation)
  7. LINK signers are distinct                                   (no double-signing)
  8. if a PDF hash is supplied: it equals doc_hash               (document identity)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from .chain import ROLE_CLOSE, ROLE_LINK, ROLE_OPEN, SCHEMA, block_hash


class Status(str, Enum):
    OK = "OK"
    SCHEMA_ERROR = "SCHEMA_ERROR"
    NOT_OPENED = "NOT_OPENED"
    NOT_CLOSED = "NOT_CLOSED"
    DOC_HASH_MISMATCH = "DOC_HASH_MISMATCH"  # blocks disagree on doc_hash
    BROKEN_LINK = "BROKEN_LINK"  # a block.prev != hash(previous block)
    MISSING_ATTESTATION = "MISSING_ATTESTATION"  # prev_legit is false
    DUPLICATE_SIGNER = "DUPLICATE_SIGNER"  # a participant signed more than one LINK
    PDF_MISMATCH = "PDF_MISMATCH"  # supplied PDF hash != chain doc_hash


@dataclass
class Verdict:
    status: Status
    closed: bool = False
    doc_hash: Optional[str] = None
    n_links: int = 0
    signers: List[str] = field(default_factory=list)
    detail: str = ""
    failed_index: Optional[int] = None

    def ok(self) -> bool:
        return self.status == Status.OK


def verify_chain(ceremony: dict, pdf_sha256: Optional[str] = None) -> Verdict:
    blocks = ceremony.get("blocks") if isinstance(ceremony, dict) else None
    if not isinstance(blocks, list) or len(blocks) < 2:
        return Verdict(Status.SCHEMA_ERROR, detail="chain needs >=2 blocks (OPEN..CLOSE)")

    for i, b in enumerate(blocks):
        if not isinstance(b, dict) or b.get("schema") != SCHEMA:
            return Verdict(Status.SCHEMA_ERROR, detail=f"bad schema at block {i}", failed_index=i)

    if blocks[0].get("role") != ROLE_OPEN:
        return Verdict(Status.NOT_OPENED, detail="first block is not OPEN")
    if blocks[-1].get("role") != ROLE_CLOSE:
        return Verdict(Status.NOT_CLOSED, detail="last block is not CLOSE")

    initiator = blocks[0].get("signer_id")
    if blocks[-1].get("signer_id") != initiator:
        return Verdict(
            Status.NOT_CLOSED,
            detail="CLOSE signer != OPEN signer (loop not closed by initiator)",
        )

    doc_hash = blocks[0].get("doc_hash")
    for i, b in enumerate(blocks):
        if b.get("doc_hash") != doc_hash:
            return Verdict(
                Status.DOC_HASH_MISMATCH,
                doc_hash=doc_hash,
                detail=f"block {i} doc_hash differs from OPEN",
                failed_index=i,
            )

    link_signers: List[str] = []
    for i in range(1, len(blocks)):
        b = blocks[i]
        expected_prev = block_hash(blocks[i - 1])
        if b.get("prev") != expected_prev:
            return Verdict(
                Status.BROKEN_LINK,
                doc_hash=doc_hash,
                detail=f"block {i} prev != hash(block {i - 1})",
                failed_index=i,
            )
        if not b.get("prev_legit", False):
            return Verdict(
                Status.MISSING_ATTESTATION,
                doc_hash=doc_hash,
                detail=f"block {i} prev_legit is false",
                failed_index=i,
            )
        if b.get("role") == ROLE_LINK:
            link_signers.append(b.get("signer_id"))

    if len(set(link_signers)) != len(link_signers):
        return Verdict(
            Status.DUPLICATE_SIGNER,
            doc_hash=doc_hash,
            detail="a participant appears in more than one LINK",
        )

    if pdf_sha256 is not None and pdf_sha256 != doc_hash:
        return Verdict(
            Status.PDF_MISMATCH,
            doc_hash=doc_hash,
            detail="supplied PDF hash != chain doc_hash",
        )

    return Verdict(
        Status.OK,
        closed=True,
        doc_hash=doc_hash,
        n_links=len(link_signers),
        signers=link_signers,
        detail="loop closed and sound",
    )
