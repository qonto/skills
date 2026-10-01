# Well for Qonto

Board-ready finance numbers for Qonto customers, computed by [Well](https://wellapp.ai) across Qonto and every other connected bank and tool.

## Install

1. Connect Qonto. On claude.ai or Claude Desktop, use the official Qonto connector. In Claude Code:
   `claude mcp add --transport http qonto https://mcp.qonto.com/mcp`
2. Connect Well. The plugin's `.mcp.json` declares it for Claude Code. Elsewhere, add the Well connector at
   `https://api.wellapp.ai/v1/mcp`.
3. Install the plugin from the Qonto marketplace and ask for your board pack.

## Skills

| Skill | Ask | What you get |
|---|---|---|
| `board-pack` | "Put my board pack together" · "Prépare mon board pack" | Cash, burn, runway, recurring revenue, receivables and payables, each with its window and scope |

## How it works

Each skill reads the Qonto organization and balances through the Qonto MCP, then loads its current instructions from Well (`well_get_skill`) and lets Well compute every figure. Well's instructions are versioned and served by Well, so the skill stays current without a new release here.

## Scope

Reads Qonto and writes nothing to Qonto. Any change happens inside the Well workspace, after you confirm it. Not financial or tax advice.
