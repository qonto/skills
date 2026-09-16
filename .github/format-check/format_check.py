#!/usr/bin/env python3
"""Format check: public, deterministic shape rules for community skills.

Runs the same locally and in CI:

    python3 .github/format-check/format_check.py --all                # every plugin under community/ and featured/
    python3 .github/format-check/format_check.py --base origin/main   # only what a branch changed

Everything here is a rule a contributor can read, reproduce and fix. Intent and
behaviour are reviewed elsewhere; this gate only checks shape.
"""
from __future__ import annotations

import argparse
import difflib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("format-check: pyyaml is required (pip install pyyaml==6.0.2)")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CATALOGUE = json.loads((HERE / "tools.json").read_text())
KNOWN_TOOLS: dict[str, dict] = {t["name"]: t for t in CATALOGUE["tools"]}
WRITE_TOOLS = {n for n, t in KNOWN_TOOLS.items() if not t["read_only"]}
DESTRUCTIVE_TOOLS = {n for n, t in KNOWN_TOOLS.items() if t["destructive"]}

PLUGIN_ROOTS = ("featured", "community")   # featured/ is Qonto's, community/ takes contributions
BASE = ""                                  # set from --base: lets checks compare with what main already has
CONTRIB_ROOT = "community"
SKILLS_DIR = "skills"                      # inside a plugin: <plugin>/skills/<skill>/SKILL.md
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][\w.]+)?$")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HOST_RE = re.compile(r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
TOOL_TOKEN_RE = re.compile(r"`(?:mcp__qonto__|qonto\.)?([a-z][a-z0-9]*(?:_[a-z0-9]+)+)`")
# mcp__qonto__<tool> anywhere, or qonto.<tool> where <tool> has the snake_case shape every catalogue entry has
# (so qonto.com, qonto.co, qonto.s3 in prose are domains, not tool references)
QUALIFIED_TOOL_RE = re.compile(r"mcp__qonto__([A-Za-z0-9_]+)|\bqonto\.([a-z][a-z0-9]*(?:_[a-z0-9]+)+)\b(?![./-])")
TOOL_VERBS = ("list_", "get_", "create_", "update_", "delete_", "send_", "mark_",
              "change_", "modify_", "remove_", "decline_", "request_", "upload_")
URL_RE = re.compile(r"https?://[^\s)\]>'\"`]+", re.I)

FRONTMATTER_KEYS = {"name", "description", "license", "allowed-tools", "metadata",
                    "compatibility", "permissions"}
NATIVE_TOOLS = {"Read", "Write", "Edit", "MultiEdit", "Bash", "Glob", "Grep", "WebFetch",
                "WebSearch", "Task", "NotebookEdit", "TodoWrite", "AskUserQuestion", "Skill"}

TEXT_EXT = {".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".py", ".js", ".mjs", ".cjs",
            ".ts", ".tsx", ".jsx", ".sh", ".html", ".css", ".toml", ".example", ".svg"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
ALLOWED_EXT = TEXT_EXT | IMAGE_EXT
ALLOWED_DOTFILES = {".mcp.json", ".gitignore"}
ALLOWED_DOTDIRS = {".claude-plugin", ".codex-plugin"}   # the plugin's own manifests
CODE_EXT = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".sh"}

MAX_FILE_BYTES = 1 * 1024 * 1024
MAX_PLUGIN_BYTES = 10 * 1024 * 1024
MAX_FILES = 200
SKILL_MD_WARN_LINES = 500
SKILL_MD_FAIL_LINES = 1000

# Paths only maintainers may touch (catalogue, manifests, workflows, this check, the featured tier).
PROTECTED_PREFIXES = (".github/", ".claude-plugin/", ".codex-plugin/", ".agents/", "featured/")
PROTECTED_FILES = {"LICENSE", "MAINTAINERS", "CODEOWNERS"}

# Install commands are tokenised rather than regex-matched so flags (`npm i -D x`, `pip install -U x`) cannot hide
# the package, several packages on one line are all checked, and `pkg@latest` counts as unpinned.
INSTALLERS = (
    (re.compile(r"\bpip3?\s+install\b"), "pip"),
    (re.compile(r"\buv\s+pip\s+install\b"), "pip"),
    (re.compile(r"\b(?:npm|pnpm)\s+(?:i|install|add)\b"), "npm"),
    (re.compile(r"\byarn\s+add\b"), "npm"),
    (re.compile(r"\bnpx\b"), "npx"),
    (re.compile(r"\buvx\b"), "uvx"),
)
FLAG_TAKES_VALUE = {"-r", "--requirement", "-c", "--constraint", "-i", "--index-url", "--extra-index-url", "-t",
                    "--target", "--prefix", "--python", "-p", "--package", "--from", "--with", "--filter", "--registry",
                    "--index", "--find-links", "-f", "--root", "--platform", "--implementation", "--abi"}
PIP_PINNED = re.compile(r"^[A-Za-z0-9][\w.\-]*(?:\[[\w,.\-]+\])?==\d[\w.]*$")
NPM_EXACT = re.compile(r"^\d+\.\d+\.\d+(?:[-+][\w.]+)?$")
SPEC_TOKEN = re.compile(r"^[-@\w.][\w./@:+~^<>=!,\[\]#%&?-]*$")
LOCAL_SPEC = ("./", "../", "/", "~", "file:", "link:", "workspace:")            # inside the plugin: reviewed code
REMOTE_SPEC = ("http://", "https://", "git+", "git:", "github:", "gitlab:", "bitbucket:", "ssh://", "hg+", "svn+", "bzr+")
ARCHIVE_EXT = (".whl", ".tar.gz", ".tgz", ".zip", ".tar.bz2", ".tar.xz")
SOURCE_FLAGS = ("-i", "--index-url", "--extra-index-url", "-f", "--find-links", "--trusted-host", "--registry")
INCLUDE_FLAGS = ("-r", "--requirement", "-c", "--constraint")


def split_flag(tok: str, flags: tuple[str, ...]) -> tuple[str, str] | None:
    """`-rFILE`, `-r FILE` (value in the next token, returned as ""), `--requirement=FILE`: (flag, value) or None."""
    for f in flags:
        if tok == f:
            return f, ""
        if tok.startswith(f + "="):
            return f, tok[len(f) + 1:]
        if len(f) == 2 and tok.startswith(f) and len(tok) > 2:
            return f, tok[2:]
    return None


def is_remote_spec(tok: str) -> bool:
    return tok.startswith(REMOTE_SPEC) or tok.lower().endswith(ARCHIVE_EXT) or " @ " in tok
NPX_YES = re.compile(r"\bnpx\s+(-y|--yes)\b")


@dataclass
class Finding:
    level: str          # fail | warn | note
    check: str
    message: str
    file: str = ""
    line: int = 0
    fix: str = ""


@dataclass
class Report:
    plugins: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    def add(self, level: str, check: str, message: str, file: str = "", line: int = 0, fix: str = ""):
        self.findings.append(Finding(level, check, message, file, line, fix))

    @property
    def failed(self) -> bool:
        return any(f.level == "fail" for f in self.findings)


# --------------------------------------------------------------------------- helpers

def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=True).stdout


def changed_files(base: str, head: str) -> list[str]:
    # three-dot: only what the branch adds since it forked from base. In CI head is the merge commit, so
    # this equals the plain diff; locally it keeps base's own newer commits out of the picture.
    # --no-renames so a rename shows as delete + add, and D/T so a deletion or a file turned into a symlink
    # cannot slip past the protected-path rule.
    out = git("diff", "--name-only", "--no-renames", "--diff-filter=ACDMTUXB", f"{base}...{head}")
    return sorted(p for p in out.splitlines() if p.strip())


def all_plugin_files() -> list[str]:
    out = git("ls-files", "--", *PLUGIN_ROOTS, "README.md")
    return sorted(p for p in out.splitlines() if p.strip())


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def parse_frontmatter(text: str) -> tuple[dict | None, str, int]:
    """Returns (frontmatter, body, body_start_line). None when absent or invalid."""
    if not text.startswith("---"):
        return None, text, 1
    lines = text.splitlines()
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            try:
                data = yaml.safe_load("\n".join(lines[1:i]))
            except yaml.YAMLError:
                return None, text, 1
            if not isinstance(data, dict):
                return None, text, 1
            return data, "\n".join(lines[i + 1:]), i + 2
    return None, text, 1


def maintainers(base: str) -> set[str]:
    """Maintainers from trusted base commit, never contributor-controlled PR head."""
    try:
        text = git("show", f"{base}:MAINTAINERS")
    except subprocess.CalledProcessError:
        return set()
    return {l.strip().lstrip("@").lower() for l in text.splitlines()
            if l.strip() and not l.startswith("#")}


def semver_key(v: str) -> tuple:
    core, _, tail = v.partition("-")
    core = core.split("+")[0]
    return tuple(int(x) for x in core.split(".")), tail == "", tail


def suggest(name: str) -> str:
    m = difflib.get_close_matches(name, KNOWN_TOOLS, n=1, cutoff=0.6)
    return f" Did you mean `{m[0]}`?" if m else ""


# --------------------------------------------------------------------------- checks

def check_repo_level(files: list[str], actor: str, base: str, rep: Report) -> set[str]:
    """Protected paths, stray files. Returns the set of plugin dirs touched."""
    is_maintainer = actor.lower() in maintainers(base) if actor else False
    plugins: set[str] = set()
    for f in files:
        parts = f.split("/")
        if f.startswith(PROTECTED_PREFIXES) or f in PROTECTED_FILES:
            if not is_maintainer:
                rep.add("fail", "protected-path",
                        f"`{f}` is maintained by the Qonto team and cannot change in a skill submission.",
                        file=f, fix=f"Remove this file from the pull request. Contributions go under `{CONTRIB_ROOT}/`.")
                continue
            if parts[0] not in PLUGIN_ROOTS:
                continue  # a maintainer edit to the tooling: a featured plugin falls through and gets checked
        if f == "README.md" or (parts[0] in PLUGIN_ROOTS and parts[1:] == [".gitkeep"]):
            continue
        if not (ROOT / f).exists() and not (ROOT / f).is_symlink():
            if parts[0] in PLUGIN_ROOTS and len(parts) >= 3:
                plugins.add(f"{parts[0]}/{parts[1]}")   # a file removed from a plugin: the plugin is re-checked
            continue   # a deletion cannot be a stray file (protected deletions were caught above)
        if parts[0] in PLUGIN_ROOTS and len(parts) >= 3:
            plugins.add(f"{parts[0]}/{parts[1]}")
            continue
        if parts[0] in PLUGIN_ROOTS and len(parts) == 2:
            rep.add("fail", "stray-file", f"`{f}` sits loose in `{parts[0]}/` and would be ignored by every agent.",
                    file=f, fix=f"Move it into `{parts[0]}/<plugin-name>/`.")
            continue
        if is_maintainer and "/" not in f and f.lower().endswith(".md"):
            continue  # maintainers may edit top-level docs
        rep.add("fail", "stray-file", f"`{f}` is outside `{CONTRIB_ROOT}/<plugin-name>/`.",
                file=f, fix=f"A contribution is one plugin directory: `{CONTRIB_ROOT}/<plugin-name>/.claude-plugin/plugin.json` "
                            "plus its skills under `skills/<skill-name>/SKILL.md`. Move the file there, or drop it if it is "
                            "build output or documentation for humans.")
    return plugins


def walk_plugin(pdir: Path, rep: Report) -> list[Path]:
    kept: list[Path] = []
    total = 0
    count = 0
    for p in sorted(pdir.rglob("*")):
        r = rel(p)
        if p.is_symlink():
            rep.add("fail", "file-type", f"`{r}` is a symlink.", file=r, fix="Ship the file itself.")
            continue
        if p.is_dir():
            if p.name.startswith(".") and p.name not in ALLOWED_DOTDIRS:
                rep.add("fail", "file-type", f"Hidden directory `{r}/` is not allowed in a plugin.",
                        file=r, fix="Remove it. Manifests go in `.claude-plugin/`, hooks in `hooks/`, agents in `agents/`, "
                                    "commands in `commands/`.")
            continue
        count += 1
        size = p.stat().st_size
        total += size
        if p.name.startswith(".") and p.name not in ALLOWED_DOTFILES:
            rep.add("fail", "file-type", f"Hidden file `{r}` is not allowed.", file=r, fix="Remove it.")
            continue
        ext = p.suffix.lower()
        if p.name in ALLOWED_DOTFILES:
            ext = ".json" if p.name.endswith(".json") else ".txt"
        if p.name.lower() in {"dockerfile", "makefile", "license", "license.md", "readme"}:
            ext = ".txt"
        if ext not in ALLOWED_EXT:
            rep.add("fail", "file-type",
                    f"`{r}` has a file type we do not accept ({ext or 'no extension'}).", file=r,
                    fix="Allowed: Markdown, text, JSON, YAML, CSV, Python, JavaScript/TypeScript, shell, HTML/CSS, "
                        "SVG and PNG/JPEG/GIF/WebP images. No archives, documents, notebooks or compiled files.")
            continue
        if size > MAX_FILE_BYTES:
            rep.add("fail", "size-cap", f"`{r}` is {size // 1024} KiB, over the 1 MiB per-file cap.", file=r,
                    fix="Split it, trim it, or link to it instead.")
            continue
        if ext in TEXT_EXT:
            head = p.read_bytes()[:8192]
            if b"\x00" in head:
                rep.add("fail", "file-type", f"`{r}` looks binary despite its extension.", file=r,
                        fix="Text files only. Re-save it as UTF-8 text or remove it.")
                continue
        kept.append(p)
    if count > MAX_FILES:
        rep.add("fail", "size-cap", f"`{rel(pdir)}/` has {count} files, over the cap of {MAX_FILES}.",
                file=rel(pdir), fix="A skill is instructions plus a few scripts. Remove generated output and vendored code.")
    if total > MAX_PLUGIN_BYTES:
        rep.add("fail", "size-cap", f"`{rel(pdir)}/` is {total // (1024 * 1024)} MiB, over the 10 MiB cap.",
                file=rel(pdir), fix="Remove large assets.")
    return kept


def str_list(perms: dict, key: str, r: str, rep: Report) -> list[str]:
    """`permissions.<key>` as a list of strings, or a finding and an empty list."""
    v = perms.get(key)
    if v is None:
        return []
    if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
        rep.add("fail", "permissions", f"`permissions.{key}` must be a list of strings.", file=r, line=2,
                fix=f"Example: `{key}: []` or `{key}: [one, two]`.")
        return []
    return v


def check_plugin_manifest(pdir: Path, rep: Report) -> dict:
    """`<plugin>/.claude-plugin/plugin.json`: the marketplace entry is generated from it."""
    name = pdir.name
    if not NAME_RE.match(name) or len(name) > 64:
        rep.add("fail", "layout", f"Plugin directory `{name}` must be lowercase letters, digits and single hyphens (max 64).",
                file=rel(pdir), fix="Rename the directory, for example `overdue-invoice-chaser`.")
    manifest = pdir / ".claude-plugin" / "plugin.json"
    r = rel(manifest)
    if not manifest.is_file():
        rep.add("fail", "layout", f"`{r}` is missing.", file=rel(pdir),
                fix="Every plugin carries a manifest, the marketplace entry is built from it:\n```json\n{\n"
                    '  "name": "' + name + '",\n  "version": "0.1.0",\n  "description": "What it does, and when an agent should use it.",\n'
                    '  "author": { "name": "Your name", "url": "https://github.com/you" },\n  "license": "MIT"\n}\n```')
        return {}
    try:
        m = json.loads(read_text(manifest))
    except json.JSONDecodeError as e:
        rep.add("fail", "layout", f"`{r}` is not valid JSON ({e.msg}, line {e.lineno}).", file=r, line=e.lineno)
        return {}
    if not isinstance(m, dict):
        rep.add("fail", "layout", f"`{r}` must be a JSON object.", file=r)
        return {}
    if m.get("name") != name:
        rep.add("fail", "layout", f"Manifest `name` is `{m.get('name')}` but the directory is `{name}`.", file=r,
                fix="Make them identical.")
    desc = m.get("description")
    if not isinstance(desc, str) or len(desc.strip()) < 20:
        rep.add("fail", "layout", "Manifest `description` is missing or too short.", file=r,
                fix="One or two sentences: what the plugin does and who it is for.")
    if not isinstance(m.get("version"), str) or not SEMVER_RE.match(m["version"]):
        rep.add("fail", "layout", f"Manifest `version` `{m.get('version')}` is not a semantic version.", file=r,
                fix="Use `MAJOR.MINOR.PATCH`, for example `0.1.0`.")
    elif BASE:
        try:
            old = json.loads(git("show", f"{BASE}:{r}"))
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            old = None   # new plugin, or no manifest on base
        if isinstance(old, dict) and isinstance(old.get("version"), str) and SEMVER_RE.match(old["version"]) \
                and semver_key(m["version"]) <= semver_key(old["version"]):
            rep.add("fail", "layout", f"Manifest `version` is still `{m['version']}` although the plugin changed.", file=r,
                    fix="Bump it, for example `0.1.0` -> `0.1.1`. The marketplace republishes this version and agents "
                        "skip an update whose version they already have.")
    if not isinstance(m.get("author"), dict) or not m["author"].get("name"):
        rep.add("warn", "layout", "Manifest has no `author.name`.", file=r, fix='Add `"author": { "name": "...", "url": "..." }`.')
    if m.get("license") not in (None, "MIT"):
        rep.add("warn", "layout", f"Manifest `license` is `{m.get('license')}`, the repository is MIT.", file=r)
    if "skills" in m and m["skills"] not in ("./skills/", "./skills", "skills", "skills/"):
        rep.add("fail", "layout", f"Manifest `skills` points at `{m['skills']}`.", file=r,
                fix="Skills live in `skills/` inside the plugin. Drop the key or set it to `./skills/`.")
    return m


def check_frontmatter(pdir: Path, rep: Report) -> tuple[dict, set[str], set[str]]:
    """Returns (frontmatter, declared qonto tools, declared network hosts)."""
    skill_md = pdir / "SKILL.md"
    r = rel(skill_md)
    name = pdir.name
    if not NAME_RE.match(name) or len(name) > 64:
        rep.add("fail", "layout", f"Skill directory `{name}` must be lowercase letters, digits and single hyphens (max 64).",
                file=rel(pdir), fix="Rename the directory, for example `overdue-invoice-chaser`.")
    if not skill_md.is_file():
        rep.add("fail", "layout", f"`{rel(pdir)}/SKILL.md` is missing.", file=rel(pdir),
                fix="Every skill needs a `SKILL.md` with YAML frontmatter (`name`, `description`, `permissions`).")
        return {}, set(), set()
    text = read_text(skill_md)
    n_lines = text.count("\n") + 1
    if n_lines > SKILL_MD_FAIL_LINES:
        rep.add("fail", "size-cap", f"`SKILL.md` is {n_lines} lines. The cap is {SKILL_MD_FAIL_LINES}.", file=r,
                fix="Move detail into `references/` and keep `SKILL.md` to the steps an agent follows.")
    elif n_lines > SKILL_MD_WARN_LINES:
        rep.add("warn", "size-cap", f"`SKILL.md` is {n_lines} lines. Aim for under {SKILL_MD_WARN_LINES}.", file=r,
                fix="Move detail into `references/`.")
    fm, _, _ = parse_frontmatter(text)
    if fm is None:
        rep.add("fail", "layout", "`SKILL.md` must start with YAML frontmatter between two `---` lines.", file=r, line=1,
                fix="Start the file with:\n```\n---\nname: my-skill\ndescription: What it does. Use when ...\npermissions:\n  mcp:\n    qonto: []\n  network: []\n  env: []\n  tools: []\n---\n```")
        return {}, set(), set()
    if fm.get("name") != name:
        rep.add("fail", "layout", f"Frontmatter `name` is `{fm.get('name')}` but the directory is `{name}`.", file=r, line=2,
                fix="Make them identical.")
    desc = fm.get("description")
    if not isinstance(desc, str) or len(desc.strip()) < 20:
        rep.add("fail", "layout", "`description` is missing or too short.", file=r, line=2,
                fix="Say what the skill does and when an agent should load it, in one or two sentences.")
    elif len(desc) > 1024:
        rep.add("fail", "layout", f"`description` is {len(desc)} characters. The cap is 1024.", file=r, line=2,
                fix="Keep the trigger in `description`, move the rest into the body.")
    for k in fm:
        if k not in FRONTMATTER_KEYS:
            rep.add("warn", "layout", f"Unknown frontmatter key `{k}`.", file=r, line=2,
                    fix=f"Known keys: {', '.join(sorted(FRONTMATTER_KEYS))}.")

    declared: set[str] = set()
    hosts: set[str] = set()
    perms = fm.get("permissions")
    if not isinstance(perms, dict):
        rep.add("fail", "permissions", "The `permissions` block is missing from the frontmatter.", file=r, line=2,
                fix="Declare what the skill needs, even when the answer is nothing:\n```yaml\npermissions:\n  mcp:\n"
                    "    qonto: [list_client_invoices, get_client]\n  network: []\n  env: []\n  tools: [Read]\n```")
        return fm, declared, hosts
    for key in ("mcp", "network", "env", "tools"):
        if key not in perms:
            rep.add("fail", "permissions", f"`permissions.{key}` is missing.", file=r, line=2,
                    fix=f"Add `{key}: []` if the skill needs none.")
    mcp = perms.get("mcp")
    if mcp is not None and not isinstance(mcp, dict):
        rep.add("fail", "permissions", "`permissions.mcp` must be a map of server name to tool list.", file=r, line=2,
                fix="Example: `mcp:\\n  qonto: [list_transactions]`")
        mcp = {}
    for server, tools in (mcp or {}).items():
        if not isinstance(tools, list) or not all(isinstance(t, str) for t in tools):
            rep.add("fail", "permissions", f"`permissions.mcp.{server}` must be a list of tool names.", file=r, line=2)
            continue
        if server != "qonto":
            rep.add("note", "permissions", f"Declares a second MCP server `{server}` with {len(tools)} tool(s). "
                    "Reviewers look at this closely.", file=r, line=2)
            continue
        for t in tools:
            if t not in KNOWN_TOOLS:
                rep.add("fail", "tool-name", f"`{t}` is not a Qonto MCP tool.{suggest(t)}", file=r, line=2,
                        fix="Tool names come from the Qonto MCP catalogue. See `.github/format-check/tools.json`.")
            else:
                declared.add(t)
    if declared & DESTRUCTIVE_TOOLS:
        rep.add("note", "permissions", "Declares destructive tools: " + ", ".join(sorted(declared & DESTRUCTIVE_TOOLS)) +
                ". Reviewers will check every call site.", file=r, line=2)
    elif declared & WRITE_TOOLS:
        rep.add("note", "permissions", "Declares write tools: " + ", ".join(sorted(declared & WRITE_TOOLS)) + ".",
                file=r, line=2)
    for h in str_list(perms, "network", r, rep):
        if not HOST_RE.match(h.lower()):
            rep.add("fail", "permissions", f"`permissions.network` entry `{h}` is not a hostname.", file=r, line=2,
                    fix="Use bare hostnames such as `api.example.com`, no scheme, no path, no wildcard.")
        else:
            hosts.add(h.lower())
    for e in str_list(perms, "env", r, rep):
        if not ENV_RE.match(e):
            rep.add("fail", "permissions", f"`permissions.env` entry `{e}` is not an environment variable name.",
                    file=r, line=2, fix="Upper-case letters, digits and underscores, for example `MY_SERVICE_TOKEN`.")
    for t in str_list(perms, "tools", r, rep):
        if t not in NATIVE_TOOLS:
            rep.add("warn", "permissions", f"`permissions.tools` entry `{t}` is not a native agent tool we know.",
                    file=r, line=2, fix=f"Known: {', '.join(sorted(NATIVE_TOOLS))}.")

    at = fm.get("allowed-tools")
    if at:
        items = at.replace(",", " ").split() if isinstance(at, str) else [str(x) for x in at]
        for item in items:
            if item.startswith("mcp__qonto__"):
                t = item[len("mcp__qonto__"):]
                if t not in KNOWN_TOOLS:
                    rep.add("fail", "tool-name", f"`allowed-tools` lists `{item}`, which is not a Qonto MCP tool.{suggest(t)}",
                            file=r, line=2)
                elif t not in declared:
                    rep.add("fail", "permissions", f"`allowed-tools` lists `{item}` but `permissions.mcp.qonto` does not declare `{t}`.",
                            file=r, line=2, fix="Add it to `permissions.mcp.qonto`.")
    return fm, declared, hosts


DENY_KEYS = ("disallowedTools", "disallowed-tools", "disallowed_tools", "deny", "denied", "blocked")
DENY_LINE_RE = re.compile(r"^\s*(?:" + "|".join(DENY_KEYS) + r")\s*:")


def blank_deny_lists(text: str, r: str, rep: Report) -> str:
    """Return the text with frontmatter deny lists blanked out (line numbers kept): a tool an agent is forbidden to call
    is not a call site, so it needs no `permissions` entry. Unknown names in a deny list only get a warning."""
    fm, _, _ = parse_frontmatter(text)
    if fm is None:
        return text
    lines = text.splitlines()
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), 0)
    i = 1
    while i < end:
        if DENY_LINE_RE.match(lines[i]):
            block = [i]
            j = i + 1
            while j < end and (lines[j].startswith((" ", "\t")) or not lines[j].strip()):
                block.append(j); j += 1
            joined = "\n".join(lines[k] for k in block)
            for mm in QUALIFIED_TOOL_RE.finditer(joined):
                t = mm.group(1) or mm.group(2)
                if t not in KNOWN_TOOLS:
                    rep.add("warn", "tool-name", f"Deny list names `{mm.group(0)}`, which is not a Qonto MCP tool, so the entry "
                            f"does nothing.{suggest(t)}", file=r, line=i + 1)
            for k in block:
                lines[k] = ""
            i = j
        else:
            i += 1
    return "\n".join(lines)


def resolve_include(p: Path, pdir: Path, name: str) -> Path | None:
    """`-r name` in an install command: the file it points at, if it lives inside the plugin."""
    for cand in (p.parent / name, pdir / name):
        try:
            if cand.is_file() and cand.resolve().is_relative_to(pdir.resolve()):
                return cand
        except OSError:
            pass
    return None


def scan_text_file(p: Path, declared: set[str], hosts: set[str], rep: Report,
                   reported: set[str] | None = None, perms_present: bool = True,
                   where: str = "the skill", pdir: Path | None = None, validated: set[Path] | None = None):
    reported = set() if reported is None else reported
    r = rel(p)
    text = read_text(p)
    ext = p.suffix.lower()
    if ext == ".md":
        text = blank_deny_lists(text, r, rep)
    # 1. pinned dependencies
    for ln, line in enumerate(text.splitlines(), 1):
        if NPX_YES.search(line):
            rep.add("fail", "pinned-deps", "`npx --yes` installs and runs a package without asking.", file=r, line=ln,
                    fix="Pin the version (`npx pkg@1.2.3`) and drop `--yes`.")
        for cmd, pkg, what in unpinned_installs(line):
            if what == "include":
                target = resolve_include(p, pdir, pkg) if pdir else None
                if target is None:
                    rep.add("fail", "pinned-deps", f"`{cmd} {pkg}` reads a dependency file that is not in the plugin.",
                            file=r, line=ln, fix="Ship the file inside the plugin with every package pinned to an exact version.")
                elif validated is not None and target not in validated:
                    validated.add(target)
                    check_pinned_manifest(target, rep, as_requirements=True)
                continue
            if what == "source":
                rep.add("fail", "pinned-deps", f"`{cmd} {pkg}` pulls packages from a place this check does not validate.",
                        file=r, line=ln, fix="Install exact versions from the default registry only.")
                continue
            if what == "remote":
                rep.add("fail", "pinned-deps", f"`{cmd}` installs `{pkg}` from a URL, repository or archive.", file=r, line=ln,
                        fix="Only exact versions from the default registry are accepted (`pkg==1.2.3`, `pkg@1.2.3`); "
                            "code that is not on the registry ships inside the plugin.")
                continue
            rep.add("fail", "pinned-deps", f"`{cmd}` installs `{pkg}` without an exact version.", file=r, line=ln,
                    fix="Pin an exact version, for example `pip install requests==2.32.3`, `npm install left-pad@1.3.0`, "
                        "`npx prettier@3.3.3`.")
    # 2. tool references
    seen: set[str] = set()
    for ln, line in enumerate(text.splitlines(), 1):
        for m in QUALIFIED_TOOL_RE.finditer(line):
            t = m.group(1) or m.group(2)
            if t in seen:
                continue
            seen.add(t)
            if t not in KNOWN_TOOLS:
                if t not in reported:
                    reported.add(t)
                    rep.add("fail", "tool-name", f"`{m.group(0)}` is not a Qonto MCP tool.{suggest(t)}", file=r, line=ln)
            elif t not in declared and perms_present and t not in reported:
                reported.add(t)
                rep.add("fail", "permissions", f"Uses `{t}` but {where} does not declare it in `permissions.mcp.qonto`.",
                        file=r, line=ln, fix="Declare it, or remove the reference.")
        for m in TOOL_TOKEN_RE.finditer(line):
            t = m.group(1)
            if t in seen:
                continue
            if t in KNOWN_TOOLS:
                seen.add(t)
                if t not in declared and perms_present and t not in reported:
                    reported.add(t)
                    rep.add("fail", "permissions", f"Uses `{t}` but {where} does not declare it in `permissions.mcp.qonto`.",
                            file=r, line=ln, fix="Declare it, or remove the reference.")
            elif t.startswith(TOOL_VERBS) and ext == ".md" and t not in reported:
                seen.add(t)
                reported.add(t)
                rep.add("warn", "tool-name", f"`{t}` looks like a tool name but is not in the Qonto MCP catalogue.{suggest(t)}",
                        file=r, line=ln)
    # 3. .mcp.json servers
    if p.name == ".mcp.json":
        try:
            cfg = json.loads(text)
        except json.JSONDecodeError:
            rep.add("fail", "layout", "`.mcp.json` is not valid JSON.", file=r)
            return
        for sname, s in (cfg.get("mcpServers") or {}).items():
            url = (s or {}).get("url", "")
            host = re.sub(r"^https?://", "", url).split("/")[0].split(":")[0].lower()
            if url and host not in hosts:
                rep.add("fail", "permissions", f"`.mcp.json` server `{sname}` connects to `{host}`, which `permissions.network` does not declare.",
                        file=r, fix="Add the host to `permissions.network`.")
            rep.add("note", "permissions", f"Bundles an MCP server config `{sname}`.", file=r)


def unpinned_installs(line: str):
    """Yield (command, spec, kind) for what an install command on this line would fetch: kind is "unpinned" for a
    package without an exact version, "include" for a `-r`/`-c` file, "source" for an index or find-links option,
    "remote" for a URL, repository or archive spec (pip and npm both accept those, they are not reviewable)."""
    for verb_re, kind in INSTALLERS:
        for m in verb_re.finditer(line):
            rest = re.split(r"\s(?:&&|\|\||;|\||#|>|2>)\s", line[m.end():])[0]
            rest = rest.split("`")[0]     # an inline code span ends the command in Markdown prose
            toks = rest.replace("'", " ").replace('"', " ").split()
            packages: list[str] = []
            kind0 = kind
            i = 0
            while i < len(toks):
                t = toks[i].rstrip(".,;:)")
                if not t or not SPEC_TOKEN.match(t):
                    break                 # prose after the command, not a package
                if t.startswith("-"):
                    inc = split_flag(t, INCLUDE_FLAGS)
                    src = split_flag(t, SOURCE_FLAGS)
                    for hit, what in ((inc, "include"), (src, "source")):
                        if hit is None:
                            continue
                        flag, value = hit
                        if value:
                            yield f"{m.group(0).strip()} {flag}", value, what
                            i += 1
                        elif i + 1 < len(toks):
                            yield f"{m.group(0).strip()} {flag}", toks[i + 1], what
                            i += 2
                        else:
                            i += 1
                        break
                    else:
                        if t in ("-e", "--editable") and i + 1 < len(toks):
                            packages.append(toks[i + 1])       # a path or a URL, checked like any other spec
                            i += 2
                            continue
                        if t in FLAG_TAKES_VALUE and i + 1 < len(toks):
                            if t in ("-p", "--package", "--from", "--with"):   # the value is a package
                                packages.append(toks[i + 1])
                                if kind in ("npx", "uvx"):
                                    kind = "cmd-follows"   # the command that follows is not a package any more
                            i += 2
                            continue
                        i += 1
                    continue
                if t == "@" and packages and i + 1 < len(toks):   # PEP 508 direct reference: `pkg @ url`
                    packages[-1] = f"{packages[-1]} @ {toks[i + 1]}"
                    i += 2
                    continue
                if kind in ("npx", "uvx"):
                    packages.append(t)          # the first bare token is the package, the rest are its arguments
                    break
                if kind == "cmd-follows":
                    break
                packages.append(t)
                i += 1
            for pkg in packages:
                if is_remote_spec(pkg):
                    yield m.group(0).strip(), pkg, "remote"
                    continue
                if pkg.startswith(LOCAL_SPEC) or pkg in (".", "-"):
                    continue
                if kind0 == "pip" or (kind0 == "uvx" and "==" in pkg):
                    if not PIP_PINNED.match(pkg):
                        yield m.group(0).strip(), pkg, "unpinned"
                    continue
                name, sep, ver = (pkg[1:].partition("@") if pkg.startswith("@") else pkg.partition("@"))
                if not sep or not NPM_EXACT.match(ver):
                    yield m.group(0).strip(), pkg, "unpinned"


def check_pinned_manifest(p: Path, rep: Report, as_requirements: bool = False):
    r = rel(p)
    text = read_text(p)
    if as_requirements or (p.name.startswith("requirements") and p.suffix == ".txt"):
        for ln, line in enumerate(text.splitlines(), 1):
            s = line.split("#")[0].strip()
            if not s:
                continue
            if s.startswith(("-r", "--requirement", "-c", "--constraint", "-e", "--editable", "-i", "--index-url",
                             "--extra-index-url", "-f", "--find-links", "--trusted-host")):
                rep.add("fail", "pinned-deps", f"`{s}` pulls dependencies from a place this check does not validate.",
                        file=r, line=ln, fix="List every package in this file with an exact version, from the default index.")
                continue
            if s.startswith("-"):
                continue   # a plain pip option such as --pre
            req = s.split(";")[0].strip()
            spec = req.split("--hash")[0].strip()
            if is_remote_spec(spec) or spec.startswith(LOCAL_SPEC) or spec.startswith("."):
                if "--hash=" not in req:
                    rep.add("fail", "pinned-deps", f"`{spec}` is a direct reference (URL, repository, archive or path) "
                            "without `--hash`, so what it installs can change after review.", file=r, line=ln,
                            fix="Use `package==1.2.3` from the index, or add `--hash=sha256:...` to the line.")
                continue
            if not PIP_PINNED.match(spec):
                rep.add("fail", "pinned-deps", f"`{s}` is not pinned to an exact version.", file=r, line=ln,
                        fix="Use `package==1.2.3`.")
    elif p.name == "package.json":
        try:
            pkg = json.loads(text)
        except json.JSONDecodeError:
            rep.add("fail", "layout", "`package.json` is not valid JSON.", file=r)
            return
        for section in ("dependencies", "devDependencies", "optionalDependencies"):
            for dep, ver in (pkg.get(section) or {}).items():
                if not isinstance(ver, str) or not re.match(r"^\d+\.\d+\.\d+(?:[-+][\w.]+)?$", ver):
                    rep.add("fail", "pinned-deps", f"`{dep}: {ver}` in `{section}` is not an exact version.", file=r,
                            fix="Use exact versions such as `1.2.3`, no `^`, `~`, ranges, tags or URLs.")
    elif p.name == "pyproject.toml":
        for ln, line in enumerate(text.splitlines(), 1):
            if re.search(r'^\s*"[^"]*\s@\s[^"]*"', line) or re.search(r"\b(?:git|url)\s*=\s*\"", line):
                rep.add("fail", "pinned-deps", f"`{line.strip()}` is a direct reference, not a pinned index version.",
                        file=r, line=ln, fix="Use `package==1.2.3`.")
                continue
            m = re.match(r'^\s*"([A-Za-z0-9_.\-\[\]]+)\s*([<>=!~]{1,2})?', line)
            if m and m.group(2) and m.group(2) != "==":
                rep.add("fail", "pinned-deps", f"`{line.strip()}` is not pinned with `==`.", file=r, line=ln)


def check_hooks(pdir: Path, rep: Report):
    hooks = pdir / "hooks" / "hooks.json"
    if hooks.is_file():
        rep.add("note", "hooks", "Registers agent hooks. Reviewers read every hook and the script it runs.", file=rel(hooks))
    for sub in ("agents", "commands"):
        if (pdir / sub).is_dir():
            rep.add("note", "layout", f"Ships `{sub}/`.", file=rel(pdir / sub))


def check_manifest(rep: Report):
    """Validate the marketplace the merge would produce: render it from the plugin directories with
    `.github/scripts/marketplace.py`, refuse duplicate plugin names, then run `claude plugin validate` on that
    rendering (written in place for the run, the validator does not follow symlinks, and restored afterwards)."""
    script = ROOT / ".github" / "scripts" / "marketplace.py"
    if not script.is_file():
        rep.add("note", "manifest", "No `.github/scripts/marketplace.py`, manifest validation skipped.")
        return
    try:
        sys.dont_write_bytecode = True   # no __pycache__ left behind in the contributor's checkout
        spec = importlib.util.spec_from_file_location("marketplace", script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        found = mod.plugins()
        rendered = mod.render()[0]
    except Exception as e:   # a broken plugin.json is already a `layout` failure from check_plugin_manifest
        rep.add("warn", "manifest", f"Could not render the marketplace from the plugin directories ({e.__class__.__name__}: {e}).")
        return
    by_name: dict[str, list[str]] = {}
    for tier, d, m in found:
        by_name.setdefault(str(m.get("name")), []).append(f"{tier}/{d.name}")
    for n, dirs in sorted(by_name.items()):
        if len(dirs) > 1:
            rep.add("fail", "manifest", f"Plugin name `{n}` is used by {len(dirs)} directories: " + ", ".join(f"`{x}`" for x in dirs) + ".",
                    fix="Plugin names are unique across `featured/` and `community/`. Rename yours.")
    exe = shutil.which("claude")
    if not exe:
        rep.add("note", "manifest", "`claude` CLI not on PATH, skipped `claude plugin validate .`.")
        return
    mpath = ROOT / ".claude-plugin" / "marketplace.json"
    backup = mpath.read_bytes() if mpath.is_file() else None
    try:
        mpath.parent.mkdir(exist_ok=True)
        mpath.write_text(rendered, encoding="utf-8")
        out = subprocess.run([exe, "plugin", "validate", ".", "--strict", "--json"], cwd=ROOT, text=True,
                             capture_output=True, timeout=120)
        data = json.loads(out.stdout or "{}")
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        rep.add("warn", "manifest", f"`claude plugin validate` did not return a report ({e.__class__.__name__}).")
        return
    finally:
        if backup is None:
            mpath.unlink(missing_ok=True)
        else:
            mpath.write_bytes(backup)
    where = ".claude-plugin/marketplace.json (as regenerated after merge)"
    for w in (data.get("manifest") or {}).get("warnings", []):
        rep.add("warn", "manifest", f"{w.get('path')}: {w.get('message')}", file=where)
    if not data.get("success", False):
        for err in (data.get("manifest") or {}).get("errors", []):
            rep.add("fail", "manifest", f"{err.get('path')}: {err.get('message')}", file=where)
        for item in data.get("contents") or []:
            for err in item.get("errors", []):
                rep.add("fail", "manifest", f"{item.get('file')}: {err.get('message')}", file=str(item.get("file", "")))


def check_plugin(name: str, rep: Report):
    pdir = ROOT / name   # <tier>/<plugin>
    if not pdir.is_dir():
        return  # deleted in this PR
    files = walk_plugin(pdir, rep)
    check_plugin_manifest(pdir, rep)
    skills_dir = pdir / SKILLS_DIR
    skill_dirs = sorted(d for d in skills_dir.iterdir() if d.is_dir()) if skills_dir.is_dir() else []
    if not skill_dirs:
        rep.add("fail", "layout", f"`{rel(pdir)}/{SKILLS_DIR}/` has no skill.", file=rel(pdir),
                fix=f"Add at least one `{SKILLS_DIR}/<skill-name>/SKILL.md`.")
    # Each skill is scanned against its own permissions block, so one skill cannot borrow another's declaration.
    # Files outside skills/ (hooks, agents, commands, docs, .mcp.json) belong to the plugin as a whole and are
    # scanned against the union of the blocks.
    scopes = []   # (dir, label, declared tools, declared hosts, permissions block present)
    for sd in skill_dirs:
        fm, d, h = check_frontmatter(sd, rep)
        scopes.append((sd, f"`{rel(sd)}/SKILL.md`", d, h, isinstance(fm.get("permissions"), dict)))
    union = (None, "any skill of the plugin",
             set().union(*(sc[2] for sc in scopes)) if scopes else set(),
             set().union(*(sc[3] for sc in scopes)) if scopes else set(),
             all(sc[4] for sc in scopes))
    reported: dict[str, set[str]] = {}
    validated: set[Path] = set()
    for p in files:
        ext = p.suffix.lower()
        if p.name in {"requirements.txt", "package.json", "pyproject.toml"} or p.name.startswith("requirements"):
            validated.add(p)
            check_pinned_manifest(p, rep)
        if ext in TEXT_EXT and ext != ".svg" or p.name in ALLOWED_DOTFILES:
            scope = next((sc for sc in scopes if p.is_relative_to(sc[0])), union)
            scan_text_file(p, scope[2], scope[3], rep, reported=reported.setdefault(scope[1], set()),
                           perms_present=scope[4], where=scope[1], pdir=pdir, validated=validated)
    check_hooks(pdir, rep)


# --------------------------------------------------------------------------- output

def annotations(rep: Report):
    lvl = {"fail": "error", "warn": "warning", "note": "notice"}
    for f in rep.findings:
        loc = f"file={f.file}," if f.file else ""
        loc += f"line={f.line}," if f.line else ""
        msg = f.message.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
        print(f"::{lvl[f.level]} {loc}title=format-check/{f.check}::{msg}")


def esc(s: str) -> str:
    """The report is posted as a comment: file names and frontmatter values from the pull request must not become HTML."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def markdown(rep: Report) -> str:
    fails = [f for f in rep.findings if f.level == "fail"]
    warns = [f for f in rep.findings if f.level == "warn"]
    notes = [f for f in rep.findings if f.level == "note"]
    out = ["<!-- format-check -->"]
    if rep.failed:
        out.append(f"### Format check failed ({len(fails)} to fix)\n")
        out.append("These are shape rules, not a judgement on the skill. Fix them, push, and the check reruns.\n")
    else:
        out.append("### Format check passed\n")
        out.append("The submission has the right shape. The Qonto team reviews every skill before merging.\n")
    if rep.plugins:
        out.append("Plugins in this pull request: " + ", ".join(f"`{esc(p)}`" for p in rep.plugins) + "\n")

    def block(title: str, items: list[Finding], with_fix: bool):
        if not items:
            return
        out.append(f"<details open><summary><b>{title}</b> ({len(items)})</summary>\n")
        for f in items:
            where = f"`{esc(f.file)}`" + (f":{f.line}" if f.line else "") if f.file else ""
            out.append(f"- **{f.check}** {where}  \n  {esc(f.message)}")
            if with_fix and f.fix:
                out.append(f"  \n  Fix: {esc(f.fix)}" if "```" not in f.fix else f"  \n  Fix:\n{esc(f.fix)}")
        out.append("\n</details>\n")

    block("Must fix", fails, True)
    block("Worth a look", warns, True)
    block("For the reviewers", notes, False)
    out.append("Run the same check locally: `python3 .github/format-check/format_check.py --base origin/main`")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", help="git ref to diff against (default: scan everything with --all)")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--all", action="store_true", help="check every plugin under community/ and featured/")
    ap.add_argument("--actor", default=os.environ.get("FORMAT_CHECK_ACTOR", ""), help="GitHub login of the PR author")
    ap.add_argument("--json", help="write the report as JSON here")
    ap.add_argument("--markdown", help="write the Markdown summary here")
    ap.add_argument("--annotations", action="store_true", help="print GitHub workflow annotations")
    args = ap.parse_args()

    global BASE
    rep = Report()
    if args.all or not args.base:
        files = all_plugin_files()
        plugins = {"/".join(f.split("/")[:2]) for f in files if f.split("/")[0] in PLUGIN_ROOTS and f.count("/") >= 2}
    else:
        BASE = args.base
        files = changed_files(args.base, args.head)
        plugins = check_repo_level(files, args.actor, args.base, rep)
    rep.plugins = sorted(plugins)
    for name in rep.plugins:
        check_plugin(name, rep)
    check_manifest(rep)

    md = markdown(rep)
    if args.annotations:
        annotations(rep)
    if args.json:
        Path(args.json).write_text(json.dumps({"failed": rep.failed, "plugins": rep.plugins,
                                               "findings": [asdict(f) for f in rep.findings]}, indent=2))
    if args.markdown:
        Path(args.markdown).write_text(md)
    print(md)
    return 1 if rep.failed else 0


if __name__ == "__main__":
    sys.exit(main())
