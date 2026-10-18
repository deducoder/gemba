"""Checks version-close's release script: the merge of develop into main, the tag of the
version, where it leaves develop, what it prints and what it refuses."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/skills/version-close/scripts/release.py"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.com",
       "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.com"}


def git(cwd, *args):
    result = subprocess.run(["git", *args], cwd=cwd, env=ENV, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def run(cwd, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, env=ENV, capture_output=True, text=True)


class Release(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.remote = base / "remote.git"
        self.work = base / "work"
        self.other = base / "other"
        git(base, "init", "-q", "--bare", str(self.remote))
        git(base, "clone", "-q", str(self.remote), str(self.work))
        self.commit(self.work, "a", "a", "chore: initial commit")
        git(self.work, "branch", "-M", "main")
        git(self.work, "push", "-q", "origin", "main")
        git(self.work, "switch", "-q", "-c", "develop")
        self.commit(self.work, "b", "b", "feat(billing): add invoice export")
        git(self.work, "push", "-q", "-u", "origin", "develop")
        self.origin_main = git(self.work, "rev-parse", "origin/main")

    def commit(self, cwd, name, content, message):
        (cwd / name).write_text(content)
        git(cwd, "add", name)
        git(cwd, "commit", "-qm", message)

    def clone_other(self):
        git(self.other.parent, "clone", "-q", str(self.remote), str(self.other))

    def released(self, *args):
        result = run(self.work, *(args or ("v0.1.0",)))
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.splitlines()

    def refused(self, *words, args=("v0.1.0",)):
        before = {ref: git(self.work, "rev-parse", ref) for ref in ("main", "develop")} if self.has("main") else None
        result = run(self.work, *args)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual(result.stdout, "")
        for word in words:
            self.assertIn(word, result.stderr)
        if before:
            self.assertEqual({ref: git(self.work, "rev-parse", ref) for ref in before}, before)
        self.assertEqual(git(self.work, "tag", "--list", "v0.1.0", "--points-at", "main") if self.has("main") else "", "")
        return result

    def has(self, ref):
        return subprocess.run(["git", "rev-parse", "--verify", "-q", ref], cwd=self.work, capture_output=True).returncode == 0

    def test_it_merges_develop_into_main_with_a_merge_commit_that_names_it(self):
        develop = git(self.work, "rev-parse", "develop")
        self.released()
        self.assertEqual(git(self.work, "log", "-1", "--format=%s", "main"), "Merge branch 'develop' into main")
        self.assertEqual(git(self.work, "rev-parse", "main^1", "main^2").split(), [self.origin_main, develop])

    def test_the_tag_is_annotated_on_the_merge(self):
        self.released()
        self.assertEqual(git(self.work, "cat-file", "-t", "v0.1.0"), "tag")
        self.assertEqual(git(self.work, "rev-parse", "v0.1.0^{commit}"), git(self.work, "rev-parse", "main"))

    def test_it_leaves_develop_level_with_main_and_the_work_on_develop(self):
        self.released()
        self.assertEqual(git(self.work, "rev-parse", "develop"), git(self.work, "rev-parse", "main"))
        self.assertEqual(git(self.work, "branch", "--show-current"), "develop")

    def test_it_pushes_nothing(self):
        self.released()
        self.assertEqual(git(self.work, "ls-remote", "--tags", "origin"), "")
        self.assertEqual(git(self.work, "ls-remote", "origin", "refs/heads/main").split()[0], self.origin_main)

    def test_it_prints_the_tag_the_state_and_the_commits_the_push_of_main_sends(self):
        lines = self.released()
        self.assertEqual(lines[:2], ["v0.1.0", "released"])
        self.assertEqual(len(lines), 4)
        self.assertTrue(lines[2].endswith("Merge branch 'develop' into main"))
        self.assertTrue(lines[3].endswith("feat(billing): add invoice export"))

    def test_it_brings_in_what_reached_origin_after_the_local_branches(self):
        self.clone_other()
        git(self.other, "switch", "-q", "develop")
        self.commit(self.other, "c", "c", "feat(billing): add credit notes")
        git(self.other, "push", "-q", "origin", "develop")
        self.released()
        self.assertEqual(git(self.work, "rev-parse", "main^2"), git(self.other, "rev-parse", "develop"))

    def test_it_resumes_a_release_not_pushed_without_merging_again(self):
        self.released()
        main = git(self.work, "rev-parse", "main")
        lines = self.released()
        self.assertEqual(lines[:2], ["v0.1.0", "already released"])
        self.assertEqual(git(self.work, "rev-parse", "main"), main)

    def test_it_refuses_uncommitted_changes_in_files_with_tracking(self):
        (self.work / "b").write_text("changed")
        self.refused("uncommitted")

    def test_untracked_files_do_not_count(self):
        (self.work / "notes").write_text("mine")
        self.released()

    def test_it_refuses_a_tag_that_already_exists_elsewhere(self):
        git(self.work, "tag", "-a", "v0.1.0", "-m", "v0.1.0", "main")
        self.refused("v0.1.0", "exists")

    def test_it_refuses_a_develop_with_nothing_main_lacks(self):
        git(self.work, "switch", "-q", "main")
        git(self.work, "merge", "-q", "--ff-only", "develop")
        git(self.work, "push", "-q", "origin", "main")
        git(self.work, "switch", "-q", "develop")
        self.refused("nothing")

    def test_it_refuses_local_commits_of_develop_that_origin_lacks(self):
        self.commit(self.work, "d", "d", "feat(billing): add discounts")
        self.refused("develop", "origin/develop")

    def test_it_refuses_local_commits_of_main_that_origin_lacks(self):
        git(self.work, "switch", "-q", "main")
        self.commit(self.work, "m", "m", "fix: hotfix")
        git(self.work, "switch", "-q", "develop")
        self.refused("main", "origin/main")

    def test_it_refuses_without_origin_main(self):
        git(self.work, "push", "-q", "origin", "--delete", "main")
        git(self.work, "fetch", "-q", "--prune")
        self.refused("origin/main")

    def test_it_refuses_a_tag_that_is_not_a_version(self):
        self.refused("v<X.Y.Z>", args=("0.1",))

    def test_with_conflicts_it_aborts_names_the_files_and_leaves_main_unmerged(self):
        self.clone_other()
        git(self.other, "switch", "-q", "main")
        self.commit(self.other, "b", "from main", "fix: hotfix")
        git(self.other, "push", "-q", "origin", "main")
        result = run(self.work, "v0.1.0")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("b", result.stderr)
        self.assertIn("conflict", result.stderr.lower())
        self.assertEqual(git(self.work, "rev-parse", "main"), git(self.work, "rev-parse", "origin/main"))
        self.assertEqual(git(self.work, "branch", "--show-current"), "develop")
        self.assertEqual(git(self.work, "status", "--porcelain", "--untracked-files=no"), "")
        self.assertEqual(git(self.work, "tag", "--list"), "")


if __name__ == "__main__":
    unittest.main()
