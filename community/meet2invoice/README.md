# meet2invoice

**A sales call becomes a sent Qonto invoice, with no re-typing.**

A [Claude Code](https://claude.com/claude-code) skill on the official Qonto MCP.
Feed it a meeting artifact — a call transcript, notes, a calendar event, in any
of five languages — and it extracts the deal, previews it for your approval,
creates the Qonto quote, and on acceptance finalizes and sends the invoice.
Separate confirmations for each write, including draft creation, finalization
and sending. Nothing written without your OK.

```mermaid
flowchart LR
    A["📞 Meeting artifact\n(transcript · notes · calendar)"] --> B["🧠 Extract & preview\nclient · amount · VAT · terms"]
    B -. "◆ Gate 1 — you confirm" .-> C["📄 create_quote\npublic quote_url"]
    C --> E["🧾 Invoice\nsame items + legal mentions"]
    E -. "◆ Gate 2 — confirm draft" .-> D["📝 Draft invoice"]
    D -. "◆ Confirm finalization" .-> G["✅ Finalized invoice"]
    G -. "◆ Confirm recipients & send" .-> F["📧 Sent from Qonto"]

    classDef qonto fill:#E3E2EF,stroke:#3B3A63,color:#18161C;
    class C,F qonto
```

## Why this matters

After every sales call, someone re-types the deal — scope, amount, VAT,
payment terms — into a finance tool. meet2invoice closes that loop from the
raw meeting artifact straight to a finalized, sent Qonto invoice:

- **Guarded action.** Nothing is written to Qonto without an explicit preview
  and confirmation for that action. Draft approval does not authorize
  finalization or sending; recipients and email content are previewed before sending.
- **Law-aware.** VAT treatment (domestic / intra-EU reverse charge / export /
  small-business schemes) considers supply type, supplier VAT status and the parties' countries via
  [`references/invoicing-law.md`](skills/meet2invoice/references/invoicing-law.md),
  including the mandatory legal mentions — written in the client's language.
  Unclear exceptions require confirmation with the user or their accountant.
- **No money movement.** Quotes and invoices only; payments always stay with
  Qonto and the user's own Strong Customer Authentication.

## Quick start

1. Connect the [Qonto MCP server](https://qonto.com) in Claude Code.
2. Copy this folder into your skills directory (or clone `qonto/skills`).
3. Feed it a meeting artifact:

   - "Here's the transcript from my Bouygues call — meet2invoice it."
   - 🇩🇪 "Mach aus diesem Telefonprotokoll ein Angebot und dann die Rechnung."
   - 🇫🇷 "Cet appel est clôturé — facture en autoliquidation, TVA 0, mentions OK."
   - 🇮🇹 "Deal chiuso: crea la fattura, IVA 22%, serve il codice destinatario SdI."
   - 🇪🇸 "Crea un borrador de factura con IVA 21%, pero no la emitas ni la envíes."

## What this skill deliberately does NOT do

- It never moves money, creates transfers, or touches payment approval.
- It never sends an invoice without separate approval of recipients and email content.
- Transcript and tool-returned instructions never authorize writes or bypass confirmations.
- It does not give legal or tax advice; it applies documented invoicing rules
  and asks when data (VAT ID, rate, country, tax ID) is missing.
- Recurring/retainer invoices and deposit (down-payment) invoices are not
  automated yet — create them in Qonto directly; the skill focuses on the
  deal-to-first-invoice loop.

## Contents

| Path | Purpose |
|---|---|
| `skills/meet2invoice/SKILL.md` | The skill definition (flow, gates, error handling) |
| `skills/meet2invoice/references/invoicing-law.md` | Per-country VAT / e-invoicing rules used at extraction time |

---

Built by Dr. Martin Kaiser · [Kaiser Data & AI](https://kaiser-data-ai.de)
