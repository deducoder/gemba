"""Checks the hooks of every plugin: the files they reference and what they print."""

import json
import subprocess
import sys
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


GATE = ROOT / "plugins/gemba-code/scripts/push_gate.py"

ASK = [
    "git push origin develop",
    "git -C . push",
    "git -c push.default=current push origin main",
    "git status && git push",
    "cd repo; git push",
    "GIT_TRACE=1 git push",
    "/usr/bin/git push",
    "git status\ngit push origin develop",
    "if true; then git push; fi",
    "{ git push; }",
    "`git push`",
    "git status #\ngit push",
    "echo 'unterminated git push",
]
DENY = [
    "git push --force",
    "git push -f origin main",
    "git push -uf origin main",
    "git push --force-with-lease",
    "git push origin +main",
    "git status\ngit push --force origin main",
    "git push --force origin 'main",
]
NONE = ["git status", 'echo "git push"', "git log --grep=push", "git pushx"]


def gate(command):
    """Runs the push gate as Claude Code does and returns its decision, or None."""
    result = subprocess.run(
        [sys.executable, str(GATE)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}),
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    if not result.stdout.strip():
        return None
    output = json.loads(result.stdout)["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert output["permissionDecisionReason"]
    return output["permissionDecision"]


class PushGate(unittest.TestCase):
    def test_gemba_code_registers_the_gate_on_bash_before_the_tool_runs(self):
        plugin = ROOT / "plugins/gemba-code"
        groups = HOOKS[plugin]["PreToolUse"]
        self.assertEqual([group["matcher"] for group in groups], ["Bash"])
        self.assertEqual(argv(plugin, groups[0]["hooks"][0]), ["python3", str(GATE)])

    def test_a_push_asks(self):
        for command in ASK:
            with self.subTest(command=command):
                self.assertEqual(gate(command), "ask")

    def test_a_forced_push_is_denied(self):
        for command in DENY:
            with self.subTest(command=command):
                self.assertEqual(gate(command), "deny")

    def test_a_malformed_tool_input_gets_no_decision_and_does_not_fail(self):
        result = subprocess.run([sys.executable, str(GATE)], input='{"tool_input": null}', capture_output=True, text=True, timeout=10)
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_anything_else_gets_no_decision(self):
        for command in NONE:
            with self.subTest(command=command):
                self.assertIsNone(gate(command))


if __name__ == "__main__":
    unittest.main()
