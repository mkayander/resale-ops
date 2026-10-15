import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.check_package import ROOT, check, read_frontmatter


class PackageTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "package"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv"))
        self.skill = self.root / "skills/resale-ops/SKILL.md"

    def validate(self):
        with contextlib.redirect_stdout(io.StringIO()):
            check(self.root)

    def test_current_package(self):
        self.validate()

    def test_valid_folded_yaml_and_external_link(self):
        self.skill.write_text(
            "---\nname: resale-ops\ndescription: >\n  First line\n  second line\nlicense: MIT\n---\n"
            "[Source](https://example.com/product)\n", encoding="utf-8",
        )
        self.assertEqual(read_frontmatter(self.skill)["description"], "First line second line\n")
        self.validate()

    def test_duplicate_and_non_string_yaml_fields_are_rejected(self):
        for description in ("description: true", "description: test\nname: different", "description: []"):
            with self.subTest(description=description):
                self.skill.write_text(f"---\nname: resale-ops\n{description}\nlicense: MIT\n---\nBody\n", encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.validate()

    def test_broken_documentation_link_is_rejected(self):
        document = self.root / "docs/INSTALL.md"
        document.write_text("[Missing](not-here.md)\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Broken or escaping link"):
            self.validate()

    def test_skill_cannot_depend_on_files_outside_installed_subtree(self):
        with self.skill.open("a", encoding="utf-8") as stream:
            stream.write("\n[Root docs](../../README.md)\n")
        with self.assertRaisesRegex(ValueError, "Broken or escaping link"):
            self.validate()

    def test_missing_license_is_rejected(self):
        (self.skill.parent / "LICENSE").unlink()
        with self.assertRaises(OSError):
            self.validate()

    def test_package_json_version_must_match_manifest(self):
        path = self.root / "package.json"
        original = json.loads(path.read_text(encoding="utf-8"))
        path.write_text(json.dumps({**original, "version": "9.9.9"}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "package.json version differs"):
            self.validate()

    def test_invalid_manifests_are_rejected(self):
        path = self.root / "plugin.json"
        original = json.loads(path.read_text(encoding="utf-8"))
        for changes in ({"name": "another"}, {"version": 3}, {"version": "0.0.0"}, {"mcpServers": {}}):
            with self.subTest(changes=changes):
                path.write_text(json.dumps({**original, **changes}), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.validate()

    def test_legacy_mcp_autowiring_is_rejected(self):
        (self.root / ".mcp.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "automatic client configuration"):
            self.validate()

    def test_runnable_profiles_are_rejected_even_if_named_inspection(self):
        for folder in ("examples", "skills/resale-ops", "docs"):
            with self.subTest(folder=folder):
                path = self.root / folder / "inspection.client.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({"mcpServers": {"inspection": {
                    "command": "uv", "args": ["run", "compare-mcp"],
                    "env": {"MARKETPLACE_SOURCES": "yandex_market"},
                }}}), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Runnable MCP client profile"):
                    self.validate()
                path.unlink()

    def test_optimized_python_cannot_disable_validation(self):
        (self.root / ".mcp.json").write_text("{}", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-O", "scripts/check_package.py"], cwd=self.root,
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("automatic client configuration", result.stderr)


if __name__ == "__main__":
    unittest.main()
