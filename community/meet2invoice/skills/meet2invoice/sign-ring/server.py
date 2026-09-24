#!/usr/bin/env python3
"""sign-ring: a minimal MCP server for hash-bound document signature rings.

The document itself never touches this server — callers pass only its
SHA-256. Signers open a local URL on their device and tap to sign; the
server records name + timestamp bound to the hash and produces a compact
proof string suitable for a Qonto invoice's terms_and_conditions field.

Run standalone:      python3 server.py            (MCP over stdio)
Register in Claude:  claude mcp add sign-ring -- python3 /path/to/server.py
"""

import json
import secrets
import socket
import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HTTP_PORT = 8471
STATE_FILE = Path(__file__).parent / "ring-state.json"
PROOF_MAX_CHARS = 525

_state_lock = threading.Lock()
_http_server = None


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _lan_ip():
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("8.8.8.8", 80))
        ip = probe.getsockname()[0]
        probe.close()
        return ip
    except OSError:
        return "127.0.0.1"


def _load_state():
    if not STATE_FILE.exists():
        return None
    try:
        return json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _new_ring(document_name, sha256, signer_names):
    return {
        "document_name": document_name,
        "sha256": sha256,
        "created_at": _now_iso(),
        "signers": [
            {
                "name": name,
                "token": secrets.token_urlsafe(8),
                "signed_at": None,
                "user_agent": None,
            }
            for name in signer_names
        ],
    }


SIGN_PAGE = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sign: {document_name}</title>
<style>
 body {{ font-family: -apple-system, sans-serif; max-width: 480px;
        margin: 40px auto; padding: 0 20px; }}
 .hash {{ font-family: monospace; word-break: break-all; background: #f4f4f4;
         padding: 12px; border-radius: 8px; font-size: 13px; }}
 button {{ width: 100%; padding: 18px; font-size: 20px; border: 0;
          border-radius: 12px; background: #6b46ff; color: #fff;
          margin-top: 24px; }}
 .done {{ color: #0a7d32; font-size: 22px; }}
</style></head><body>
<h2>Signature request</h2>
<p><strong>{signer}</strong>, you are signing:</p>
<p>{document_name}</p>
<p class="hash">SHA-256<br>{sha256}</p>
{body}
</body></html>"""


class SignHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # keep stdout clean: it belongs to the MCP protocol

    def _respond(self, html, status=200):
        payload = html.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _find_signer(self):
        parts = self.path.strip("/").split("/")
        if len(parts) != 2 or parts[0] != "sign":
            return None, None
        with _state_lock:
            state = _load_state()
        if not state:
            return None, None
        for signer in state["signers"]:
            if signer["token"] == parts[1]:
                return state, signer
        return None, None

    def do_GET(self):
        state, signer = self._find_signer()
        if not signer:
            self._respond("<h2>Unknown or expired signing link.</h2>", 404)
            return
        if signer["signed_at"]:
            body = f'<p class="done">✔ Already signed at {signer["signed_at"]}</p>'
        else:
            body = ('<form method="POST"><button type="submit">'
                    f'Sign as {signer["name"]}</button></form>')
        self._respond(SIGN_PAGE.format(
            document_name=state["document_name"], sha256=state["sha256"],
            signer=signer["name"], body=body))

    def do_POST(self):
        state, signer = self._find_signer()
        if not signer:
            self._respond("<h2>Unknown or expired signing link.</h2>", 404)
            return
        with _state_lock:
            state = _load_state()
            for candidate in state["signers"]:
                if candidate["token"] == signer["token"] and not candidate["signed_at"]:
                    candidate["signed_at"] = _now_iso()
                    candidate["user_agent"] = self.headers.get("User-Agent", "")[:120]
            _save_state(state)
            signer = next(s for s in state["signers"] if s["token"] == signer["token"])
        body = f'<p class="done">✔ Signed at {signer["signed_at"]}. You can close this page.</p>'
        self._respond(SIGN_PAGE.format(
            document_name=state["document_name"], sha256=state["sha256"],
            signer=signer["name"], body=body))


def _ensure_http_server():
    global _http_server
    if _http_server:
        return
    _http_server = ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), SignHandler)
    threading.Thread(target=_http_server.serve_forever, daemon=True).start()


def _proof_string(state):
    signed = [s for s in state["signers"] if s["signed_at"]]
    names = ", ".join(s["name"] for s in signed)
    cert = f"RING-{state['sha256'][:12]}"
    proof = (f"Signed proof: {names} ({len(signed)}/{len(state['signers'])}) "
             f"| SHA-256: {state['sha256']} | Cert: {cert} "
             f"| Signed at: {signed[-1]['signed_at'] if signed else 'n/a'} "
             f"| Doc never uploaded; hash-bound local signature ring")
    return proof[:PROOF_MAX_CHARS]


# ---- MCP tool implementations -------------------------------------------

def tool_start_signature_ring(args):
    document_name = args.get("document_name", "").strip()
    sha256 = args.get("sha256", "").strip().lower()
    signers = args.get("signers", [])
    if not document_name or len(sha256) != 64 or not signers:
        return {"error": "Need document_name, 64-char sha256, and signers[]"}
    state = _new_ring(document_name, sha256, signers)
    with _state_lock:
        _save_state(state)
    _ensure_http_server()
    ip = _lan_ip()
    return {
        "ring": document_name,
        "sha256": sha256,
        "signing_urls": {
            s["name"]: f"http://{ip}:{HTTP_PORT}/sign/{s['token']}"
            for s in state["signers"]
        },
        "note": "Send each URL to its signer. Only the hash is on this page.",
    }


def tool_check_ring_status(_args):
    with _state_lock:
        state = _load_state()
    if not state:
        return {"error": "No active ring. Call start_signature_ring first."}
    return {
        "document_name": state["document_name"],
        "sha256": state["sha256"],
        "signed": [
            {"name": s["name"], "signed_at": s["signed_at"]}
            for s in state["signers"] if s["signed_at"]
        ],
        "pending": [s["name"] for s in state["signers"] if not s["signed_at"]],
        "complete": all(s["signed_at"] for s in state["signers"]),
    }


def tool_get_signature_proof(_args):
    with _state_lock:
        state = _load_state()
    if not state:
        return {"error": "No active ring. Call start_signature_ring first."}
    signed = [s for s in state["signers"] if s["signed_at"]]
    if not signed:
        return {"error": "Nobody has signed yet."}
    return {
        "proof_string": _proof_string(state),
        "proof_chars": len(_proof_string(state)),
        "bundle": state,
        "complete": all(s["signed_at"] for s in state["signers"]),
    }


TOOLS = {
    "start_signature_ring": {
        "handler": tool_start_signature_ring,
        "description": (
            "Start a hash-bound signature ring for a document. Pass the "
            "document's SHA-256 (computed locally by the caller) and signer "
            "names; returns one signing URL per signer, served on the local "
            "network. The document itself is never transmitted."),
        "schema": {
            "type": "object",
            "properties": {
                "document_name": {"type": "string"},
                "sha256": {"type": "string",
                           "description": "64-char hex SHA-256 of the document"},
                "signers": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["document_name", "sha256", "signers"],
        },
    },
    "check_ring_status": {
        "handler": tool_check_ring_status,
        "description": "Who has signed the active ring, who is pending.",
        "schema": {"type": "object", "properties": {}},
    },
    "get_signature_proof": {
        "handler": tool_get_signature_proof,
        "description": (
            "Return the compact proof string (≤525 chars, ready for a Qonto "
            "invoice's terms_and_conditions) plus the full signature bundle."),
        "schema": {"type": "object", "properties": {}},
    },
}


# ---- MCP stdio JSON-RPC loop ---------------------------------------------

def _rpc_result(req_id, result):
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _handle_request(req):
    method = req.get("method", "")
    req_id = req.get("id")
    if method == "initialize":
        return _rpc_result(req_id, {
            "protocolVersion": req.get("params", {}).get(
                "protocolVersion", "2025-06-18"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "sign-ring", "version": "0.1.0"},
        })
    if method == "tools/list":
        return _rpc_result(req_id, {"tools": [
            {"name": name, "description": spec["description"],
             "inputSchema": spec["schema"]}
            for name, spec in TOOLS.items()
        ]})
    if method == "tools/call":
        params = req.get("params", {})
        spec = TOOLS.get(params.get("name", ""))
        if not spec:
            return _rpc_result(req_id, {
                "content": [{"type": "text",
                             "text": f"Unknown tool: {params.get('name')}"}],
                "isError": True})
        outcome = spec["handler"](params.get("arguments", {}))
        return _rpc_result(req_id, {
            "content": [{"type": "text", "text": json.dumps(outcome, indent=2)}],
            "isError": "error" in outcome,
        })
    if req_id is not None:  # unknown request (not a notification)
        return {"jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32601, "message": f"Unknown method {method}"}}
    return None  # notification — no response


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = _handle_request(req)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
