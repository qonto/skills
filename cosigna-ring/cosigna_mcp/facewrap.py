"""Python mirror of the FROZEN browser wrap — UX/mobile-signer/facecrypto.js.  # mcp D2

WHY THIS FILE EXISTS
--------------------
The COSIGNA connector must, entirely on the user's machine and WITHOUT ever uploading
the document or the key, produce the two artifacts a signer's browser would otherwise
produce:

  1. the AES-GCM ciphertext blob POSTed to /faces (enc=aesgcm) — the encrypted selfie, and
  2. the "wrapped content key" that rides in each signer link's URL fragment as `#wk=…`,
     which the signer's browser unwraps with the doc-hash to recover the content key (CK).

Both must be BYTE-COMPATIBLE with the frozen `facecrypto.js`, because the real signer
browsers (and the verifier) run that JS. This module re-implements ONLY the wrap/encrypt
half; correctness is proven by `mcp/tests/test_facewrap_parity.py`, which round-trips
against the ACTUAL frozen JS in both directions.

It is a deliberate, from-scratch RE-IMPLEMENTATION (F1 of the §3-validated plan). It does
NOT import `src/cosigna/facecrypto.py` (which is pinned) and touches no pinned file. It uses
`cryptography` (AESGCM), the same primitive the reference Python uses.

THE SCHEME (transcribed from facecrypto.js — cited line-by-line below)
----------------------------------------------------------------------
Content-key encryption of the selfie (`encryptFace`, facecrypto.js:53-66):
  - CK          = 32 random bytes (AES-256)                         [generateKeyRaw :44-46]
  - face_hash   = SHA-256(plaintext) hex                            [:57 `sha256Hex(plaintext)`]
  - nonce       = 12 random bytes                                   [NONCE_LEN=12, :22]
  - AAD         = UTF-8 bytes of the face_hash hex string           [:58 `new TextEncoder().encode(fh)`]
  - blob        = nonce(12) || ciphertext || GCM-tag(16)            [:62-65 nonce then ct(WebCrypto appends tag)]

Document-wrapped key (`wrapKeyWithDocHash`, facecrypto.js:126-136) — THE `#wk=` primitive:
  - kekRaw      = hexToBytes(docHashHex)  → the 32 raw bytes of the SHA-256 doc-hash,
                  used DIRECTLY as the AES-256 KEK — NO KDF / NO stretch.               [:128]
  - nonce       = 12 random bytes                                                        [:130]
  - NO AAD      (unlike encryptFace — wrapKeyWithDocHash passes no `additionalData`)      [:131]
  - blob        = nonce(12) || ciphertext || tag(16)                                      [:132-134]
  - return      bytesToB64url(blob)  → URL-safe base64, '+'→'-' '/'→'_' , '=' stripped    [:135, :92-96]

What the doc-hash KEK does (MCPSEC-005, 2026-07-12 — corrected framing): it BINDS the wrapped
key to a specific document — you must know the right doc-hash to unwrap — but it is NOT a secret.
The doc-hash is PUBLIC (the coordinator is even given it at /ceremonies creation, and it appears in
the public /proof), so the KEK provides document-binding, not confidentiality. The reason the
coordinator can never recover CK is that it never receives the `#wk=` fragment — a URL fragment is
client-only, never sent to the server. Confidentiality of CK (and thus the consent photos) therefore
rests on the SECRECY OF THE `#wk=` LINK FRAGMENT (the F7 capability-link-secrecy property), not on
possession of the document: anyone holding a signer link plus the public doc-hash can unwrap CK.

Stdlib + `cryptography` only.
"""
from __future__ import annotations

import base64
import hashlib
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# facecrypto.js:22-23 — const NONCE_LEN = 12; const KEY_LEN = 32;
NONCE_LEN = 12          # 96-bit AES-GCM nonce (WebCrypto default; matches the JS + reference Python)
KEY_LEN = 32            # AES-256 content key
_MIN_BLOB = NONCE_LEN + 16   # nonce + minimum GCM tag


class FaceWrapError(Exception):
    """Raised on any wrap/encrypt integrity failure. Never leaks plaintext or key."""


# ---------------------------------------------------------------------------
# byte helpers — mirror facecrypto.js:92-104 (bytesToB64url / b64urlToBytes)
# ---------------------------------------------------------------------------

def bytes_to_b64url(data: bytes) -> str:
    """URL-safe base64 with padding stripped — mirrors facecrypto.js bytesToB64url (:92-96):
    `btoa(bin).replace(/\\+/g,'-').replace(/\\//g,'_').replace(/=+$/,'')`.
    Python's urlsafe_b64encode already does the +/- and / / _ substitution; we strip '='."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_to_bytes(s: str) -> bytes:
    """Inverse of bytes_to_b64url — mirrors facecrypto.js b64urlToBytes (:98-104), re-adding
    the padding the JS computes as `'='.repeat((-len % 4 + 4) % 4)`."""
    pad = "=" * ((-len(s) % 4 + 4) % 4)
    return base64.urlsafe_b64decode(s + pad)


def sha256_hex(data: bytes) -> str:
    """SHA-256 hex — the value committed in the chain (facecrypto.js sha256Hex, :34-37)."""
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# content key — mirror facecrypto.js generateKeyRaw (:44-46)
# ---------------------------------------------------------------------------

def generate_content_key() -> bytes:
    """A fresh per-ceremony Content Key (CK): 32 random bytes.

    NONCE-SAFETY INVARIANT (facecrypto.js:16-20 / the reference-Python note): CK is
    per-ceremony and encrypts only a handful of blobs (the selfie + small optional sealed
    blobs), so random 96-bit nonces are safe. Do NOT widen CK scope — that needs a gated
    crypto review + a nonce-design change. This connector generates one CK per ceremony.
    """
    return os.urandom(KEY_LEN)


# ---------------------------------------------------------------------------
# encrypt_face — mirror facecrypto.js encryptFace (:53-66)
# ---------------------------------------------------------------------------

def encrypt_face(content_key: bytes, plaintext: bytes) -> tuple[str, bytes]:
    """Encrypt a selfie with the content key. Returns (face_hash, blob) where:
      - face_hash = SHA-256(plaintext) hex — the chain commitment (UNCHANGED by encryption)
      - blob      = nonce(12) || ciphertext || GCM-tag(16) — what POST /faces stores at rest

    AAD = the face_hash hex (UTF-8), binding the ciphertext to its content-address
    (facecrypto.js:58 — `const aad = new TextEncoder().encode(fh)`). AESGCM.encrypt appends
    the 16-byte tag to the ciphertext, so `nonce + ct` gives the WebCrypto wire layout exactly.
    """
    if len(content_key) != KEY_LEN:
        raise FaceWrapError(f"content key must be {KEY_LEN} bytes")
    fh = sha256_hex(plaintext)
    nonce = os.urandom(NONCE_LEN)
    ct = AESGCM(content_key).encrypt(nonce, plaintext, fh.encode("utf-8"))
    return fh, nonce + ct


def decrypt_face(content_key: bytes, blob: bytes, expected_face_hash: str) -> bytes:
    """Inverse of encrypt_face — provided for the parity test's PY-decrypt direction and for
    local self-checks. Mirrors facecrypto.js decryptFace (:69-88): AEAD-authenticate with
    AAD=expected_face_hash, THEN re-hash the plaintext and require it equals the face_hash."""
    if len(content_key) != KEY_LEN:
        raise FaceWrapError(f"content key must be {KEY_LEN} bytes")
    if len(blob) < _MIN_BLOB:
        raise FaceWrapError("blob too short")
    nonce, ct = blob[:NONCE_LEN], blob[NONCE_LEN:]
    try:
        plaintext = AESGCM(content_key).decrypt(nonce, ct, expected_face_hash.encode("utf-8"))
    except InvalidTag:
        raise FaceWrapError("authentication failed (wrong key, tampered blob, or AAD mismatch)")
    if sha256_hex(plaintext) != expected_face_hash:
        raise FaceWrapError("content-address mismatch: decrypted hash != expected face_hash")
    return plaintext


# ---------------------------------------------------------------------------
# wrap_key_with_doc_hash — mirror facecrypto.js wrapKeyWithDocHash (:126-136)
# This is the `#wk=` primitive: the KEK is the RAW doc-hash bytes (no KDF), NO AAD.
# ---------------------------------------------------------------------------

def _kek_from_doc_hash(doc_hash_hex: str) -> bytes:
    """The KEK = the raw bytes of the SHA-256 doc-hash, used directly as an AES-256 key.
    Mirrors facecrypto.js:128 `const kekRaw = hexToBytes(docHashHex)`. A 64-hex-char doc-hash
    yields exactly 32 bytes → AES-256. No stretch/KDF is applied (matching the JS)."""
    kek = bytes.fromhex(doc_hash_hex.strip())
    if len(kek) != KEY_LEN:
        raise FaceWrapError("doc_hash must be a 32-byte (64 hex char) SHA-256 to key the KEK")
    return kek


def wrap_key_with_doc_hash(content_key: bytes, doc_hash_hex: str) -> str:
    """Wrap the content key under the document hash → the b64url string carried in `#wk=`.

    Mirrors facecrypto.js wrapKeyWithDocHash (:126-136) byte-for-byte:
      kek   = raw doc-hash bytes (AES-256)                                 [:128]
      nonce = 12 random bytes                                              [:130]
      ct    = AES-GCM(kek).encrypt(nonce, content_key)  -- NO AAD          [:131]
      blob  = nonce || ct || tag                                          [:132-134]
      out   = bytes_to_b64url(blob)                                       [:135]

    Only a party holding the doc-hash can unwrap this, which is exactly the server-blindness
    property: the coordinator never receives the document (hash-only ceremony) and so can
    never recover CK from the wrapped key alone.
    """
    if len(content_key) != KEY_LEN:
        raise FaceWrapError(f"content key must be {KEY_LEN} bytes")
    kek = _kek_from_doc_hash(doc_hash_hex)
    nonce = os.urandom(NONCE_LEN)
    ct = AESGCM(kek).encrypt(nonce, content_key, None)  # NO AAD — matches the JS
    return bytes_to_b64url(nonce + ct)


def unwrap_key_with_doc_hash(wrapped_b64url: str, doc_hash_hex: str) -> bytes:
    """Inverse of wrap_key_with_doc_hash — mirrors facecrypto.js unwrapKeyWithDocHash
    (:138-152). Present for the parity test's PY-unwrap direction and for local self-checks."""
    blob = b64url_to_bytes(wrapped_b64url)
    if len(blob) < _MIN_BLOB:
        raise FaceWrapError("wrapped key too short")
    kek = _kek_from_doc_hash(doc_hash_hex)
    nonce, ct = blob[:NONCE_LEN], blob[NONCE_LEN:]
    try:
        content_key = AESGCM(kek).decrypt(nonce, ct, None)
    except InvalidTag:
        raise FaceWrapError("document hash incorrect or wrapped key invalid")
    if len(content_key) != KEY_LEN:
        raise FaceWrapError("unwrapped key must be 32 bytes")
    return content_key
