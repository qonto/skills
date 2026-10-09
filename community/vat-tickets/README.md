# VAT Tickets — the deductible VAT you forgot, turned into scratch cards

**Demo:** https://app.claap.io/lou-workspace/c-ATujRYEn3j-MG74rsUrrLtR

**Your accountant never saw these invoices. The State kept the VAT. We go get it back.**

French businesses lose deductible VAT every month for one boring reason: the
invoice never made it into the books. The card payment is in the bank account,
the expense is in the FEC (the legal accounting ledger), but the invoice — the
only document that opens the right to deduct — is sleeping in a supplier
account nobody logs into. After two years, the right expires. Silently.

VAT Tickets reads the company's FEC and bank flow through Claude + Qonto MCP,
finds every expense whose VAT was never claimed, and turns each one into a
**scratch card**: *"Up to 449 € at LDLC — 3 min to get the invoice."* The user
scratches, fetches the invoice, drops it in the chat. Claude reads it (vision),
the card cracks open, confetti, and the amount moves from **LOCKED** to
**SECURED**. When they're done playing, one click produces the pack their
accountant needs to file it on the next VAT return: CSV for line 21, a draft
letter to the tax office, the missing-invoices list, and an annex that gives
the accountant an honorable way out.

## Why this is defensible (the part that isn't a game)

Tax is the worst place for an LLM to improvise. So it doesn't:

- **No firm amount without reading the invoice.** Everything inferred from
  history, supplier habit or category is an *upper bound* ("up to X €"),
  never a gain. The words "probable"/"likely" are mechanically forbidden.
- **Tickets are built by a deterministic script** (`build_tickets.py`), not by
  the model. Its invariants *halt the run* rather than ship a wrong amount: a
  `won` ticket without an invoice and a positive VAT amount read on it is a
  crash, not a warning.
- **Two counters that never add up.** SECURED (invoice in hand, declarable) and
  LOCKED (upper bound) are never totalled together — a single merged number
  would be a misleading commercial claim, and a disappointment machine.
- **Every verdict is sourced** (CGI articles, BOFiP doctrine, case law), with
  the legal deadline computed per line. A `check_bofip.py` CI script verifies
  each cited BOFiP reference still exists and is in force against the official
  open-data dataset.
- **No side effects.** Nothing is filed, nothing is sent. The accountant email
  is a draft. The board displays and celebrates; all intelligence stays in the
  chat thread.

## How it works

```
FEC (extract_fec.py)   ─┐
Invoices read by vision ─┼─>  build_tickets.py  ─>  tickets.json ─┬─> make_board.py ─> board (artifact)
Bank transactions (MCP) ─┘   deterministic locks                  └─> build_pack.py ─> accountant pack
```

1. `extract_fec.py` parses the FEC (legal French format), reconciles booked vs.
   filed VAT, and surfaces the candidates: expenses with recoverable VAT and
   payments with no invoice on file.
2. `route_label.py` + `qualify_ticket.py` classify each line (word-boundary
   patterns over French bank labels) and return a sourced verdict: deductible,
   excluded, reverse charge, time-barred — with the legal deadline.
3. `build_tickets.py` merges FEC candidates, bank orphans and vision-read
   invoices into tickets, under hard invariants.
4. `make_board.py` injects `tickets.json` into the scratch-card board
   (`board-ready.html`) — and refuses any "won" card that nothing proves.
5. On GO, `build_pack.py` produces the four deliverables:
   `pack-line21.csv`, `sie-letter.md`, `missing-invoices.md`,
   `accountant-annex.md`.

Every step has fixtures: **114 tests**, run with `--test` on each script.

## Repository map

| Path | What it is |
|---|---|
| `SKILL.md` | The fiscal brain: verdicts, deadlines, regimes, invariants |
| `CLAUDE.md` | The orchestration: how a session unfolds, the five hard rules |
| `scripts/` | The deterministic pipeline (extract → qualify → tickets → board → pack) |
| `assets/board.html` | The scratch-card board (artifact; state survives the session) |
| `references/` | Sourced tax documentation (exclusions, deadlines, FEC accounts, invoice retrieval paths per supplier…) |
| `client-config.example.json` | Per-client routing rules (mission refs, known subcontractors) |

## Try it

```bash
python3 scripts/extract_fec.py your-fec.txt --json fec.json
python3 scripts/build_tickets.py --fec fec.json --invoices invoices.json --out tickets.json
python3 scripts/make_board.py tickets.json --out board-ready.html
python3 scripts/build_pack.py tickets.json --siren 123456789 --company "ACME" --out-dir deliverables/
```

Or just the test suites: each script accepts `--test`.

---

*Co-created by Matthieu, Sami and Louis.*

*Built for the Qonto × Anthropic MCP Hackathon. The product speaks English;
the tax law, bank labels and legal citations it manipulates are French — that
data stays French on purpose (FEC columns, CGI/BOFiP citations, verified
navigation paths on French supplier sites).*
