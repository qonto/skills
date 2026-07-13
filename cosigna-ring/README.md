# COSIGNA MCP connector

Drive **COSIGNA** async signature ceremonies from a Claude agent — while the document
**never leaves your machine**. The connector hashes the document locally and sends only its
SHA-256; neither COSIGNA's server nor the agent's transport ever receives the bytes.

> The ring is strong because the loop is closed.

This is a local **stdio** MCP server exposing seven tools. It is server-blind by construction:
the consent selfie is encrypted **on your machine** with a freshly generated content key, and
that key only ever leaves the process **wrapped inside each signer link's URL fragment**
(`#wk=…`) — a fragment the server never receives. The wrap key is the document's **public**
SHA-256 hash, so the consent photos' confidentiality rests on the **secrecy of the `#wk=`
fragment**, not on holding the document.

> **First time? Start with [`QUICKSTART.md`](QUICKSTART.md)** — a 10-minute path from install to a
> real ceremony end-to-end. This README is the full reference.

---

## What it is — and what it is not (honest limits)

Read this before the demo. Every surface COSIGNA ships repeats it, and so does this connector.

- **COSigna does NOT verify identity.** Signatures are **self-declared**. The connector, the
  ceremony, and the certificate assert who *declared* they signed — never that an identity was
  checked. Copy says "provided / declared," never "verified."
- **The proof is a court-EVIDENCE bundle** — evidentiary robustness (a tamper-evident,
  offline-verifiable record of who affirmed what, in sequence, over which document hash). It is
  **not** a statement of legal enforceability, and **not** identity verification.
- **The anchor confirms over hours.** When `anchor_enabled` is on (the connector always sets it),
  the close digest is anchored to Bitcoin/OpenTimestamps. Confirmation is **not instant** — it
  settles over hours. Do not narrate "anchored ✓" on camera until it has actually confirmed;
  close the ceremony a day early for a recorded take.
- **The ring closes by human hand.** There is deliberately **no close tool**. A human closes the
  ring on their own device — honest semantics, and it keeps the connector from forging the shape
  of consent.

---

## Setup

### 1. Mint a session token

The connector authenticates with an existing COSIGNA **bearer session** (a 30-day token — far
longer than any demo window). Mint one:

```bash
# (a) request a magic sign-in link for your founder-domain email
curl -s -X POST https://cosigna.eu/auth/request-link \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@your-founder-domain"}'

# (b) open the emailed link, copy its ?token=… value, then exchange it for a session token.
#     The `Accept: application/json` header is what returns JSON (a browser would get an HTML
#     auto-login page instead):
curl -s 'https://cosigna.eu/auth/verify-link?token=PASTE_TOKEN_HERE' \
  -H 'Accept: application/json'
# -> {"session_token":"…","account_id":"…","email":"…","expires_in_ms":…}
```

Copy `session_token` into your Claude Desktop config as `COSIGNA_SESSION_TOKEN`.

### 2. Configure Claude Desktop

```json
{
  "mcpServers": {
    "cosigna": {
      "command": "python3.12",
      "args": ["-m", "cosigna_mcp.server"],
      "env": {
        "COSIGNA_SESSION_TOKEN": "PASTE_YOUR_SESSION_TOKEN",
        "COSIGNA_MCP_BASE_URL": "https://cosigna.eu",
        "COSIGNA_MCP_ALLOWED_DOMAINS": "your-founder-domain.example",
        "PYTHONPATH": "_verifycore"
      }
    }
  }
}
```

Requirements: Python 3.12, and the packages `mcp`, `httpx`, `cryptography`. The
`verify_ceremony` tool needs `PYTHONPATH` to point at the vendored `_verifycore` (or, on the
COSIGNA dev machine, at `src`) so `import cosigna.verify` resolves.

The server **preflights the session at startup** and hard-fails with a re-mint recipe if the
token is missing or rejected — you will see the failure immediately, not mid-demo.

### 3. Environment variables

| Var | Default | Meaning |
|---|---|---|
| `COSIGNA_SESSION_TOKEN` | — (required) | Your COSIGNA bearer session. **Never commit it.** |
| `COSIGNA_MCP_BASE_URL` | `https://cosigna.eu` | The COSIGNA service base URL. |
| `COSIGNA_MCP_ALLOWED_DOMAINS` | *(empty)* | Comma-separated email-domain allowlist. **Empty ⇒ the connector will not email anyone** — it returns links for you to deliver by hand. |
| `COSIGNA_MCP_MAX_PARTICIPANTS` | `4` | Demo cap on participants per ceremony. |
| `COSIGNA_MCP_MAX_OPENS` | `3` | Max ceremonies opened/notarized per process. |
| `COSIGNA_MCP_MAX_SELFIE_BYTES` | `15728640` (15 MB) | Cap on a selfie file read into memory before encryption. |
| `COSIGNA_MCP_MAX_RESPONSE_BYTES` | `2097152` (2 MB) | Cap on any HTTP response body the connector will parse. |
| `COSIGNA_MCP_STATE` | `~/.cosigna_mcp_state.json` | Local **0600** file holding per-ceremony capability tokens (not re-derivable). |
| `COSIGNA_MCP_AUDIT_LOG` | `~/.cosigna_mcp_audit.jsonl` | Append-only **0600** audit log — one redacted JSONL record per tool call. |
| `COSIGNA_MCP_RATE_<TOOL>` | *(per-tool defaults)* | Override a tool's rate limit, `"<count>/<window_seconds>"` (e.g. `COSIGNA_MCP_RATE_OPEN_CEREMONY="2/300"`; `"0/0"` disables). |

---

## The seven tools

| Tool | What it does |
|---|---|
| `hash_document(path)` | SHA-256 a **local** file, on your machine. Returns the hex hash + filename. The bytes are **never uploaded** — this is the server-blindness proof point. |
| `open_ceremony(doc_hash, doc_filename, participants[], initiator_selfie_path, …)` | Encrypts the initiator selfie locally, creates the ceremony (`anchor_enabled=true` always), uploads the encrypted blob, and opens the ring. Returns the ceremony id + one **capability link** per signer: `…/sign/{cid}/{sid}?t={tok}#wk={wrapped}`. **Dry-run by default** — see the abuse gates below. |
| `notarize_document(path, selfie_path)` | Self-notarization (**COAutoCert**): creates a `self_notarization` ceremony + opens it, then **returns the self-sign link** for your own second device. It does **not** auto-close (COAutoCert is two-device by definition). |
| `ceremony_status(cid)` | Reads the initiator monitor — ring progress, signed count, state. Uses the persisted initiator capability token. |
| `fetch_proof(cid)` | Fetches the **public, hash-only** proof bundle + the certificate PDF URL, once the ring is closed. Never the account-gated court-bundle route. |
| `verify_ceremony(cid \| bundle_path, expected_doc_hash=…)` | Independently **re-verifies** the chain + document-hash with the COSIGNA Python verify core (the on-camera kicker). Labelled honestly: it proves chain integrity + the doc-hash binding; for the Ed25519 **seal** and the Bitcoin **anchor**, use the offline verifier. **Pass `expected_doc_hash`** (what `hash_document` returned for *your* file) so the verdict is cross-checked against the document you actually hold — a spoofed server can otherwise present a self-consistent "verified" bundle over a hash it chose. |
| `evidence_note(cid)` | A formatted, **public-data-only** evidence block (verify URL + cid + doc-hash + certificate ref) to paste into an invoice or quote's notes. Contains **no** `?t=` token and **no** `#wk` key. |

### Abuse gates (enforced, not advisory)

`open_ceremony` and `notarize_document` are guarded:

- **Dry-run by default.** They return the *would-be* payload and send nothing. You must pass
  `confirm=true` for anything to leave the machine. (`dry_run=true` + `confirm=false` = a preview.)
- **Participant cap** — at most `COSIGNA_MCP_MAX_PARTICIPANTS` (default 4) in demo mode.
- **Opens budget** — at most `COSIGNA_MCP_MAX_OPENS` (default 3) real opens per process.
- **Session required** — no session token ⇒ hard refusal with the re-mint recipe.
- **Email allowlist** — the connector refuses to email any address whose domain is not in
  `COSIGNA_MCP_ALLOWED_DOMAINS`. With the list empty it emails no one and hands you the links.

### Production hardening (defence in depth)

Beyond the abuse gates, the connector adds four production controls. None weakens
server-blindness; all are process-local governors on top of the server's own limits.

- **Audit log.** Every tool invocation appends one JSONL record to `COSIGNA_MCP_AUDIT_LOG`
  (`~/.cosigna_mcp_audit.jsonl`, created **0600**): `{ts, seq, tool, args, outcome, duration_ms, pid}`.
  The record is **redacted before it is written** — a capability token (`?t=`), a wrapped content
  key (`#wk=`), a bearer session, an encrypted blob, or any token-shaped string can never reach the
  file. Return values are distilled to a secret-free outcome summary (never the raw signer links).
  The public doc-hash is preserved (it is the contract, not a secret). This is the record of what an
  agent actually did on your session.
- **Per-tool rate limiting.** Each tool has its own sliding-window budget (writes are stricter than
  reads); a runaway or misbehaving agent cannot hammer the server or spin the CPU. Override any tool
  with `COSIGNA_MCP_RATE_<TOOL>`.
- **Selfie image-gate.** Because the selfie is encrypted **locally** and the server only ever sees
  ciphertext, the server can no longer reject a non-image. The connector therefore checks the selfie
  is a real JPEG/PNG/WebP (magic bytes) **before** encrypting — so an agent cannot be misdirected into
  pointing `*_selfie_path` at an arbitrary local file it has not read (an SSH key, a document) and
  having it encrypted-and-uploaded as a "selfie." (This is a magic-byte prefix check: it blocks naive
  misdirection, not a capable adversary who crafts a valid image header — such an adversary already
  holds the bytes and gains nothing.) The selfie is also **size-capped** before it is read into
  memory (`COSIGNA_MCP_MAX_SELFIE_BYTES`, default 15 MB) so a huge file cannot OOM the process, and
  HTTP **response** bodies the connector parses are capped too (`COSIGNA_MCP_MAX_RESPONSE_BYTES`,
  default 2 MB) so a malicious server cannot force an unbounded body into memory.
- **Verify cross-check.** `verify_ceremony(..., expected_doc_hash=…)` binds the verdict to the
  document *you* hold, defeating a spoofed/hostile server that returns a self-consistent bundle over
  a hash it chose. Always pass it on camera. **Scope:** this re-verifies chain integrity + the
  document-hash binding — it does **not** verify the Ed25519 seal or the Bitcoin anchor, so it is not
  by itself an authenticity proof (a chain forged over your *public* doc-hash would still pass the
  chain check). For authenticity, use the **offline verifier** (seal + anchor). This is what the
  tool's `honest_scope` field says on every call.

### Accepted residuals

- **Local-file oracle (low severity, accepted).** `hash_document` and `verify_ceremony` operate on
  local paths, so an **already-compromised** agent driving this connector can learn whether an
  arbitrary readable file **exists**, its **size**, and its **SHA-256** — a file existence/size/hash
  oracle. The file **contents are never uploaded** (only the hash is ever sent, and only for a
  ceremony you open), so **server-blindness is unaffected**; the oracle is available only to an agent
  that already has local read access to those files. This is accepted as a low-severity residual
  rather than fenced behind an allowed-paths root, to keep the demo path unobstructed.

---

## Capability links — read this

Every tool output that returns a signer link carries this banner verbatim:

> **CAPABILITY LINKS** — anyone with a link can sign as that participant and view this
> ceremony's consent photos. Deliver each link to its signer out-of-band; do not paste back
> into chat.

A signer link is a **bearer capability**: possession is authority. `?t=` is the participant's
capability token (act as them); `#wk=` is the content key wrapped under the **public** document
hash. Because that hash is public (the server is even given it), the consent photos are protected
by the **secrecy of this `#wk=` fragment** — which the server never receives — not by holding the
document. Treat both as secrets.

### The assistant sees these links

Be explicit with yourself and your team: **the assistant, and any conversation logging or
transcript retention in your Claude setup, can see any capability link this connector returns
into the chat.** For a routine demo that is acceptable — the links are short-lived and the
ceremony is a test. For a **sensitive** ceremony:

- Prefer having the connector **email** the links (with a configured allowlist) so they are
  delivered out-of-band and never rendered into the transcript, **or**
- Use COSIGNA's **PIN mode** for the ceremony: the content key is additionally wrapped under a
  PIN the parties exchange separately, so a leaked link alone cannot decrypt the consent photos.

`evidence_note` is the one output designed to be pasted anywhere — it is **public data only**
and is unit-tested to never contain a `?t=` or `#wk` secret.

---

## Reserved terms

These terms are brand-reserved and appear **verbatim**, untranslated:

- **COSignee** (a signing participant). FR: **COSignataire**. DE: **COSignee**.
- **COSignMaster** (the organizer).
- **COSigna Ring Certified**.
- The brand baseline, **always in English**, never translated or altered:
  **"The ring is strong because the loop is closed."**

---

## How it stays server-blind (crypto note)

`cosigna_mcp/facewrap.py` is a Python mirror of the frozen browser crypto
(`UX/mobile-signer/facecrypto.js`), proven byte-compatible by `tests/test_facewrap_parity.py`
(it round-trips against the actual frozen JS, both directions). The scheme:

- **content key** `CK` = 32 random bytes, generated locally, one per ceremony.
- **selfie** → `AES-256-GCM(CK)`, blob = `nonce(12) ‖ ciphertext ‖ tag(16)`, AAD = the
  face-hash hex. POSTed to `/faces` as `enc=aesgcm`; the server stores opaque ciphertext.
- **wrapped key** (`#wk=`): `CK` is wrapped with **the raw document-hash bytes as the AES-256
  key** (no KDF), same layout, b64url-encoded, and carried **only in the signer link's URL
  fragment** — which the server never receives. The wrap key is the document's **public** hash
  (the coordinator is even given it in the `/ceremonies` payload), so the consent photos'
  confidentiality rests **entirely on the secrecy of the `#wk=` fragment**, not on holding the
  document. The coordinator, which sees the doc-hash but never the fragment, cannot unwrap `CK`.

`face_hash = SHA-256(plaintext)` is unchanged by encryption, so the attestation chain is
byte-identical whether faces are encrypted or not.
