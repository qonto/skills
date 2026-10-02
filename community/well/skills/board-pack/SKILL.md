---
name: board-pack
description: Assemble the board numbers for a Qonto customer in one pass. Cash, burn, runway, recurring revenue, and what is owed on each side, computed by Well from the balances, transactions and invoices of Qonto and every other connected account, each figure with the window and scope it was measured under. Use when the user asks "put my board pack together", "what numbers do I put in front of the board", "board numbers for this quarter", "what do I report to my investors", "prépare mon board pack", or "mes chiffres pour le board". Requires the Qonto connector and a Well workspace. It writes nothing to Qonto.
permissions:
  mcp:
    qonto: [get_organization, list_bank_accounts]
    well: [well_get_skill, well_search_skill, well_list_workspaces, well_show_workspace_picker, well_switch_workspace, well_wait_for_selection, well_list_connectors, well_get_connector_coverage, well_get_worklist_status, well_get_schema, well_query_records, well_get_entity, well_show_records, well_list_account_balances, well_list_accounts_needing_company, well_assign_account, well_set_own_company, well_update_company, well_delete_company, well_list_cash_scope, well_list_uncategorized_window, well_set_transaction_category, well_list_burn_exemptions, well_list_recurring_contexts, well_sum_transactions, well_sum_invoices, well_render_cash_position, well_render_burn, well_render_runway, well_render_mrr, well_get_session_digest, well_propose_next_steps]
  network: [api.wellapp.ai]
  env: []
  tools: []
metadata:
  source: https://github.com/WellApp-ai/skills/tree/main/skills/board-pack
  well-skills: [board-pack]
---

# Board pack

## Purpose

Answer "what numbers do I put in front of the board?" for a Qonto customer: cash, burn, runway, recurring revenue, receivables and payables, each one computed by Well and each one carrying the window and the scope it was measured under.

Qonto proves the account and gives a live balance to cross-check. Well computes every figure, across Qonto and every other bank, invoicing and accounting tool the customer connected. The figures are never computed by the model from raw rows.

## Tooling

- **Qonto MCP** (`qonto`): `get_organization` identifies the company, `list_bank_accounts` gives the live Qonto balances used to cross-check Well's cash figure. If no Qonto tool is available, tell the user to connect Qonto first and stop.
- **Well MCP** (`well`, `https://api.wellapp.ai/v1/mcp`, bundled in this plugin's `.mcp.json`): computes every page of the pack. If no `well_*` tool is available, tell the user how to get them, say in one line what Well adds (every other bank and tool in the same figures), and stop. In Claude Code, the plugin already declares the server: the user runs `/mcp`, picks the Well server and signs in. On claude.ai or Claude Desktop, the user adds the Well connector at that address. Never fall back to computing the figures from Qonto transactions.

## Workflow

1. **Identify the Qonto company.** Call `get_organization`. Keep the company name and the list of Qonto accounts.
2. **Check Well is there.** If no `well_*` tool is in the toolset, stop as described in Tooling.
3. **Load the board pack instructions.** Call `well_get_skill({ skill: "board-pack" })` and follow the returned document exactly. It is the authoritative instruction set, kept current by Well. Do not substitute your own plan for it. When it tells you to run another Well skill, load that one the same way, at the moment it says to. If the call returns `success: false` or an error, tell the user the board pack is temporarily unavailable and stop. Do not improvise from memory.
4. **Make sure Qonto is inside the Well figures.** When the loaded document reaches its connection check (`well_list_connectors`), confirm that Qonto is among the connected banks of the Well workspace. If it is not, tell the user that Well's figures do not yet include their Qonto accounts, and let the document's connection step connect it before any page is measured.
5. **Cross-check the cash page.** After the cash page is measured, call `list_bank_accounts` and compare each Qonto account's balance with the balance Well used for the same account. If they differ, say so in one line with Well's last sync time. Never silently prefer either figure.
6. **Answer** with the pages the loaded document produced, in its format.

## Output requirements

- Quote every figure exactly as the Well tool returned it, with its currency, its window and its scope. Never add, divide or round figures yourself.
- Name a page as "not measured" when the document skipped it (for example recurring revenue with no invoicing source), never as zero.
- Nothing is written to Qonto. Any change the document makes happens inside the Well workspace, after the user confirms it.

## Examples

**Request:** "Prépare mon board pack pour le trimestre."
**Expected behavior:** reads the Qonto organization, loads `board-pack` from Well, follows it, and answers with the cash, burn, runway, recurring revenue, receivables and payables pages, each with its window. The Qonto balance of "Compte principal" matches Well's figure, so no cross-check line appears.

**Request:** "What numbers do I put in front of the board?" (Well is not connected)
**Expected behavior:** reads the Qonto organization, finds no `well_*` tool, tells the user to add the Well connector at `https://api.wellapp.ai/v1/mcp`, and stops without any figure.

**Request:** "Board numbers for this quarter." (Qonto is not connected in the Well workspace)
**Expected behavior:** loads `board-pack`, and at the connection check says Well's figures do not include Qonto yet, connects it through the document's connection step, waits for the sync, then measures the pages.
