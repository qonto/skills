# Evaluations

Six scenarios that pin the behaviours this skill must get right, per the Anthropic
[skill best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
("build evaluations first"). Each line of `evals.jsonl` is one scenario:
`{skills, query, files, expected_behavior}`.

They run **offline** on the de-identified demo data (`demo/*.json`, `demo/receipts/*`),
so no real account is needed.

| # | What it checks |
|---|---|
| 1 | Core month review: reverse-charge VAT · mileage on the far restaurant (web-resolved) · drops the local one · hotel VAT non-recoverable · always defers to the accountant |
| 2 | Receipt reading: cryptic label → `Qonto:get_attachment` → address off the receipt → city (Reims) → mileage web search couldn't find; never fabricates a distance |
| 3 | Niches honesty: CESU shown as eligibility-uncertain (no employee) · abolished CIFD never proposed |
| 4 | Regime = micro/auto-entrepreneur: loads `rules-fr-micro.md`; no expense deductions; still flags reverse-charge VAT; surfaces micro-specific items (CA/franchise thresholds, VFL, ACRE) |
| 5 | Regime = SASU/assimilé-salarié: loads `rules-fr-is-assimile.md`; keeps company nudges + IS niches; drops Madelin & the 26% TNS abatement; dividends get the 40% allowance with no 10% threshold |
| 6 | Regime = EI au réel (IR): loads `rules-fr-ir-reel.md`; keeps expense & VAT nudges + TNS niches; drops the IS 15% band & dividends; owner's own draw is not deductible |

There's no built-in runner; use these as the source of truth when iterating (run the
skill on each `query`+`files`, check every `expected_behavior`).
