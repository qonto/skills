# Qonto AI Skills

A marketplace of [Agent Skills](https://agentskills.io) for [Qonto](https://qonto.com), packaged as plugins for
Claude, Codex, GitHub Copilot and other agents.

The skills in this marketplace use the [Qonto MCP server](https://docs.qonto.com/mcp/overview) to read and act on
your Qonto account.

> [!NOTE]
> The Qonto MCP server cannot move money. At most it creates a transfer request, which a member with approval rights
> signs in the Qonto app with their own two-factor authentication. See
> [what the MCP server can and cannot do](https://docs.qonto.com/mcp/capabilities).

> [!IMPORTANT]
> Every call runs as you through OAuth, so there are no API keys to share and an agent never goes beyond your role.
> Read more in [security and limits](https://docs.qonto.com/mcp/security), and the
> [terms and disclosures](https://docs.qonto.com/mcp/terms-and-disclosures) before you connect.

## Install

Connect the Qonto MCP server first, then add the skills. Pick your agent below.

<details open>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add --transport http qonto https://mcp.qonto.com/mcp
```

Run `/mcp` to sign in to Qonto, then add the marketplace and the plugins you want.

```
/plugin marketplace add qonto/skills
/plugin install veto@qonto
/reload-plugins
```

Every plugin in the table below installs as `<plugin>@qonto`. Pull updates with `/plugin marketplace update qonto`.

</details>

<details>
<summary><b>Claude Desktop, claude.ai and Cowork</b></summary>

Plugins need a paid plan (Pro, Max, Team or Enterprise).

1. In **Customize › Connectors**, add Qonto and sign in.
2. In **Customize › Plugins**, choose **Add › Add marketplace › Add from a repository** and enter `qonto/skills`.
3. Install the plugins you want from the list.

</details>

<details>
<summary><b>Codex</b></summary>

```bash
codex mcp add qonto --url https://mcp.qonto.com/mcp
codex plugin marketplace add qonto/skills
codex plugin add veto@qonto
```

The first command opens the Qonto sign-in in your browser.

</details>

<details>
<summary><b>GitHub Copilot CLI</b></summary>

```bash
copilot mcp add --transport http qonto https://mcp.qonto.com/mcp
copilot plugin marketplace add qonto/skills
copilot plugin install veto@qonto
```

</details>

<details>
<summary><b>Cursor, Gemini CLI and other agents</b></summary>

[Connect the Qonto MCP server](https://docs.qonto.com/mcp/install/quickstart) in your agent, then install the skills
with the [skills CLI](https://github.com/vercel-labs/skills).

```bash
npx skills add qonto/skills
```

It asks which skills to install and for which agents. `--skill veto` picks one skill and `-g` installs for every
project. Needs Node.js 22.20 or later.

</details>

## Available skills

<!-- Generated from every plugin's .claude-plugin/plugin.json after each merge to main. Do not edit the table by hand. -->
<!-- skills:start -->
| Plugin | What it does | Author | Tier |
|---|---|---|---|
| [`qonto-asset-registry`](./community/qonto-asset-registry) | Read-only fixed-asset register and insurance inventory built from Qonto transactions and supplier invoices. | [seb](https://github.com/SebDeNoocode) | community |
| [`qonto-counterparty-watch`](./community/qonto-counterparty-watch) | Legal-health radar for the clients and suppliers of a Qonto account. | [seb](https://github.com/SebDeNoocode) | community |
| [`qonto-crew-onboard`](./community/qonto-crew-onboard) | One-sentence financial onboarding (and offboarding) of an employee on Qonto. | [seb](https://github.com/SebDeNoocode) | community |
| [`qonto-grant-scout`](./community/qonto-grant-scout) | Public-funding scout for Qonto accounts. | [seb](https://github.com/SebDeNoocode) | community |
| [`qonto-prescription-guard`](./community/qonto-prescription-guard) | Legal expiry radar for unpaid client invoices on Qonto accounts (France). | [seb](https://github.com/SebDeNoocode) | community |
| [`qonto-tax-pilot`](./community/qonto-tax-pilot) | French tax radar and cash pilot for Qonto accounts. | [seb](https://github.com/SebDeNoocode) | community |
| [`qonto-tax-radar`](./community/qonto-tax-radar) | French tax pre-audit ("pré-contrôle fiscal") for Qonto accounts, 100% read-only. | [seb](https://github.com/SebDeNoocode) | community |
| [`qonto-vat-return`](./community/qonto-vat-return) | French VAT return (CA3, form 3310-CA3) preparer for Qonto accounts. | [seb](https://github.com/SebDeNoocode) | community |
| [`veto`](./community/veto) | Manages guarded accounts receivable in Qonto for French businesses. | [Abdel-Karim](https://github.com/UnknOownU) | community |
<!-- skills:end -->

## Contribute

Open a pull request that adds `community/<plugin-name>/`. The pull request template lists what the format check
expects. Everything in a pull request is public, the Qonto team reviews every plugin before it merges, and
contributions are published under the [MIT License](LICENSE).
