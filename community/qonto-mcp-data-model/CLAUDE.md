# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A collection of Agent Skills for Qonto (the French/European B2B neobank), created for the Qonto x Anthropic MCP Hackathon. There is no application code, build system, or test suite — the deliverables are Markdown skill packages that AI agents load at runtime.

## Layout

Skills are grouped by domain in top-level folders (currently only `mcp/`, for skills that help agents use the Qonto MCP server). Each skill is a directory:

```
mcp/
  README.md                    # index table of the skills in this domain
  qonto-mcp-data-model/
    SKILL.md                   # entry point: frontmatter + compact overview + pointers
    references/                # detail files, loaded on demand by the agent
```

## Skill authoring conventions

- `SKILL.md` begins with YAML frontmatter: `name` (matches the directory name) and a one-line `description` phrased as *when to use* the skill.
- Progressive disclosure: `SKILL.md` holds only the compact essentials (entity map, the few rules that prevent most mistakes, typical call chains) plus a table mapping each `references/*.md` file to the situations it covers. Depth goes in `references/`, never inline in `SKILL.md`.
- Reference files cross-link with relative Markdown links and flag traps/inconsistencies with ⚠️.
- Accuracy standard of the existing skill — hold new content to it: shapes were captured against a live Qonto MCP session (July 2026) and cross-checked against the official API docs at docs.qonto.com; field names and enum values are verbatim; example values are anonymized placeholders; where the MCP layer and the upstream API diverge, both are noted, and live tool output wins over the docs.
- When adding a skill: create its folder with `SKILL.md` (+ `references/` if needed) and add a row to the domain `README.md` index table.

## Qonto domain invariants

Any edit to the Qonto skill content must not contradict these (documented in `mcp/qonto-mcp-data-model/`):

- **No MCP tool moves money.** The strongest write creates a *pending* request that a human approves in the Qonto app with their own SCA (2FA). Never describe the MCP as able to send transfers or approve payments.
- All entity ids are UUIDs; entities link by id, never by (possibly localized) name.
- Money has three coexisting representations, and `vat_rate` switches between fraction and percent scale per document type (`"0.2"` on invoices vs `"20"` on quotes for 20 %) — see `references/conventions.md` before writing anything about amounts or rates.
- HTTP 403 from tools usually means plan- or role-gating (e.g. requests need Business/Enterprise), not broken auth.
