"""Checks the plugin's hooks: the files they reference and what they print."""

import json
import subprocess
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent / "plugins" / "gemba"
HOOKS = json.loads((PLUGIN / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]


def commands(event):
    """Returns each command hook of an event as an argument list, with the plugin root filled in."""
    return [
        [part.replace("${CLAUDE_PLUGIN_ROOT}", str(PLUGIN)) for part in [hook["command"], *hook.get("args", [])]]
        for group in HOOKS.get(event, [])
        for hook in group["hooks"]
        if hook["type"] == "command"
    ]


class Hooks(unittest.TestCase):
    def test_every_plugin_path_a_hook_references_exists(self):
        for event in HOOKS:
            for argv in commands(event):
                for part in argv[1:]:
                    if str(PLUGIN) in part:
                        with self.subTest(event=event, path=part):
                            self.assertTrue(Path(part).exists())

    def test_session_start_hooks_set_a_timeout(self):
        for group in HOOKS.get("SessionStart", []):
            for hook in group["hooks"]:
                self.assertIn("timeout", hook)

    def test_session_start_output_fits_the_10000_character_cap(self):
        for argv in commands("SessionStart"):
            result = subprocess.run(argv, capture_output=True, text=True)
            with self.subTest(command=argv):
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(0 < len(result.stdout) <= 10000)


if __name__ == "__main__":
    unittest.main()
