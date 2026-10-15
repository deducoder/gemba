"""Checks the branch script of the work item skills: the branch it creates, where
it starts from and what it prints."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/scripts/branch.py"
SUMMARY = "Let customers download their invoices"


def git(cwd, *args):
    result = subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", *args],
        cwd=cwd, capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def run(cwd, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True)


class Branch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.remote = base / "remote.git"
        self.work = base / "work"
        self.other = base / "other"
        git(base, "init", "-q", "--bare", str(self.remote))
        git(base, "clone", "-q", str(self.remote), str(self.work))
        (self.work / "a").write_text("a")
        git(self.work, "add", "a")
        git(self.work, "commit", "-qm", "initial commit")
        git(self.work, "branch", "-M", "main")
        git(self.work, "push", "-q", "origin", "main")
        git(self.work, "switch", "-q", "-c", "develop")
        git(self.work, "push", "-q", "-u", "origin", "develop")

    def push_a_commit_to_develop_from_another_clone(self):
        git(self.other.parent, "clone", "-q", str(self.remote), str(self.other))
        git(self.other, "switch", "-q", "develop")
        (self.other / "b").write_text("b")
        git(self.other, "add", "b")
        git(self.other, "commit", "-qm", "feat(billing): add invoice export")
        git(self.other, "push", "-q", "origin", "develop")

    def test_it_creates_the_branch_from_origin_develop_even_when_develop_is_behind(self):
        self.push_a_commit_to_develop_from_another_clone()
        result = run(self.work, "story", "ABC-1", SUMMARY)
        self.assertEqual(result.returncode, 0, result.stderr)
        branch = "story/ABC-1/let-customers-download-their-invoices"
        self.assertEqual(result.stdout.strip(), branch)
        self.assertEqual(git(self.work, "branch", "--show-current"), branch)
        self.assertEqual(git(self.work, "rev-parse", "HEAD"), git(self.other, "rev-parse", "HEAD"))
        self.assertEqual(git(self.work, "rev-parse", "develop"), git(self.work, "rev-parse", "HEAD~1"))

    def test_it_neither_pushes_nor_sets_an_upstream(self):
        run(self.work, "story", "ABC-1", SUMMARY)
        self.assertEqual(git(self.work, "ls-remote", "--heads", "origin", "story/*"), "")
        upstream = subprocess.run(["git", "rev-parse", "--abbrev-ref", "@{upstream}"], cwd=self.work, capture_output=True, text=True)
        self.assertNotEqual(upstream.returncode, 0)

    def test_the_summary_becomes_lowercase_kebab_case(self):
        cases = {
            "Handle epics, keys and non-story ideas in story-start": "handle-epics-keys-and-non-story-ideas-in-story-start",
            "Don't \"quote\": it's 100% (ok)?": "don-t-quote-it-s-100-ok",
        }
        for summary, slug in cases.items():
            with self.subTest(summary=summary):
                git(self.work, "switch", "-q", "develop")
                result = run(self.work, "story", "ABC-2", summary)
                self.assertEqual(result.stdout.strip(), f"story/ABC-2/{slug}", result.stderr)

    def test_the_type_is_part_of_the_branch(self):
        result = run(self.work, "bug", "ABC-3", "Totals leave out the tax")
        self.assertEqual(result.stdout.strip(), "bug/ABC-3/totals-leave-out-the-tax", result.stderr)

    def test_a_summary_without_letters_or_digits_creates_nothing(self):
        result = run(self.work, "story", "ABC-4", "日本語")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("Summary", result.stderr)
        self.assertEqual(git(self.work, "branch", "--list", "story/*"), "")

    def test_wrong_arguments_print_the_usage_and_create_nothing(self):
        result = run(self.work, "story", "ABC-1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("Usage", result.stderr)
        self.assertEqual(git(self.work, "branch", "--list", "story/*"), "")


if __name__ == "__main__":
    unittest.main()
