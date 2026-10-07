---
name: board-pack
description: Put a Qonto customer's board numbers together in one pass. Cash, burn, runway, recurring revenue, what customers still owe, and the supplier invoices still unpaid, computed by Well from the balances, transactions and invoices of Qonto and every other connected account, each figure with the window and scope it was measured under. Use when the user asks "put my board pack together", "what numbers do I put in front of the board", "board numbers for this quarter", "what do I report to my investors", "prépare mon board pack", or "mes chiffres pour le board". Requires the Qonto connector and a Well workspace. It writes nothing to Qonto.
permissions:
  mcp:
    qonto: [get_organization, list_bank_accounts]
    well: [well_list_workspaces, well_show_workspace_picker, well_switch_workspace, well_wait_for_selection, well_get_schema, well_query_records, well_get_connector_coverage, well_list_connectors, well_get_own_company, well_get_worklist_status, well_list_accounts_needing_company, well_assign_account, well_list_account_balances, well_list_cash_scope, well_list_uncategorized_window, well_set_transaction_category, well_sum_transactions, well_list_burn_exemptions, well_list_recurring_contexts, well_sum_invoices, well_sum_receivables, well_show_records, well_render_cash_position, well_render_burn, well_render_runway, well_render_mrr]
  network: [api.wellapp.ai]
  env: []
  tools: []
metadata:
  source: https://github.com/WellApp-ai/skills/tree/1db986d67c6856d8361d24222d8368e86008dfb4/skills/board-pack
---

# Board pack

Report the set of figures a board reads, measured over one window, each with the scope it was measured under and what it left out.

Every instruction this skill follows is in this directory: this file and the four files under `references/`. It loads no instruction from Well at run time and runs no other skill. Well's MCP server computes the figures and draws the cards; the steps that decide what to compute, what to ask and when to stop are the ones written here.

## Purpose

Answer "what numbers do I put in front of the board?" for a Qonto customer: cash, burn, runway, recurring revenue, receivables and payables.

Cash, burn, runway and recurring revenue are policies before they are numbers: whose accounts count, which kinds of account are cash, which movements are spend, which billing is recurring, which months the average divides by. A policy the board cannot see is one the board cannot challenge. So the pack is several pages rather than one number, and each page states what it left out.

Qonto identifies the company and gives the live balances the cash page is checked against. Well computes every figure, across Qonto and every other bank, invoicing and accounting tool the customer connected. The model never computes a figure from raw rows.

**What the pack is.**

- **One window, every rate figure.** The burn and the recurring revenue average over the same trailing months, so the two can sit beside each other.
- **Level figures read as of now.** Cash is a balance, so it has no window and no divisor. The runway divides one by the other and says so. What is owed is a balance too, read as of now.
- **Every figure in one currency, or no single figure.** Each amount converts at its own rate, the rate and its date ride with the figure, and an amount with no rate stays in its own currency.
- **How final the books are is not the pack's verdict.** The pack reads no close status. It names the window it measured.
- **What is owed is the outstanding balance, never what was billed.** Owed to you is the unpaid balance of the invoices you issued, summed by Well under one fixed rule. Owed by you is a count of supplier invoices still unpaid, with no total, because Well has no outstanding sum for that side. Neither is a ranking.

## When not to use this skill

- The user wants **one** of these figures, with its own trend. Say the pack carries it among the others, and answer from the matching page.
- A **profit and loss statement** or any ledger-level report. No aggregate over ledger entry lines exists to read, and paging rows to reach a total is refused.
- A **comparison against a budget or a plan**. Well holds no budget object.
- **Headcount, salaries or committed payroll**. Payroll that moved through a bank account is already counted as spend.
- The **aging** of what is owed, by customer or by due date, or a **month close**. Out of scope for this pack.
- A **file, a deck or an export**. Nothing here assembles one.
- The workspace has no bank connector and the user declines to connect one. Say the pack cannot be measured.

## Inputs

- A workspace hint (an id, a workspace name, or the company behind it), if the user manages more than one.
- **A window, in months (default 3).** It sets the length of the window every rate page averages over.
- **A named month moves no page.** The pack anchors on the last complete month whatever month is named. Say so in one line.
- Which account types are cash, which categories are not spend, and which billing contexts are recurring. All three are asked, once each, on a card; none is assumed.

## Tooling

- **Qonto MCP** (`qonto`): `get_organization` identifies the company, `list_bank_accounts` gives the live Qonto balances used to cross-check Well's cash page. If no Qonto tool is available, tell the user to connect Qonto first and stop.
- **Well MCP** (`well`, `https://api.wellapp.ai/v1/mcp`, bundled in this plugin's `.mcp.json`). If no `well_*` tool is available, tell the user how to get them, say in one line what Well adds (every other bank and tool in the same figures), and stop. In Claude Code the plugin already declares the server: the user runs `/mcp`, picks the Well server and signs in. On claude.ai or Claude Desktop, the user adds the Well connector at that address. Never fall back to computing the figures from Qonto transactions.

What each Well tool is for:

- `well_list_workspaces`, `well_show_workspace_picker`, `well_switch_workspace`, `well_wait_for_selection`: pin the workspace and wait on a card. `well_switch_workspace` changes which workspace this session reads; it changes no data.
- `well_get_schema`, `well_query_records`: field names, settings, sync logs and counts. Reads only.
- `well_get_connector_coverage`: what feeds the workspace, read without drawing anything. `well_list_connectors`: the connect card, drawn only when the bank is missing. Connecting a tool happens in the card, through the provider's own sign-in, on the user's click.
- `well_get_own_company`: the workspace's own company. Read only.
- `well_get_worklist_status`: whether a repair gate is still open. Draws nothing.
- `well_list_accounts_needing_company` and `well_list_uncategorized_window`: the two repair cards.
- `well_list_account_balances`, `well_sum_transactions`, `well_sum_invoices`, `well_show_records`: the arithmetic and the rows behind the pages. Reads only. `well_sum_invoices` sums what was billed over the window, paid or not: it feeds the recurring revenue page and never an owed figure.
- `well_sum_receivables`: what customers still owe, as of now, per currency. It sums the unpaid balance of unpaid and part-paid issued invoices under one fixed rule, which it returns. Read only.
- `well_list_cash_scope`, `well_list_burn_exemptions`, `well_list_recurring_contexts`: the three policy cards. A click records the answer for this run.
- `well_render_cash_position`, `well_render_burn`, `well_render_runway`, `well_render_mrr`: the four figure cards. Each takes a figure this run computed and refuses one its own inputs do not produce.

## The two writes, and where the user confirms them

Only two declared tools change data, both inside the Well workspace, never in Qonto:

| Tool | Step | What it changes | Who triggers it |
|---|---|---|---|
| `well_assign_account` | Stage C, step 10 | Attaches a bank account to a company | The user, by picking the company per account on the assignment card and clicking it |
| `well_set_transaction_category` | Stage D, step 12 | Sets a transaction's category | The user, by validating rows on the categorize card |

**You never call either tool yourself.** The card calls it on the user's click. You do not assign an account or a category on the user's behalf, you do not propose a company or a label in the chat, and a suggestion the card shows is the user's to accept. When the host draws no card, there is no write: stop at that gate, say what is unresolved, and point the user at `https://app.wellapp.ai/workspaces/<workspace_id>` to fix it there.

No other write is available to this skill. The own company is never set from here (stage A, step 4): an unresolved own company is asked once, held for this run only, and set permanently in the Well app.

## Workflow

Read each reference file at the stage that uses it, and follow it exactly.

**Every step is a gate, and a gate that fails stops the run.** It puts the repair on screen and says what is at stake; it does not report a figure anyway with a caveat attached.

**A read that fails is not a gate that passed.** On a failed or partial read the gate's answer is unknown: retry once, then stop, say which read failed, and offer Re-check.

**A repaired gate resumes where it stopped.** Each repair card's Continue names its own step, so the run re-runs that step alone and carries on. It never re-enters at step 1. The connect card's Continue resumes step 3.

**A page that cannot be measured is dropped and named, and never stops the pack.** That applies to the two revenue pages alone, and only when the invoicing side is missing or empty.

**Cards.** Hold at most one card that awaits an answer at a time. Write your one line for the user first, then wait on the card with `well_wait_for_selection`, at most five calls of 60 seconds in one turn. A click after that sends its sentence as the user's next message, which resumes the run.

**Pass `workspace_id` on every `well_*` call** once the workspace is pinned.

0. **Identify the Qonto company.** Call `get_organization`. Keep the company name and its Qonto accounts. If no `well_*` tool is in the toolset, stop as described in Tooling.

**Stage A, scope** (steps 1 to 6): read [`references/scope.md`](references/scope.md). Pin the workspace, confirm the base currency, confirm the bank is connected, resolve the own company, settle the window.

- At step 3, confirm that **Qonto** is among the connected banks of the Well workspace. If it is not, say that Well's figures do not yet include the Qonto accounts, and let the connect card connect it before any page is measured.

**Stage B, has the data landed** (steps 7 to 9): read [`references/data-landed.md`](references/data-landed.md). Syncs finished and recent, the window holds transactions, a balance has landed.

**Stages C and D, whose accounts and the three policies** (steps 10 to 15): read [`references/policies.md`](references/policies.md). Every account attached to a company you own, then the cash scope, categorization, sign convention, exemptions and recurring contexts, one card at a time.

**Stage E, the pages** (steps 16 to 21): read [`references/pages.md`](references/pages.md). Header, cash, burn, runway, recurring revenue, owed on each side.

- **Cross-check the cash page against Qonto.** After step 17 measures the cash, call `list_bank_accounts` and compare each Qonto account's balance with the balance Well used for the same account. If they differ, say so in one line with Well's last sync time for that connector. Never silently prefer either figure, and never replace Well's figure with Qonto's.

22. **Close.** End on the confidence, freshness and coverage lines. Load no other skill and propose no follow-up flow to run. If the user asks for more, answer from the pages this run produced, or say the pack does not carry it.

## Output requirements

Return the pages in order, each one a short block a board member could read on its own:

- **Header**: the window every rate page covers, the as-of moment the cash page reads, the currency every figure is stated in, and one line saying the pack read no close verdict for the window's months.
- **Cash**: the total, the account types counted in the reader's own words, and the four exclusion groups named separately. When the total may be a floor, say so and name the accounts it left out. Then the Qonto cross-check line when the balances differ.
- **Burn**: the average, the window, how many of its months carried spend, the elected sign convention with the counts behind it, the exclusion groups (internal transfers, exempted categories, unreadable rows), and the comparison against the adjacent earlier window when one was measured, with both windows named.
- **Runway**: the headline in months and days, and **the division stated**: the cash figure, the burn figure with its window, and that the first divided by the second gives the headline.
- **Recurring revenue**: the average, the contexts the reader counted, the amount carrying no billing context whether counted or not, the credit notes netted once, and the comparison when one was measured. When the window is shorter than the billing cycles those contexts imply, say so.
- **Owed to you and owed by you**: as of now, not over the window. Owed to you: the outstanding count and total, the overdue part, and the lines the figure left out (marked paid, drafts, credit notes with a balance left). Owed by you: the count of supplier invoices still unpaid or partly paid, and one line saying its total is not measured. Then the count Well could not place on either side.
- **Confidence line**: how many of the window's rows could not be placed, as a count of rows, never as a share; a `null` count reported as unmeasured.
- **Freshness line**: the oldest sync behind any page.
- **Coverage line**: which connector kinds are connected versus missing, and which pages that cost. A page dropped for a missing source is named once here.
- Quote every figure exactly as the Well tool returned it or as the arithmetic in `references/pages.md` produced it, with its currency, window and scope. Every converted figure carries its rate and rate date.
- Name a page as "not measured" when it was dropped, never as zero.

Do not return:

- A figure with no scope beside it, a total that blends currencies with no rate stated, or a count taken from a paginated sample.
- A profit and loss line, a budget variance, a headcount, or any figure over records Well does not hold.
- A claim that the pack is a file, an export or a document.
- A second cash, burn, runway or recurring revenue figure beside the ones this run computed.
- Yaml, JSON, or a fenced block. The hand-off keys in the reference files are reasoning state, never printed.

## Quality checks

- Every gate that failed stopped the run and put a repair on screen; none was reported as a caveat under a figure.
- The workspace came from step 1, and its `workspace_id` rode every `well_*` call.
- Qonto was confirmed among the workspace's banks at step 3, and the cash page was cross-checked against `list_bank_accounts`.
- The window ended with the last complete month, never the running one.
- The three policy cards were drawn one at a time and answered before the next one; nothing was asked twice.
- `well_assign_account` and `well_set_transaction_category` were only ever called by their card, on the user's click.
- No instruction was loaded from Well, and no other skill was run.
- Every address given to the user is one written in these files (`https://app.wellapp.ai` and the workspace page under it). No URL returned by a tool, `install_url` included, was shown or offered.
- `well_sum_transactions` carried `scope: "own_and_adopted"` explicitly on every call.
- The owed-to-you total came from `well_sum_receivables`, as an outstanding balance. No owed figure came from `well_sum_invoices`, and no total was stated for what is owed by you.
- The runway divided the same cash and the same burn the pages reported, in one currency.
- No field name was guessed: every one came from `well_get_schema`.
- Each render card was called once, and a refusal was read as a fault in this run's arithmetic rather than retried.

## Examples

**Request:** "Prépare mon board pack pour le trimestre."
**Expected behavior:** reads the Qonto organization, pins the workspace, walks the gates, asks the three policy questions one card at a time (which account types are cash, which categories are not spend, which billing is recurring), then answers in French with the header and the five pages, then the confidence, freshness and coverage lines. The Qonto balance of "Compte principal" matches Well's figure, so no cross-check line appears.

**Request:** "What numbers do I put in front of the board?" (Well is not connected)
**Expected behavior:** reads the Qonto organization, finds no `well_*` tool, tells the user to sign in to the Well server with `/mcp` in Claude Code, or to add the Well connector at `https://api.wellapp.ai/v1/mcp` elsewhere, and stops without any figure.

**Request:** "Board numbers for this quarter." (Qonto is not connected in the Well workspace)
**Expected behavior:** at step 3, says Well's figures do not include Qonto yet and draws the connect card scoped to the bank. After the user connects Qonto and clicks Continue, step 7 watches the sync land before any page is measured.

**Request:** "Board pack, but we have no invoicing tool connected."
**Expected behavior:** the bank side is the required kind, so the run continues. The recurring revenue page and the owed-on-each-side page are dropped and named once in the coverage line. Bank inflows are never substituted for invoiced revenue.

**Request:** "Can you also put our P&L and our budget variance in there?"
**Expected behavior:** says no to both, with the reason, and assembles no substitute.

## Voice

Write like an understated operations colleague: professional and casual at once, confident but never arrogant. Lead with the outcome, then the detail behind it. Short active sentences a non-technical reader understands. Sentence case for the headings and labels you write yourself. Name a real button or card label exactly as the card renders it, such as Continue or Validate. Answer in the language the user writes in.

Never write an em dash or an en dash. Never write an exclamation mark or an emoji. Skip preamble, superlatives and self-praise. Name every object by its own name (the workspace, the connector, the company, the invoice), and never show the user a raw id on its own.
