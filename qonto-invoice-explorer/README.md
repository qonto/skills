# qonto-invoice-explorer

An exploration skill for coding agents running on a Qonto account. Submitted to the Qonto × Anthropic MCP Hackathon (July 2026).

The premise is that Qonto's Invoice Collector already handles the OCR and auto-match once a PDF reaches the receipts inbox; what it doesn't do is the exploration upstream, deciding where each missing receipt should be looked for. A human doesn't need that — a human opens Qonto, sees the gap, remembers where the invoice lives, retrieves it. An AI agent running headlessly doesn't have that memory. This skill is the taxonomy and the retrieval recipes that let an agent do the exploration itself, then hand the PDF back to Qonto for attachment.

The skill was written after a production run on a live French SAS: about sixty-five receipts justified over nine months, across twenty-odd vendor archetypes spread over email inboxes, a foreign-supplier WhatsApp thread, three SaaS billing dashboards behind logins, and a folder of AirDropped photos. The failure modes in `SKILL.md` are the ones that actually caused problems in that run, not the ones a checklist would predict.

The reason we ship extraction and matching scripts (`scripts/extract_pdf.py`, `scripts/match.py`) alongside the exploration recipes is that Invoice Collector isn't reachable from MCP today. When it is, those scripts become obsolete and the skill collapses to the exploration layer plus the handoff. That's the intended end state.

## What's in here

`SKILL.md` is the workflow and the failure modes. `references/` is loaded on demand: `vendor-archetypes.md` classifies vendors into eight patterns; `modality-*.md` documents the per-channel retrieval recipes for email via Unipile, browser via Claude for Chrome, local folders, and WhatsApp / LinkedIn via Unipile chats; `pdf-extraction.md` is the regex library keyed by archetype; `matching-strategy.md` and `qonto-mcp-recipes.md` document the currency-aware matching rules and the verified MCP call patterns. `scripts/` is the deterministic Python for pieces that shouldn't be an LLM's job.

## Try it

The skill needs a Qonto MCP registered as `qonto` with admin or owner access. It works better with a Unipile API key connected (for email and WhatsApp), Claude for Chrome installed (for dashboard-only vendors like Vercel or OpenAI top-ups), and `pdftotext` on the path (from `poppler`). Python 3.9 or newer for the scripts.

Once installed, ask Claude any variant of "attach the missing receipts on Qonto for last quarter". The skill runs a discovery phase (`get_organization`), inventories missing debits across bank accounts, groups by vendor, proposes a plan modality by modality, waits for approval, then executes with one confirmation per vendor group.

## Feedback for Qonto

Exposing Invoice Collector via MCP would remove most of the extraction and matching burden from this skill. Extending the fifteen-minute signed S3 upload URL to thirty would remove the tightest constraint on batching uploads. Shipping a CLI alongside the MCP would cut token cost per session by an order of magnitude, which matters when a full run makes sixty-plus tool calls. Server-side filters on `list_transactions` (counterparty, label, `attachment_required=true`) would remove the client-side filter loop after paginating.

## Video

Demo attached in a PR comment before the deadline.
