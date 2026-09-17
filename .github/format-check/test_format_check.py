import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


HERE = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location("format_check", HERE / "format_check.py")
fc = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = fc
SPEC.loader.exec_module(fc)


class AutomaticExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old_root = fc.ROOT
        fc.ROOT = self.root

    def tearDown(self):
        fc.ROOT = self.old_root
        self.temp.cleanup()

    def test_community_hooks_are_rejected(self):
        plugin = self.root / "community" / "plugin"
        hooks = plugin / "hooks"
        hooks.mkdir(parents=True)
        (hooks / "hooks.json").write_text("{}")
        report = fc.Report()

        fc.check_hooks(plugin, report)

        self.assertTrue(any(f.level == "fail" and f.check == "hooks" for f in report.findings))

    def test_community_local_mcp_command_is_rejected(self):
        plugin = self.root / "community" / "plugin"
        plugin.mkdir(parents=True)
        config = plugin / ".mcp.json"
        config.write_text(json.dumps({"mcpServers": {"local": {"command": "sh", "args": ["-c", "env"]}}}))
        report = fc.Report()

        fc.scan_text_file(config, set(), set(), report, pdir=plugin)

        self.assertTrue(any(f.level == "fail" and f.check == "mcp-command" for f in report.findings))

    def test_featured_hooks_remain_reviewable(self):
        plugin = self.root / "featured" / "plugin"
        hooks = plugin / "hooks"
        hooks.mkdir(parents=True)
        (hooks / "hooks.json").write_text("{}")
        report = fc.Report()

        fc.check_hooks(plugin, report)

        self.assertFalse(report.failed)
        self.assertTrue(any(f.level == "note" and f.check == "hooks" for f in report.findings))


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old_root = fc.ROOT
        fc.ROOT = self.root

    def tearDown(self):
        fc.ROOT = self.old_root
        self.temp.cleanup()

    def test_mixed_root_and_nested_skills_fail(self):
        plugin = self.root / "community" / "plugin"
        skill = plugin / "skills" / "nested"
        manifest = plugin / ".claude-plugin"
        skill.mkdir(parents=True)
        manifest.mkdir()
        (plugin / "SKILL.md").write_text("legacy")
        (skill / "SKILL.md").write_text("nested")
        (manifest / "plugin.json").write_text(json.dumps({
            "name": "plugin", "version": "0.1.0", "description": "A sufficiently detailed plugin description."
        }))
        report = fc.Report()

        fc.check_plugin("community/plugin", report)

        self.assertTrue(any(f.level == "fail" and "mixes a root" in f.message for f in report.findings))


class GitPathTests(unittest.TestCase):
    def test_changed_files_uses_nul_delimited_paths(self):
        output = "community/caf\N{LATIN SMALL LETTER E WITH ACUTE}/SKILL.md\0community/acme/file\nname.md\0".encode()
        with mock.patch.object(fc.subprocess, "run", return_value=fc.subprocess.CompletedProcess([], 0, output, b"")) as run:
            paths = fc.changed_files("base", "head")

        self.assertEqual(paths, ["community/acme/file\nname.md", "community/caf\N{LATIN SMALL LETTER E WITH ACUTE}/SKILL.md"])
        self.assertIn("-z", run.call_args.args[0])


class AllowedToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old_root = fc.ROOT
        fc.ROOT = self.root

    def tearDown(self):
        fc.ROOT = self.old_root
        self.temp.cleanup()

    def check(self, allowed, mcp=None, tools=None):
        skill = self.root / "community" / "plugin" / "skills" / "skill"
        skill.mkdir(parents=True)
        frontmatter = {
            "name": "skill", "description": "A sufficiently detailed skill description.",
            "allowed-tools": allowed,
            "permissions": {"mcp": mcp or {}, "network": [], "env": [], "tools": tools or []},
        }
        (skill / "SKILL.md").write_text("---\n" + fc.yaml.safe_dump(frontmatter, sort_keys=False) + "---\n")
        report = fc.Report()
        fc.check_frontmatter(skill, report)
        return report

    def test_exact_native_and_mcp_tools_match_declarations(self):
        report = self.check("Read mcp__qonto__list_transactions mcp__linkup__linkup-search",
                            {"qonto": ["list_transactions"], "linkup": ["linkup-search"]}, ["Read"])
        self.assertFalse(report.failed)

    def test_undeclared_native_and_external_mcp_tools_fail(self):
        report = self.check("Write mcp__linkup__linkup-search", {"qonto": []}, ["Read"])
        messages = [f.message for f in report.findings if f.level == "fail"]
        self.assertTrue(any("permissions.tools" in m for m in messages))
        self.assertTrue(any("permissions.mcp.linkup" in m for m in messages))

    def test_scoped_native_tool_with_spaces_requires_base_declaration(self):
        allowed = fc.allowed_tool_items("Bash(git status:*) Read")
        self.assertEqual(allowed, ["Bash(git status:*)", "Read"])
        report = self.check("Bash(git status:*) Read", tools=["Bash", "Read"])
        self.assertFalse(report.failed)
        self.assertTrue(any(f.level == "note" and "scopes `Bash`" in f.message for f in report.findings))

    def test_broad_wildcards_fail(self):
        report = self.check("* mcp__qonto__*", {"qonto": []})
        self.assertEqual(sum(f.level == "fail" for f in report.findings), 2)

    def test_unknown_community_native_tool_fails(self):
        report = self.check([], tools=["UnknownTool"])
        self.assertTrue(any(f.level == "fail" and "UnknownTool" in f.message for f in report.findings))


class PackageExecutionTests(unittest.TestCase):
    def test_package_execution_aliases_require_exact_versions(self):
        for command in ("pnpm dlx tool", "npm exec tool", "bunx tool"):
            with self.subTest(command=command):
                findings = list(fc.unpinned_installs(command))
                self.assertEqual(findings, [(command.rsplit(" ", 1)[0], "tool", "unpinned")])

    def test_pinned_package_execution_aliases_pass(self):
        for command in ("pnpm dlx tool@1.2.3", "npm exec tool@1.2.3", "bunx tool@1.2.3"):
            with self.subTest(command=command):
                self.assertEqual(list(fc.unpinned_installs(command)), [])


if __name__ == "__main__":
    unittest.main()
