# The back office that reconciles itself
*A Claude + Qonto-MCP agent that keeps three real companies audit-ready — on live data.*

## Context
- **One group, three entities** — a holding (SAS) and two property SCIs → **3 Qonto accounts**, but in practice a single business.
- Manages **18 apartments, 1 vacation rental, and 11 parking spaces.**
- Runs on its own calendar: a **fiscal year from 1 Aug → 31 Jul.**
- **250+ transactions a year** (≈ 800 over the last four).
- **Started before the official live MCP server and this Hackaton**, built on a patched **Qonto's open-source MCP from github. and then migrated on the official live MCP server on July 1st**

## The problem — nothing here is a "normal company"
- **Unusual accounting shape.** Real-estate holding, *impôt sur les sociétés SCI*, no VAT, per-property tracking — far from a typical commercial business.
- **Death by tiny transactions.** Renovation, electricity, water, internet, taxes… 250+ a year, many small — each still legally needs a justificatif. Enormously time-consuming.
- **No clients, no issued invoices.** Revenue isn't billed — it lands from **real-estate agencies and vacation-rental platforms** (Airbnb, Booking, Stripe). The usual "invoice → client" logic simply doesn't apply.
- **One email for three companies** — which makes Qonto's Gmail connector impractical.
- **Invoices scattered everywhere:** email, supplier portals, postal mail. Chasing them by hand is the real tax on my time.

## What I needed
- **Every Qonto transaction backed by ≥ 1 receipt.**
- **Qonto as the single source of truth.**
- **All receipts, statements & official docs in a clean, shared folder tree the accounting firm can actually use.**
- **No new UI already have Obsidian**

## Objectives
- **Automate the matching** — get my time back.
- **Do it retroactively**, across four years of history.
- **Always see what's still missing.**
- **0 code to write myself as I'm not a developer**
- **Plug it into my broader "AI second brain."**

## The solution
A vibe-coded headless app on **Claude Code + Chrome plugin + Qonto MCP** — **15 skills** and a few scripts:

| Layer | Skills |
|---|---|
| **Orchestrators** | `sync-gestion` (refresh → attach → mirror → regenerate) · `reconcile-receipts` (batch audit → fetch → attach) |
| **Qonto core** | `qonto-receipt-audit` · `qonto-attach-receipt` · `archive-qonto-attachments` (Qonto→tree mirror — *sole tree-writer*) · `qonto-operations-csv` · `qonto-statements-download` |
| **Intake** | `sort-inbox` (classify inbox; stage transaction-docs, file standalone) |
| **Fetch / source** | `airbnb-earnings` · `booking-payouts` · `stripe-payouts` · `sosh-invoices` · `smdea-invoices` · `credit-agricole-docs` |
| **Reporting** | `gestion-dashboard` (Obsidian gaps dashboard) |

## How it's built
- **Thinking & planning:** the *superpowers* workflow (brainstorm → spec → plan → subagent-driven build).
- **Skills** scaffolded with *Skill Creator*, versioned on **GitHub**.
- **Reach:** Chrome DevTools MCP + Chrome plugin (supplier portals), Gmail & Google Drive connectors, Stripe connector.

## Results
- **≈ 2 h/week saved → 104 h/year ≈ 13 working days back — for a ~2-day build.**
- **An AI that knows the whole group** — not just receipts, but *every* transaction and **4 years of history**, queryable across all three companies in one place.
- **A clean, shared tree → a happy accountant.**
- **Wired into Obsidian**, with live visibility on exactly where I stand — **~99% reconciled.**

## Limitations
- From Anthropic:
	- Impossible to download a PDF from a Gmail inbox need a Google Workspace Studio rule for that
	- Impossible to connect to Booking.com for security reason but it's possible to connect to Aibnb...
	
- From Qonto:
	- Not possible to mark a receipt as not needed (eg. 0€ transactions). 
	- Not possible to attach receipts to third parties (other banks) accounts. 
Yet possible in the app

## What's next
- **Profitability dashboards** on the collected data: rental-revenue trends, true vacation-rental margins (revenue − real costs), per-property P&L.
- **Auto-chasing suppliers** for the invoices still missing.

