# COSIGna MCP connector — Quickstart (first-tester guide)

> A 10-minute path to driving a real COSIGna signature ceremony from Claude Desktop, with the
> document **never leaving your machine**. This is the short onboarding; the full reference is
> `README.md`.

You will: install the connector, connect it to Claude Desktop with your own COSIGna session,
and run one ceremony end-to-end — hash → open → sign on your phone → verify → evidence note.

---

## 0. What you need (5 min)

- **Python 3.12** (`python3.12 --version`) and `pip install mcp httpx cryptography`
- **Claude Desktop** (macOS or Windows)
- **A COSIGna account** — sign in once at https://cosigna.eu so your email can mint a session
  (if you can't sign in, ask the COSIGna team to enable your address)
- The **connector folder** (`cosigna_mcp/` + `_verifycore/` + `mcp.json` + `.env.example`)

---

## 1. Mint your session token (2 min)

The connector acts as **you**, using a 30-day bearer session — no password is ever stored.

```bash
# (a) request a magic sign-in link for your email
curl -s -X POST https://cosigna.eu/auth/request-link \
  -H 'Content-Type: application/json' \
  -d '{"email":"YOUR_EMAIL"}'

# (b) open the emailed link, copy its ?token=... value, then exchange it (the Accept header is
#     what returns JSON rather than an HTML page):
curl -s 'https://cosigna.eu/auth/verify-link?token=PASTE_TOKEN_HERE' \
  -H 'Accept: application/json'
# -> {"session_token":"...", "account_id":"...", "email":"...", "expires_in_ms":...}
```

Copy the `session_token` — you'll paste it into the config next. **Treat it like a password.**

---

## 2. Connect it to Claude Desktop (2 min)

Add this to your Claude Desktop config (Settings → Developer → Edit Config), putting your token in
`COSIGNA_SESSION_TOKEN`, then **restart Claude Desktop**:

```json
{
  "mcpServers": {
    "cosigna": {
      "command": "python3.12",
      "args": ["-m", "cosigna_mcp.server"],
      "env": {
        "COSIGNA_SESSION_TOKEN": "PASTE_YOUR_SESSION_TOKEN",
        "COSIGNA_MCP_BASE_URL": "https://cosigna.eu",
        "COSIGNA_MCP_ALLOWED_DOMAINS": "your-domain.example",
        "PYTHONPATH": "_verifycore"
      }
    }
  }
}
```

> Run Claude Desktop from the folder containing `cosigna_mcp/` and `_verifycore/`, or use absolute
> paths. The server **preflights your session on startup** and fails immediately (with a re-mint
> recipe) if the token is missing or expired — you learn at launch, not mid-test.

**Connected check:** in a new chat, the `cosigna` tools appear, and asking Claude to "check my
COSIGna session" succeeds.

---

## 3. Run one ceremony end-to-end (the spine)

Ask Claude, in plain language, to walk this path with a test PDF on your machine:

1. **`hash_document`** a local PDF → returns its SHA-256. *(The bytes never leave your machine —
   this is the server-blindness proof point.)*
2. **`open_ceremony`** with the hash + one participant + your selfie photo. It is **dry-run by
   default** — Claude shows the would-be payload; you tell it to pass `confirm=true` to actually
   open. You get back one **capability link** per signer.
3. **Sign on your phone** — open the returned link, do the consent selfie + hold-to-sign.
4. **`ceremony_status`** → watch the ring progress to CLOSED (a human closes it — there is no
   close tool by design).
5. **`fetch_proof`** → the public, hash-only proof bundle + certificate URL.
6. **`verify_ceremony`** with `expected_doc_hash` = the hash from step 1 → independent re-check.
7. **`evidence_note`** → a public-data-only block you could paste into an invoice or email.

---

## 4. Know this before you judge it (honest limits)

- **Your document never leaves your machine** — only its SHA-256 is sent. Verify this yourself:
  watch the network; only the hash goes out.
- **COSIGna does not verify identity.** Signatures are self-declared. The proof is court
  *evidence* (a tamper-evident record of who affirmed what, in sequence), **not** identity
  verification or legal enforceability.
- **Signer links are bearer capabilities** — anyone holding one can sign as that participant and
  view the consent photos. They appear in your chat, and the assistant/transcript can see them.
  Fine for a test; for anything real, have the connector **email** them (set
  `COSIGNA_MCP_ALLOWED_DOMAINS`) or use **PIN mode**. Never paste a link back into chat.
- **`verify_ceremony` checks structure, not authenticity.** It returns `authenticity: "UNCHECKED"`
  — it re-verifies the chain shape + the document-hash binding, but does **not** verify the
  Ed25519 seal or the Bitcoin anchor. For authenticity, open the proof bundle in the **offline
  verifier** (it pins COSIGna's signing key and checks seal + anchor). This honesty is deliberate.
- **The anchor confirms over hours** — don't expect an instant "anchored ✓".

---

## 5. If something snags

| Symptom | Fix |
|---|---|
| Server won't start / "session invalid" | Token missing or >30 days old — re-mint (step 1). |
| `verify_ceremony` says "verify core unavailable" | `PYTHONPATH` isn't pointing at `_verifycore` — check the config env block. |
| `ModuleNotFoundError` at launch | Not Python 3.12, or `mcp`/`httpx`/`cryptography` not installed in that interpreter. |
| "rate limit" on a tool | Per-tool throttle (defence-in-depth) — wait the stated window, or override `COSIGNA_MCP_RATE_<TOOL>`. |
| `open_ceremony` "did nothing" | It's dry-run by default — tell Claude to pass `confirm=true`. |
| Selfie rejected as "not an image" | The connector only accepts JPEG/PNG/WebP for the selfie. |

---

*Feedback welcome — what was confusing, what you expected that didn't happen, and whether the
server-blindness claim felt real to you.*
