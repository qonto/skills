# Natural-language policy — examples

You may author the trusted policy in plain English. The **skill** compiles each
sentence into a typed directive, shows you the compiled file, and **you ratify
it**. Only the typed form is passed to `prepare --policy`. The engine never
interprets prose and never lets a model make the block/allow decision — so a
stray sentence can't silently change who gets paid.

Flow: **write prose → skill compiles → you confirm → engine reads only the typed keys.**

## Rules that compile (prose → typed directive)

| You write (natural language) | Compiles to |
|---|---|
| "All limits are in euros." | `currency = EUR` |
| "Hard-block anything over €9,000." | `hard_block = 9000` |
| "An owner can approve up to €10,000." | `role.owner = 10000` |
| "Admins up to €10,000." | `role.admin = 10000` |
| "Managers can go up to €5,000." | `role.manager = 5000` |
| "Employees up to €1,000." | `role.employee = 1000` |
| "Block the supplier Solutions Industrielles." | `block_supplier = Solutions Industrielles` |
| "Never pay Acme Corp or Globex." | `block_supplier = Acme Corp`<br>`block_supplier = Globex` |
| "Block supplier id 019f55f1-214a-724e." | `block_supplier_id = 019f55f1-214a-724e` |
| "Treat US dollars as 0.92 euro for the limits." | `fx.USD.EUR = 0.92` |
| "Count British pounds at 1.17 euro." | `fx.GBP.EUR = 1.17` |

Semantics of the compiled rules:

- **`currency`** — the one currency the limits are denominated in.
- **`hard_block`** — an amount *strictly above* this fails the
  `within_trusted_policy_hard_limit` gate → decision **blocked**.
- **`role.<name>`** — the limit for the **initiator's Qonto role**. Above it →
  `policy breach` signal → **manual review** (not a block). Valid Qonto roles are
  `owner`, `admin`, `manager`, `employee`. (`designated_approver` /
  `finance_reviewer` are Finance-PR labels, **not** Qonto roles — don't use them.)
- **`block_supplier`** — matched on the **structured** Qonto `supplier_name`,
  accent- and case-insensitive. Repeatable. Fails the `supplier_not_blocked` gate
  → **blocked**.
- **`block_supplier_id`** — exact match on the Qonto `supplier_id`. Repeatable.
- **`fx.<FROM>.<TO>`** — an **operator-frozen** constant (1 FROM = rate TO), bound
  into the PR hash and labeled "not a market rate". A foreign-currency invoice is
  converted for the limit checks **only** when such a rate exists; otherwise it
  stays `not_applicable` and is never converted.

## A worked example

**You write (`policy.txt`, prose):**

```
Everything is in euros.
Hard-block anything above 9,000.
Owners can approve up to 10,000; managers up to 5,000.
Block the supplier Solutions Industrielles.
Treat US dollars at 0.92 euro.
```

**Skill compiles → you ratify (`policy.compiled.txt`):**

```
currency   = EUR
hard_block = 9000
role.owner   = 10000
role.manager = 5000
block_supplier = Solutions Industrielles
fx.USD.EUR = 0.92
```

**Engine reads only the compiled file** (`prepare --policy policy.compiled.txt`).

## Rules that do NOT compile (surfaced, never hand-enforced)

These have no typed directive. The skill will tell you it can't compile them
rather than inventing enforcement — that ambiguity is exactly what the engine is
built to refuse.

| You write | Why it can't compile |
|---|---|
| "Flag anything that looks suspicious." | Unbounded judgement — no deterministic rule. |
| "Use today's exchange rate for USD." | Live/market rate — forbidden; only a frozen `fx.*` constant is allowed. |
| "Block invoices over €5,000 unless the supplier is trusted." | Conditional logic isn't in the grammar. |
| "Require two approvers above €20,000." | Approval-workflow rules aren't part of this engine (that's Qonto's job). |
| "Block any supplier based in Russia." | No country field in the policy grammar. |
| "Solutions Industrielles can only go up to €2,000." | Per-supplier limits aren't supported (only global/role limits + block list). |
| "No payments on weekends." | No date/schedule rule in the grammar. |

If you need one of these, it must become a real typed directive in the engine
first — it is never enforced from prose.
