"""Checks the branch script of the work item skills: the branch it creates, where
it starts from and what it prints."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/scripts/branch.py"
SUMMARY = "Let customers download their invoices"
IDENTITY = {"GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.com"}


def git(cwd, *args):
    result = subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", *args],
        cwd=cwd, capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def run(cwd, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, env={**os.environ, **IDENTITY},
                          capture_output=True, text=True)


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

    def push_a_commit_to_develop_from_another_clone(self, name="b", content="b"):
        git(self.other.parent, "clone", "-q", str(self.remote), str(self.other))
        git(self.other, "switch", "-q", "develop")
        (self.other / name).write_text(content)
        git(self.other, "add", name)
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
        self.assertIn("--check", result.stderr)
        self.assertEqual(git(self.work, "branch", "--list", "story/*"), "")

    def make_the_tracked_file_dirty(self):
        (self.work / "a").write_text("changed")

    def delete_develop_from_the_remote_only(self):
        git(self.remote, "update-ref", "-d", "refs/heads/develop")

    def test_check_passes_on_a_clean_tree_and_prints_nothing(self):
        result = run(self.work, "--check")
        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)

    def test_check_ignores_untracked_files(self):
        (self.work / "private.md").write_text("notes")
        self.assertEqual(run(self.work, "--check").returncode, 0)

    def test_check_refuses_a_modified_tracked_file_and_names_it(self):
        self.make_the_tracked_file_dirty()
        result = run(self.work, "--check")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("Uncommitted", result.stderr)
        self.assertIn(" M a", result.stderr)

    def test_check_refuses_without_origin_develop_even_when_the_local_ref_is_stale(self):
        self.delete_develop_from_the_remote_only()
        result = run(self.work, "--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("origin/develop", result.stderr)

    def test_the_create_command_refuses_and_creates_nothing_when_the_check_fails(self):
        for name, prepare in (("dirty tree", self.make_the_tracked_file_dirty), ("no origin/develop", self.delete_develop_from_the_remote_only)):
            with self.subTest(case=name):
                prepare()
                result = run(self.work, "story", "ABC-1", SUMMARY)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, "")
                self.assertEqual(git(self.work, "branch", "--list", "story/*"), "")
                git(self.work, "checkout", "-q", "--", "a")

    def test_changes_on_the_branch_of_the_same_work_do_not_stop_it(self):
        branch = run(self.work, "story", "ABC-1", SUMMARY).stdout.strip()
        self.make_the_tracked_file_dirty()
        for args in (("--check", "story", "ABC-1", SUMMARY), ("story", "ABC-1", SUMMARY)):
            with self.subTest(args=args):
                result = run(self.work, *args)
                self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(git(self.work, "branch", "--show-current"), branch)
        self.assertEqual((self.work / "a").read_text(), "changed")

    def test_changes_stop_it_when_the_work_is_on_another_branch(self):
        run(self.work, "story", "ABC-1", SUMMARY)
        git(self.work, "switch", "-q", "develop")
        self.make_the_tracked_file_dirty()
        for args in (("--check", "story", "ABC-1", SUMMARY), ("story", "ABC-1", SUMMARY)):
            with self.subTest(args=args):
                result = run(self.work, *args)
                self.assertEqual(result.returncode, 1)
                self.assertIn("Uncommitted", result.stderr)
        self.assertEqual(git(self.work, "branch", "--show-current"), "develop")

    def test_a_tag_with_the_name_of_the_branch_does_not_stand_for_the_branch(self):
        branch = "story/ABC-1/let-customers-download-their-invoices"
        git(self.work, "tag", branch)
        result = run(self.work, "story", "ABC-1", SUMMARY)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(git(self.work, "branch", "--show-current"), branch)

    def test_an_existing_local_branch_is_switched_to_without_new_commits(self):
        branch = run(self.work, "story", "ABC-1", SUMMARY).stdout.strip()
        git(self.work, "switch", "-q", "develop")
        result = run(self.work, "story", "ABC-1", SUMMARY)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), branch)
        self.assertEqual(git(self.work, "branch", "--show-current"), branch)
        self.assertEqual(git(self.work, "log", "--oneline", "develop..HEAD"), "")

    def test_a_branch_that_exists_only_on_origin_is_switched_to_as_a_tracking_branch(self):
        branch = "story/ABC-1/let-customers-download-their-invoices"
        git(self.other.parent, "clone", "-q", str(self.remote), str(self.other))
        git(self.other, "switch", "-q", "-c", branch, "origin/develop")
        git(self.other, "push", "-q", "-u", "origin", branch)
        result = run(self.work, "story", "ABC-1", SUMMARY)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(git(self.work, "branch", "--show-current"), branch)
        self.assertEqual(git(self.work, "rev-parse", "--abbrev-ref", "@{upstream}"), f"origin/{branch}")

    def start_the_work_with_a_commit_of_its_own(self):
        branch = run(self.work, "story", "ABC-1", SUMMARY).stdout.strip()
        (self.work / "c").write_text("c")
        git(self.work, "add", "c")
        git(self.work, "commit", "-qm", "feat(billing): add invoice csv")
        return branch

    def test_ready_passes_on_the_branch_of_the_work_with_a_commit_of_its_own_and_prints_nothing(self):
        self.start_the_work_with_a_commit_of_its_own()
        (self.work / "private.md").write_text("notes")
        result = run(self.work, "--ready", "story", "ABC-1", SUMMARY)
        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)

    def test_ready_refuses_another_branch_and_names_the_one_it_expected(self):
        branch = self.start_the_work_with_a_commit_of_its_own()
        git(self.work, "switch", "-q", "develop")
        result = run(self.work, "--ready", "story", "ABC-1", SUMMARY)
        self.assertEqual((result.returncode, result.stdout), (1, ""))
        self.assertIn("develop", result.stderr)
        self.assertIn(branch, result.stderr)
        self.assertEqual(git(self.work, "branch", "--show-current"), "develop")

    def test_ready_refuses_a_branch_without_commits_of_its_own(self):
        run(self.work, "story", "ABC-1", SUMMARY)
        result = run(self.work, "--ready", "story", "ABC-1", SUMMARY)
        self.assertEqual((result.returncode, result.stdout), (1, ""))
        self.assertIn("no commits", result.stderr.lower())

    def test_ready_refuses_uncommitted_changes_in_files_with_tracking_and_names_them(self):
        self.start_the_work_with_a_commit_of_its_own()
        self.make_the_tracked_file_dirty()
        result = run(self.work, "--ready", "story", "ABC-1", SUMMARY)
        self.assertEqual((result.returncode, result.stdout), (1, ""))
        self.assertIn("Uncommitted", result.stderr)
        self.assertIn(" M a", result.stderr)
        self.assertEqual((self.work / "a").read_text(), "changed")

    def test_ready_refuses_a_branch_behind_origin_develop_and_counts_the_commits(self):
        self.start_the_work_with_a_commit_of_its_own()
        self.push_a_commit_to_develop_from_another_clone()
        result = run(self.work, "--ready", "story", "ABC-1", SUMMARY)
        self.assertEqual((result.returncode, result.stdout), (1, ""))
        self.assertIn("behind", result.stderr.lower())
        self.assertIn("1 commit", result.stderr)

    def test_ready_refuses_without_origin_develop(self):
        self.start_the_work_with_a_commit_of_its_own()
        self.delete_develop_from_the_remote_only()
        result = run(self.work, "--ready", "story", "ABC-1", SUMMARY)
        self.assertEqual(result.returncode, 1)
        self.assertIn("origin/develop", result.stderr)

    def test_ready_and_merge_need_the_work_item_arguments(self):
        for flag in ("--ready", "--merge"):
            for args in ((flag,), (flag, "story", "ABC-1")):
                with self.subTest(args=args):
                    result = run(self.work, *args)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn(flag, result.stderr)

    def push_the_work_with_a_commit_of_its_own(self):
        branch = self.start_the_work_with_a_commit_of_its_own()
        git(self.work, "push", "-q", "-u", "origin", branch)
        return branch

    def test_merge_puts_the_remote_branch_in_develop_with_a_merge_commit_that_names_it(self):
        branch = self.push_the_work_with_a_commit_of_its_own()
        result = run(self.work, "--merge", "story", "ABC-1", SUMMARY)
        self.assertEqual((result.returncode, result.stdout.strip()), (0, branch), result.stderr)
        self.assertEqual(git(self.work, "log", "-1", "--format=%s", "develop"), f"Merge branch '{branch}' into develop")
        self.assertEqual(len(git(self.work, "log", "-1", "--format=%P", "develop").split()), 2)
        self.assertEqual((self.work / "c").read_text(), "c")

    def test_merge_leaves_the_work_on_develop(self):
        self.push_the_work_with_a_commit_of_its_own()
        run(self.work, "--merge", "story", "ABC-1", SUMMARY)
        self.assertEqual(git(self.work, "branch", "--show-current"), "develop")

    def test_merge_brings_in_what_reached_origin_develop_after_the_branch_was_cut(self):
        self.push_the_work_with_a_commit_of_its_own()
        self.push_a_commit_to_develop_from_another_clone()
        result = run(self.work, "--merge", "story", "ABC-1", SUMMARY)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.work / "b").read_text(), "b")
        ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", "origin/develop", "develop"], cwd=self.work)
        self.assertEqual(ancestor.returncode, 0)

    def refused_merge(self, branch, reason):
        """Runs --merge and checks it refused, with the reason named, and touched nothing."""
        develops = (git(self.work, "rev-parse", "develop"), git(self.remote, "rev-parse", "develop"))
        result = run(self.work, "--merge", "story", "ABC-1", SUMMARY)
        self.assertEqual((result.returncode, result.stdout), (1, ""), result.stderr)
        self.assertIn(reason, result.stderr)
        self.assertEqual(git(self.work, "branch", "--show-current"), branch)
        self.assertEqual((git(self.work, "rev-parse", "develop"), git(self.remote, "rev-parse", "develop")), develops)
        return result

    def test_merge_refuses_a_branch_that_is_not_on_origin_and_names_it(self):
        branch = self.start_the_work_with_a_commit_of_its_own()
        self.refused_merge(branch, f"origin/{branch} does not exist")

    def test_merge_refuses_local_commits_that_origin_lacks_and_counts_them(self):
        branch = self.push_the_work_with_a_commit_of_its_own()
        (self.work / "d").write_text("d")
        git(self.work, "add", "d")
        git(self.work, "commit", "-qm", "fix(billing): not pushed")
        self.refused_merge(branch, "1 commit")

    def test_merge_refuses_uncommitted_changes_in_files_with_tracking_even_on_the_work_branch(self):
        branch = self.push_the_work_with_a_commit_of_its_own()
        self.make_the_tracked_file_dirty()
        self.refused_merge(branch, " M a")
        self.assertEqual((self.work / "a").read_text(), "changed")

    def test_merge_refuses_a_develop_that_does_not_fast_forward(self):
        branch = self.push_the_work_with_a_commit_of_its_own()
        git(self.work, "switch", "-q", "develop")
        (self.work / "e").write_text("e")
        git(self.work, "add", "e")
        git(self.work, "commit", "-qm", "feat(local): only here")
        git(self.work, "switch", "-q", branch)
        self.push_a_commit_to_develop_from_another_clone()
        self.refused_merge(branch, "fast-forward")

    def test_merge_with_conflicts_aborts_names_the_files_and_leaves_develop_unmerged(self):
        branch = self.push_the_work_with_a_commit_of_its_own()
        self.push_a_commit_to_develop_from_another_clone("c", "not c")
        result = run(self.work, "--merge", "story", "ABC-1", SUMMARY)
        self.assertEqual((result.returncode, result.stdout), (1, ""), result.stderr)
        self.assertIn("Merge conflicts in: c", result.stderr)
        self.assertEqual(git(self.work, "rev-parse", "develop"), git(self.work, "rev-parse", "origin/develop"))
        self.assertNotEqual(subprocess.run(["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"], cwd=self.work, capture_output=True).returncode, 0)
        self.assertEqual(git(self.work, "status", "--porcelain", "--untracked-files=no"), "")
        self.assertEqual(git(self.work, "branch", "--show-current"), branch)

    def test_merge_that_fails_without_conflicts_leaves_the_person_on_the_work_branch(self):
        branch = self.push_the_work_with_a_commit_of_its_own()
        self.push_a_commit_to_develop_from_another_clone("u", "from develop")
        (self.work / "u").write_text("untracked and in the way")
        develops = (git(self.work, "rev-parse", "develop"), git(self.remote, "rev-parse", "develop"))
        result = run(self.work, "--merge", "story", "ABC-1", SUMMARY)
        self.assertEqual((result.returncode, result.stdout), (1, ""), result.stderr)
        self.assertEqual(git(self.work, "branch", "--show-current"), branch)
        self.assertEqual((git(self.work, "rev-parse", "develop"), git(self.remote, "rev-parse", "develop")), (develops[0], develops[1]))

    def test_merge_neither_pushes_nor_deletes_a_branch(self):
        branch = self.push_the_work_with_a_commit_of_its_own()
        before = git(self.remote, "rev-parse", "develop")
        run(self.work, "--merge", "story", "ABC-1", SUMMARY)
        self.assertEqual(git(self.remote, "rev-parse", "develop"), before)
        self.assertEqual(git(self.work, "branch", "--list", branch), branch)
        self.assertIn(branch, git(self.remote, "branch", "--list"))


if __name__ == "__main__":
    unittest.main()
