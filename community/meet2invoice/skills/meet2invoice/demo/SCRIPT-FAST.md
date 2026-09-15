# meet2invoice — fast Zoom script (~2:15)

Talk over a Zoom screenshare. No editing needed. Have three things ready:
`demo/transcript.md`, Claude Code, and the architecture page open in a tab.

> **Before recording:** create the client with a placeholder SIREN up front so
> the live run doesn't stall on the tax-ID (422) error.

---

### 0:00 · Architecture tab (15s)
> "This is meet2invoice — a Claude Code skill that turns a sales call into a
> provable Qonto invoice. Two human approvals, and the document never leaves
> your machine. Let me show you live."

### 0:15 · Open `transcript.md`, scroll (15s)
> "Here's a raw, messy sales-call transcript. A deal is buried in here — an
> amount, a VAT rate, payment terms. Normally someone re-types all of this into
> an invoice tool."

### 0:30 · Claude Code (25s)
Type: **"Here's the transcript from my Atelier Lumière call — meet2invoice it."**
> "It reads the call, extracts the deal, applies the right VAT — and stops.
> Nothing is written to Qonto until I confirm. That's gate one."
→ **confirm.**

### 0:55 · Qonto quote + local hash (30s) — the security beat
Show the `quote_url`.
> "The quote is live in Qonto — real quote, public link. Now the proof step:
> it hashes the quote PDF locally with SHA-256, a one-way fingerprint. The
> document itself never leaves my machine — only these 64 characters do, and
> you can't reverse them back into the file. Change one euro on the quote and
> the fingerprint breaks."

### 1:25 · Invoice → Gate 2 (25s)
"The client accepted." → continue → show invoice preview.
> "Second gate — I see exactly what gets written, including the proof line."
→ **confirm.** "Finalized. Real Qonto invoice number."

### 1:50 · The payoff — verify live (25s)
Open the invoice PDF, zoom the footer.
> "There's the fingerprint, rendered right in the official Qonto invoice footer,
> cryptographically bound to this exact quote. Don't trust me — verify it."
→ run `scripts/verify-proof.sh quote.pdf invoice.pdf` → **green ✔ PROOF VERIFIED.**
> "The invoice provably references the exact PDF on my machine. No account, no
> network — both sides of the deal can check it. That's tamper-evidence with
> zero document exposure."

### 2:15 · Close (10s)
> "From a messy call to a payable, provable invoice. The document never left the
> machine — only the hash traveled. meet2invoice makes EU freelance deals fluent."

---

### Qonto proof-points to zoom (judges must SEE it's Qonto)
- **`BIC QNTOFRP1XXX`** in the payment block — Qonto's own BIC.
- The **auto-added French legal mentions** (penalties, €40 indemnity) — Qonto's
  compliance engine added those, not the skill.
- German document + French legal mentions = client's language, org's law.
- `F-2026-004` sequential numbering; `qonto-mcp-sandbox` tool names in Claude Code.

### The one honest line if asked "is the hash really secure?"
> "It's tamper-evidence between two parties who each hold the quote — not a
> digital signature. It secures the link where invoice fraud actually happens,
> and never exposes the document. The sign-ring extension adds identity signing."
