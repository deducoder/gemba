"""Checks the plugin's hooks: the files they reference and what they print."""

import json
import subprocess
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent / "plugins" / "gemba"
HOOKS = json.loads((PLUGIN / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]


def command_hooks(event):
    """Returns each command hook of an event."""
    return [hook for group in HOOKS.get(event, []) for hook in group["hooks"] if hook["type"] == "command"]


def argv(hook):
    """Returns a hook's command and arguments, with the plugin root filled in."""
    return [part.replace("${CLAUDE_PLUGIN_ROOT}", str(PLUGIN)) for part in [hook["command"], *hook.get("args", [])]]


class Hooks(unittest.TestCase):
    def test_session_start_has_a_command_hook(self):
        self.assertTrue(command_hooks("SessionStart"))

    def test_every_plugin_path_a_hook_references_exists(self):
        for event in HOOKS:
            for hook in command_hooks(event):
                for part in argv(hook):
                    with self.subTest(event=event, part=part):
                        self.assertNotIn("${", part)  # a misspelled placeholder is never filled in
                        if str(PLUGIN) in part:
                            self.assertTrue(Path(part).exists())

    def test_every_command_hook_sets_a_positive_timeout(self):
        for event in HOOKS:
            for hook in command_hooks(event):
                with self.subTest(event=event, command=hook["command"]):
                    self.assertIsInstance(hook.get("timeout"), int)
                    self.assertGreater(hook["timeout"], 0)

    def test_session_start_output_fits_the_10000_character_cap(self):
        for hook in command_hooks("SessionStart"):
            with self.subTest(command=hook["command"]):
                result = subprocess.run(
                    argv(hook), capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=hook["timeout"]
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(0 < len(result.stdout) <= 10000)


if __name__ == "__main__":
    unittest.main()
