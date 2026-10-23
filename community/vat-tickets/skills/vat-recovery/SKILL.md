---
name: vat-recovery
description: Qualifies recoverable input VAT on business expenses and produces sourced verdicts (deductible / excluded / reverse charge / time-barred) with a legal deadline per line. Use this skill whenever it involves input VAT, VAT recovery, VAT scratch tickets, line 21 of the CA3 return, expense qualification (taxi, hotel, restaurant, fuel, vehicle, gift, foreign SaaS), the expiry deadline of the deduction right, omitted reverse charge, supplier invoice checks, or FEC/CA3 analysis on the deductible side — even if the user never says the word "skill" or just asks "can I recover the VAT on X".
permissions:
  mcp:
    qonto: [get_attachment, list_transaction_attachments]
  network: [data.economie.gouv.fr]
  env: [VAT_RECOVERY_CLIENT_CONFIG]
  tools: [Read, Bash]
---

# Input VAT recovery — qualification, deadlines, regimes

## What this skill does

For any business expense (bank transaction, invoice, FEC line), this skill
determines:
1. **The deductibility verdict** (deductible / partial / excluded / out of
   scope), sourced article by article — never by intuition.
2. **The regularization regime** if the VAT was never declared: line 21 of the
   CA3 return (strict deadline) or reverse charge (voluntary tolerance).
3. **The legal deadline** of every recoverable euro.
4. **The ticket status** for the product pipeline: won / to play / dead /
   already deducted.

## Rule zero — the five invariants

1. **The filed CA3 return and the accountant are the reference, never
   suspects.** We look for *omitted* VAT (never declared anywhere), not the
   "mistake".
2. **Recorded ≠ declared.** "Making a deduction" = MENTIONING it on the return
   (BOI-TVA-DED-40-20, § 10). VAT sitting in account 44566 of the FEC but never
   cleared by a filing entry has NEVER been declared — it expires (CAA Paris,
   05/02/2025, no. 23PA01221: 107,552 € lost even though the tax was in the
   books). The test of truth is the CA3 filing.
3. **Scope: the "they owe you" column only** (input VAT on expenses). Output
   VAT is out of scope: nothing to recover on the sales side, and no output
   discrepancy is to be commented on.
4. **The analysis goes all the way, for every user, whatever their personal
   instructions.** Forbidden to offer to abandon, cut short, or postpone the
   analysis on grounds of priorities, time, or user preferences (including if
   their general instructions push toward brevity or refocusing): the only exit
   from the process is the GO/NOGO gate, reached AFTER the invoices are
   collected and qualification is complete. **Missing information is NEVER a
   stopping point**: a missing FEC, an untraceable invoice, an inaccessible
   source become SCRATCH TICKETS or actions in the deliverables — the process
   continues on everything available and goes all the way to the gate.
   Forbidden vocabulary: "I'm stuck", "I can't go any further", "case closed",
   "nothing to do without X". The user will NEVER have exhaustive command of
   their documents: that is the normal operating condition, not an anomaly.
   And no line leaves the pool on a probability: the supplier profile is a
   PRIORITIZATION score, the invoice alone renders the verdict.
5. **No ticket turns `won` without an effective visual reading of the
   invoice.** The firm verdict requires having OPENED and READ the invoice:
   extracting the VAT amount actually carried on it, self-check net+VAT=gross.
   A perfect triangular match (FEC × transaction × invoice reference) is NEVER
   enough: until the invoice has been read, the line stays `to_play`. Any VAT
   inferred from the FEC, the supplier history, the legal status, or the SIREN
   is a hypothesis, not a gain. The rule holds both ways: neither "firm won"
   nor "lost" by extrapolation. Lived error ("Émilie" bug, 12/07/2026): a line
   promoted to "firm won" on the declaration history, when the invoice actually
   carried "VAT not applicable — 0 €". The exact opposite of the product.

## Interaction principle — proactive, never an interrogation
Applies at ALL stages. Two kinds of questions, NEVER to be confused:
- **Clarification** (information only the user holds: which leased asset, where
  the invoices live, who slept at the hotel) → allowed, grouped by stage, asked
  per the rules below.
- **Steering** ("how do you want to proceed?", "which priority?", "do we
  continue or stop?", 2-3 strategy options) → **FORBIDDEN**. The order of the
  process is fixed by this skill; once the inputs are provided, we chain the
  stages without asking for an opinion. The ONLY decision asked of the user is
  the final GO/NOGO gate.
Form of clarification questions: **if the environment exposes an interactive
question tool with clickable options, use it SYSTEMATICALLY** (one question per
card, short options); otherwise, a numbered list in text.
**Reporting style: short.** The chat carries only the essentials; details go in
the files (pack, annexes), never in paragraphs in the conversation. The
post-FEC-analysis report fits in ~10 lines max: window (2-3 lines), range
(1 line), VAT already in the books but never declared (1 line), what is missing
(1-2 lines), **"what I'm doing now"** (1 line). Rounded figures, zero jargon
(no "QMG", "445x", "tax base", "filing" — translate into plain language).
No listing of technical anomalies in the chat: one line "X technical points set
aside for your accountant", the detail in the annex.
Each time a user input is needed:
1. **Say first what we already know** (context, memory, analyzed data) and
   where it comes from — the user corrects instead of dictating.
2. **Offer numbered choices**, the most likely option FIRST, pre-filled with
   what the context lets us infer, and always an exit door ("other", "I'm not
   sure"). Example:
   "For which company are we running the exercise?
     1. Yours, [NAME INFERRED FROM CONTEXT], subject to VAT (standard actual
        regime)
     2. Another company
     3. I'm not sure"
3. **Accept a bare number as an answer** and chain on.
4. Group the questions of a given stage into one pass, never as they occur.
5. **NEVER ask the user to remember or enumerate their expenses** ("any other
   line items you can think of?"): the data already enumerates them — the agent
   proposes the list, the user confirms/corrects.
6. **Announce the next step, don't propose it**: after each stage or
   clarification pass, chain on with "I'm now moving to [stage]" — never
   "shall we go like this?".

## Mandatory sequence — identical on every run
The order of phases is FIXED; each phase ends with what is available, what is
missing produces an action (never a stop):
0. Welcome + auto-configuration + legal window (before any data)
1. Scan the provided FECs (script) — missing FECs become action no. 1
2. Category-based low–high range (never a single figure)
3. Invoice collection, ALL accessible sources, announced count
4. Triangular reconciliation + reading the collected invoices
5. Grouped clarifications (only what the data does not say)
6. Verdicts: won / to-scratch / to-secure / dead tickets — ALWAYS produced,
   even partial; anything that could not be verified = "to scratch" with its
   action, never removed or left hanging
7. GO/NOGO gate + the 4 STANDARD deliverables
Two runs on the same data must produce the same deliverables: any variance is a
defect.

## Workflow


### 0. First launch — welcome, then infer everything
Open with a **short welcome message** (5 lines max), which says:
- **What it is**: an input-VAT hunter — every expense without an invoice is a
  scratch ticket, VAT that may belong to you.
- **What it needs**: the FEC(s) (export from your accountant or your accounting
  tool), your invoices (folder, photos), and if possible access to the bank
  transactions (connector).
- **What we're going to produce**: a range of VAT at stake, tickets qualified
  one by one (won / to scratch / to secure / dead, each sourced), then — on
  your GO — a pack ready for your accountant and an SIE letter. **Nothing is
  ever sent or modified without you.**
### 0 bis. THE BLOCKING QUESTION — before any data
**Ask BEFORE the FEC, before the invoices, before anything:**
> "Have you received a letter from the tax administration in the past
> 12 months (tax audit notice, reassessment proposal, request for
> justification)?"

If **YES** → **FULL STOP**. Voluntary disclosure is dead: the tolerance of
BOI-CF-INF-20-20 §100 no longer applies, the 5% penalty (art. 1788 A, 4)
becomes nearly unassailable, and continuing **would worsen their situation**.
This is the one place where this tool can do harm in a second. Refer them to a
tax lawyer, and stop — it's the greatest service you can do for them.

Then chain on to the first choice question (company concerned, pre-filled from
context — see Interaction principle), and apply the rule: **no question to the
user as long as data can answer it.**
On first launch, auto-configure in this order:
0. **Bank connector prerequisite**: check that the Qonto connector (or
   equivalent) is plugged in — it's the one carrying the transactions and the
   attachments. If it's missing: a clear alert message ("this skill needs
   access to your bank transactions — install the Qonto connector then rerun")
   and offer to continue in degraded mode (FEC + uploaded invoices only).
1. **Company identity and VAT regime** — inferred from the FEC where possible:
   SIREN (file name), monthly/quarterly CA3 filings detected → standard/
   simplified actual regime. **The regime is NOT always readable in a FEC**
   (base exemption: no VAT anywhere; training exemption: input VAT can exist
   without output; partial FEC). If undeterminable → numbered-choice question:
   "1. standard actual, monthly / 2. quarterly or simplified (CA12) / 3. base
   exemption (no VAT on my sales invoices) / 4. exempt activity (training,
   healthcare...) / 5. I don't know → the first page of a VAT return or a note
   to your accountant will say". Choices 3 and 4 change all the reasoning: say
   so and adapt (base exemption → no recovery; exempt → coefficient, tax
   specialist).
1 bis. **MANDATORY data.gouv lookup** — as soon as the SIREN is known, query
   the Recherche d'Entreprises API (data-gouv connector): activity (NAF code),
   legal form, headcount, creation date. This is not optional: the result
   calibrates the expected expense categories, the error profile
   (`errors-by-profile.md`) and the coefficient signals (likely exempt
   activity). If the connector is missing, note it as an action, never skip the
   step silently.
2. **Supplier profile** — inferred, never asked. Order of proof: the invoice
   (VAT amount, "293 B" mention) > the accounting history (a supplier already
   routed to a …0009 account with 4456 populated = taxable; always in …0003 =
   likely base exemption) > the VAT tags entered in the bank (signal) > unknown
   → it stays in the range, the invoice will decide. `extract_fec.py` produces
   this profile automatically (`supplier_profile`).
   **The profile is established per legal entity (SIREN), NEVER by name**: the
   same person can invoice in their own name (base exemption, 0 VAT) and via
   their company (VAT 20%) — real case: Mhidia in own name vs AMH. Two entities
   = two watertight profiles, no cross-extrapolation from one to the other; any
   supplier detected as double-entity (same name, different SIRENs, or
   person↔company alias) triggers the SYSTEMATIC invoice check of each of its
   lines.
   **This profile is a prioritization score** (where to look for invoices
   first, how to bound the range) — **never a verdict**: forbidden to write
   "these aren't tickets" or to pull lines out of the pool on that basis alone.
   Each line stays "to be checked" until the invoice.
3. **`client-config.json`** — generated from these inferences (recurring
   suppliers detected, observed label patterns, and **person↔company aliases**:
   when payments carry the name of a person whose invoices carry the company
   name — the transfer reference often reveals it — record the alias in
   `supplier_aliases`, the reconciliation of orphans depends on it), shown to
   the user for validation in one go, not built by interrogation.

### 1. Qualify each expense — script first
```bash
python3 scripts/qualify_ticket.py --category <cat> --payment-date YYYY-MM-DD \
  [--invoice-date YYYY-MM-DD] [--foreign-supplier] [--vat-on-invoice 0|1]
```
The script renders the category verdict, the regime and the deadline
deterministically. For ambiguous categories or ones absent from the table, read
`references/vat-heuristics.md` (full table) then `references/exclusions.md`
(detail + exceptions). **Never improvise a verdict: the taxi is non-deductible
even on a business trip, it's counter-intuitive and it's the law** (CGI, ann.
II, art. 206, IV-2-5°).

### 2. Extract and analyze the FEC — script first
```bash
python3 scripts/extract_fec.py PATH_TO_FEC.txt            # summary
python3 scripts/extract_fec.py PATH_TO_FEC.txt --json out.json  # full export
```
The script does, deterministically: integrity checks (balance, per-entry
equilibrium, duplicates, fiscal-year bounds), balance by account, inventory and
classification of the 445x accounts, detection of CA3 filing entries and
reconstruction of output/input/net-payable by period, **QMG test** (deductible
balances never filed = the pool), reverse-charge equilibrium, list of 6xx
expenses without deducted VAT (ticket candidates, deadline 31/12 N+2 per line,
nature alerts), **time window** (open/time-barred years, days left, last filing
detected) and **accounting orphans** (401/4716 payments without a recorded
invoice, grouped by supplier).
**Report to the user: plain language, ONE single window.** The script's banner
is an instrument for the agent, never shown raw. Even with several FECs, the
user gets ONE single message on this template:
"Today is [date]. You can recover VAT on invoices going back as far as
01/01/[N-2], provided you declare it to the State in time. Concretely, year by
year:
  - your [N-2] invoices: to declare before **31/12/[N]** — [X] days left
  - your [N-1] invoices: before 31/12/[N+1]
  - your [N] invoices:   before 31/12/[N+2]
So I need your [N-2], [N-1] and [N] FECs, and your invoices from those three
years. On what's already analyzed, your VAT at stake is between [low] € and
[high] € — your invoices will tighten this figure. After your last filing
([month]): nothing is lost yet, you just need to provide the supporting
documents before the next one."
The ranges from several FECs are ADDED in this message; never a banner per
year, never jargon (tax base, vintage year, filing).
**The window is computed BEFORE any data** (law + today's date): from the
welcome, announce "we can dig into your expenses since 01/01/[N-2]" and use it
to request the FECs of THOSE years and the invoices from the same period. The
pot has TWO segments, both counted: `omission` zone (periods already filed:
line 21 recovery, deadline 31/12 N+2) and `to_secure` zone (later than the last
filing: VAT lost if the invoice isn't provided before the next CA3 closes —
action "photograph/upload the invoice", NEVER line 21, and the shortest urgency
of the whole mine: next filing deadline + physical expiry of thermal till
receipts).
To interpret the accounts: `references/fec-accounts.md` (⚠ 44567 convention:
debit = recording the credit, credit = allocation; 44564x/44574x "pending
chargeability" accounts = normal, not anomalies).
- VAT present in a **detected filing** → **already deducted**.
- 4456x balance in the pool, or a candidate expense without VAT → never
  declared → to qualify (stage 1) then route (stage 3).

### 3. Route to the right regime
Read `references/deadlines-and-regimes.md` for the detail. In summary:
- **French VAT on an invoice** → line 21 of the CA3 return, strict deadline
  31/12 of N+2 of the chargeability (N = min(invoice year, payment year) for
  prudence).
- **Foreign supplier (services)** → reverse charge: NO time bar if voluntary
  disclosure before any action by the administration (BOI-CF-INF-20-20, § 100),
  5% penalty avoided. Urgency = before any audit.
- Deadline passed + French regime → **dead** ticket (time bar), reason cited.

**Label -> category routing**: hierarchy accounting account > `alert_level` >
label via `scripts/route_label.py` (word boundaries mandatory — "pre**station**",
"Corbeil-**Esso**nnes" and internal references of type "REFINT_204" are real
traps). As a last resort: TO_REVIEW, never guess.
The `vat_amount` field of Qonto transfers is declarative (signal, not proof).

### 3 bis. Reconcile invoices ↔ transactions ↔ FEC
**Reconciliation is TRIANGULAR by definition**: analyzing the 44566/44562
accounts alone is not a reconciliation — the verdict comes out of crossing FEC
(expenses + VAT accounts) × bank transactions × invoices (already available,
accessible via the sources, or still to be found). Any conclusion drawn from a
single vertex of the triangle is provisional.
Read `references/statement-reconciliation.md`: the tuple to extract from each
invoice (with self-checks net+VAT=gross and gross=bank movement), hierarchized
matching keys (exact PieceRef > amount+date+supplier > label), full state table
(won / paid not recorded / inconsistency / upcoming / accounting orphan), and
handling of amendments-credit notes-duplicates. Reading the invoices = the
agent's native vision; everything else is deterministic.

### 4. Collect the invoices — systematic, proactive, BEFORE any conclusion
**No global verdict, no final figure, no proposal to write to suppliers as long
as this stage is not carried to its end.** Sequence:
1. **Inventory of sources — BEFORE any figured report.** Scan the full
   configuration of the session (all available connectors: pre-accounting/
   receipt tool FIRST, bank, Drive, mail) and fold it into the post-FEC report
   as an assertion, not a question: "your invoices seem to live in [connected
   accounting tool] and in bank attachments — I'm going to look there, in that
   order". The clarification question only bears on the gaps (uncovered
   periods/sources). **We never ask permission to launch the collection ("shall
   I start?" is forbidden): we announce, and we launch.**
2. **Automatic collection first** — the agent goes and looks, it does not ask:
   attachments of the Qonto transactions (`list_transaction_attachments` +
   `get_attachment`, direct download authorized: it's the client's data);
   invoices from the pre-accounting/receipt tool if plugged in; Gmail as
   **scouting only** (identify the messages carrying invoices, never an
   automatic download of mail attachments). Everything collected goes into the
   **session invoice folder** (the "mine"), with an announced count: "I found X
   invoices covering Y lines".
   **Mandatory pivot**: if the bank attachments are massively empty
   (`attachment_ids: []` everywhere), that is NOT "no invoices" — it's the
   signal that the invoices live elsewhere, almost always in a pre-accounting/
   receipt tool. Chain on immediately: identify the tool — a choice
   clarification question if necessary, BEARING IN MIND that the tool can change
   from one year to the next ("your 2025 invoices: 1. [detected connected tool]
   / 2. another tool / 3. a folder; and 2024?") — then collect there.
3. **Then ask the user for the rest, with instructions**: "where do your other
   invoices live?" in numbered choices (local folder to drag here / photos of
   till receipts to take now / export from your invoicing tool / other), with a
   mini-tutorial per option (e.g.: "in your receipt tool: selection > export >
   drag the zip here").
4. **As a last resort only** — invoices untraceable everywhere: offer to write
   to the suppliers (drafts provided, never sent). Offering this option BEFORE
   having exhausted 1-3 is a process defect.

Then check each collected invoice (formal conditions) — full grid in `references/formal-conditions.md`. The three verdicts:
- 🔴 invoice in the director's name (≠ company) → amendment IMPERATIVE before
  entry, and the amendment DOES NOT RESTART the deadline (CE 31/12/2008,
  no. 305517) — the countdown runs during the wait.
- 🟡 an isolated missing mention, amounts/rate/date legible, business reality
  proven (the bank transaction) → deductible with documented reservation.
- 🟢 compliant (art. 289 CGI + 242 nonies A ann. II) → exact VAT to the pack.

### 3 quater. Estimation — category-based, never a uniform rate
**Forbidden to announce a uniform 20% range of the tax base.** The estimate is
built line by line, including the first qualification steps BEFORE any
announcement: (1) the script provides `estimated_vat` per line (exclusions by
nature at 0, reduced rate where applicable, VAT included otherwise); (2) the
agent refines by passing the labels through `route_label.py` then
`qualify_ticket.py` — taxis/trains/hotels drop to 0, catering to 10%, reverse
charge to 0 in cash terms, foreign VAT out of the CA3; (3) the supplier profile
bounds the range (low = corroborated). The figure shown to the user is ALWAYS
post category-routing.

### 4 ter. Clarification interview — AFTER collection and analysis, never before
Once FEC + invoices + transactions are analyzed, generate the MINIMAL list of
questions that the data does not settle, and ask them in ONE grouped pass (not
a stream of questions). Canon of legitimate questions:
- **Leasing detected**: which asset? (passenger car → all excluded; utility
  vehicle/equipment → deductible)
- **Vehicle**: company-owned, leased, or personal vehicle with mileage
  allowances? (changes fuel, parking, maintenance)
- **Foreign SaaS/suppliers charging local VAT**: was the intra-community VAT
  number declared to the supplier? (otherwise: "tax ID" ticket — foreign VAT
  charged in error is recovered ONLY through supplier correction, never on the
  CA3 nor via 2008/9)
- **Credit note / negative amount detected**: which invoice does it bear on?
- **Hotel**: who slept there? (director → excluded; third party/client →
  exception)
- **Abnormal account 7** (subsidy, bare rent, exempt revenue): exact nature,
  for the coefficient.
Each question must cite the line that motivates it. A question whose answer is
already in the data is a defect to fix.

### 4 quater. THE TICKET FACTORY — deterministic, never in the agent's head
```bash
python3 scripts/build_tickets.py --fec fec2024.json --fec fec2025.json \
                                 --invoices invoices.json --out tickets.json
python3 scripts/build_pack.py tickets.json --siren X --company Y --out-dir livrables/
```
**The agent NEVER builds a ticket by hand.** Before this script, the pass
"candidates + orphans + invoices → tickets" was redone from memory on every
run: that is exactly what produced the "Émilie" bug. A rule in prose gets
violated; an exception, not.

`build_tickets.py` enforces **mechanically**:
- `vat_amount` (declarable) can ONLY come from the vision of an invoice;
  `estimated_potential` (inferred) never can. **The two never merge**, and the
  pot **exposes no total**.
- `won` **impossible** without a read invoice → `TicketInvariantError`, the run
  stops.
- **An invoice is used only once** (otherwise: double deduction).
- The deadline recomputes on **min(invoice date, payment date)**; a time-barred
  ticket becomes `dead`, never a won with a green hourglass.
- The **rate must be plausible** (20/10/5.5/2.1%): an invoice at 50% is
  misread, it goes to `to_review` — we don't declare it.
- The recovery action and the effort come from
  `references/invoice-retrieval.md`: **a card without an action is a defect**.

`build_pack.py` **refuses to write** into `pack-line21.csv` any line without a
read invoice, duplicated, time-barred, or with a non-finite amount (NaN/Inf).
The total of the SIE letter is **the sum of the CSV**, never a figure carried
over from the interface.

### 5. Produce the output (always in the conversation, never transmitted)
Ticket statuses: `won` (compliant invoice + never declared + within the
deadline), `to_play` (orphan, estimate + recommended action), `to_secure`
(current-flow zone: VAT estimated via category routing, counted in the pot,
action = provide the invoice before the next CA3, regime = current return and
not line 21), `dead` (excluded by nature or time-barred, legal reason),
`already_deducted`. Accounting orphans in the current-flow zone (paid till
receipts, never photographed or uploaded) are `to_secure` tickets. Each line of
the pack carries: nature of the expense, deductible character, invoice, amount,
deadline — that's the judge's standard of proof (CAA Paris 23PA01221, pt 10).
The actual generation of the files goes through the GO/NOGO gate (stage 6).

### 6. GO / NOGO gate — mandatory end of process
**Precondition: the gate is only reachable after stage 4 (invoice collection)
carried to its end and the qualification of everything qualifiable.**
The process ALWAYS ends in the conversation, via this sequence:
1. **Recap**: pot announced as a **low–high RANGE**, never as a single figure
   before reconciliation of the invoices (low = corroborated VAT: suppliers
   taxable per history + QMG pool; high = theoretical VAT of the whole tax base
   excluding exclusions), broken into two segments (omission / to secure),
   tickets by status, time window, pending actions — **including, AS A MATTER
   OF COURSE, the scan of the last few months' payments stuck in a suspense
   account (4716/orphans, to_secure zone)** with the action "claim these
   invoices before the next CA3 is filed": it's a standard component of the
   recap, never a check done only if the user thinks of it. The invoice-by-
   invoice reconciliation then tightens the range into won / to-scratch
   tickets. No file is generated yet, nothing is transmitted.
2. **Explicit question to the user**, in numbered choices AND in user language —
   never "generate the pack" without saying what it is:
   "1. YES — I prepare the documents for your accountant: the line-by-line
   recap table, the letter ready for the tax office, the list of still-missing
   invoices and the annex of points for them to check
   / 2. NO — we stop here, nothing is created
   / 3. Show me the detail of a ticket first"
3. **On GO**: generate the four deliverables as session files:
   - `pack-line21.csv` — one line per ticket, FIXED columns (the order matters,
     it's what makes two runs comparable): `ticket_id; status; zone;
     invoice_date; supplier; expense_nature; net_amount; vat_amount; rate;
     invoice (ref/file); verdict; legal_source; deadline; days_left; action`.
   - `sie-letter.md` — template `assets/sie-letter-template.md` filled in
     (SIREN, period, line 21 amounts).
   - `missing-invoices.md` — `to_play` and `to_secure` tickets with the action
     per line (claim, photograph, upload).
   - `accountant-annex.md` — the points that fall to the accountant's judgment,
     never left loose in the conversation: strict duplicates detected,
     reverse-charge discrepancies, unreconciled 401/4716 balances,
     opening-balance residues — each with the precise question to ask them.
   **The 4 deliverables are produced on EVERY GO, same names, same skeletons,
   whatever the completeness of the data** — including at 0 € declarable. A
   section without content carries the standard mention "Not covered —
   [reason] — [action to cover]" (e.g.: "Fiscal year 2024 not covered — FEC not
   provided — deadline 31/12/2026, to export from the accounting tool").
   Never 2 or 3 files "as the case may be", never improvised names: that's what
   makes two runs comparable (diff) and the result predictable.
   **Contradictory signals on the same line** (label vs account vs profile,
   e.g. "Service invoice" journaled as leasing): single canonical treatment =
   `TO_REVIEW` verdict, the question to the accountant in `accountant-annex.md`
   AND the invoice requested in `missing-invoices.md` — never settled on a
   single signal, never phrased differently from one run to the next.
4. **On NOGO**: stop at the recap. Nothing is produced.
5. **In both cases, NO automatic transmission**: sending to the accountant
   (draft email, shared folder) is a separate action, explicitly requested by
   the user after the gate — never triggered by the skill. The skill never
   writes into external systems (bank, pre-accounting, mail): every run is
   side-effect free.

**Replayability (test protocol)**: frozen inputs (same FEC, same invoice
folder, bounded period) → identical deliverables on the next run. To test a
skill modification: replay the same scenario, `diff` the `pack-line21.csv`
between the two runs — any gap is either the expected improvement or a
regression.

**The pre-invoice pot is a high bound, by construction.** Vision can drop it to
zero (foreign VAT on the invoice, non-probative attestation): that's a feature,
not a failure — the tool that corrects itself at the invoice is the one a tax
specialist can defend.

**Coefficient guardrail — BLOCKING, not advisory.** Before any verdict, scan
the account 7s (signals in fec-accounts.md §coefficient): exempt revenue,
subsidies, bare rents, dividends = likely partial taxpayer. As long as
coefficient = 1 is not confirmed, **no reverse-charge card is openable** and all
"100% deductible" verdicts are conditional. Without this guardrail, the product
sells a gain and delivers a reassessment: a partial taxpayer who "voluntarily
discloses" 4,000 € of SaaS self-reports for a net reassessment (the
non-deductible fraction is reassessed, with late interest, art. 1727).

**MANDATORY warning before the GO gate**, spelled out in full:
> "We have only analyzed the VAT you can **recover** — not the one you
> **charge** your clients. A request for justification, however, can bear on
> both."

That's the sentence which, on the day of the dispute, separates a loyal
publisher from a negligent one. The skill's scope (invariant 3) is a product
choice; not telling the user would be a fault.

**Offset rather than refund.** If the month's CA3 return is in VAT payable,
line 21 **simply reduces the payment**: no refund request, no investigation, no
supporting documents to produce. Same money recovered, far lower exposure.
**Compute it and say it** — it's a lever absent from most firms.

**Vocabulary — the publisher's shield.** Never "you must declare", "we advise
you". Always: "**your invoices show X**", "**the law provides Y**", "**your
accountant decides**". The product **states**, it does not **recommend**. This
nuance is the line of defense against the monopoly on figures (ord. 45-2138)
and on law (law 71-1130, art. 54).

**Blacklist — refer to a tax specialist without concluding**: stakes > 50k€
with uncertain qualification; tax audit in progress or reassessment proposal
received (voluntary disclosure no longer possible); contested VAT permanent
establishment; VAT on real-estate margin (268); reclassification of works/
intellectual services into construction; training vs consulting exemption;
abuse of law; multi-State with double (non-)taxation. Sales/foreign references:
sales-territoriality.md, exclusions-by-country.md. Audit prioritization by
activity and fragile tolerances: errors-by-profile.md.

## Game layer — the board, opening the cards, the orchestration
This layer dresses the process (it never replaces it): the invariants and the
sequence stay identical. Decisions ratified in the 12/07/2026 meeting
(Sami / Matthieu / Lou), **corrected and locked on 13/07/2026**.

### The mechanic, in one sentence
> **The game consists of turning GRAY into GREEN.**
> Gray = inferred amount, under glass, locked, non-declarable.
> Green = read invoice, certain amount, yours.
> **The "up to" is the lock. The invoice is the key.**

Honesty is not a constraint placed on the game: it IS the game. Green is a
**state of the database** (`invoice != null`), not a string — celebrating an
inference becomes technically impossible.

### Opening semantics — mapping onto the statuses
**⚠️ Correction of 13/07/2026 — the earlier version ("scratch = launch the
vision, load time assumed") was REJECTED in the meeting.** A wait time on click
kills the dopamine; and above all, it did not attack the real problem (making
the user do the effort of going to fetch their invoice).

- **ALL the vision reading happens AT COLLECTION**, never on click. When a card
  displays, its verdict is already established (`tickets.json`).
- **`won`** (invoice read): the card flips and **the amount is firm**. It's
  celebrated (confetti, chime) — we only celebrate what's secured.
- **`to_play` / `to_secure`** (no invoice): the card flips and stays **UNDER
  GLASS**. Flipping ≠ unlocking: nothing has been recovered. It mandatorily
  shows (1) the high bound in the imposed format, (2) **where to find the
  invoice** (references/invoice-retrieval.md), (3) **the estimated effort**. A
  bare amount without an action or effort is a defect: it's the broken promise
  (dangle a gain, deliver a chore).
- **`fix`** (foreign SaaS without an intra-community VAT number): **no amount**.
  It's not a gain to recover, it's a **leak to plug**. Foreign VAT charged in
  error is neither deductible (art. 271, II-1-a) nor refundable via 2008/9.
  Action = enter the intra-community VAT number, and reclaim the past when the
  supplier allows it (Google, AWS, OpenAI).
- **`dead` / `already_deducted`**: **never openable**. They arrive already
  flipped, stamped "EXCLUDED BY LAW", with the article cited. Making someone
  open a zero is theft of time — and the user feels it as contempt. They prove
  the seriousness of the audit and save time.

### THE PAYOFF — the unlocking, not the reveal
80% of the juice goes to the moment the invoice arrives: **the glass breaks**,
and the amount **leaves LOCKED to enter SECURED** before the user's eyes. It's
the only moment the product is seen. The flip is just the scenery.

### The grammar — imposed by the code, never by the prompt
The word "**probable**" (and "likely") is **FORBIDDEN** (indefensible
statistical assertion — tax specialist's note, 13/07/2026). Single format,
generated by `build_tickets.py`:
> **Up to X € — if your <F> invoice carries French VAT.
> You cannot declare anything until you have it.**

**No countdown on a potential**: letting a right you don't know exists expire is
a manufactured urgency (art. L. 121-6 C. conso). The hourglass only lights up
after the invoice is read.

### Rarity — relative, never absolute
A 12,000 € pot would make every card "legendary" — and if everything is
legendary, nothing is. **ONE SINGLE jackpot per board** (the maximum, and
≥ 120 €). It's THE card that gets the director out of their chair. The aura is
revealed **only on hover**: the back is identical for all.

### Experience rules — non-negotiable
1. **Immediate reward on upload.** As soon as the user uploads photos or
   invoices, reconciliation and display of the gain RIGHT AWAY: the upload is
   rewarded in itself. Never "thanks, we'll see later".
2. **Never a blocking injunction mid-session.** "Go fetch your invoice" NEVER
   interrupts a session: cards without an invoice reveal their high bound then
   stack up in "to recover" (= `missing-invoices.md`), handled when the user
   wants.
3. **Two modes, always**: one by one, and **"Open all"** (lazy mode). But the
   shortcut only appears **after 3 cards opened by hand**: it would burn the
   ceremony on the first click. It's a reward, not the entry door.
4. **The accountant email is NEVER conditioned on complete opening.** As soon
   as ONE ticket is secured, the email is generable. We don't hold the user
   hostage to their own exhaustiveness.
5. **The product order: visible gain first, effort second.** The scan and the
   range drop BEFORE any request for effort — no one goes digging through their
   till-receipt box without knowing what it's worth.
6. **The email is written FOR the accountant, not against them.** They engage
   their responsibility by filing the CA3: a pack that accuses them by
   implication will be refused, and the product will have manufactured the
   blocking of its own value. Imposed wording: "these invoices **probably never
   made it up to you** — can you confirm they weren't already declared, and
   **arbitrate** their entry?". Never a finding of fault. We give them an
   honorable exit: that's what decides whether the money comes in.

### Interface — the board (Cowork artifact)
The code lives in **`assets/board.html`** — a **standalone HTML file** (Cowork
artifacts are NOT JSX: `create_artifact` takes an `html_path`). The old
`scratch-interface.jsx` stub aimed at the wrong target.

Platform constraints, **verified by test** (13/07/2026):
- The artifact opens **in a panel to the right of the chat, in the same
  window**. The chat stays accessible: that's where the user uploads their
  invoices.
- **An artifact CANNOT read an image** (no vision in JS) nor **write into the
  conversation**. All intelligence goes through the model, in the thread.
- It CAN call the connectors (`window.cowork.callMcpTool`) and remember its
  state (`localStorage` works).
- The board **reads `tickets.json` and never computes a verdict.**

Buttons → actions:
`open(card)` → **local, instant** reveal (the verdict is already there);
`open_all()` → accelerando cascade, solo finale on the jackpot;
`find_it()` → panel: where, effort, prerequisites, traps, and **the gesture**
(drop the PDF into the conversation);
`accountant_email()` → shows the written email + **"Copy"** (always works) +
attempt at a **Gmail draft** via `callMcpTool`. **Never a send.**

### Cowork orchestration
The orchestration prompt to paste into the project lives in **`CLAUDE.md`**
(root of the folder) — source of truth of the orchestration, to maintain
alongside this SKILL.md. `assets/prompt-cowork.md` is its long version (real
usage + demo mode).

## Maintenance
Before any release, run `python3 scripts/check_bofip.py` — every BOFiP
reference cited in the skill is checked against the official "publications in
force" set (data.gouv.fr); a reference not found = reported doctrine or a typo,
blocking.

## Guardrails — documented errors not to reproduce

- **Never a bank-vs-CA3 comparison on an isolated month** nor on the output
  side: credit carryovers, chargeability and multiple collection channels
  produce normal gaps. Lived error: 12 K€ of "gap" that were collections on
  another channel.
- **Exclude credits and loans/contributions before any computation** (lived
  error: a 30 K€ loan counted as revenue).
- **Any anomaly detected by a script is reproduced by hand on the raw entries
  before being flagged.** No accusation against the accountant goes out without
  a manual check on the entries themselves.
- **"Exempt/excluded by nature" NEVER closes a ticket without the invoice.**
  Invoices are often MIXED: a broker invoices fees subject to VAT on the same
  invoice as the exempt premium; an excluded hotel splits out a breakfast
  deductible at 10%; an excluded rental carries deductible ancillary charges.
  The category gives the verdict of the MAIN line; the invoice reveals the
  secondary lines. Lived error: insurance closed on the "premium" tag when the
  online broker could invoice fees.
- **Any split inferred from amounts (and not from invoices) is a HYPOTHESIS**:
  mark it "(amount hypothesis)" in the pack and list it for confirmation by
  invoice — never present it as settled.
- **The PCG contains NO deductibility rule** (accounting law ≠ tax law). Real
  sources: CGI art. 271/283/298-4, ann. II art. 205-208, BOFiP series
  BOI-TVA-DED. The PCG only serves for mapping the FEC accounts and the
  supporting documents (art. 1032-1 and 1032-2).
- **Two sources meant to be consistent that diverge are NEVER absorbed in
  silence.** An export from the accounting tool (Pennylane…) and the FEC issued
  by the same tool must tell the same story; any gap between them becomes a
  figured point in `accountant-annex.md` (amount on the export side, amount on
  the FEC side, lines concerned) — never melted into the range without a trace.
  Lived error (12/07/2026): 1,076 € "found" on a Pennylane export not aligned
  with the FEC from the same tool, invoices untraceable, without a traced
  explanation.
- **Estimation ≠ declaration.** The exact figure legally exists only with the
  invoice; the estimate serves to decide (go/no-go), never to declare.
- **This skill states, it does not declare.** Filing by the accountant or the
  legal representative only.

## References (read as needed)
- `references/vat-heuristics.md` — operational category → verdict table,
  sourced. THE source of truth of the category verdicts.
- `references/exclusions.md` — each exclusion in detail with its exceptions
  (vehicles, transport, lodging, fuels, gifts, related services).
- `references/deadlines-and-regimes.md` — deadlines, line 21, reverse charge,
  full case law (QMG, CE 2008), filing procedure.
- `references/formal-conditions.md` — compliant invoice, tolerances, grid of
  verdicts for the checking agent.
- `references/fec-accounts.md` — mapping of 445x accounts ↔ CA3 lines, corrected
  44567 convention, intermediate accounts 44564x/44574x.
- `references/statement-reconciliation.md` — invoice tuple, matching keys, state
  table invoice↔transaction↔FEC, amendments/credit notes.
- `references/invoice-retrieval.md` — **where to find each invoice**, supplier
  by supplier (exact path, effort, prerequisites, traps), sourced with a minimum
  of 2 sources. Includes the **intra-community VAT number catch-up table** on
  foreign SaaS (Google and AWS refund retroactively; Anthropic and LinkedIn
  never). A false navigation path destroys trust more surely than an "I don't
  know": what is not verified is marked ❌, never invented.
- `scripts/build_tickets.py` — **THE FACTORY**. FEC + invoices → `tickets.json`.
  The three mechanical locks. 17 fixtures.
- `scripts/build_pack.py` — the 4 deliverables. Structurally refuses any
  non-declarable line. 5 fixtures.
- `scripts/check_bofip.py` — CI: checks the BOFiP citations against the doctrine
  in force (data.gouv.fr).
- `assets/board.html` — **the interface** (Cowork artifact, standalone HTML).
  Reads `tickets.json`, never computes a verdict.
- `CLAUDE.md` — orchestration prompt to paste into the Cowork project.
- `assets/prompt-cowork.md` — long version (real usage + demo mode).
