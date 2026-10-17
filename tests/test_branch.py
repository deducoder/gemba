"""Checks the branch script of the work item skills: the branch it creates, where
it starts from and what it prints."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/scripts/branch.py"
SUMMARY = "Let customers download their invoices"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.com",
       "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.com"}


def git(cwd, *args):
    result = subprocess.run(["git", *args], cwd=cwd, env=ENV, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def run(cwd, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, env=ENV, capture_output=True, text=True)


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

    def merged_as(self, branch, state):
        """Runs --merge and checks it succeeded, printing the branch and the state on its first two lines."""
        result = run(self.work, "--merge", "story", "ABC-1", SUMMARY)
        self.assertEqual((result.returncode, result.stdout.splitlines()[:2]), (0, [branch, state]), result.stderr)
        return result.stdout.splitlines()

    def test_merge_puts_the_remote_branch_in_develop_with_a_merge_commit_that_names_it(self):
        branch = self.push_the_work_with_a_commit_of_its_own()
        self.merged_as(branch, "merged")
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

    def merge_without_pushing(self):
        branch = self.push_the_work_with_a_commit_of_its_own()
        self.merged_as(branch, "merged")
        return branch

    def test_merge_resumes_a_merge_not_pushed_without_merging_again(self):
        branch = self.merge_without_pushing()
        merged = git(self.work, "rev-parse", "develop")
        git(self.work, "switch", "-q", branch)
        self.merged_as(branch, "merged, not pushed")
        self.assertEqual(git(self.work, "rev-parse", "develop"), merged)
        self.assertEqual(git(self.work, "branch", "--show-current"), "develop")

    def test_merge_resumes_a_close_already_pushed_without_merging(self):
        branch = self.merge_without_pushing()
        git(self.work, "push", "-q", "origin", "develop")
        pushed = git(self.remote, "rev-parse", "develop")
        git(self.work, "switch", "-q", branch)
        self.assertEqual(self.merged_as(branch, "already pushed"), [branch, "already pushed"])
        self.assertEqual((git(self.work, "rev-parse", "develop"), git(self.remote, "rev-parse", "develop")), (pushed, pushed))
        self.assertEqual(git(self.work, "branch", "--show-current"), "develop")

    def test_merge_lists_after_its_second_line_the_commits_the_push_of_develop_sends(self):
        branch = self.push_the_work_with_a_commit_of_its_own()
        sent = self.merged_as(branch, "merged")[2:]
        self.assertEqual(sent, git(self.work, "log", "--oneline", "origin/develop..develop").splitlines())
        self.assertEqual(len(sent), 2)
        git(self.work, "switch", "-q", branch)
        self.assertEqual(self.merged_as(branch, "merged, not pushed")[2:], sent)

    def test_merge_refuses_a_merge_not_pushed_once_origin_develop_moved_and_names_its_commits(self):
        self.merge_without_pushing()
        self.push_a_commit_to_develop_from_another_clone()
        self.refused_merge("develop", "feat(billing): add invoice export")

    def test_merge_refuses_a_develop_whose_commit_of_its_own_is_not_the_merge_of_the_branch(self):
        branch = self.push_the_work_with_a_commit_of_its_own()
        git(self.work, "switch", "-q", "develop")
        git(self.work, "merge", "-q", "--ff-only", f"origin/{branch}")
        (self.work / "e").write_text("e")
        git(self.work, "add", "e")
        git(self.work, "commit", "-qm", "feat(local): not reviewed")
        self.refused_merge("develop", "fast-forward")

    def test_merge_still_refuses_a_develop_with_commits_besides_the_merge(self):
        self.merge_without_pushing()
        (self.work / "e").write_text("e")
        git(self.work, "add", "e")
        git(self.work, "commit", "-qm", "feat(local): only here")
        self.refused_merge("develop", "fast-forward")

    def test_worktree_opens_the_branch_from_origin_develop_in_a_folder_named_by_the_key(self):
        self.push_a_commit_to_develop_from_another_clone()
        result = run(self.work, "--worktree", "spike", "ABC-5", "Check a partial unique index")
        self.assertEqual(result.returncode, 0, result.stderr)
        branch, path = result.stdout.split("\n")[:2]
        self.assertEqual(branch, "spike/ABC-5/check-a-partial-unique-index")
        self.assertEqual(path, ".claude/worktrees/ABC-5")
        worktree = self.work / path
        self.assertEqual(git(worktree, "branch", "--show-current"), branch)
        self.assertEqual(git(worktree, "rev-parse", "HEAD"), git(self.other, "rev-parse", "HEAD"))

    def test_worktree_leaves_the_working_tree_where_it_was(self):
        run(self.work, "--worktree", "spike", "ABC-5", "Check a partial unique index")
        self.assertEqual(git(self.work, "branch", "--show-current"), "develop")
        self.assertEqual(git(self.work, "status", "--porcelain", "--untracked-files=no"), "")

    def test_worktree_neither_pushes_nor_sets_an_upstream(self):
        result = run(self.work, "--worktree", "spike", "ABC-5", "Check a partial unique index")
        branch = result.stdout.split("\n")[0]
        self.assertEqual(git(self.work, "ls-remote", "--heads", "origin", "spike/*"), "")
        upstream = subprocess.run(["git", "rev-parse", "--abbrev-ref", "@{upstream}"], cwd=self.work / ".claude/worktrees/ABC-5", capture_output=True, text=True)
        self.assertNotEqual(upstream.returncode, 0)
        self.assertEqual(subprocess.run(["git", "config", f"branch.{branch}.remote"], cwd=self.work, capture_output=True, text=True).stdout, "")

    def test_worktree_refuses_uncommitted_changes_in_files_with_tracking(self):
        (self.work / "a").write_text("changed")
        result = run(self.work, "--worktree", "spike", "ABC-5", "Check a partial unique index")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("Uncommitted changes", result.stderr)
        self.assertFalse((self.work / ".claude/worktrees/ABC-5").exists())
        self.assertEqual(git(self.work, "branch", "--list", "spike/*"), "")

    def open_worktree_with_a_commit(self):
        run(self.work, "--worktree", "spike", "ABC-5", "Check a partial unique index")
        folder = self.work / ".claude/worktrees/ABC-5"
        (folder / "probe.txt").write_text("probe")
        git(folder, "add", "probe.txt")
        git(folder, "commit", "-qm", "test(probe): experimental commit")
        return folder, git(folder, "rev-parse", "HEAD")

    def test_worktree_resumes_one_whose_branch_and_folder_exist(self):
        folder, head = self.open_worktree_with_a_commit()
        result = run(self.work, "--worktree", "spike", "ABC-5", "Check a partial unique index")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split("\n")[:2], ["spike/ABC-5/check-a-partial-unique-index", ".claude/worktrees/ABC-5"])
        self.assertEqual(git(folder, "rev-parse", "HEAD"), head)
        self.assertEqual(git(self.work, "worktree", "list").count("worktrees/ABC-5"), 1)

    def test_worktree_recreates_the_folder_from_the_branch_when_it_is_gone(self):
        folder, head = self.open_worktree_with_a_commit()
        shutil.rmtree(folder)
        result = run(self.work, "--worktree", "spike", "ABC-5", "Check a partial unique index")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split("\n")[:2], ["spike/ABC-5/check-a-partial-unique-index", ".claude/worktrees/ABC-5"])
        self.assertEqual(git(folder, "branch", "--show-current"), "spike/ABC-5/check-a-partial-unique-index")
        self.assertEqual(git(folder, "rev-parse", "HEAD"), head)
        upstream = subprocess.run(["git", "rev-parse", "--abbrev-ref", "@{upstream}"], cwd=folder, capture_output=True, text=True)
        self.assertNotEqual(upstream.returncode, 0)

    def test_worktree_opens_the_folder_for_a_branch_that_already_exists(self):
        git(self.work, "branch", "spike/ABC-5/check-a-partial-unique-index", "origin/develop")
        result = run(self.work, "--worktree", "spike", "ABC-5", "Check a partial unique index")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(git(self.work / ".claude/worktrees/ABC-5", "branch", "--show-current"), "spike/ABC-5/check-a-partial-unique-index")

    def test_worktree_opens_a_branch_that_only_exists_on_origin_with_its_commits(self):
        git(self.work, "switch", "-q", "-c", "spike/ABC-5/check-a-partial-unique-index", "origin/develop")
        (self.work / "probe.txt").write_text("probe")
        git(self.work, "add", "probe.txt")
        git(self.work, "commit", "-qm", "test(probe): experimental commit")
        head = git(self.work, "rev-parse", "HEAD")
        git(self.work, "push", "-q", "origin", "spike/ABC-5/check-a-partial-unique-index")
        git(self.work, "switch", "-q", "develop")
        git(self.work, "branch", "-D", "spike/ABC-5/check-a-partial-unique-index")
        result = run(self.work, "--worktree", "spike", "ABC-5", "Check a partial unique index")
        self.assertEqual(result.returncode, 0, result.stderr)
        folder = self.work / ".claude/worktrees/ABC-5"
        self.assertEqual(git(folder, "rev-parse", "HEAD"), head)
        upstream = subprocess.run(["git", "rev-parse", "--abbrev-ref", "@{upstream}"], cwd=folder, capture_output=True, text=True)
        self.assertNotEqual(upstream.returncode, 0)

    def test_worktree_refuses_a_folder_that_is_not_a_worktree_of_the_branch(self):
        (self.work / ".claude/worktrees/ABC-5").mkdir(parents=True)
        result = run(self.work, "--worktree", "spike", "ABC-5", "Check a partial unique index")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn(".claude/worktrees/ABC-5", result.stderr)
        self.assertEqual(git(self.work, "branch", "--list", "spike/*"), "")

    def test_discard_deletes_the_folder_and_the_branch_and_prints_what_it_discards(self):
        folder, head = self.open_worktree_with_a_commit()
        develop = git(self.work, "rev-parse", "develop")
        result = run(self.work, "--discard", "spike", "ABC-5", "Check a partial unique index")
        self.assertEqual(result.returncode, 0, result.stderr)
        branch, remote, *commits = result.stdout.splitlines()
        self.assertEqual(branch, "spike/ABC-5/check-a-partial-unique-index")
        self.assertEqual(remote, "local only")
        self.assertEqual(commits, [f"{head[:7]} test(probe): experimental commit"])
        self.assertFalse(folder.exists())
        self.assertEqual(git(self.work, "branch", "--list", "spike/*"), "")
        self.assertEqual(git(self.work, "branch", "--show-current"), "develop")
        self.assertEqual(git(self.work, "rev-parse", "develop"), develop)
        self.assertEqual(git(self.work, "ls-remote", "--heads", "origin", "spike/*"), "")

    def test_discard_says_the_branch_is_on_origin_and_leaves_that_branch_alone(self):
        folder, head = self.open_worktree_with_a_commit()
        git(folder, "push", "-q", "origin", "HEAD")
        result = run(self.work, "--discard", "spike", "ABC-5", "Check a partial unique index")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines()[1], "on origin")
        self.assertEqual(git(self.work, "branch", "--list", "spike/*"), "")
        self.assertIn(head, git(self.work, "ls-remote", "--heads", "origin", "spike/*"))

    def test_discard_dry_run_prints_the_same_and_deletes_nothing(self):
        folder, head = self.open_worktree_with_a_commit()
        real = run(self.work, "--discard", "--dry-run", "spike", "ABC-5", "Check a partial unique index")
        self.assertEqual(real.returncode, 0, real.stderr)
        self.assertEqual(real.stdout.splitlines(), ["spike/ABC-5/check-a-partial-unique-index", "local only", f"{head[:7]} test(probe): experimental commit"])
        self.assertTrue(folder.is_dir())
        self.assertEqual(git(self.work, "branch", "--list", "spike/*").split()[-1], "spike/ABC-5/check-a-partial-unique-index")


    def test_discard_deletes_the_branch_when_its_folder_is_already_gone(self):
        folder, head = self.open_worktree_with_a_commit()
        shutil.rmtree(folder)
        result = run(self.work, "--discard", "spike", "ABC-5", "Check a partial unique index")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(git(self.work, "branch", "--list", "spike/*"), "")
        self.assertNotIn("worktrees/ABC-5", git(self.work, "worktree", "list"))


if __name__ == "__main__":
    unittest.main()
