"""COSigna attestation chain.  # v0.1 S2-2

A serial hash chain that closes into a ring. NOT a sorted Merkle set.

    OPEN (initiator, no predecessor)
      -> LINK_1 (participant: validates predecessor + document)
      -> LINK_2 ...
      -> CLOSE (initiator: validates last participant, shuts the loop)

Each block after OPEN commits the previous block's hash via `prev`. Altering any
earlier block changes its hash, which breaks the `prev` of every later block — so
the closing block (timestamped/anchored downstream) transitively commits the whole
chain. The loop is "closed" because OPEN and CLOSE are the same initiator.

Dual validation, recorded per block:
  - document: `doc_hash` (re-verified client-side against the QR) — the OBJECT.
  - predecessor: `prev` + `prev_legit` — the PERSON (human recognition).

Privacy (Q4 = Option A): blocks carry only `face_hash` (a SHA-256 hex), never raw
face bytes and never a biometric template.

v0.5.1 (gated chain change): a signing block (OPEN / LINK) MAY additionally carry, when the
initiator turned the feature on, three OPTIONAL self-asserted fields that ride the hashed block →
anchor (so they become tamper-evident):
  - `captured_at` : the signer's device clock at capture (unix ms) — ADVISORY only; the canonical,
                    authoritative time is the server `ts` already in `_base`. Labelled "as reported
                    by the device" on the certificate.
  - `tz`          : the signer's IANA timezone (e.g. "Europe/Paris"), for local-time rendering.
  - `location`    : `{coarse, hash}` — coarse city/region in PLAINTEXT (for the certificate + the
                    later signee map), and the SHA-256 `hash` of the precise coordinates (a tamper-
                    evident commitment WITHOUT exposing the exact position; precise coords stay on the
                    signer's device). Self-asserted → the certificate labels it "declared location".

Backward-compatibility (the irreversible gate): these fields are attached ONLY when provided, so a
block built without them is **byte-identical** to a pre-v0.5.1 block and hashes to the same value —
every existing chain/proof still verifies unchanged. Canonicalization (`hashing.hash_object`,
`sort_keys`) and the JS verifier (`chain-verify.js`, `Object.keys().sort()`) already serialize
whatever keys are present, so a new field is committed identically on both sides with NO kernel edit.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .hashing import hash_object


def _attach_meta(
    b: Block,
    captured_at: Optional[int],
    tz: Optional[str],
    location: Optional[Dict[str, Any]],
) -> Block:
    """v0.5.1: conditionally attach the optional capture-time / timezone / location fields.

    Each is added ONLY when supplied, so omitting them yields a block byte-identical to pre-v0.5.1
    (preserving every existing hash). `location` is sanitized to exactly `{coarse?, hash?}` — the
    server never commits arbitrary client keys, and precise coordinates never enter the block (only
    their `hash` does)."""
    if captured_at is not None:
        _reject_bad_numbers(captured_at, "captured_at")
        b["captured_at"] = int(captured_at)
    if tz:
        b["tz"] = str(tz)[:64]
    if location:
        loc: Dict[str, str] = {}
        if location.get("coarse"):
            loc["coarse"] = str(location["coarse"])[:120]
        if location.get("hash"):
            loc["hash"] = str(location["hash"])[:64]
        if loc:
            b["location"] = loc
    return b

SCHEMA = "cosigna.chain/1"
CEREMONY_SCHEMA = "cosigna.ceremony/1"

ROLE_OPEN = "OPEN"
ROLE_LINK = "LINK"
ROLE_CLOSE = "CLOSE"

Block = Dict[str, Any]


_JS_MAX_SAFE_INTEGER = 9007199254740991  # 2**53 - 1; mirrors JS Number.MAX_SAFE_INTEGER


def _reject_bad_numbers(value: Any, path: str = "block") -> None:
    """Build-time guard for numeric fields entering NEW chain blocks.

    Do not call this from block_hash()/verify paths: historical hashes must remain reproducible.
    """
    if isinstance(value, bool):
        return
    if isinstance(value, float):
        raise ValueError(f"{path}: floats are forbidden in chain blocks")
    if isinstance(value, int):
        if value > _JS_MAX_SAFE_INTEGER or value < -_JS_MAX_SAFE_INTEGER:
            raise ValueError(f"{path}: integer exceeds JS safe-integer range")
        return
    if isinstance(value, dict):
        for k, v in value.items():
            _reject_bad_numbers(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _reject_bad_numbers(v, f"{path}[{i}]")


def _finalize(b: Block) -> Block:
    """Validate a newly-built block just before return (build path only).
    Deliberate asymmetry (D3): guards run here on the Python BUILD path; the JS VERIFY path
    applies safeScalar() in chain-verify.js instead (different call site, same invariant).
    """
    _reject_bad_numbers(b)
    return b


def _base(role: str, ceremony_id: str, signer_id: str, ts: int, doc_hash: str) -> Block:
    return {
        "schema": SCHEMA,
        "role": role,
        "ceremony_id": ceremony_id,
        "signer_id": signer_id,
        "ts": int(ts),  # unix milliseconds, integer — no floats
        "doc_hash": doc_hash,  # SHA-256 hex of the ORIGINAL document
    }


def _attach_attachments(b: Block, attachment_hashes: Optional[List[Dict[str, Any]]]) -> Block:
    """v0.512.0 S-attach: attach the attachments array as an additive-optional field.

    KEY OMITTED ENTIRELY when attachment_hashes is None or empty (NEVER set to null/[]).
    Preserves byte-identity of every existing block — same pattern as _attach_consent_record.
    The frozen chain-verify.js (Object.keys().sort()) hashes attachments when present with
    NO kernel edit — the existing cosigna.chain/1 canonicalization covers it.

    Each attachment dict is sanitized to exactly 4 keys (fixed allowlist) so a malicious
    client cannot inject arbitrary data into the signed proof.  Keys are in alphabetical order
    so they match chain-verify.js's Object.keys().sort() per-element canonicalization."""
    if not attachment_hashes:
        return b
    safe = []
    for a in attachment_hashes:
        safe.append({
            "hash": str(a["hash"])[:128],
            "mime": str(a.get("mime") or "application/octet-stream")[:128],
            "name": str(a.get("name") or "file")[:256],
            "size": int(a["size"]),
        })
    b["attachments"] = safe
    return b


def _attach_consent_record(b: Block, consent_record: Optional[Dict[str, Any]]) -> Block:
    """v0.510.0 consent-hardening: attach consent_record as an additive-optional field.

    KEY OMITTED ENTIRELY when consent_record is None (NEVER set to null/None).
    Preserves byte-identity of every existing block — the v0.503.0 / credential-rail precedent.
    The frozen chain-verify.js (Object.keys().sort()) hashes consent_record when present with NO
    kernel edit — the existing cosigna.chain/1 canonicalization covers it.

    Sanitization: only the known top-level keys are committed; unknown client keys are stripped
    so a malicious client cannot inject arbitrary data into the signed proof.
    Sub-dict shapes are preserved as-is (the caller / server validates structure before calling).

    v0.516.0 A3 (C1): three new bound fields added to the allowlist (additive; consent is dark
    so no prod sealed records exist):
      - ceremony_id   — anti-replay: ties record to this ceremony
      - doc_hash      — anti-replay: ties record to this document
      - signer_id     — anti-replay: ties record to this roster slot
    These are validated by cosigna.consent.validate_consent_record before this function is
    called, so we can safely pass them through verbatim (bounded by str()[:128])."""
    if consent_record is None:
        return b
    safe: Dict[str, Any] = {}
    if consent_record.get("read") is not None:
        safe["read"] = dict(consent_record["read"])
    if consent_record.get("name_declared") is not None:
        safe["name_declared"] = str(consent_record["name_declared"])[:200]
    if consent_record.get("binding") is not None:
        safe["binding"] = dict(consent_record["binding"])
    if consent_record.get("selfie_consent") is not None:
        safe["selfie_consent"] = dict(consent_record["selfie_consent"])
    # v0.516.0 A3: bound fields — committed into the sealed block for downstream replay protection.
    if consent_record.get("ceremony_id") is not None:
        safe["ceremony_id"] = str(consent_record["ceremony_id"])[:128]
    if consent_record.get("doc_hash") is not None:
        safe["doc_hash"] = str(consent_record["doc_hash"])[:128]
    if consent_record.get("signer_id") is not None:
        safe["signer_id"] = str(consent_record["signer_id"])[:200]
    if safe:
        safe["v"] = int(consent_record.get("v", 1))
        b["consent_record"] = safe
    return b


def _attach_credential_rail(b: Block, credential_commitment: Optional[Dict[str, Any]]) -> Block:
    """v0.504.0 Rung-3 B1: attach credential_rail as an additive-optional 4-field dict.

    KEY OMITTED ENTIRELY when credential_commitment is None (NEVER set to null/None).
    This preserves byte-identity of every existing block — the v0.5.1 / v0.503.0 precedent.

    The 4 fields sealed into the block are immutable (rail, trust_root_id, scope, commitment_hash).
    validation_level is EXCLUDED: it is mutable-intent and must NOT be chain-sealed (H1 fold).
    The scope list is SORTED so the hash is deterministic regardless of insertion order.
    The frozen chain-verify.js (Object.keys().sort()) hashes credential_rail when present, with
    NO edit to any kernel file — the existing cosigna.chain/1 canonicalization rule covers it.

    commitment_hash binds the single-use nonce in its preimage; the nonce is not persisted →
    post-facto re-derivation from chain data alone is impossible by design; independent
    verification needs the server nonce-issuance log.
    """
    if credential_commitment is None:
        return b
    b["credential_rail"] = {
        "rail": str(credential_commitment["rail"]),
        "trust_root_id": str(credential_commitment["trust_root_id"]),
        "scope": sorted(str(e) for e in credential_commitment.get("verified_element_scope", [])),
        "commitment_hash": str(credential_commitment["commitment_hash"]),
    }
    return b


def build_open(
    ceremony_id: str, initiator_id: str, ts: int, doc_hash: str, face_hash: Optional[str] = None,
    captured_at: Optional[int] = None, tz: Optional[str] = None,
    location: Optional[Dict[str, Any]] = None,
    credential_commitment: Optional[Dict[str, Any]] = None,
) -> Block:
    """First block. Initiator proposes the document; no predecessor to validate.
    v0.5.1: may carry optional capture-time / tz / location (attached only when provided).
    v0.503.0 (§3 fold-1): face_hash is OPTIONAL — when None (an acceptance receipt has no consent
    selfie) the key is OMITTED entirely (NOT set to ''). Byte-ADDITIVE: the frozen JS verifier hashes
    only the keys PRESENT (sorted), so an OPEN without face_hash hashes deterministically on both sides
    and verifies. Ceremonies always pass a real face_hash, so their chain stays byte-unchanged.
    v0.504.0 (Rung-3 B1): credential_commitment is OPTIONAL — when not None (initiator presents
    a credential), 4-field credential_rail dict attached; key OMITTED entirely when None."""
    b = _base(ROLE_OPEN, ceremony_id, initiator_id, ts, doc_hash)
    if face_hash is not None:
        b["face_hash"] = face_hash
    b = _attach_meta(b, captured_at, tz, location)
    return _finalize(_attach_credential_rail(b, credential_commitment))


def build_link(
    ceremony_id: str,
    signer_id: str,
    ts: int,
    doc_hash: str,
    face_hash: str,
    prev_hash: str,
    prev_legit: bool = True,
    captured_at: Optional[int] = None,
    tz: Optional[str] = None,
    location: Optional[Dict[str, Any]] = None,
    credential_commitment: Optional[Dict[str, Any]] = None,
    consent_record: Optional[Dict[str, Any]] = None,
    attachment_hashes: Optional[List[Dict[str, Any]]] = None,
) -> Block:
    """A participant's link. Validates the document (`doc_hash`) and the predecessor
    (`prev` commitment + `prev_legit` human attestation).
    v0.5.1: may carry optional capture-time / tz / location (attached only when provided).
    v0.504.0 (Rung-3 B1): credential_commitment is OPTIONAL — when not None (signer presents
    a credential), 4-field credential_rail dict attached; key OMITTED entirely when None.
    No validation_level in the chain (mutable → not sealable; H1 fold).
    v0.510.0 consent-hardening: consent_record is OPTIONAL — when not None (ceremony has
    consent_required=True), the 4-gate client attestation is attached; key OMITTED entirely
    when None so every existing/non-consent chain stays byte-identical (additive-optional).
    v0.512.0 S-attach: attachment_hashes is OPTIONAL — when provided (signer attached evidence
    files), the 4-key allowlist dicts are sealed into the block; key OMITTED entirely when None
    so every existing/non-attachment chain stays byte-identical (additive-optional)."""
    b = _base(ROLE_LINK, ceremony_id, signer_id, ts, doc_hash)
    b["face_hash"] = face_hash
    b["prev"] = prev_hash
    b["prev_legit"] = bool(prev_legit)
    b = _attach_meta(b, captured_at, tz, location)
    b = _attach_credential_rail(b, credential_commitment)
    b = _attach_consent_record(b, consent_record)
    return _finalize(_attach_attachments(b, attachment_hashes))


def build_close(
    ceremony_id: str,
    initiator_id: str,
    ts: int,
    doc_hash: str,
    prev_hash: str,
    prev_legit: bool = True,
) -> Block:
    """Closing block. Initiator validates the last participant, shutting the loop."""
    b = _base(ROLE_CLOSE, ceremony_id, initiator_id, ts, doc_hash)
    b["prev"] = prev_hash
    b["prev_legit"] = bool(prev_legit)
    return _finalize(b)


def block_hash(block: Block) -> str:
    """Canonical SHA-256 hex of a block. This is what the next block's `prev` commits."""
    return hash_object(block)


class ChainBuilder:
    """Convenience builder for assembling a chain in order. Used by tests, demos, and
    the future server. The server holds the chain-tip and appends blocks as signers act.
    """

    def __init__(self, ceremony_id: str, initiator_id: str, doc_hash: str):
        self.ceremony_id = ceremony_id
        self.initiator_id = initiator_id
        self.doc_hash = doc_hash
        self.blocks: List[Block] = []

    def open(self, ts: int, face_hash: str) -> Block:
        if self.blocks:
            raise ValueError("chain already opened")
        b = build_open(self.ceremony_id, self.initiator_id, ts, self.doc_hash, face_hash)
        self.blocks.append(b)
        return b

    def link(self, signer_id: str, ts: int, face_hash: str, prev_legit: bool = True) -> Block:
        if not self.blocks:
            raise ValueError("cannot add a link before OPEN")
        prev = block_hash(self.blocks[-1])
        b = build_link(self.ceremony_id, signer_id, ts, self.doc_hash, face_hash, prev, prev_legit)
        self.blocks.append(b)
        return b

    def close(self, ts: int, prev_legit: bool = True) -> Block:
        if not self.blocks:
            raise ValueError("cannot close before OPEN")
        prev = block_hash(self.blocks[-1])
        b = build_close(self.ceremony_id, self.initiator_id, ts, self.doc_hash, prev, prev_legit)
        self.blocks.append(b)
        return b

    def document(self) -> Dict[str, Any]:
        """The self-contained ceremony document (what the verifier consumes)."""
        return {
            "schema": CEREMONY_SCHEMA,
            "ceremony_id": self.ceremony_id,
            "doc_hash": self.doc_hash,
            "blocks": self.blocks,
        }
