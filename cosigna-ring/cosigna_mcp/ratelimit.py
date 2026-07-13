"""Per-tool sliding-window rate limiting for the MCP connector.  # mcp harden

WHY THIS FILE EXISTS
--------------------
The connector runs on the founder's live session. An AI agent (correct or misbehaving) can call
the tools in a loop. The existing `_opens_used` budget caps *real* ceremony creations, but the
READ tools (hash_document, ceremony_status, fetch_proof, verify_ceremony, evidence_note) were
unthrottled — a runaway agent could hammer the COSIGna server or spin the CPU hashing files. This
adds a per-tool sliding-window limiter so no single tool can be called more than N times per W
seconds within one process.

It is defence-in-depth, NOT a replacement for the server-side limits or the opens budget: it is
the connector's own governor, process-scoped (resets on restart), and deliberately conservative.

Defaults (per tool, calls / seconds) — generous enough for a real demo, tight enough to stop a
loop. Every default is overridable via env `COSIGNA_MCP_RATE_<TOOL>` = "<count>/<window_seconds>"
(e.g. COSIGNA_MCP_RATE_OPEN_CEREMONY="2/300"). "0/0" disables the limit for that tool.
Stdlib only.
"""
from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict

# tool -> (max_calls, window_seconds). Writes are stricter than reads.
_DEFAULTS: Dict[str, tuple] = {
    "hash_document": (60, 60),        # local CPU work; still bounded
    "open_ceremony": (5, 300),        # real sends — stacks with the opens budget
    "notarize_document": (5, 300),
    "ceremony_status": (120, 60),     # polling is expected — generous
    "fetch_proof": (60, 60),
    "verify_ceremony": (60, 60),
    "evidence_note": (60, 60),
}

# Fallback for any tool not named above.
_GLOBAL_DEFAULT = (60, 60)


class RateLimitError(RuntimeError):
    """Raised when a tool exceeds its per-window budget. The message is safe to surface."""


def _parse_env(tool: str) -> tuple | None:
    raw = os.environ.get(f"COSIGNA_MCP_RATE_{tool.upper()}", "").strip()
    if not raw:
        return None
    try:
        count_s, window_s = raw.split("/", 1)
        return (int(count_s), float(window_s))
    except (ValueError, TypeError):
        return None  # malformed override → fall back to the default (fail safe, not open)


def _limit_for(tool: str) -> tuple:
    return _parse_env(tool) or _DEFAULTS.get(tool, _GLOBAL_DEFAULT)


_calls: Dict[str, Deque[float]] = defaultdict(deque)
_lock = threading.Lock()


def check(tool: str, *, now: float | None = None) -> None:
    """Record a call to `tool` and raise RateLimitError if it exceeds the window budget.

    Sliding window: keep the timestamps of recent calls, evict those older than the window, and
    reject if the survivor count already meets the cap. A cap of 0 (or window 0) disables the limit.
    """
    max_calls, window = _limit_for(tool)
    if max_calls <= 0 or window <= 0:
        return
    t = time.time() if now is None else now
    with _lock:
        dq = _calls[tool]
        cutoff = t - window
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) >= max_calls:
            retry_in = round(dq[0] + window - t, 1)
            raise RateLimitError(
                f"rate limit for {tool}: max {max_calls} calls / {int(window)}s reached; "
                f"retry in ~{retry_in}s (override with COSIGNA_MCP_RATE_{tool.upper()})."
            )
        dq.append(t)


def reset(tool: str | None = None) -> None:
    """Clear the window state (used by tests). None clears every tool."""
    with _lock:
        if tool is None:
            _calls.clear()
        else:
            _calls.pop(tool, None)
