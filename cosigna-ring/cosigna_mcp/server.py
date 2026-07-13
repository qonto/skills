"""COSIGNA MCP server — 7 tools that let a Claude agent drive a signature ceremony.  # mcp D1

Transport: local stdio (the document NEVER leaves the user's machine — only its SHA-256).
Auth: an existing COSIGNA bearer session (F6) read from env COSIGNA_SESSION_TOKEN; sent as
`Authorization: Bearer` on every call. Startup HARD-FAILS with a re-mint recipe if the token
is missing or rejected.

Server-blindness (the product's core claim, preserved here):
  - hash_document reads bytes LOCALLY and returns only the SHA-256 — bytes are never uploaded.
  - the selfie is encrypted LOCALLY with a generated content key (facewrap, byte-compatible
    with the frozen browser JS) before POST /faces; the content key never leaves this process
    except WRAPPED inside each signer link's `#wk=` fragment — a fragment the server never
    receives. The wrap KEK is the document's PUBLIC SHA-256 (the server is even given it in the
    /ceremonies payload), so the consent photos' confidentiality rests on the SECRECY OF THE
    `#wk=` LINK FRAGMENT, not on holding the document.

Abuse gates (F8 — ENFORCED, not advisory): dry-run-by-default + confirm=true second phase,
participant cap, an opens/notarize budget per process, a founder-domain email allowlist, and
a hard refusal when no session is configured. See README.md.

Capability-link secrecy (F7): every output that returns a signer link carries the
CAPABILITY-LINK BANNER; evidence_note returns PUBLIC data only (never `?t=` / `#wk`), asserted
by tests/test_evidence_note_no_secrets.py.
"""
from __future__ import annotations

import functools
import inspect
import json
import os
import re
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

import httpx
from mcp.server.fastmcp import FastMCP

from . import audit, facewrap, ratelimit

# ── configuration (all from env; no secrets in code) ──────────────────────────

BASE_URL = os.environ.get("COSIGNA_MCP_BASE_URL", "https://cosigna.eu").rstrip("/")
SESSION_TOKEN = os.environ.get("COSIGNA_SESSION_TOKEN", "").strip()

# F8 abuse controls
MAX_PARTICIPANTS_DEMO = int(os.environ.get("COSIGNA_MCP_MAX_PARTICIPANTS", "4"))
MAX_OPENS = int(os.environ.get("COSIGNA_MCP_MAX_OPENS", "3"))
# Comma-separated allowlist of email domains the connector may invite. Empty = refuse ALL
# outbound-email participants (safe default — the founder must opt in explicitly).
_allowed = os.environ.get("COSIGNA_MCP_ALLOWED_DOMAINS", "").strip()
ALLOWED_DOMAINS = {d.strip().lower() for d in _allowed.split(",") if d.strip()}

# Local 0600 state file — persists capability tokens (NOT re-derivable) keyed by cid, so
# status/proof survive a restart. Overridable for tests via COSIGNA_MCP_STATE.
STATE_PATH = Path(
    os.environ.get(
        "COSIGNA_MCP_STATE",
        os.path.join(os.path.expanduser("~"), ".cosigna_mcp_state.json"),
    )
)

HTTP_TIMEOUT = float(os.environ.get("COSIGNA_MCP_HTTP_TIMEOUT", "30"))
# MCPSEC-003: cap the selfie size read into memory before encryption (whole-file read).
MAX_SELFIE_BYTES = int(os.environ.get("COSIGNA_MCP_MAX_SELFIE_BYTES", str(15 * 1024 * 1024)))
# MCPSEC-004: cap the size of any HTTP response body the connector will parse. A malicious or
# broken server could otherwise return a multi-GB body and force `r.json()` to buffer it into
# memory (a DoS + a prompt-injection amplification surface, since the body is echoed to the
# agent). Default 2 MB — comfortably above every real COSIGNA payload (incl. the largest snapshot).
MAX_RESPONSE_BYTES = int(os.environ.get("COSIGNA_MCP_MAX_RESPONSE_BYTES", str(2 * 1024 * 1024)))

_CID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
# A participant / signer id: URL- and roster-safe, bounded. Anything else is rejected before it
# can reach a capability link path or the server roster.
_PID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
# Basic, conservative email shape — a real deliverability check is out of scope; this only rejects
# obviously malformed values before the domain-allowlist gate sees them.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# Ids the connector reserves for the initiator/self role — a participant may not claim them.
_RESERVED_IDS = {"initiator", "self"}

# The capability-link banner — attached verbatim to every link-returning output (F7).
CAPABILITY_LINK_BANNER = (
    "CAPABILITY LINKS — anyone with a link can sign as that participant and view this "
    "ceremony's consent photos. Deliver each link to its signer out-of-band; do not paste "
    "back into chat."
)

# Runtime open/notarize budget (F8) — process-scoped, resets when the server restarts.
_opens_used = 0


# ── state persistence (0600) ──────────────────────────────────────────────────

def _load_state() -> dict:
    try:
        if STATE_PATH.exists():
            return json.loads(STATE_PATH.read_text() or "{}")
    except Exception:
        pass
    return {}


def _save_state(state: dict) -> None:
    """Write the state file with owner-only (0600) permissions — it holds capability tokens."""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(STATE_PATH.suffix + ".tmp")
    # Create the temp file 0600 up front so tokens are never briefly world-readable.
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(str(tmp), str(STATE_PATH))
    try:
        os.chmod(str(STATE_PATH), 0o600)
    except OSError:
        pass


_state_lock = threading.Lock()


def _remember_ceremony(cid: str, record: dict) -> None:
    # MCPSEC-007: serialize the load-modify-save so concurrent opens cannot lose a record.
    with _state_lock:
        state = _load_state()
        state.setdefault("ceremonies", {})[cid] = record
        _save_state(state)


def _recall_ceremony(cid: str) -> Optional[dict]:
    return _load_state().get("ceremonies", {}).get(cid)


# ── HTTP client + auth ────────────────────────────────────────────────────────

def _validate_base_url(url: str) -> None:
    """MCPSEC-001: the bearer session rides on EVERY request, so refuse a non-TLS base URL
    (only https://, or http://localhost for dev/tests) — an http:// or repointed host would
    leak the founder's 30-day session on the first call."""
    from urllib.parse import urlparse
    u = urlparse(url or "")
    host = (u.hostname or "").lower()
    if u.scheme == "https":
        return
    if u.scheme == "http" and host in {"localhost", "127.0.0.1", "::1"}:
        return
    raise AuthError(
        f"refusing COSIGNA_MCP_BASE_URL={url!r}: the bearer session is attached to every request, "
        "so only https:// (or http://localhost for dev) is permitted.")


def _client() -> httpx.Client:
    _validate_base_url(BASE_URL)
    headers = {"Accept": "application/json"}
    if SESSION_TOKEN:
        headers["Authorization"] = f"Bearer {SESSION_TOKEN}"
    return httpx.Client(base_url=BASE_URL, headers=headers, timeout=HTTP_TIMEOUT)


_REMINT_RECIPE = (
    "No valid COSIGNA session. Mint one and set COSIGNA_SESSION_TOKEN in the Claude Desktop "
    "config env block, then restart:\n"
    "  1) curl -s -X POST {base}/auth/request-link -H 'Content-Type: application/json' "
    "-d '{{\"email\":\"you@founder-domain\"}}'\n"
    "  2) open the emailed link's token, then:\n"
    "     curl -s '{base}/auth/verify-link?token=<TOKEN>' -H 'Accept: application/json'\n"
    "  3) copy session_token → env COSIGNA_SESSION_TOKEN (30-day TTL)."
).format(base=BASE_URL)


class AuthError(RuntimeError):
    pass


def _preflight_auth() -> dict:
    """Verify the session at startup (F6). HARD-FAIL with the re-mint recipe on 401/missing.
    Returns the /auth/me profile on success."""
    if not SESSION_TOKEN:
        raise AuthError("COSIGNA_SESSION_TOKEN is not set.\n" + _REMINT_RECIPE)
    try:
        with _client() as c:
            r = c.get("/auth/me")
    except httpx.HTTPError as e:
        raise AuthError(f"could not reach COSIGNA at {BASE_URL}: {e}")
    if r.status_code == 401:
        raise AuthError("COSIGNA session is invalid or expired (401).\n" + _REMINT_RECIPE)
    if r.status_code != 200:
        raise AuthError(f"unexpected /auth/me status {r.status_code}: {r.text[:200]}")
    return r.json()


def _require_auth() -> None:
    """Per-call guard (F8 'refuse if no session'): fail fast when the token is absent."""
    if not SESSION_TOKEN:
        raise AuthError("refusing: no COSIGNA session configured.\n" + _REMINT_RECIPE)


# ── small helpers ─────────────────────────────────────────────────────────────

def _err(msg: str) -> dict:
    return {"ok": False, "error": msg}


def _oversize_response(r: Any) -> Optional[str]:
    """MCPSEC-004: reject an over-large server body BEFORE it is parsed with `r.json()`, so a
    malicious/huge response can't be buffered into memory (DoS) or echoed to the agent. Checks the
    advertised `content-length` when present AND the actual bytes already read. Returns an error
    string if the body exceeds MAX_RESPONSE_BYTES, else None (a response object with no
    headers/content — e.g. a test double — is treated as within bounds)."""
    headers = getattr(r, "headers", None)
    if headers is not None:
        try:
            cl = headers.get("content-length")
        except AttributeError:
            cl = None
        if cl is not None:
            try:
                if int(cl) > MAX_RESPONSE_BYTES:
                    return (f"server response too large (content-length {cl} bytes > cap "
                            f"{MAX_RESPONSE_BYTES}; COSIGNA_MCP_MAX_RESPONSE_BYTES) — refusing to parse.")
            except (TypeError, ValueError):
                pass
    body = getattr(r, "content", None)
    if body is not None:
        try:
            n = len(body)
        except TypeError:
            n = None
        if n is not None and n > MAX_RESPONSE_BYTES:
            return (f"server response too large ({n} bytes > cap {MAX_RESPONSE_BYTES}; "
                    "COSIGNA_MCP_MAX_RESPONSE_BYTES) — refusing to parse.")
    return None


def _sniff_filename(path: str) -> str:
    return Path(path).name


def _domain_of(email: str) -> str:
    return email.rsplit("@", 1)[-1].strip().lower() if "@" in email else ""


def _check_email_allowlist(emails: list[str]) -> Optional[str]:
    """Return an error string if any email is outside the allowlist (F8), else None."""
    if not emails:
        return None
    if not ALLOWED_DOMAINS:
        return (
            "refusing to email participants: COSIGNA_MCP_ALLOWED_DOMAINS is empty. Set it to a "
            "comma-separated founder-domain allowlist to enable invitations."
        )
    bad = [e for e in emails if _domain_of(e) not in ALLOWED_DOMAINS]
    if bad:
        return (
            "refusing to email outside the allowlist "
            f"({sorted(ALLOWED_DOMAINS)}): {bad}"
        )
    return None


def _signer_link(cid: str, signer_id: str, token: str, wrapped_wk: str) -> str:
    """Build the capability link locally — matches service.dispatch_invitations:884
    (`/sign/{cid}/{signer_id}?t={token}`) plus the `#wk=` fragment the browser unwraps
    with the doc-hash. The fragment is client-only (never sent to the server)."""
    return f"{BASE_URL}/sign/{cid}/{signer_id}?t={token}#wk={wrapped_wk}"


def _public_verify_url(cid: str) -> str:
    """The PUBLIC, keyless verify entry — hash-only, no `?t=`/`#wk`."""
    return f"{BASE_URL}/verify?cid={cid}"


# ── input validation (hardening) ──────────────────────────────────────────────

def _sanitize_filename(name: str) -> str:
    """A document filename is caller-supplied metadata that gets stored + echoed. Strip any path
    component and control characters, and bound the length — it must never be able to carry a path
    traversal, a newline (log/line injection), or an unbounded blob into the server or the audit
    log. Returns the safe basename (never empty)."""
    base = Path(str(name or "")).name  # drops any dir component ('../', absolute paths, etc.)
    base = "".join(ch for ch in base if ch.isprintable() and ch not in "\r\n\t")
    base = base.strip()[:255]
    return base or "document.pdf"


def _validate_participants(participants: list[str]) -> Optional[str]:
    """Return an error string if any participant id is malformed / reserved / duplicated, else None."""
    for pid in participants:
        if not _PID_RE.match(pid):
            return (f"invalid participant id {pid!r}: must be 1–64 chars of "
                    "[A-Za-z0-9_-] (URL/roster-safe).")
        if pid.lower() in _RESERVED_IDS:
            return f"participant id {pid!r} is reserved (the initiator/self role owns it)."
    return None


# ── instrumentation: per-tool rate limit + audit log around every tool ─────────

def _summarize_outcome(ret: Any) -> dict:
    """Distil a tool's return value into a SECRET-FREE outcome summary for the audit log. Never
    dumps the full dict — that would carry signer_links / self_sign_link. Only safe scalars +
    the set of returned key names. (audit.redact scrubs this again as belt-and-braces.)"""
    if not isinstance(ret, dict):
        return {"type": type(ret).__name__}
    summary: dict = {"ok": ret.get("ok"), "returned_keys": sorted(ret.keys())}
    for k in ("error", "ceremony_id", "status", "dry_run", "closed", "signed_count",
              "participant_count", "anchored", "public_only", "label", "authenticity",
              "doc_hash_match", "checks"):
        if k in ret:
            summary[k] = ret[k]
    return summary


def _instrument(tool_name: str) -> Callable:
    """Wrap a tool with (1) a per-tool sliding-window rate limit and (2) an audit-log record of
    every invocation + outcome. functools.wraps preserves the wrapped signature + docstring so
    FastMCP still introspects the correct tool schema."""
    def deco(fn: Callable) -> Callable:
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                arg_snapshot = dict(bound.arguments)
            except TypeError:
                arg_snapshot = {"_args": list(args), "_kwargs": dict(kwargs)}

            # (1) rate limit — reject before any work / any network call.
            try:
                ratelimit.check(tool_name)
            except ratelimit.RateLimitError as e:
                ret = _err(str(e))
                audit.log_event(tool_name, arg_snapshot,
                                {"ok": False, "error": str(e), "rate_limited": True},
                                (time.time() - start) * 1000)
                return ret

            # (2) run the tool; a tool must never crash the server — convert to a clean error.
            try:
                ret = fn(*args, **kwargs)
            except Exception as e:  # noqa: BLE001 — defensive boundary around every tool
                ret = _err(f"internal error in {tool_name}: {audit._scrub_string(str(e))}")

            audit.log_event(tool_name, arg_snapshot, _summarize_outcome(ret),
                            (time.time() - start) * 1000)
            return ret

        return wrapper
    return deco


# ── the MCP server + tools ────────────────────────────────────────────────────

mcp = FastMCP(
    "cosigna",
    instructions=(
        "Drive COSIGNA async signature ceremonies. The document stays on this machine — only "
        "its SHA-256 hash is sent. Signer links are capabilities: whoever holds one can sign as "
        "that participant. Deliver links out-of-band; never paste them back into chat. COSIGNA "
        "does NOT verify identity — signatures are self-declared; the proof is court EVIDENCE "
        "(evidentiary robustness), not legal enforceability or identity."
    ),
)


@mcp.tool()
@_instrument("hash_document")
def hash_document(path: str) -> dict:
    """Compute the SHA-256 of a LOCAL document, on this machine. The bytes are read locally and
    NEVER uploaded — this is the server-blindness proof point. Returns the hex hash + filename."""
    p = Path(path).expanduser()
    if not p.is_file():
        return _err(f"no such file: {p}")
    try:
        h = facewrap.hashlib.sha256()  # reuse the module's hashlib (stdlib)
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        doc_hash = h.hexdigest()
    except OSError as e:
        return _err(f"could not read {p}: {e}")
    return {
        "ok": True,
        "doc_hash": doc_hash,
        "doc_filename": p.name,
        "size_bytes": p.stat().st_size,
        "note": "hashed locally; the document bytes were NOT uploaded.",
    }


def _looks_like_image(data: bytes) -> bool:
    """Magic-byte gate matching the server's accepted selfie types (JPEG/PNG/WebP). The connector
    encrypts the selfie LOCALLY and uploads only ciphertext, so the server can no longer reject a
    non-image — which means an agent could otherwise point *_selfie_path at ANY local file and have
    the connector encrypt-and-upload it as a 'selfie' (a decryptable exfiltration channel for
    whoever holds the link + doc-hash). This check keeps the E2E path honest: selfie in, selfie out."""
    if len(data) < 12:
        return False
    if data[:3] == b"\xff\xd8\xff":                       # JPEG
        return True
    if data[:8] == b"\x89PNG\r\n\x1a\n":                    # PNG
        return True
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":       # WebP
        return True
    return False


def _encrypt_selfie_local(doc_hash: str, selfie_path: str) -> dict:
    """Generate a content key (CK), encrypt the selfie with it locally, and wrap CK under the
    doc-hash. Returns {ck, face_hash, blob, wrapped_wk}. Raises on bad input."""
    p = Path(selfie_path).expanduser()
    if not p.is_file():
        raise FileNotFoundError(f"no such selfie file: {p}")
    try:
        _size = p.stat().st_size
    except OSError as e:
        raise facewrap.FaceWrapError(f"cannot stat selfie {p.name}: {e}")
    if _size > MAX_SELFIE_BYTES:
        raise facewrap.FaceWrapError(
            f"{p.name} is {_size} bytes > cap {MAX_SELFIE_BYTES} (COSIGNA_MCP_MAX_SELFIE_BYTES) — "
            "refusing to load a selfie that large into memory.")
    plaintext = p.read_bytes()
    if not _looks_like_image(plaintext):
        raise facewrap.FaceWrapError(
            f"{p.name} is not a JPEG/PNG/WebP image — refusing to encrypt-and-upload a "
            "non-image as a selfie (the E2E path can't be validated server-side).")
    ck = facewrap.generate_content_key()
    face_hash, blob = facewrap.encrypt_face(ck, plaintext)
    wrapped_wk = facewrap.wrap_key_with_doc_hash(ck, doc_hash)
    return {"ck": ck, "face_hash": face_hash, "blob": blob, "wrapped_wk": wrapped_wk}


def _post_face(client: httpx.Client, cid: str, subject_id: str, token: str,
               face_hash: str, blob: bytes, *, as_initiator: bool) -> None:
    """POST /faces enc=aesgcm — upload the encrypted selfie blob. The token rides in the
    X-COSIGNA-Token header (never in the URL — P1 hardening, server.py:2809)."""
    data = {"enc": "aesgcm", "face_hash": face_hash, "cid": cid}
    if not as_initiator:
        data["signer_id"] = subject_id
    files = {"file": ("selfie.enc", blob, "application/octet-stream")}
    r = client.post("/faces", data=data, files=files, headers={"X-COSIGNA-Token": token})
    if r.status_code == 409:
        raise RuntimeError(
            "POST /faces returned 409 (a different blob already exists at this hash). In "
            "rehearsals, use a distinct selfie per ceremony — identical plaintext across "
            "ceremonies collides on the content-address."
        )
    if r.status_code >= 400:
        raise RuntimeError(f"POST /faces failed {r.status_code}: {r.text[:200]}")


@mcp.tool()
@_instrument("open_ceremony")
def open_ceremony(
    doc_hash: str,
    doc_filename: str,
    participants: list[str],
    initiator_selfie_path: str,
    participant_emails: Optional[dict] = None,
    consent_required: bool = False,
    dry_run: bool = True,
    confirm: bool = False,
) -> dict:
    """Open a signature ceremony for a document identified ONLY by its hash.

    Pipeline (only when confirm=True): (a) encrypt the initiator selfie locally with a fresh
    content key + wrap that key under the doc-hash; (b) POST /ceremonies (anchor_enabled=TRUE
    always — F10); (c) POST /faces the encrypted initiator blob; (d) POST /open with the
    initiator face-hash. Returns the cid + one capability link per signer:
    `…/sign/{cid}/{sid}?t={tok}#wk={wrapped}` (built locally; the `#wk=` fragment is never sent
    to the server).

    ABUSE GATES (F8, ENFORCED): dry_run defaults TRUE and returns the would-be payload WITHOUT
    sending; only confirm=True actually sends. participants are capped at the demo limit; there
    is an opens budget per process; a session is required; and emailing a participant outside
    COSIGNA_MCP_ALLOWED_DOMAINS is refused.

    participant_emails (optional): {signer_id: email} for out-of-band invitation dispatch. Every
    address must fall inside the allowlist. If omitted, the connector returns the links for you to
    deliver by hand (the recommended, most private path).
    """
    global _opens_used
    try:
        _require_auth()
    except AuthError as e:
        return _err(str(e))

    doc_hash = (doc_hash or "").strip().lower()
    if not _HASH_RE.match(doc_hash):
        return _err("doc_hash must be a 64-char lowercase SHA-256 hex (use hash_document first).")
    participants = [str(p).strip() for p in (participants or []) if str(p).strip()]
    if not participants:
        return _err("at least one participant (COSignee) id is required.")
    if len(participants) != len(set(participants)):
        return _err("participant ids must be distinct.")
    if len(participants) > MAX_PARTICIPANTS_DEMO:
        return _err(f"demo mode caps participants at {MAX_PARTICIPANTS_DEMO} "
                    f"(got {len(participants)}); set COSIGNA_MCP_MAX_PARTICIPANTS to change.")
    pid_err = _validate_participants(participants)
    if pid_err:
        return _err(pid_err)

    # Caller-supplied filename is stored + echoed — sanitize it (no path/control chars).
    doc_filename = _sanitize_filename(doc_filename)

    emails = participant_emails or {}
    if not isinstance(emails, dict):
        return _err("participant_emails must be a {signer_id: email} object.")
    # Every email key must name an actual participant (no emailing an unrelated address).
    stray = [k for k in emails if k not in participants]
    if stray:
        return _err(f"participant_emails has keys that are not participants: {sorted(stray)}.")
    email_list = [v for v in emails.values() if isinstance(v, str) and v.strip()]
    malformed = [e for e in email_list if not _EMAIL_RE.match(e)]
    if malformed:
        return _err(f"malformed email address(es): {sorted(malformed)}.")
    allow_err = _check_email_allowlist(email_list)
    if allow_err and email_list:
        return _err(allow_err)

    initiator_id = "initiator"
    would_be = {
        "endpoint": f"POST {BASE_URL}/ceremonies",
        "payload": {
            "initiator_id": initiator_id,
            "participant_ids": participants,
            "doc_hash": doc_hash,
            "doc_filename": doc_filename,
            "self_notarization": False,
            "anchor_enabled": True,  # F10 — the connector always anchors
            "consent_required": bool(consent_required),
            "participant_emails": {k: v for k, v in emails.items()} or None,
        },
        "then": ["POST /faces (encrypted initiator selfie)", f"POST /ceremonies/<cid>/open"],
        "will_email": sorted(email_list) if email_list else [],
    }

    if dry_run and not confirm:
        return {
            "ok": True,
            "dry_run": True,
            "would_do": would_be,
            "note": ("DRY RUN — nothing sent. Re-call with confirm=True to open the ceremony. "
                     "The document hash is sent; the document bytes are not."),
        }

    if not confirm:
        return _err("refusing to send: pass confirm=True to actually open the ceremony.")

    # Budget check happens only on a real send.
    if _opens_used >= MAX_OPENS:
        return _err(f"opens budget exhausted ({MAX_OPENS} per process). Restart the server or "
                    f"raise COSIGNA_MCP_MAX_OPENS.")

    # (a) encrypt the initiator selfie locally.
    try:
        env = _encrypt_selfie_local(doc_hash, initiator_selfie_path)
    except (FileNotFoundError, facewrap.FaceWrapError) as e:
        return _err(f"initiator selfie encryption failed: {e}")

    try:
        with _client() as c:
            # (b) create the ceremony.
            create_payload = {
                "initiator_id": initiator_id,
                "participant_ids": participants,
                "doc_hash": doc_hash,
                "doc_filename": doc_filename,
                "self_notarization": False,
                "anchor_enabled": True,  # F10
                "consent_required": bool(consent_required),
            }
            if emails:
                create_payload["participant_emails"] = {
                    k: v for k, v in emails.items() if isinstance(v, str) and "@" in v
                }
            rc = c.post("/ceremonies", json=create_payload)
            if rc.status_code >= 400:
                return _err(f"POST /ceremonies failed {rc.status_code}: {rc.text[:300]}")
            oversize = _oversize_response(rc)  # MCPSEC-004
            if oversize:
                return _err(oversize)
            created = rc.json()
            cid = created["ceremony_id"]
            initiator_token = created["initiator_token"]
            signer_tokens = created.get("signer_tokens", {})
            if not _CID_RE.match(str(cid or "")):
                return _err("server returned an invalid ceremony id; refusing to proceed.")
            # MCPSEC-006: persist non-re-derivable tokens BEFORE /faces + /open so a later
            # failure cannot orphan the ceremony (status/proof stay drivable).
            _remember_ceremony(cid, {
                "cid": cid, "doc_hash": doc_hash, "doc_filename": doc_filename,
                "initiator_id": initiator_id, "initiator_token": initiator_token,
                "signer_tokens": signer_tokens, "self_notarization": False,
                "created_ts": int(time.time()),
            })

            # (c) upload the encrypted initiator selfie.
            _post_face(c, cid, initiator_id, initiator_token,
                       env["face_hash"], env["blob"], as_initiator=True)

            # (d) open with the initiator face-hash.
            ro = c.post(f"/ceremonies/{cid}/open",
                        json={"initiator_face_hash": env["face_hash"]},
                        headers={"X-COSIGNA-Token": initiator_token})
            if ro.status_code >= 400:
                return _err(f"POST /ceremonies/{cid}/open failed {ro.status_code}: {ro.text[:300]}")
            oversize = _oversize_response(ro)  # MCPSEC-004
            if oversize:
                return _err(oversize)
            status = ro.json().get("status")
    except (httpx.HTTPError, RuntimeError, KeyError) as e:
        return _err(f"open pipeline failed: {e}")

    _opens_used += 1

    # Build the capability links locally (wrapped key in the fragment). The ceremony record was
    # already persisted BEFORE /faces+/open (MCPSEC-006), field-identical to what a trailing write
    # would produce, so no second _remember_ceremony is needed here (MCPSEC-006 follow-up).
    links = {
        sid: _signer_link(cid, sid, tok, env["wrapped_wk"])
        for sid, tok in signer_tokens.items()
    }

    return {
        "ok": True,
        "capability_link_banner": CAPABILITY_LINK_BANNER,
        "ceremony_id": cid,
        "status": status,
        "anchored": True,
        "signer_links": links,
        "emailed": would_be["will_email"],
        "public_verify_url": _public_verify_url(cid),
        "note": ("Ceremony OPEN. Deliver each signer link out-of-band. The document bytes were "
                 "never uploaded — only the hash. Close is BY HUMAN HAND (no auto-close)."),
    }


@mcp.tool()
@_instrument("notarize_document")
def notarize_document(
    path: str,
    selfie_path: str,
    dry_run: bool = True,
    confirm: bool = False,
) -> dict:
    """Self-notarize (COAutoCert): create a self_notarization ceremony + open it, then RETURN
    the self-sign link for the founder's OWN phone. COAutoCert is two-device by definition — the
    human completes on their second device; this tool NEVER auto-closes (F3). Same dry-run/confirm
    and opens-budget gates as open_ceremony. The document is hashed locally; bytes are not uploaded.
    """
    global _opens_used
    try:
        _require_auth()
    except AuthError as e:
        return _err(str(e))

    p = Path(path).expanduser()
    if not p.is_file():
        return _err(f"no such document: {p}")
    try:
        h = facewrap.hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        doc_hash = h.hexdigest()
    except OSError as e:
        return _err(f"could not read {p}: {e}")

    self_signer = "self"
    would_be = {
        "endpoint": f"POST {BASE_URL}/ceremonies (self_notarization=True, anchor_enabled=True)",
        "doc_hash": doc_hash,
        "doc_filename": p.name,
        "then": ["POST /faces (encrypted initiator selfie)", "POST /open", "RETURN self-sign link"],
    }
    if dry_run and not confirm:
        return {"ok": True, "dry_run": True, "would_do": would_be,
                "note": "DRY RUN — nothing sent. Re-call with confirm=True to create the self-notarization."}
    if not confirm:
        return _err("refusing to send: pass confirm=True to create the self-notarization.")
    if _opens_used >= MAX_OPENS:
        return _err(f"opens budget exhausted ({MAX_OPENS} per process).")

    try:
        env = _encrypt_selfie_local(doc_hash, selfie_path)
    except (FileNotFoundError, facewrap.FaceWrapError) as e:
        return _err(f"selfie encryption failed: {e}")

    try:
        with _client() as c:
            rc = c.post("/ceremonies", json={
                "initiator_id": self_signer,
                "participant_ids": [self_signer],
                "doc_hash": doc_hash,
                "doc_filename": p.name,
                "self_notarization": True,
                "anchor_enabled": True,  # F10
            })
            if rc.status_code >= 400:
                return _err(f"POST /ceremonies failed {rc.status_code}: {rc.text[:300]}")
            oversize = _oversize_response(rc)  # MCPSEC-004
            if oversize:
                return _err(oversize)
            created = rc.json()
            cid = created["ceremony_id"]
            initiator_token = created["initiator_token"]
            signer_tokens = created.get("signer_tokens", {})
            if not _CID_RE.match(str(cid or "")):
                return _err("server returned an invalid ceremony id; refusing to proceed.")
            # MCPSEC-006: persist tokens before /faces + /open (see open_ceremony).
            _remember_ceremony(cid, {
                "cid": cid, "doc_hash": doc_hash, "doc_filename": p.name,
                "initiator_id": self_signer, "initiator_token": initiator_token,
                "signer_tokens": signer_tokens, "self_notarization": True,
                "created_ts": int(time.time()),
            })

            _post_face(c, cid, self_signer, initiator_token,
                       env["face_hash"], env["blob"], as_initiator=True)

            ro = c.post(f"/ceremonies/{cid}/open",
                        json={"initiator_face_hash": env["face_hash"]},
                        headers={"X-COSIGNA-Token": initiator_token})
            if ro.status_code >= 400:
                return _err(f"POST /ceremonies/{cid}/open failed {ro.status_code}: {ro.text[:300]}")
            oversize = _oversize_response(ro)  # MCPSEC-004
            if oversize:
                return _err(oversize)
            status = ro.json().get("status")
    except (httpx.HTTPError, RuntimeError, KeyError) as e:
        return _err(f"notarize pipeline failed: {e}")

    _opens_used += 1

    # The record was already persisted BEFORE /faces+/open (MCPSEC-006), field-identical to a
    # trailing write, so no second _remember_ceremony is needed here (MCPSEC-006 follow-up).
    self_tok = signer_tokens.get(self_signer)
    self_link = _signer_link(cid, self_signer, self_tok, env["wrapped_wk"]) if self_tok else None

    return {
        "ok": True,
        "capability_link_banner": CAPABILITY_LINK_BANNER,
        "ceremony_id": cid,
        "status": status,
        "anchored": True,
        "self_sign_link": self_link,
        "public_verify_url": _public_verify_url(cid),
        "note": ("Self-notarization OPEN. Open the self-sign link on your SECOND device to "
                 "complete — this tool does NOT auto-close (COAutoCert is two-device by design)."),
    }


@mcp.tool()
@_instrument("ceremony_status")
def ceremony_status(cid: str) -> dict:
    """Read the initiator monitor for a ceremony (ring progress, signed count, state). Uses the
    persisted initiator capability token (not re-derivable) — the ceremony must have been opened
    by this connector (or its token present in the local state file)."""
    try:
        _require_auth()
    except AuthError as e:
        return _err(str(e))
    if not _CID_RE.match(cid or ""):
        return _err("invalid ceremony id.")
    rec = _recall_ceremony(cid)
    if not rec:
        return _err(f"no local capability token for {cid} — open it via this connector first "
                    "(tokens are not re-derivable).")
    try:
        with _client() as c:
            r = c.get(f"/ceremonies/{cid}",
                      headers={"X-COSIGNA-Token": rec["initiator_token"]})
    except httpx.HTTPError as e:
        return _err(f"status fetch failed: {e}")
    if r.status_code >= 400:
        return _err(f"GET /ceremonies/{cid} failed {r.status_code}: {r.text[:200]}")
    oversize = _oversize_response(r)  # MCPSEC-004
    if oversize:
        return _err(oversize)
    snap = r.json()
    # Surface a compact progress view without assuming the full snapshot schema. Prefer a
    # LIST-typed field: a hostile/broken server sending a truthy non-list `participants` (e.g. a
    # string) must not shadow a real `roster` and silently zero the derived counts (2026-07-10 audit).
    parts = snap.get("participants")
    if not isinstance(parts, list):
        parts = snap.get("roster")
    if not isinstance(parts, list):
        parts = []
    signed = sum(1 for p in parts if isinstance(p, dict) and (p.get("signed") or p.get("face_hash")))
    return {
        "ok": True,
        "ceremony_id": cid,
        "status": snap.get("status"),
        "closed": bool(snap.get("closed")),
        "participant_count": len(parts) if isinstance(parts, list) else None,
        "signed_count": signed,
        "snapshot": snap,
    }


@mcp.tool()
@_instrument("fetch_proof")
def fetch_proof(cid: str) -> dict:
    """Fetch the PUBLIC, hash-only proof bundle (GET /proof) for a CLOSED ceremony, plus the
    public certificate PDF URL. NEVER the court-bundle route (F5/Q3a — that is account-gated and
    debits a credit). 409 if the ceremony is not yet closed by human hand."""
    try:
        _require_auth()
    except AuthError as e:
        return _err(str(e))
    if not _CID_RE.match(cid or ""):
        return _err("invalid ceremony id.")
    try:
        with _client() as c:
            r = c.get(f"/ceremonies/{cid}/proof")  # PUBLIC — no capability token needed
    except httpx.HTTPError as e:
        return _err(f"proof fetch failed: {e}")
    if r.status_code == 409:
        return _err("ceremony is not CLOSED yet — the ring closes by human hand; poll "
                    "ceremony_status until closed, then re-fetch.")
    if r.status_code == 404:
        return _err(f"ceremony {cid} not found.")
    if r.status_code >= 400:
        return _err(f"GET /ceremonies/{cid}/proof failed {r.status_code}: {r.text[:200]}")
    oversize = _oversize_response(r)  # MCPSEC-004
    if oversize:
        return _err(oversize)
    return {
        "ok": True,
        "ceremony_id": cid,
        "proof": r.json(),
        "certificate_pdf_url": f"{BASE_URL}/ceremonies/{cid}/certificate",
        "note": "public hash-only proof bundle (schema cosigna.proof/1) — offline-verifiable.",
    }


def _verify_via_core(bundle: dict) -> dict:
    """Run the stdlib verify core over a proof bundle / chain document. Imported lazily so the
    connector still loads without PYTHONPATH=src (verify_ceremony then reports honestly)."""
    from cosigna.verify import verify_chain  # requires PYTHONPATH=src on the demo machine
    # The proof bundle carries the chain as 'chain' (list of blocks) or nests it; accept both.
    chain_doc = bundle
    if isinstance(bundle, dict) and "blocks" not in bundle:
        for k in ("chain", "chain_document", "ceremony"):
            if isinstance(bundle.get(k), dict) and "blocks" in bundle[k]:
                chain_doc = bundle[k]
                break
            if isinstance(bundle.get(k), list):
                chain_doc = {"blocks": bundle[k]}
                break
    pdf_hash = bundle.get("doc_hash") if isinstance(bundle, dict) else None
    v = verify_chain(chain_doc, pdf_sha256=pdf_hash)
    return {
        "status": v.status.value,
        "closed": v.closed,
        "doc_hash": v.doc_hash,
        "n_links": v.n_links,
        "signers": v.signers,
        "detail": v.detail,
        "ok": v.ok(),
    }


@mcp.tool()
@_instrument("verify_ceremony")
def verify_ceremony(cid_or_bundle_path: str, expected_doc_hash: Optional[str] = None) -> dict:
    """Independently re-verify a ceremony's chain + document-hash using the COSIGNA Python verify
    core (the on-camera kicker). Accepts either a ceremony id (fetches the public /proof) or a
    path to a downloaded proof-bundle JSON file.

    TRUST-ANCHORING (expected_doc_hash): the core checks the chain against the doc-hash carried
    INSIDE the bundle — so a spoofed/hostile server could present a self-consistent 'verified'
    verdict over a hash it chose. Pass expected_doc_hash (the value hash_document returned for the
    file YOU hold) to cross-check: if the verified doc-hash does not equal it, the tool returns
    ok=False with doc_hash_match=False, no matter what the chain says. Always pass it on camera.

    HONEST LABELLING: this re-checks chain STRUCTURE + the doc-hash binding. It does NOT verify the
    Ed25519 seal or the Bitcoin/OTS anchor, so the output carries `authenticity: "UNCHECKED"` — a
    structural PASS is not an authenticity proof (a chain forged over your public doc-hash can pass).
    Real authenticity = the offline verifier (seal + anchor). The output says exactly what was
    proven and routes you there."""
    if expected_doc_hash is not None:
        expected_doc_hash = expected_doc_hash.strip().lower()
        if not _HASH_RE.match(expected_doc_hash):
            return _err("expected_doc_hash must be a 64-char lowercase SHA-256 hex "
                        "(use hash_document on your file first).")
    try:
        _require_auth()
    except AuthError as e:
        # verify of a local bundle path does not strictly need a session, but the fetch path does;
        # allow a local-file verify to proceed even without auth.
        if not (cid_or_bundle_path and Path(cid_or_bundle_path).expanduser().is_file()):
            return _err(str(e))

    bundle: Optional[dict] = None
    source = ""
    p = Path(cid_or_bundle_path).expanduser()
    if p.is_file():
        try:
            bundle = json.loads(p.read_text())
            source = f"local bundle {p.name}"
        except (OSError, json.JSONDecodeError) as e:
            return _err(f"could not read bundle {p}: {e}")
    elif _CID_RE.match(cid_or_bundle_path or ""):
        try:
            with _client() as c:
                r = c.get(f"/ceremonies/{cid_or_bundle_path}/proof")
        except httpx.HTTPError as e:
            return _err(f"proof fetch failed: {e}")
        if r.status_code == 409:
            return _err("ceremony not CLOSED yet — cannot verify an open ring.")
        if r.status_code >= 400:
            return _err(f"proof fetch failed {r.status_code}: {r.text[:200]}")
        oversize = _oversize_response(r)  # MCPSEC-004
        if oversize:
            return _err(oversize)
        bundle = r.json()
        source = f"public /proof for {cid_or_bundle_path}"
    else:
        return _err("argument is neither an existing bundle file nor a valid ceremony id.")

    try:
        result = _verify_via_core(bundle)
    except ImportError:
        return _err("verify core unavailable — run the connector with PYTHONPATH=src so "
                    "`import cosigna.verify` resolves (demo-side setup).")
    except Exception as e:  # defensive — a malformed bundle should not crash the tool
        return _err(f"verification error: {e}")

    core_ok = bool(result.get("ok", False))

    # Trust-anchor cross-check (S1): the core verdict trusts the doc-hash carried in the bundle.
    # If the caller supplied the hash of the file they actually hold, the verified doc-hash MUST
    # equal it — otherwise a hostile server presented a self-consistent verdict over another doc.
    doc_hash_match: Optional[bool] = None
    if expected_doc_hash is not None:
        verified_hash = (result.get("doc_hash") or "").strip().lower()
        doc_hash_match = (verified_hash == expected_doc_hash)

    structural_ok = core_ok and (doc_hash_match is not False)

    # (b) 2026-07-10 (finding M-1): this tool checks CHAIN STRUCTURE + the doc-hash binding ONLY.
    # It performs NO Ed25519-seal or Bitcoin/OTS-anchor verification, so `ok` here means
    # "structurally sound + bound to your document" — NOT "authentic ceremony." Because the
    # doc-hash is PUBLIC, a chain forged over it can pass this check. We say so as a STRUCTURED,
    # unmissable field (`authenticity`) and route real authenticity to the offline verifier — the
    # single source of truth (it pins the COSigna signing key and checks the seal + anchor). We do
    # NOT reimplement seal verification here (that would duplicate the frozen offline verifier and
    # blur the connector's orchestration-not-trust-anchor boundary).
    if not structural_ok and doc_hash_match is False:
        label = ("structural check REJECTED — the verified doc-hash does NOT match the document you "
                 "hold (possible spoofed bundle/server).")
    elif structural_ok:
        label = ("chain structure + doc-hash binding OK"
                 + (" (matches the document you hold)" if doc_hash_match else "")
                 + " — NOT an authenticity proof; run the offline verifier (see `authenticity`).")
    else:
        label = f"structural check NON-OK: {result.get('status')}"

    return {
        "ok": structural_ok,
        "checks": "chain-structure + doc-hash-binding",   # what `ok` actually attests to
        "authenticity": "UNCHECKED",                       # seal + anchor are NOT verified here
        "authenticity_note": (
            "This tool does NOT verify the Ed25519 SEAL or the Bitcoin/OTS ANCHOR. A structural "
            "PASS proves a well-formed closed ring bound to your document — NOT that the ceremony "
            "genuinely occurred. Because the doc-hash is public, a chain forged over it can pass "
            "this check. For authenticity, run the COSigna OFFLINE VERIFIER over the proof bundle: "
            "it pins the COSigna signing-key fingerprint and verifies the seal + anchor."),
        "offline_verifier": "Open the proof bundle in the COSigna offline verifier (seal + anchor).",
        "source": source,
        "verdict": result,
        "doc_hash_match": doc_hash_match,
        "expected_doc_hash": expected_doc_hash,
        "trust_anchored": doc_hash_match is True,
        "needs_expected_doc_hash": (expected_doc_hash is None and source.startswith("public /proof")),
        "label": label,
        "honest_scope": ("This re-verifies CHAIN INTEGRITY + the DOCUMENT-HASH binding. For the "
                         "Ed25519 SEAL and the Bitcoin/OTS ANCHOR (which confirms over hours), use "
                         "the offline verifier bundle — verify in 2040 with no vendor required."),
    }


@mcp.tool()
@_instrument("evidence_note")
def evidence_note(cid: str) -> dict:
    """Produce a formatted, PUBLIC evidence block for pasting into an invoice/quote's notes:
    the public verify URL + cid + doc_hash + certificate reference. PUBLIC DATA ONLY — this output
    NEVER contains a `?t=` capability token or a `#wk` wrapped key (F7; enforced by the test suite).
    """
    if not _CID_RE.match(cid or ""):
        return _err("invalid ceremony id.")
    # Prefer the doc-hash from the public proof; fall back to local state.
    doc_hash = None
    doc_filename = None
    try:
        with _client() as c:
            r = c.get(f"/ceremonies/{cid}/proof")
        if r.status_code == 200 and _oversize_response(r) is None:  # MCPSEC-004
            b = r.json()
            doc_hash = b.get("doc_hash")
    except httpx.HTTPError:
        pass
    rec = _recall_ceremony(cid)
    if rec:
        doc_hash = doc_hash or rec.get("doc_hash")
        doc_filename = rec.get("doc_filename")

    verify_url = _public_verify_url(cid)
    cert_url = f"{BASE_URL}/ceremonies/{cid}/certificate"
    lines = [
        "— COSigna court-evidence proof —",
        f"Ceremony: {cid}",
    ]
    if doc_filename:
        lines.append(f"Document: {doc_filename}")
    if doc_hash:
        lines.append(f"Document SHA-256: {doc_hash}")
    lines += [
        f"Verify (public, keyless): {verify_url}",
        f"Certificate (PDF): {cert_url}",
        "COSigna does not verify identity; signatures are self-declared. This is court "
        "EVIDENCE (evidentiary robustness), not legal enforceability.",
    ]
    block = "\n".join(lines)

    # Belt-and-braces: never emit a secret substring, even if state were corrupted.
    if "?t=" in block or "#wk" in block:
        return _err("internal: evidence block unexpectedly contained a capability secret; refused.")

    return {
        "ok": True,
        "ceremony_id": cid,
        "evidence_note": block,
        "public_only": True,
        "note": "Safe to paste into an invoice/quote — contains PUBLIC data only.",
    }


def main() -> None:
    """Entry point: preflight the session, then serve over stdio."""
    try:
        profile = _preflight_auth()
        print(f"[cosigna-mcp] authenticated as {profile.get('email','?')} "
              f"@ {BASE_URL}", file=sys.stderr)
        # Audit the session start (identity is redacted-safe: email is not a capability secret,
        # but it is scrubbed anyway if it were ever token-shaped).
        audit.log_event("_startup", {"base_url": BASE_URL, "email": profile.get("email")},
                        {"ok": True}, 0.0)
    except AuthError as e:
        print(f"[cosigna-mcp] STARTUP FAILED — {e}", file=sys.stderr)
        sys.exit(1)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
