"""Checks the plugin manifests: what each plugin declares it depends on, and that the
Claude Code CLI honors it, installing and keeping the dependency."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def manifest(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def names(dependencies):
    """Returns the plugin names of a `dependencies` list, whose items are a name or an object with `name`."""
    return [item if isinstance(item, str) else item["name"] for item in dependencies]


class Dependencies(unittest.TestCase):
    def test_gemba_code_declares_that_it_depends_on_gemba(self):
        self.assertEqual(manifest("plugins/gemba-code/.claude-plugin/plugin.json").get("dependencies"), ["gemba"])

    def test_every_dependency_is_a_plugin_of_the_marketplace(self):
        in_marketplace = {plugin["name"] for plugin in manifest(".claude-plugin/marketplace.json")["plugins"]}
        for path in sorted(ROOT.glob("plugins/*/.claude-plugin/plugin.json")):
            with self.subTest(plugin=path.parents[1].name):
                declared = names(json.loads(path.read_text(encoding="utf-8")).get("dependencies", []))
                self.assertLessEqual(set(declared), in_marketplace)


@unittest.skipUnless(shutil.which("claude"), "claude CLI not installed")
class InstallingWithDependencies(unittest.TestCase):
    """Runs the CLI on a renamed copy of the marketplace and a config directory of its own, so the
    installation of the person running the tests is never touched."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.marketplace = base / "marketplace"
        self.project = base / "project"
        self.project.mkdir()
        self.env = {**os.environ, "CLAUDE_CONFIG_DIR": str(base / "config")}
        shutil.copytree(ROOT / "plugins", self.marketplace / "plugins", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / ".claude-plugin", self.marketplace / ".claude-plugin")
        path = self.marketplace / ".claude-plugin/marketplace.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["name"] = "gemba-test"
        path.write_text(json.dumps(data), encoding="utf-8")

    def claude(self, *args):
        return subprocess.run(["claude", "plugin", *args], cwd=self.project, env=self.env, capture_output=True, text=True)

    def test_installing_gemba_code_enables_gemba_and_gemba_cannot_be_disabled_while_it_is_enabled(self):
        added = self.claude("marketplace", "add", str(self.marketplace), "--scope", "project")
        self.assertEqual(added.returncode, 0, added.stdout + added.stderr)
        installed = self.claude("install", "gemba-code@gemba-test", "--scope", "project")
        self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        settings = json.loads((self.project / ".claude/settings.json").read_text(encoding="utf-8"))
        self.assertEqual(settings["enabledPlugins"], {"gemba-code@gemba-test": True, "gemba@gemba-test": True})
        disabled = self.claude("disable", "gemba@gemba-test", "--scope", "project")
        self.assertNotEqual(disabled.returncode, 0)
        self.assertIn("gemba-code", disabled.stdout + disabled.stderr)


if __name__ == "__main__":
    unittest.main()
