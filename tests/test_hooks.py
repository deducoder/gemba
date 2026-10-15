"""Checks the hooks of every plugin: the files they reference and what they print."""

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS = {
    path.parent.parent: json.loads(path.read_text(encoding="utf-8"))["hooks"]
    for path in sorted(ROOT.glob("plugins/*/hooks/hooks.json"))
}


def command_hooks(event=None):
    """Yields each plugin, event and command hook, for one event or for all."""
    for plugin, hooks in HOOKS.items():
        for name, groups in hooks.items():
            if event in (None, name):
                for group in groups:
                    for hook in group["hooks"]:
                        if hook["type"] == "command":
                            yield plugin, name, hook


def argv(plugin, hook):
    """Returns a hook's command and arguments, with the plugin root filled in."""
    return [part.replace("${CLAUDE_PLUGIN_ROOT}", str(plugin)) for part in [hook["command"], *hook.get("args", [])]]


class Hooks(unittest.TestCase):
    def test_every_plugin_injects_its_context_at_session_start(self):
        contexts = sorted(ROOT.glob("plugins/*/context/*.md"))
        self.assertTrue(contexts)
        for context in contexts:
            plugin = context.parent.parent
            with self.subTest(plugin=plugin.name, context=context.name):
                outputs = [
                    subprocess.run(argv(plugin, hook), capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=hook["timeout"]).stdout
                    for owner, _, hook in command_hooks("SessionStart")
                    if owner == plugin
                ]
                self.assertIn(context.read_text(encoding="utf-8"), outputs)

    def test_every_plugin_path_a_hook_references_exists(self):
        for plugin, event, hook in command_hooks():
            for part in argv(plugin, hook):
                with self.subTest(plugin=plugin.name, event=event, part=part):
                    self.assertNotIn("${", part)  # a misspelled placeholder is never filled in
                    if str(plugin) in part:
                        self.assertTrue(Path(part).exists())

    def test_every_command_hook_sets_a_positive_timeout(self):
        for plugin, event, hook in command_hooks():
            with self.subTest(plugin=plugin.name, event=event, command=hook["command"]):
                self.assertIsInstance(hook.get("timeout"), int)
                self.assertGreater(hook["timeout"], 0)

    def test_session_start_output_fits_the_10000_character_cap(self):
        for plugin, _, hook in command_hooks("SessionStart"):
            with self.subTest(plugin=plugin.name, command=hook["command"]):
                result = subprocess.run(
                    argv(plugin, hook), capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=hook["timeout"]
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(0 < len(result.stdout) <= 10000)


if __name__ == "__main__":
    unittest.main()
