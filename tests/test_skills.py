"""Checks the structure of every skill in the plugin: frontmatter, the files
each SKILL.md references, and the shapes other parts depend on."""

import importlib.util
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent / "plugins" / "gemba"
SKILLS = sorted(PLUGIN.glob("skills/*/SKILL.md"))
SIDE_EFFECTS = ["setup", "session-close"]

sys.dont_write_bytecode = True  # importing handoff.py must leave no __pycache__ inside the plugin


def read(path):
    """Returns the frontmatter fields and the full text of a SKILL.md."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    fields = dict(re.findall(r"^([\w-]+):[ \t]*(.*)$", match.group(1), re.MULTILINE)) if match else {}
    return fields, text


class SkillStructure(unittest.TestCase):
    def test_the_plugin_has_skills(self):
        self.assertTrue(SKILLS)

    def test_name_matches_the_directory_in_kebab_case(self):
        for path in SKILLS:
            with self.subTest(skill=path.parent.name):
                self.assertEqual(read(path)[0].get("name"), path.parent.name)
                self.assertRegex(path.parent.name, r"^[a-z0-9]+(-[a-z0-9]+)*$")

    def test_description_has_1_to_1024_characters(self):
        for path in SKILLS:
            with self.subTest(skill=path.parent.name):
                self.assertTrue(0 < len(read(path)[0].get("description", "")) <= 1024)

    def test_referenced_files_exist(self):
        for path in SKILLS:
            for ref in re.findall(r"\$\{CLAUDE_SKILL_DIR\}/([\w./-]+)", read(path)[1]):
                with self.subTest(skill=path.parent.name, ref=ref):
                    self.assertTrue((path.parent / ref).exists())

    def test_injected_commands_have_no_command_substitution(self):
        for path in SKILLS:
            for command in re.findall(r"!`([^`]*)`", read(path)[1]):
                with self.subTest(skill=path.parent.name, command=command):
                    self.assertNotIn("$(", command)

    def test_skills_with_side_effects_are_invoked_only_by_the_user(self):
        for name in SIDE_EFFECTS:
            with self.subTest(skill=name):
                fields = read(PLUGIN / "skills" / name / "SKILL.md")[0]
                self.assertEqual(fields.get("disable-model-invocation"), "true")

    def test_setup_template_has_the_gemba_and_language_headings(self):
        lines = (PLUGIN / "skills/setup/assets/CLAUDE.md").read_text(encoding="utf-8").splitlines()
        for heading in ("# Gemba", "## Language"):
            self.assertIn(heading, lines)

    def test_handoff_template_has_the_sections_the_validator_expects(self):
        skill = PLUGIN / "skills/session-close"
        spec = importlib.util.spec_from_file_location("handoff", skill / "scripts/handoff.py")
        handoff = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(handoff)
        template = (skill / "assets/handoff.md").read_text(encoding="utf-8")
        self.assertEqual([heading for heading, _ in handoff.sections(template)], handoff.SECTIONS + ["State"])

    @unittest.skipUnless(shutil.which("claude"), "claude CLI not installed")
    def test_claude_plugin_validate_strict_passes(self):
        result = subprocess.run(["claude", "plugin", "validate", str(PLUGIN), "--strict"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
