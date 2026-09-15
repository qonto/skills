# meet2invoice — 3-minute demo video script

Target: **≤ 3:00**. Narration in English. Screen = Claude Code + the Qonto web
app side by side (or tab-switch). Record one clean take after the rehearsal
checklist at the bottom passes.

> Recommended run = **Option B**: core flow + local SHA-256 proof injected into
> the invoice. No second MCP needed, nothing can break live.

---

## Shot list (with timings + narration)

### 0:00–0:20 · Cold open — the messy input
- **On screen:** open `demo/transcript.md` (the Atelier Lumière call). Scroll it.
- **Say:** "This is a raw, auto-transcribed sales call. A deal is buried in
  here — an amount, a VAT rate, payment terms. Normally someone re-types all of
  that into an invoice tool. Watch meet2invoice do it end to end, with proof."

### 0:20–0:50 · Extract → Gate 1
- **Do:** in Claude Code: `"Here's the transcript from my Atelier Lumière call — meet2invoice it."`
- **On screen:** the extraction preview table (client, scope, €4,800, VAT 20%,
  net 30, deal state).
- **Say:** "It reads the call, pulls the deal, and — crucially — stops. Nothing
  is written to Qonto until I confirm. Gate one."
- **Do:** confirm.

### 0:50–1:25 · Quote created in Qonto + local hash
- **On screen:** Qonto web app — the new quote with its public `quote_url`.
- **Say:** "The quote is live in Qonto. Now the proof step."
- **On screen:** terminal — the quote PDF downloaded, `shasum -a 256` output.
- **Say:** "It downloads the authoritative PDF and hashes it **locally**. The
  document never leaves my machine — only this SHA-256 will travel."

### 1:25–2:05 · Acceptance → invoice with proof → Gate 2
- **Say:** "The client accepted." (show the CRM line / just say it)
- **Do:** continue the skill → invoice preview showing the proof string to be
  injected into `terms_and_conditions`.
- **Say:** "Second gate before the invoice. I can see exactly what gets written,
  including the proof line."
- **Do:** confirm → invoice finalized.

### 2:05–2:40 · The payoff
- **On screen:** the finalized invoice PDF in Qonto — zoom the footer showing
  `SHA-256: … | doc never uploaded`.
- **Say:** "Finalized, real invoice number, and the cryptographic proof is
  rendered right in the footer. Don't trust me — verify it."
- **On screen:** terminal —
  `scripts/verify-proof.sh quote.pdf invoice.pdf` → green `✔ PROOF VERIFIED`.
- **Say:** "One offline script: the invoice provably references the exact PDF
  on my laptop. Then it's sent from Qonto to the client."
- **On screen:** the sent confirmation.

### 2:40–3:00 · Close
- **Say:** "From a messy call to a payable, provable invoice — two confirmation
  gates, and the document never left the machine. Only the hash traveled.
  meet2invoice makes EU freelance deals fluent."
- **On screen:** end card:
  `meet2invoice — EU freelance deals, fluent. · github.com/qonto/skills`

---

## Optional 15-sec beats (only if under time)

- **International / law-aware:** show `transcript-fr-reverse-charge.md` — "Same
  skill, a cross-border EU deal: it recognizes reverse charge, sets VAT to zero,
  and adds the required legal mention. It knows the invoicing law per country."
- **Guardrail:** show `transcript-de-angebot.md` — "And when the deal *isn't*
  closed, it refuses to invoice — it creates a quote and stops. The guardrails
  are the point."

---

## Rehearsal checklist (run before recording)

- [ ] Fresh Claude Code session, Qonto sandbox MCP connected + authenticated.
- [ ] Cancel/ignore old sandbox leftovers (`M2M-TEST-INV-001`, quote `D-2026-001`).
- [ ] Client has a `tax_identification_number` ready (or a placeholder SIREN) —
      avoids the 422 `tin_number` stall on `create_quote`.
- [ ] One full dry run with `demo/transcript.md`, **timed under 3:00**.
- [ ] Confirm the proof string renders in the finalized invoice PDF footer.
- [ ] Run `scripts/verify-proof.sh <quote.pdf> <invoice.pdf>` against the dry-run
      PDFs — must print green `✔ PROOF VERIFIED` before recording.
- [ ] Screen-recording tool set to capture both Claude Code and the Qonto tab.
- [ ] Mic check; close noisy apps/notifications.
