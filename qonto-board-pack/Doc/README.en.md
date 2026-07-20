# 📦 qonto-board-pack — The monthly investor update, ready before your coffee gets cold

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> One prompt → the complete board pack: the month's numbers, comparisons, auto-detected highlights, an executive narrative you review, a self-contained HTML deck and a ready-to-send email.
> **Zero writes to Qonto** — read-only end to end; nothing ever leaves without your review.

---

## 🎯 Why this matters (usefulness)

The monthly investor/banker update is the task every founder postpones to the last evening — then rushes, half from memory. `qonto-board-pack` does it while you watch:

1. **The month's numbers**, straight from Qonto — cash in, spend by category, end-of-month cash (from the official statement when it exists), net burn and runway
2. **Month-over-month and rolling-year comparisons** — deltas in amount and %, seasonality flagged, outstanding receivables as a forward-looking line — never a trend from a single month
3. **Auto-detected highlights** — big contract collected, first occurrence of a significant expense, a usually-recurring client payment gone missing — every fact cites its transactions; the skill states the *what*, you supply the *why*
4. **Executive narrative + formatting** — three paragraphs (highlights, numbers, outlook) that you **review and edit BEFORE** anything is formatted, then a self-contained HTML deck (or a Canva export when that MCP is present) plus a send email (Gmail draft when present)

And confidentiality is a **feature**: your banker, your investors and your team don't get the same pack — you pick the audience and the detail level (exact figures vs trends). It's not the first Monday morning of the month you'd dread anymore.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Every Qonto country** (FR, DE, ES, IT, AT, NL, BE, PT) — financial facts are universal; only currency formatting and wording adapt | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| ≥ 2 months of history | Below that: the month's numbers only, comparisons skipped and said so (≥ 12 months for the rolling year) | ⭕ |
| Canva MCP | Deck exported to Canva — detected dynamically, HTML deck otherwise | ⭕ optional |
| Gmail MCP | Email draft created in your mailbox — detected dynamically, paste-ready text otherwise | ⭕ optional |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Frame it**: target month (default: last full month) + audience — **banker** (reassurance: cash, coverage, stability), **investor** (trajectory: growth, burn, runway), **internal** (everything, unfiltered) — and detail level (exact figures vs trends)
2. **Pull the numbers**: `list_transactions` paginated ≤ 50, **internal transfers excluded** from revenue and burn, card settlement delays handled at month boundaries (`emitted_at` vs `settled_at`), spend grouped by labels (cash-flow categories return 403 on the claude.ai connector → labels fallback), end-of-month balance from the **official statement** when available
3. **Compare**: M-1 + trailing 12 months, deltas in amount and %, seasonality flagged, outstanding receivables (`list_client_invoices`) as a forward signal
4. **Detect highlights**: largest inflow vs the account's usual, first occurrence of a significant expense, missing recurring client payment, unusual category spike — every fact tied to real transactions
5. **Executive narrative**: three factual paragraphs, neither salesy nor alarmist — shown in the conversation, **hard stop**: you edit or approve before any formatting
6. **Pack & send prep**: self-contained HTML deck (pure CSS, light/dark, zero dependencies) or Canva when present + the send email (Gmail draft when present, **never sent**) → you review, you send

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The key design choice**: this skill writes **nothing** to Qonto — read-only end to end. The only "writes" are local (the HTML deck) or drafts (Gmail). An investor update never ships itself: the narrative review (step 5) is a hard stop, and the email stays a draft only you can send. **That's the product, not friction.**

## 🧪 Holds up on messy data

- Empty month or brand-new account? → the month's numbers only, comparisons skipped and stated, never invented trends
- Untagged transactions? → they land in an explicit "Other" bucket, with its share of total spend disclosed
- Internal transfers between own accounts? → excluded from revenue and burn (the classic way to accidentally double your "revenue")
- Card payments settling across month boundaries? → `emitted_at` vs `settled_at` handled, spend stays in the right month
- No statement yet for the target month? → balance computed and the method stated, official figure used when it exists
- Canva or Gmail MCP absent? → the skill says so once and continues: HTML deck + paste-ready email; the core is Qonto-only

## 👥 Three audiences (confidentiality as a feature)

| Audience | What they want | Pack content | Detail level |
|---|---|---|---|
| **Banker** | Stability: the account is healthy, obligations are covered | Cash, inflows, expense coverage, regularity | Exact figures |
| **Investor** | Trajectory: growth, controlled burn, runway | Highlights, M-1/YoY growth, burn & runway, outlook | Exact **or** trends — your call |
| **Internal** | Everything | The full pack, unfiltered, detailed spend included | Everything |

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (figures + deltas, spend, highlights) + the 3-paragraph narrative | **Always** — the baseline |
| **Self-contained HTML deck** | 5–6 slides, pure CSS, light/dark, zero external dependencies | When the host renders files; fallback to tables otherwise |
| **Canva export** | Design generated through the Canva MCP | When the Canva MCP is present |
| **Send email** | Gmail draft (**never sent**) or paste-ready text | Gmail present → draft; otherwise text |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the update postponed for three days → one prompt → numbers, highlights, narrative → **one adjective fixed live** → deck and email draft ready before the coffee is finished. It runs live on a real production account.

## 💡 Roadmap ideas

- Pack history: deltas against last month's pack ("what we told them last time")
- User-declared business KPIs (MRR, active customers) merged into the key-figures slide
- Calendar reminder ("your monthly pack is ready to generate") when a calendar MCP is detected
- Bilingual packs — FR deck for the banker, EN deck for international investors, same data

## 🛡 Guardrails

- **Read-only on Qonto** — no Qonto write tool is ever used
- **Nothing is sent, ever**: emails are drafts, decks are files — the user sends
- The narrative review is a **hard stop** before any formatting
- Audience confidentiality: exact figures never appear in a trends-level pack; the investor pack is never recycled for the banker without asking again
- Every number traceable to transactions · untagged shares disclosed · honest degradation on short history
- IBANs masked (last 4 digits) · pagination ≤ 50 everywhere

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
