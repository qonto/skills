---
name: qonto-board-pack
description: Monthly investor and banker update generator for Qonto accounts. From one prompt, builds the full board pack — the month's numbers (cash in, spend by category, end-of-month cash, burn & runway), month-over-month and rolling-year comparisons, auto-detected highlights (big contract collected, new significant expense), a three-paragraph executive narrative the user reviews BEFORE any formatting — then a self-contained HTML deck (5-6 slides) or a Canva export when that MCP is present, plus a ready-to-send email (Gmail draft when present). Audience-aware, bankers, investors and the internal team don't get the same level of detail. Use for "prepare my monthly investor update", "board pack for June", "rapport mensuel investisseurs", "mon banquier veut les chiffres du mois", "write my monthly update email".
---

# Qonto Board Pack

The monthly investor/banker update every founder postpones to the last evening. One prompt → the complete pack. **Zero writes to Qonto** (read-only); the only outputs are local files and drafts — nothing is ever sent without the user's review.

## Prerequisites
1. `get_organization` first → accounts, balances, legal name, currency, country. `list_transactions` requires `bank_account_id`/`iban`.
2. **Country-agnostic**: the pack is pure financial reporting — cash in, spend, burn, runway are universal. Works for every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT); only currency formatting and wording adapt. If the account is empty or younger than 2 months, say so and skip comparisons rather than inventing trends.
3. **Audience choice** (ask once, remember for the session): **banker** (reassurance: cash, coverage, stability — exact figures), **investor** (trajectory: growth, burn, runway, highlights — exact figures or trends per user choice), **internal** (everything, unfiltered). Confidentiality is a feature: the user picks the detail level — exact numbers vs trends/percentages.
4. Optional MCPs, detected dynamically: **Canva** (deck export) and **Gmail** (email draft). Absent → the skill says so and continues with the HTML deck and email text. The core is Qonto-only.

## Workflow

### 1. Frame the report
Confirm the target month (default: last full calendar month) and the audience/detail level. `get_organization` → enumerate accounts; the pack always consolidates all accounts and shows the split when there are several.

### 2. Pull the month's numbers
`list_transactions` per account, `per_page: "50"`, month window. **Exclude internal transfers between the organization's own accounts** from revenue and burn (match paired debit/credit on own IBANs). At month boundaries, card transactions settle 1–2 days late: window on `settled_at`, cross-check `emitted_at` to keep late-settling card spend in the right month.
- **Cash in**: credits excluding internal transfers and refunds of own spend.
- **Spend by category**: group by labels (`list_labels`); `list_cash_flow_categories` returns **403 missing oauth scope** on the claude.ai connector → labels are the fallback. Untagged spend goes into "Other", with its share disclosed.
- **End-of-month cash**: closing balance from `list_statements` / `get_statement` when the statement exists (official figure), else computed from current balance minus post-month movements — say which method was used.
- **Net burn** = out − in; **runway** = end-of-month cash ÷ average net burn over the last 3 months, only when average burn > 0 (otherwise "cash-flow positive — no runway math").

### 3. Compare M-1 and rolling year
Same metrics for the previous month and the trailing 12 months (paginate history, ≤ 50 per page). Show deltas in amount and %, flag seasonality when the same month last year shows the same pattern. `list_client_invoices` unpaid → outstanding receivables as a forward-looking line. Never conclude a trend from a single month.

### 4. Detect the month's highlights
From the data, not from imagination: largest incoming payment vs the account's typical inflow (big contract collected), first occurrence of a significant expense (new hire, new tool, new office), a usually-recurring client payment that is missing, an unusual category spike. Each highlight cites its transaction(s). The skill describes **what** happened; the user supplies the **why** — never invent causes.

### 5. Draft the executive narrative — then STOP for review
Three paragraphs: **highlights** (what mattered), **numbers** (the month in figures), **outlook** (next month, factual). Tone: factual, neither salesy nor alarmist. Show the draft in the conversation and **wait**: the user edits or approves before any formatting. An investor update never ships unreviewed — this checkpoint is the product, not friction.

### 6. Format the pack and prepare sending
- **HTML deck**, 5–6 slides, fully self-contained: pure CSS, zero external dependencies, light/dark via `prefers-color-scheme`, sober palette. Slides: cover (org + month) · highlights · key figures (cash in, spend, EoM cash, burn/runway with M-1 deltas) · spend by category · cash & runway · outlook. Figures filtered per audience.
- **Canva MCP present?** Offer `generate-design` export of the same content; otherwise don't mention it.
- **Send email**: short, professional, references the pack, matches the audience. **Gmail MCP present?** `create_draft` — a draft, never a send. Absent → email text in the conversation, ready to paste.
- Close with a one-line recap: what was generated, what remains manual (attach, send).

## Output formats
**Always** in the conversation: markdown tables (key figures + deltas, spend by category, highlights) and the 3-paragraph narrative. **When the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): the HTML deck. **When Gmail is connected**: a draft in the user's mailbox. If the host can't render files, the markdown pack is the deliverable — say nothing about what's missing.

## Guardrails
- **Read-only on Qonto** — this skill uses no Qonto write tool, ever.
- **Nothing is sent, ever**: emails are drafts, decks are files. The user reviews and sends.
- Narrative review (step 5) is a hard stop — never jump from numbers to formatted deck without user approval of the text.
- Audience confidentiality: never put exact figures in a pack the user asked to keep at trend level; never reuse the investor pack for the banker without re-asking.
- Every number traceable to transactions; untagged/unknown shares disclosed; honest degradation on short history (< 2 months → no comparisons, < 12 → no rolling year).
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50).
