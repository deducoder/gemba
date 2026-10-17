"""Checks the structure of every skill in the marketplace plugins: frontmatter, the files
each SKILL.md references, and the shapes other parts depend on."""

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "gemba"
SKILLS = sorted(ROOT.glob("plugins/*/skills/*/SKILL.md"))
SIDE_EFFECTS = [path for path in SKILLS if path.parent.name == "setup" or path.parent.name.endswith("-close")]
FRONTMATTER = re.compile(r"---\n(.*?)\n---\n", re.DOTALL)
REFERENCE = re.compile(r"\$\{CLAUDE_SKILL_DIR\}/([\w./-]+)")
PLUGIN_SCRIPT = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/(scripts/[\w./-]+)")
PLUGIN_FILE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+)")
RUN_SCRIPT = re.compile(r"python3 (\$\{CLAUDE_(?:SKILL_DIR|PLUGIN_ROOT)\}/[\w./-]+)")
INJECTED = re.compile(r"!`([^`]*)`")
PROJECT_FILE = re.compile(r"(?<![\w}\"]/)(?<!\w)(?:\.gemba/|\.claude/|CLAUDE\.md)")


def allowed_tools(text):
    """Returns the allowed-tools entries in the frontmatter of a SKILL.md, written
    as a block list or as a flow list."""
    match = FRONTMATTER.match(text)
    lines = match.group(1).splitlines() if match else []
    for i, line in enumerate(lines):
        if line.startswith("allowed-tools:"):
            rest = line.split(":", 1)[1].strip()
            if rest.startswith("["):
                return [item.strip().strip("'\"") for item in rest.strip("[]").split(",") if item.strip()]
            items = []
            for item in lines[i + 1:]:
                if not re.match(r"^\s*- ", item):
                    break
                items.append(item.strip()[2:].strip().strip("'\""))
            return items
    return []


def read(path):
    """Returns the frontmatter fields and the full text of a SKILL.md."""
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER.match(text)
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
            for pattern, base in ((REFERENCE, path.parent), (PLUGIN_FILE, path.parents[2])):
                for ref in pattern.findall(read(path)[1]):
                    with self.subTest(skill=path.parent.name, ref=ref):
                        self.assertTrue((base / ref).exists())

    def test_injected_commands_have_no_command_substitution(self):
        for path in SKILLS:
            for command in INJECTED.findall(read(path)[1]):
                with self.subTest(skill=path.parent.name, command=command):
                    self.assertNotIn("$(", command)

    def test_injected_commands_read_project_files_from_the_project_dir(self):
        for path in SKILLS:
            for command in INJECTED.findall(read(path)[1]):
                with self.subTest(skill=path.parent.name, command=command):
                    self.assertIsNone(PROJECT_FILE.search(command))

    def test_assets_are_injected_and_readable_outside_the_project(self):
        for path in SKILLS:
            text = read(path)[1]
            assets = {ref for ref in REFERENCE.findall(text) if ref.startswith("assets/") and not ref.endswith("/")}
            if not assets:
                continue
            with self.subTest(skill=path.parent.name):
                self.assertIn("Read(/${CLAUDE_SKILL_DIR}/assets/*)", allowed_tools(text))
                commands = INJECTED.findall(text)
                for asset in assets:
                    self.assertIn("cat ${CLAUDE_SKILL_DIR}/" + asset, commands)

    def test_skills_allow_only_their_own_files_and_the_scripts_of_their_plugin(self):
        for path in SKILLS:
            for tool in allowed_tools(read(path)[1]):
                with self.subTest(skill=path.parent.name, tool=tool):
                    self.assertTrue("${CLAUDE_SKILL_DIR}/" in tool or "${CLAUDE_PLUGIN_ROOT}/scripts/" in tool)

    def test_plugin_scripts_allowed_by_a_skill_exist(self):
        for path in SKILLS:
            for tool in allowed_tools(read(path)[1]):
                for script in PLUGIN_SCRIPT.findall(tool):
                    with self.subTest(skill=path.parent.name, script=script):
                        self.assertTrue((path.parents[2] / script).is_file())

    def test_a_skill_allows_exactly_the_scripts_it_runs(self):
        for path in SKILLS:
            text = read(path)[1]
            allowed = {script for tool in allowed_tools(text) for script in RUN_SCRIPT.findall(tool)}
            run = set(RUN_SCRIPT.findall(INJECTED.sub("", FRONTMATTER.sub("", text, count=1))))
            with self.subTest(skill=path.parent.name):
                self.assertEqual(allowed, run)

    def test_skills_with_side_effects_are_invoked_only_by_the_user(self):
        names = {path.parent.name for path in SIDE_EFFECTS}
        self.assertLessEqual({"setup", "session-close", "story-close", "bug-close", "spike-close"}, names)
        for path in SIDE_EFFECTS:
            with self.subTest(skill=path.parent.name):
                self.assertEqual(read(path)[0].get("disable-model-invocation"), "true")

    def test_implement_skills_cancel_with_the_cancellation_comment(self):
        for name in ("story-implement", "bug-implement", "spike-implement"):
            with self.subTest(skill=name):
                text = read(ROOT / "plugins/gemba-code/skills" / name / "SKILL.md")[1]
                self.assertIn("cat ${CLAUDE_PLUGIN_ROOT}/references/cancelled.md", INJECTED.findall(text))
                self.assertIn("python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cancelled.py --site <site>", text)

    def test_the_cancellation_comment_has_its_heading_and_lines(self):
        lines = (ROOT / "plugins/gemba-code/references/cancelled.md").read_text(encoding="utf-8").splitlines()
        self.assertIn("### Cancelled", lines)
        self.assertEqual([line.split(":")[0] for line in lines if line.startswith("* ")], ["* Reason", "* Found", "* Replaced by"])

    def test_setup_template_has_the_gemba_and_language_headings(self):
        lines = (PLUGIN / "skills/setup/assets/CLAUDE.md").read_text(encoding="utf-8").splitlines()
        for heading in ("# Gemba", "## Language"):
            self.assertIn(heading, lines)

    def test_handoff_template_has_the_sections_the_validator_expects(self):
        skill = PLUGIN / "skills/session-close"
        spec = importlib.util.spec_from_file_location("handoff", skill / "scripts/handoff.py")
        handoff = importlib.util.module_from_spec(spec)
        sys.dont_write_bytecode = True  # importing handoff.py must leave no __pycache__ inside the plugin
        try:
            spec.loader.exec_module(handoff)
        finally:
            sys.dont_write_bytecode = False
        template = (skill / "assets/handoff.md").read_text(encoding="utf-8")
        self.assertEqual([heading for heading, _ in handoff.sections(template)], handoff.SECTIONS + ["State"])

    @unittest.skipUnless(shutil.which("claude"), "claude CLI not installed")
    def test_claude_plugin_validate_strict_passes(self):
        marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        for target in [ROOT] + [ROOT / plugin["source"] for plugin in marketplace["plugins"]]:
            with self.subTest(target=target.relative_to(ROOT).as_posix()):
                result = subprocess.run(["claude", "plugin", "validate", str(target), "--strict"], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
