"""Checks the script that runs the evals of what a change touches: which `claude plugin eval`
invocations it makes for each kind of changed file, read through a fake `claude` that records
its arguments."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "evals/changed.py"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.com",
       "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.com"}
FLAGS = ["--scaffold", "--runs", "1"]
ALLOW = ["--allow-tools", "Bash(python3:*)", "Bash(git:*)", "Edit", "Write"]
FAKE_CLAUDE = """#!/usr/bin/env python3
import json, os, sys
with open(os.environ["CLAUDE_CALLS"], "a", encoding="utf-8") as calls:
    calls.write(json.dumps(sys.argv[1:]) + "\\n")
"""


def git(cwd, *args):
    result = subprocess.run(["git", *args], cwd=cwd, env=ENV, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def for_skill(skill):
    return ["plugin", "eval", ".", *FLAGS, "--case", f"{skill}-*", *ALLOW]


class Changed(unittest.TestCase):
    """Builds, per test, a repository with a copy of the plugins and evals on develop, pushed to a
    bare origin, and a work branch where each test changes files."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.work = base / "work"
        ignore = shutil.ignore_patterns("results", "__pycache__", "*.jsonl")
        for folder in ("plugins", "evals", "tests/fixtures"):
            shutil.copytree(ROOT / folder, self.work / folder, ignore=ignore)
        shutil.copy(ROOT / "README.md", self.work / "README.md")
        git(base, "init", "-q", "--bare", "origin.git")
        git(self.work, "init", "-q", "-b", "develop")
        git(self.work, "add", ".")
        git(self.work, "commit", "-qm", "initial commit")
        git(self.work, "remote", "add", "origin", str(base / "origin.git"))
        git(self.work, "push", "-q", "-u", "origin", "develop")
        git(self.work, "switch", "-q", "-c", "story/ABC-1/work")
        bin_dir = base / "bin"
        bin_dir.mkdir()
        (bin_dir / "claude").write_text(FAKE_CLAUDE, encoding="utf-8")
        (bin_dir / "claude").chmod(0o755)
        self.calls = base / "calls.jsonl"
        self.env = {**ENV, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}", "CLAUDE_CALLS": str(self.calls)}

    def touch(self, path, commit=False):
        file = self.work / path
        file.parent.mkdir(parents=True, exist_ok=True)
        with file.open("a", encoding="utf-8") as handle:
            handle.write("\n# changed\n")
        if commit:
            git(self.work, "add", path)
            git(self.work, "commit", "-qm", f"change {path}")

    def run_script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.work, env=self.env,
                              capture_output=True, text=True)

    def invocations(self):
        if not self.calls.exists():
            return []
        return [json.loads(line) for line in self.calls.read_text(encoding="utf-8").splitlines()]

    def test_a_change_to_one_skill_runs_its_evals_once_with_one_run_per_case(self):
        self.touch("evals/story-close/happy/case.yaml", commit=True)
        self.touch("plugins/gemba-code/skills/story-close/SKILL.md")
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.invocations(), [for_skill("story-close")])

    def test_a_change_to_two_skills_runs_one_invocation_per_skill(self):
        self.touch("plugins/gemba-code/skills/story-close/SKILL.md")
        self.touch("plugins/gemba-code/skills/story-start/SKILL.md")
        self.run_script()
        self.assertCountEqual(self.invocations(), [for_skill("story-close"), for_skill("story-start")])

    def test_a_change_to_a_script_runs_the_evals_of_the_skills_that_name_it(self):
        self.touch("plugins/gemba-code/scripts/develop.py", commit=True)
        self.run_script()
        self.assertCountEqual(self.invocations(), [for_skill("bug-start"), for_skill("bug-implement")])

    def test_a_change_to_a_script_another_named_script_imports_runs_the_evals_of_both(self):
        self.touch("plugins/gemba-code/scripts/branch.py")
        self.run_script()
        skills = {call[call.index("--case") + 1] for call in self.invocations()}
        self.assertEqual(skills, {"bug-implement-*", "story-close-*", "story-implement-*", "story-review-*", "bug-start-*"})

    def test_a_change_to_an_eval_file_other_skills_load_runs_their_evals_too(self):
        self.touch("evals/story-start/project.sh")
        self.run_script()
        skills = {call[call.index("--case") + 1] for call in self.invocations()}
        self.assertLessEqual({"story-start-*", "story-implement-*", "bug-start-*", "story-close-*"}, skills)
        self.assertNotIn("read-work-item", skills)

    def test_a_change_to_what_every_case_shares_runs_every_eval_once(self):
        for path in ("evals/mocks/atlassian/getJiraIssue.json", "tests/fixtures/atlassian-stub/README.md",
                     "plugins/gemba/context/gemba.md", "plugins/gemba-code/hooks/hooks.json",
                     "plugins/gemba-code/references/priority.md", "plugins/gemba-code/scripts/draft.py",
                     ".claude-plugin/marketplace.json", "plugins/gemba-code/.claude-plugin/plugin.json"):
            with self.subTest(path=path):
                git(self.work, "checkout", "-q", "--", ".")
                git(self.work, "clean", "-qfd")
                self.calls.unlink(missing_ok=True)
                self.touch(path)
                self.run_script()
                self.assertEqual(self.invocations(), [["plugin", "eval", ".", *FLAGS, *ALLOW]])

    def test_a_change_without_evals_runs_none_and_says_so(self):
        self.touch("README.md", commit=True)
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.invocations(), [])
        self.assertIn("No evals cover the changed files.", result.stdout)

    def test_dry_run_prints_each_command_without_running_it(self):
        self.touch("plugins/gemba-code/skills/story-close/SKILL.md")
        result = self.run_script("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.invocations(), [])
        self.assertIn("claude plugin eval . --scaffold --runs 1 --case 'story-close-*' --allow-tools", result.stdout)


if __name__ == "__main__":
    unittest.main()
