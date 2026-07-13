"""Canonical hashing primitives for COSigna.  # v0.1 S2-1

Deterministic JSON serialization + SHA-256. Stdlib only — no third-party crypto.

Why canonical serialization matters: the attestation chain hashes each block, and
two machines (a signer's browser and the verifier) must derive the *same* hash from
the *same* logical block. We use sorted keys + compact separators + UTF-8. No floats
appear anywhere in COSigna blocks (timestamps are integer milliseconds), so float
representation non-determinism is not a concern.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_bytes(obj: Any) -> bytes:
    """Deterministic UTF-8 serialization of a JSON-compatible object."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    """SHA-256 of raw bytes, hex-encoded."""
    return hashlib.sha256(data).hexdigest()


def hash_object(obj: Any) -> str:
    """SHA-256 hex of the canonical serialization of a JSON-compatible object."""
    return sha256_hex(canonical_bytes(obj))


def hash_file(path: str, chunk: int = 1 << 20) -> str:
    """Streaming SHA-256 hex of a file's bytes (chunked for large PDFs)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()
