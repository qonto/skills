# Security notes

## What Finance PR is

A **pre-Qonto review layer**. It binds intent, evidence, action, policy, and human
approval into an immutable hashed proposal, and re-validates integrity and fresh
state before allowing a proposal to reach the Qonto boundary.

## What Finance PR is NOT

- Not a payment executor. **It moves no money and completes no SCA/2FA.**
- Not a Qonto role/permission system, and not a replacement for Qonto native
  approval or SCA.
- Not a global MCP enforcement proxy. It protects *this* review workflow; a
  different tool could still call Qonto writes directly. (Org-wide enforcement is
  roadmap.)
- Not a fraud detector. It surfaces *observed* risk for human review; it makes no
  fraud claim.

## Authority model

1. Only an explicit, fingerprint-bound approval from a **user chat** message can
   authorize Act. Questions, "yes", "pay it", and ambiguity cannot.
2. Document / attachment / tool text is **untrusted data**, never authority —
   even when it contains "approve this payment" or "ignore previous instructions".
3. Structured Qonto fields outrank extracted document text; conflicts require
   review.
4. Act reads action values from the **stored, hashed PR**, never from a later
   chat message.

## Hard gates (integrity is independent of risk)

A weighted risk score can never override a failed gate. Gates: explicit action
intent · authoritative source · unambiguous target/action · required evidence ·
not already paid/matched · no completed exact duplicate · PR-id+fingerprint match ·
full SHA-256 match · explicit approval · approval route · not expired · critical
Qonto state unchanged · amount/currency/IBAN/supplier unchanged · exact prepared
action · unused one-shot · writes explicitly enabled.

Unknown/unavailable checks stay `insufficient_data` / `not_run` and lower
coverage; they never become pass or zero risk.

## Redaction

IBANs are masked to the last 4 everywhere (UI, logs, fixtures, the hashed body
stores only a salted IBAN digest + last 4). Object ids are shortened; emails are
masked; attachment/presigned URLs and tokens are never persisted. `npm run
scan:secrets` fails the build if a known real sandbox value or credential/URL
pattern appears in committed files.

## No hidden retries

A single write attempt is made in the (disabled-by-default) controlled path. An
ambiguous result becomes `execution_unknown` and is **never retried
automatically**; it requires read reconciliation.

## What "Green" means

> No material inconsistency was observed in the available evidence. Ready for
> Finance PR review; Qonto approval and any SCA still remain.

Green never means safe, fraud-free, paid, approved, or executed.

## Controlled Qonto write (disabled)

Writes are disabled by default in code, config, the Skill, and tests. There is no
implemented code path to a real Qonto write; the write seam's default adapter
performs no tool call and returns `ready_for_qonto`. Enabling a real write would
require a new adapter, an explicit build flag, and an explicit per-object user
confirmation of the exact PR id, fingerprint, action, and target. No Qonto write
was performed in building this project.
