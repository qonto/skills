<!--
Thanks for contributing a skill. This pull request is public, and so is
everything in it. Please read the checklist before submitting.
-->

## What does this skill do?

<!-- One or two sentences. Who is it for, and what task does it complete? -->

## When should an agent load it?

<!-- The trigger. Paste the `description` from your SKILL.md frontmatter. -->

## Which Qonto MCP tools does it use?

<!-- List them. If it only reads data, say so. -->

## How did you test it?

<!-- Which agent, which prompts, what happened. Screenshots or transcripts help. -->

---

## Checklist

- [ ] The directory name matches the `name` in the frontmatter exactly
- [ ] `name` is lowercase letters, numbers and hyphens only
- [ ] `description` says both what the skill does and when to use it
- [ ] `SKILL.md` is under roughly 500 lines, with detail moved to `references/`
- [ ] The plugin lives in `community/<plugin-name>/` with a `.claude-plugin/plugin.json`
      and its skills under `skills/<skill-name>/SKILL.md`
- [ ] The frontmatter has a `permissions` block listing every Qonto MCP tool, host,
      environment variable and native tool the skill uses
- [ ] `python3 .github/format-check/format_check.py --base origin/main` passes
- [ ] When updating a plugin that is already merged, `version` in `.claude-plugin/plugin.json` is bumped
      (the **Available skills** table in `README.md` and the marketplace are generated, nothing to add there)

## Nothing private in this pull request

Everything here becomes public the moment you open it, and stays in the git
history even if you edit or force push afterwards. Treat it as publishing.

- [ ] No credentials, API keys, tokens or cookies anywhere in the diff
- [ ] No real IBANs, account numbers, card numbers or transaction data
- [ ] No customer, client, employee or colleague names
- [ ] No internal URLs, staging hostnames, ticket links or internal identifiers
- [ ] No business data my company would not publish on its own website
- [ ] Every example is fabricated, not copied from a real Qonto account

## Review and licence

- [ ] I understand the Qonto team reviews every skill before merging, and may
      request changes or decline it
- [ ] **I agree that my contribution may be published under the
      [MIT License](../LICENSE)**, which allows anyone to use, modify and
      redistribute it
- [ ] I am entitled to license this work that way, and it does not include code
      or content owned by someone else
