"""Checks bug-start's develop.py: it opens origin/develop, after fetching, in a worktree
to reproduce a failure and closes it, leaving the branch, the uncommitted changes and
the untracked files of the project as they were."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/skills/bug-start/scripts/develop.py"


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def develop(cwd, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True)


class DevelopWorktree(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.name", "test")
        git(self.repo, "config", "user.email", "test@example.com")
        (self.repo / "app.py").write_text("print('main')\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "initial commit")
        git(self.repo, "switch", "-qc", "develop")
        (self.repo / "app.py").write_text("print('develop')\n")
        git(self.repo, "commit", "-qam", "change the app on develop")
        git(self.repo, "init", "-q", "--bare", ".remote/origin.git")
        (self.repo / ".git/info/exclude").write_text(".remote/\n")
        git(self.repo, "remote", "add", "origin", str(self.repo / ".remote/origin.git"))
        git(self.repo, "push", "-q", "origin", "main", "develop")
        git(self.repo, "switch", "-qc", "story/ABC-1/work", "main")
        (self.repo / "app.py").write_text("print('work in progress')\n")
        (self.repo / "notes.md").write_text("untracked\n")

    def tearDown(self):
        develop(self.repo, "close")
        self.tmp.cleanup()

    def open(self):
        """Opens the worktree and returns its path, failing the test before any write when it does not open."""
        result = develop(self.repo, "open")
        self.assertEqual(result.returncode, 0, result.stderr)
        path = Path(result.stdout.strip())
        self.assertTrue(path.is_absolute() and path.is_dir(), result.stdout)
        return path

    def state(self):
        return git(self.repo, "branch", "--show-current"), git(self.repo, "status", "--porcelain", "--untracked-files=all")

    def test_open_prints_a_worktree_of_develop_and_leaves_the_project_as_it_was(self):
        before = self.state()
        path = self.open()
        self.assertEqual((path / "app.py").read_text(), "print('develop')\n")
        self.assertEqual(git(path, "rev-parse", "HEAD"), git(self.repo, "rev-parse", "origin/develop"))
        self.assertEqual(self.state(), before)
        self.assertEqual((self.repo / "app.py").read_text(), "print('work in progress')\n")

    def test_close_removes_the_worktree_and_leaves_the_project_as_it_was(self):
        before = self.state()
        path = self.open()
        (path / "__pycache__").mkdir()
        (path / "output.txt").write_text("left by a run\n")
        result = develop(self.repo, "close")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(path.exists())
        self.assertEqual(len(git(self.repo, "worktree", "list").splitlines()), 1)
        self.assertEqual(self.state(), before)

    def test_run_runs_a_command_in_the_worktree_and_passes_on_its_output_and_exit_status(self):
        self.open()
        result = develop(self.repo, "run", "python3 app.py; exit 3")
        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "develop\n")
        self.assertEqual((self.repo / "app.py").read_text(), "print('work in progress')\n")

    def test_run_without_an_open_worktree_exits_1(self):
        result = develop(self.repo, "run", "python3 app.py")
        self.assertEqual(result.returncode, 1)
        self.assertIn("open", result.stderr)

    def test_open_twice_replaces_the_worktree_left_by_a_stopped_run(self):
        develop(self.repo, "open")
        result = develop(self.repo, "open")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(git(self.repo, "worktree", "list").splitlines()), 2)

    def test_the_worktree_lives_outside_the_project(self):
        path = self.open()
        self.assertFalse(path.resolve().is_relative_to(self.repo.resolve()), path)

    def test_close_removes_what_a_run_left_without_write_permission(self):
        path = self.open()
        develop(self.repo, "run", "mkdir -p ro/sub && touch ro/sub/f && chmod 555 ro/sub")
        result = develop(self.repo, "close")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(path.exists())
        self.open()

    def test_open_stops_with_its_reason_when_the_fetch_fails(self):
        git(self.repo, "remote", "set-url", "origin", str(self.repo / "nonexistent.git"))
        result = develop(self.repo, "open")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("fetch", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_close_without_a_worktree_succeeds(self):
        result = develop(self.repo, "close")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_open_takes_origin_develop_even_when_the_local_develop_is_behind(self):
        git(self.repo, "branch", "-f", "develop", "main")
        path = self.open()
        self.assertEqual(git(path, "rev-parse", "HEAD"), git(self.repo, "rev-parse", "origin/develop"))
        self.assertEqual((path / "app.py").read_text(), "print('develop')\n")

    def test_open_without_origin_develop_exits_1_and_creates_nothing(self):
        git(self.repo, "push", "-q", "origin", "--delete", "develop")
        result = develop(self.repo, "open")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("develop", result.stderr)
        self.assertEqual(len(git(self.repo, "worktree", "list").splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
