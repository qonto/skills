# MCP Skills

Skills that help AI agents work with the **Qonto MCP server** (the Model Context Protocol server exposing a Qonto business account: banking, invoicing, cards, team management).

| Skill | Purpose |
|---|---|
| [`qonto-mcp-data-model`](./qonto-mcp-data-model/SKILL.md) | Understand the data structures returned and accepted by every Qonto MCP tool: entities, field types, enums, pagination, money formats, and the quirks you need to know before building on top of it. |

Shapes were captured against a live Qonto MCP session (July 2026) and cross-checked against the official API reference at [docs.qonto.com](https://docs.qonto.com) for the collections that were empty on the test account (quotes, invoices, payment links…). Field names and enum values are verbatim; example values are anonymized placeholders. Where the MCP layer and the upstream API diverge (pagination meta keys, unexposed filters), both are noted.
