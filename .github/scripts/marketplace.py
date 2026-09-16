#!/usr/bin/env python3
"""Build the marketplace manifests from the plugin directories.

    python3 .github/scripts/marketplace.py            # rewrite the two manifests
    python3 .github/scripts/marketplace.py --check    # exit 1 if they are out of date

Every directory under featured/ and community/ that carries .claude-plugin/plugin.json is one
entry. The tier is the top-level folder. Contributors never edit the manifests, nor the
**Available skills** table in README.md: a workflow on main regenerates all three after each merge.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TIERS = ("featured", "community")

MARKETPLACE = {
    "name": "qonto",
    "owner": {"name": "Qonto", "url": "https://qonto.com"},
    "description": "Agent Skills for business banking and financial tools on Qonto. "
                   "Featured plugins are built by Qonto, community plugins are reviewed by Qonto before they ship.",
}

CLAUDE_OUT = ROOT / ".claude-plugin" / "marketplace.json"
CODEX_OUT = ROOT / ".agents" / "plugins" / "marketplace.json"
README = ROOT / "README.md"
README_START, README_END = "<!-- skills:start -->", "<!-- skills:end -->"


def plugins() -> list[tuple[str, Path, dict]]:
    out = []
    for tier in TIERS:
        base = ROOT / tier
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir()):
            manifest = d / ".claude-plugin" / "plugin.json"
            if d.is_dir() and manifest.is_file():
                out.append((tier, d, json.loads(manifest.read_text(encoding="utf-8"))))
    return out


def claude_entry(tier: str, d: Path, m: dict) -> dict:
    e = {
        "name": m["name"],
        "source": f"./{tier}/{d.name}",
        "description": m.get("description", ""),
        "version": m.get("version", "0.1.0"),
        "category": tier.capitalize(),
        "tags": sorted(set(m.get("keywords", [])) | {tier}),
    }
    for k in ("author", "homepage", "repository", "license"):
        if k in m:
            e[k] = m[k]
    return e


def codex_entry(tier: str, d: Path, m: dict) -> dict:
    return {
        "name": m["name"],
        "source": {"source": "local", "path": f"./{tier}/{d.name}"},
        "description": m.get("description", ""),
        "policy": {"installation": "AVAILABLE"},
        "category": tier.capitalize(),
        "tags": sorted(set(m.get("keywords", [])) | {tier}),
    }


def readme_table(found: list[tuple[str, Path, dict]]) -> str:
    rows = ["| Plugin | Skills | What it does | Author | Tier |", "|---|---|---|---|---|"]
    for tier, d, m in found:
        sdir = d / "skills"
        skills = ", ".join(f"`{s.name}`" for s in sorted(sdir.iterdir()) if s.is_dir()) if sdir.is_dir() else ""
        author = m.get("author")
        if isinstance(author, dict):
            author = f"[{author.get('name', '')}]({author['url']})" if author.get("url") else str(author.get("name", ""))
        desc = " ".join(str(m.get("description", "")).split()).replace("|", "\\|")
        rows.append(f"| [`{m['name']}`](./{tier}/{d.name}) | {skills} | {desc} | {author or ''} | {tier} |")
    return "\n".join(rows) + "\n"


def render_readme(found: list[tuple[str, Path, dict]]) -> str | None:
    """README.md with the table between the markers replaced. None when there is no README or no markers."""
    if not README.is_file():
        return None
    text = README.read_text(encoding="utf-8")
    if README_START not in text or README_END not in text:
        return None
    head, rest = text.split(README_START, 1)
    _, tail = rest.split(README_END, 1)
    return head + README_START + "\n" + readme_table(found) + README_END + tail


def render() -> tuple[str, str, str | None]:
    found = plugins()
    claude = dict(MARKETPLACE, plugins=[claude_entry(t, d, m) for t, d, m in found])
    codex = {
        "name": MARKETPLACE["name"],
        "interface": {"displayName": "Qonto"},
        "plugins": [codex_entry(t, d, m) for t, d, m in found if (d / ".codex-plugin" / "plugin.json").is_file()],
    }
    return json.dumps(claude, indent=2) + "\n", json.dumps(codex, indent=2) + "\n", render_readme(found)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="verify the committed manifests match the plugin directories")
    args = ap.parse_args()
    claude, codex, readme = render()
    if args.check:
        stale = [p for p, want in ((CLAUDE_OUT, claude), (CODEX_OUT, codex), (README, readme))
                 if want is not None and (not p.is_file() or p.read_text(encoding="utf-8") != want)]
        for p in stale:
            print(f"out of date: {p.relative_to(ROOT).as_posix()}")
        return 1 if stale else 0
    CLAUDE_OUT.parent.mkdir(parents=True, exist_ok=True)
    CODEX_OUT.parent.mkdir(parents=True, exist_ok=True)
    CLAUDE_OUT.write_text(claude, encoding="utf-8")
    CODEX_OUT.write_text(codex, encoding="utf-8")
    if readme is not None:
        README.write_text(readme, encoding="utf-8")
    n = len(plugins())
    print(f"{n} plugin(s): wrote {CLAUDE_OUT.relative_to(ROOT).as_posix()}, {CODEX_OUT.relative_to(ROOT).as_posix()}"
          + (" and the README table" if readme is not None else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
