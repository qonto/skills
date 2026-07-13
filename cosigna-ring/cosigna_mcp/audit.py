"""Append-only, secret-redacting audit log for every MCP tool invocation.  # mcp harden

WHY THIS FILE EXISTS
--------------------
Production requirement: EVERY MCP tool call must leave a tamper-evident trail — who called
what, when, with which (redacted) arguments, and whether it succeeded. An AI agent drives this
connector; an audit log is the record of what the agent actually did on the founder's session.

THE HARD CONSTRAINT — the log must NEVER contain a secret.
A signer link is a bearer capability (`?t=` token + `#wk=` wrapped content key); the session
bearer token, the raw content key (CK), and the encrypted selfie blob are all secrets. If any of
these landed in a plaintext log file, the log would become the very leak the connector's F7/F8
gates exist to prevent. So this module redacts BEFORE writing, on two independent layers:

  1. key-name denylist — any dict key whose (lower-cased) name matches a secret concept is
     replaced with "<redacted:key>" regardless of value;
  2. value scrubbing — any *string* value is scanned for capability substrings (`?t=…`,
     `#wk=…`, `Bearer …`, long hex/b64url runs that look like tokens) and the sensitive span
     is masked, so a secret that arrives under an innocuous key is still caught.

Return values are NEVER dumped wholesale (they carry signer_links). The caller logs a distilled,
secret-free OUTCOME summary instead (ok / cid / status / redacted-error / returned-key-names).

Layout: one JSON object per line (JSONL), append-only, file created 0600 (owner-only) up front so
a capability substring is never briefly world-readable. Overridable via COSIGNA_MCP_AUDIT_LOG.
Stdlib only.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any

# ── configuration ─────────────────────────────────────────────────────────────

AUDIT_PATH = Path(
    os.environ.get(
        "COSIGNA_MCP_AUDIT_LOG",
        os.path.join(os.path.expanduser("~"), ".cosigna_mcp_audit.jsonl"),
    )
)

# Set COSIGNA_MCP_AUDIT_DISABLE=1 only in tests that assert on the returned record directly.
_DISABLED = os.environ.get("COSIGNA_MCP_AUDIT_DISABLE", "").strip() in {"1", "true", "yes"}

_write_lock = threading.Lock()
_warned_write_fail = False

# ── redaction ─────────────────────────────────────────────────────────────────

# Any dict key whose lower-cased name CONTAINS one of these is fully redacted by name.
_SECRET_KEY_MARKERS = (
    "token",        # session_token, initiator_token, signer_tokens, X-COSIGNA-Token
    "wrapped_wk",
    "wrapped",
    "wk",
    "blob",
    "ciphertext",
    "content_key",
    "ck",
    "secret",
    "password",
    "authorization",
    "bearer",
    "cookie",
    "signer_link",
    "self_sign_link",
    "capability_link",
    "email",          # MCPSEC-014 — participant emails are PII; keep them out of the log
)

# Value-level scrubbers: mask a capability span even if it arrives under an innocuous key.
_VALUE_SCRUBBERS = (
    # signer-link capability token: ...?t=<tok>  (until the fragment or an ampersand)
    (re.compile(r"([?&]t=)[^&#\s]+"), r"\1<redacted:capability-token>"),
    # wrapped content key in the URL fragment: #wk=<b64url>
    (re.compile(r"(#wk=)[^&\s]+"), r"\1<redacted:wrapped-key>"),
    # Authorization: Bearer <tok>
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]+"), r"\1<redacted:bearer>"),
)

# A bare long token-ish run (hex or b64url, >=32 chars) that is not obviously a doc-hash context.
# doc_hash (exactly 64 lowercase hex) is PUBLIC and intentionally preserved (it is the contract),
# so we only mask runs of >=40 chars that are NOT a clean 64-hex doc-hash.
# Boundaries are EXPLICIT ASCII lookarounds, not `\b`: Python `re` counts accented-Latin/CJK as \w,
# so a `\b` would not fire at the junction between a unicode letter and an ASCII token and the token
# would leak (GAP-2, 2026-07-10 audit — reachable via FR/DE strings + server error text in the log).
_LONE_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_\-])[A-Za-z0-9_\-]{40,}(?![A-Za-z0-9_\-])")
_DOC_HASH_RE = re.compile(r"^[0-9a-f]{64}$")

_MAX_STR = 256  # never write an over-long string into the log


def _scrub_string(s: str) -> str:
    for pat, repl in _VALUE_SCRUBBERS:
        s = pat.sub(repl, s)

    def _mask_lone(m: "re.Match[str]") -> str:
        tok = m.group(0)
        if _DOC_HASH_RE.match(tok):
            return tok  # a clean doc-hash is public — keep it
        return "<redacted:token-like>"

    s = _LONE_TOKEN_RE.sub(_mask_lone, s)
    if len(s) > _MAX_STR:
        s = s[:_MAX_STR] + "…(truncated)"
    return s


def redact(value: Any, _key: str = "") -> Any:
    """Recursively redact a value for logging. Never returns a secret. `_key` is the name this
    value sits under (used for the key-name denylist)."""
    kl = (_key or "").lower()
    if any(m in kl for m in _SECRET_KEY_MARKERS):
        return "<redacted:key>"
    if isinstance(value, dict):
        # Scrub the KEY string too (GAP-1, 2026-07-10 audit): a secret sitting in key position
        # (not just as a value) must not be emitted verbatim. `_scrub_string` leaves ordinary
        # short field names untouched but masks a token-like / capability-bearing key.
        return {_scrub_string(str(k)): redact(v, _key=str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v, _key=_key) for v in value]
    if isinstance(value, str):
        return _scrub_string(value)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    # bytes / anything else: never log the value, only its type + length.
    try:
        n = len(value)  # type: ignore[arg-type]
    except TypeError:
        n = None
    return f"<{type(value).__name__}{'' if n is None else f' len={n}'}>"


# ── writing ───────────────────────────────────────────────────────────────────

def _append(record: dict) -> None:
    """Append one JSONL record with owner-only (0600) permissions, best-effort (auditing must
    never crash a tool call — a failed write is swallowed, never raised)."""
    if _DISABLED:
        return
    try:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Open with O_APPEND and mode 0600. If the file already exists with looser perms, tighten.
        fd = os.open(str(AUDIT_PATH), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(fd, (json.dumps(record, ensure_ascii=False, default=str) + "\n").encode("utf-8"))
        finally:
            os.close(fd)
        try:
            os.chmod(str(AUDIT_PATH), 0o600)
        except OSError:
            pass
    except OSError:
        global _warned_write_fail
        if not _warned_write_fail:
            _warned_write_fail = True
            import sys
            print("[cosigna-mcp] WARNING: audit log write failed — the tamper-evident trail is "
                  "degraded for this session.", file=sys.stderr)


_seq = 0
_seq_lock = threading.Lock()


def _next_seq() -> int:
    global _seq
    with _seq_lock:
        _seq += 1
        return _seq


def log_event(tool: str, args: dict, outcome: dict, duration_ms: float) -> dict:
    """Build, write, and return one audit record. `args` and `outcome` are redacted here — the
    caller passes raw values and trusts this function to scrub. Returns the (redacted) record so
    callers/tests can assert on it."""
    record = {
        "ts": round(time.time(), 3),
        "seq": _next_seq(),
        "tool": tool,
        "args": redact(args or {}),
        "outcome": redact(outcome or {}),
        "duration_ms": round(duration_ms, 2),
        "pid": os.getpid(),
    }
    with _write_lock:
        _append(record)
    return record
