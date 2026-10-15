# 🛡 qonto-brand-shield — Is the brand you're funding actually protected?

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> **100 % read-only**: the skill measures and prepares — the trademark filing itself happens on inpi.fr, decided by the user.

---

## 🎯 Why this matters (usefulness)

Every month, the account pays for things that **build a brand**: a logo, domain names, ad campaigns, packaging. Meanwhile, nobody checks whether the name itself is protected. `qonto-brand-shield` does both:

1. **Investment total per brand** — designers & logo work, domains, advertising, packaging, print, detected in real expenses and attached to each brand: "you invested €X in brand [Name] over N months", every attachment tagged 🟢 evidenced (document, domain) · 🟡 assumed
2. **Intellectual-property cross-check** — is the brand registered at INPI (the French trademark office)? By you? Do close marks exist in your Nice classes? Is the 10-year renewal approaching?
3. **Financial exposure** — the "uncovered" investment: everything already spent on a name that nothing protects
4. **Pre-filing dossier** — name, Nice classes suggested **from real activity** (detected products/services), indicative cost, ready for inpi.fr

Would someone use this on a Monday morning? It's the check every founder postpones — until a close mark shows up first. One question, one number, one €190–270 filing decision (renewal every 10 years: ~€290 + €40/class — indicative, check inpi.fr).

**Example (invented brand and amounts)**: "You spent €4,320 over 8 months on the brand *Nordlys* (logo €900, domains €120, ads €3,300). It is not registered. A close mark has existed in class 42 since 2021. Filing in 2 classes: ~€230 — about 5 % of what you've already invested, unprotected."

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | Adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Registry: INPI = France.** Other Qonto countries (DE, ES, IT…): the financial exposure stays valid everywhere; for the registry side, **EUIPO** is mentioned as the lead — registry data is never invented | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| INPI access | The data.inpi.fr API requires an **INPI account + an approved access request**. Without it: honest degraded mode — pre-filled search link + a guided 2-minute manual check. **No scraping** | ⭕ optional |
| ≥ 12 months of history | 24–36 months recommended: yearly cadences (domain renewals) only show across full years | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Brand inventory**: `get_organization` (legal name, trade names) + `list_products` (product/service labels) + domain names spotted in transactions — one company can carry several brands, each tracked separately
2. **Brand-spend scan** (12–36 months, paginated ≤ 50, debits): design & identity, domains, advertising, packaging & print — counterparties normalized (case, accents, multiple spellings merged)
3. **Attachment to a brand**: `get_attachment` on design/domain/print invoices to extract the brand name when present; domains map naturally; the rest goes to the main brand, tagged 🟡
4. **INPI check**: with API access → exact name + close variants searched (registered? owner? classes? renewal?); without → pre-filled data.inpi.fr link + 2-minute checklist, and the skill only integrates what the user reports back
5. **Nice classes suggested** from real activity: 1–3 classes proposed (e.g. SaaS → 42, clothing → 25, retail/ads → 35), always **to validate**
6. **Report**: exposure per brand, close-mark & renewal alerts, pre-filing dossier ready for inpi.fr

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The key point**: this skill is **100 % read-only** — no MCP write, no transfer, nothing to approve. The only possible "action", the trademark filing, happens on inpi.fr, decided by the user, after human validation (an IP professional is recommended). The skill never states a registry fact without a source: an API result or the user's own manual check.

## 🧪 Holds up on messy data

- No design invoices? → domains and ads still counted; the total is announced as a floor
- Attachment without a usable brand mention? → fallback on transaction label + counterparty, attachment tagged 🟡
- Short history? → annual domain cadences need 24–36 months; the skill says what it can't see yet
- Empty account? → the skill explains the method and what it would need, invents nothing
- Non-French organization? → exposure analysis delivered, registry check honestly deferred to EUIPO
- No INPI API access? → the degraded mode IS the product: pre-filled link, 2-minute check, zero guessing

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (investment per brand, protection status, exposure, alerts) | **Always** — the baseline |
| **Interactive one-pager** | **HTML** file/artifact: exposure gauge per brand, spend buckets, INPI status, dossier | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables |
| **Pre-filing dossier** | Structured text: name, suggested classes, indicative cost, inpi.fr link | Every unprotected brand detected |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem → the per-brand investment total → the INPI check (the guided manual mode, shown honestly) → **the exposure number + the pre-filing dossier**. It runs live on a real production account. The detailed shooting script is kept internal (out of the repo).

## 💡 Roadmap ideas

- Dedicated INPI MCP (data.inpi.fr API integrated) — removes the manual step; dynamically detected, the core works without it
- EUIPO / WIPO extension (EU & international marks) — Qonto is pan-European; same logic, other registries
- Watch for new close filings — the INPI opposition window is short (2 months after publication), a timely alert matters
- Automatic cross-reference with `qonto-subscription-audit` — domains are already detected annual subscriptions
- Renewal deadline pushed into `qonto-tax-pilot` — the 10-year renewal joins the dated-outflows schedule

## 🛡 Guardrails

- **100 % read-only**: no write tool, ever — filing stays a human decision on inpi.fr
- Trademark similarity is an **indicative alert, not legal analysis**: an IP professional is recommended before any filing
- Nice classes are **suggestions to validate**; costs are indicative — the source of truth is inpi.fr
- Never a registry fact without a source (API or the user's check); **no scraping** of data.inpi.fr
- Masked IBANs (last 4 digits) · pagination ≤ 50 everywhere · honest degradation on short history

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML, FR/EN).*
