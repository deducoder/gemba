#!/usr/bin/env python3
"""Creates the branch of a work item from origin/develop, or switches to it when it exists.

Usage: python3 branch.py <type> <KEY> '<Summary>'
       python3 branch.py --check [<type> <KEY> '<Summary>']   (from the project root)
       python3 branch.py --ready <type> <KEY> '<Summary>'
       python3 branch.py --merge <type> <KEY> '<Summary>'
       python3 branch.py --worktree <type> <KEY> '<Summary>'
       python3 branch.py --discard [--dry-run] <type> <KEY> '<Summary>'

The branch is `<type>/<KEY>/<summary>`, with the Summary in lowercase kebab-case.
It starts from origin/develop after fetching, so a develop that is behind does not
matter; when the branch already exists, locally or on origin, it switches to it.
Prints the branch name. Both forms first refuse, touching nothing, when origin/develop
does not exist or when a file with tracking has uncommitted changes (untracked files do
not count), unless the work is already on that branch: changes made on it are the
same work and may continue. `--check` only does the check, with the branch of the work
item when given. `--ready` asks whether the work is ready to be reviewed and refuses,
touching nothing, with the first reason that fails: it is not on the branch of the work
item, it has uncommitted changes in files with tracking, origin/develop does not exist,
it has no commits of its own or it is behind origin/develop. `--merge` brings the
work done into develop. It refuses, touching nothing, with the first reason that fails:
uncommitted changes in files with tracking (also on the work branch), origin/<branch> does
not exist, local commits origin/<branch> lacks, or a develop that does not fast-forward.
It prints the branch and, on a second line, what it found and did, staying on develop:
`already pushed` when origin/develop already holds origin/<branch> (it only updates
develop); `merged, not pushed` when develop's only commit of its own is that merge (it
merges nothing again, and refuses naming the commits when origin/develop has any develop
lacks); otherwise `merged`: it updates develop (`git pull --ff-only`) and merges
origin/<branch> with `--no-ff` and the message `Merge branch '<branch>' into develop`.
After `merged` and `merged, not pushed` it lists the commits the push of develop sends,
one per line. On conflicts it aborts the merge, goes back to the branch it came from and names
the files. `--worktree` creates the branch without tracking in `.claude/worktrees/<KEY>` and
prints the branch and, on a second line, that folder; the working tree stays where it was. When
the branch already exists it resumes it: it opens the folder again from the branch, or from
origin/<branch> when only that exists, if the folder is gone, and changes nothing if it is there;
it refuses a folder that is not a worktree of the branch. It
refuses, touching nothing, with uncommitted changes in files with tracking or without
origin/develop. It never pushes: the push is a command of its own, visible to
whoever gates it. `--discard` deletes the folder `.claude/worktrees/<KEY>` and the local branch of a work
item that is never merged. It prints the branch, on a second line `on origin` or `local only` (whether
origin has the branch) and then the commits of the branch that origin/develop lacks, one per line, which
the deletion discards; with `--dry-run` it only prints. The folder goes first, with `git worktree remove`
and no `--force`, so git refuses a folder with changes or files without tracking and nothing is deleted.
It never merges and never pushes, and it leaves the branch of origin alone.
"""

import os
import re
import subprocess
import sys

DEVELOP = "origin/develop"


def slug(summary):
    return re.sub(r"[^a-z0-9]+", "-", summary.lower()).strip("-")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True)


def succeeds(*args):
    return subprocess.run(["git", *args], capture_output=True).returncode == 0


def has_ref(ref):
    return succeeds("rev-parse", "--verify", "-q", ref)


def is_ancestor(ancestor, descendant):
    return succeeds("merge-base", "--is-ancestor", ancestor, descendant)


def current_branch():
    return git("branch", "--show-current").stdout.strip()


def check(branch=None):
    """Returns the reason the project cannot take a work item branch, or None.

    Changes to files with tracking are refused unless the work is already on `branch`, so
    `check(None)` refuses them on any branch."""
    git("fetch", "-q", "--prune", "origin")
    changes = git("status", "--porcelain", "--untracked-files=no").stdout.rstrip()
    if changes and current_branch() != branch:
        return f"Uncommitted changes in files with tracking:\n{changes}"
    if not has_ref(f"refs/remotes/{DEVELOP}"):
        return f"{DEVELOP} does not exist"
    return None


def ready(branch):
    """Returns the first reason the current branch is not ready to be reviewed, or None."""
    current = current_branch()
    if current != branch:
        return f"On {current or 'a detached HEAD'}, expected {branch}"
    reason = check(None)
    if reason:
        return reason
    behind, ahead = map(int, git("rev-list", "--left-right", "--count", f"{DEVELOP}...HEAD").stdout.split())
    if not ahead:
        return f"{branch} has no commits of its own on top of {DEVELOP}"
    if behind:
        return f"{branch} is behind {DEVELOP} by {behind} commit(s)"
    return None


def switch_to(branch):
    if has_ref(f"refs/heads/{branch}") or has_ref(f"refs/remotes/origin/{branch}"):
        git("switch", "-q", branch)
    else:
        git("switch", "-q", "-c", branch, "--no-track", DEVELOP)
    print(branch)


def open_worktree(branch, key):
    """Opens the branch in `.claude/worktrees/<KEY>`, leaving the working tree where it is, and
    prints the branch and the folder; returns the reason it refuses, or None. A folder that is
    there must hold the branch and is left as it is. A branch without its folder is opened again
    with its commits, from the local branch or from origin/<branch>; a branch that does not exist
    starts from origin/develop. None of them tracks a branch."""
    folder = f".claude/worktrees/{key}"
    if os.path.isdir(folder):
        if git("-C", folder, "branch", "--show-current").stdout.strip() != branch:
            return f"{folder} exists and is not a worktree of {branch}"
    elif has_ref(f"refs/heads/{branch}"):
        git("worktree", "prune")
        git("worktree", "add", "-q", folder, branch)
    else:
        start = f"origin/{branch}" if has_ref(f"refs/remotes/origin/{branch}") else DEVELOP
        git("worktree", "add", "-q", "--no-track", "-b", branch, folder, start)
    print(branch)
    print(folder)


def discard(branch, key, dry_run):
    """Prints the branch, whether origin has it and the commits origin/develop lacks, and deletes the
    folder `.claude/worktrees/<KEY>` and then the local branch unless it is a dry run; returns the reason
    it refuses, or None. A part that is already gone is skipped, and a folder deleted by hand is pruned so the branch can go."""
    folder = f".claude/worktrees/{key}"
    local = has_ref(f"refs/heads/{branch}")
    print(branch)
    print("on origin" if succeeds("ls-remote", "--exit-code", "--heads", "origin", branch) else "local only")
    if local:
        print(commits(f"{DEVELOP}..{branch}"))
    if not dry_run:
        if os.path.isdir(folder):
            git("worktree", "remove", folder)
        git("worktree", "prune")
        if local:
            git("branch", "-D", branch)


def mergeable(branch):
    """Returns the first reason the branch cannot be merged into develop yet, or None."""
    reason = check(None)
    if reason:
        return reason
    if not has_ref(f"refs/remotes/origin/{branch}"):
        return f"origin/{branch} does not exist"
    if has_ref(f"refs/heads/{branch}"):
        ahead = int(git("rev-list", "--count", f"origin/{branch}..{branch}").stdout)
        if ahead:
            return f"{branch} has {ahead} commit(s) that origin/{branch} does not have"
    if resumed(branch) == "merged, not pushed":
        missing = commits(f"develop..{DEVELOP}")
        if missing:
            return f"develop has the merge of {branch} unpushed and {DEVELOP} has commits it lacks:\n{missing}"
    elif has_ref("refs/heads/develop") and not is_ancestor("develop", DEVELOP):
        return f"develop does not fast-forward to {DEVELOP}"
    return None


def resumed(branch):
    """What an earlier close left of origin/<branch>: `already pushed` when origin/develop holds it,
    `merged, not pushed` when develop's only commit of its own is its merge, else None."""
    if is_ancestor(f"origin/{branch}", DEVELOP):
        return "already pushed"
    if has_ref("refs/heads/develop") and has_ref("develop^2"):
        own = git("rev-list", "develop", f"^{DEVELOP}", f"^origin/{branch}").stdout.split()
        if len(own) == 1 and git("rev-parse", "develop^2").stdout == git("rev-parse", f"origin/{branch}").stdout:
            return "merged, not pushed"
    return None


def commits(revisions):
    """The commits of a range, one `<hash> <subject>` per line."""
    return git("log", "--oneline", revisions).stdout.rstrip()


def merge_into_develop(branch):
    state = resumed(branch)
    current = current_branch()
    try:
        git("switch", "-q", "develop")
        if state != "merged, not pushed":
            git("pull", "-q", "--ff-only")
        if not state:
            git("merge", "-q", "--no-ff", "-m", f"Merge branch '{branch}' into develop", f"origin/{branch}")
            state = "merged"
    except subprocess.CalledProcessError:
        conflicts = git("diff", "--name-only", "--diff-filter=U").stdout.split()
        if conflicts:
            git("merge", "--abort")
        if current:
            subprocess.run(["git", "switch", "-q", current], capture_output=True)
        if conflicts:
            return f"Merge conflicts in: {', '.join(conflicts)}"
        raise
    print("\n".join(filter(None, (branch, state, commits(f"{DEVELOP}..develop")))))


def guarded(branch, action, verify=check):
    """Runs the action once the project passes the verification for the branch; returns the exit status.

    The verification and the action refuse by returning the reason; a failed git command refuses with its error.
    """
    try:
        reason = verify(branch) or action()
        if reason:
            print(reason, file=sys.stderr)
            return 1
    except subprocess.CalledProcessError as error:
        print(error.stderr.strip(), file=sys.stderr)
        return 1
    return 0


def main(argv):
    mode = argv[0] if argv[:1] in (["--check"], ["--ready"], ["--merge"], ["--worktree"], ["--discard"]) else None
    args = argv[1:] if mode else argv
    dry_run = mode == "--discard" and args[:1] == ["--dry-run"]
    if dry_run:
        args = args[1:]
    if mode == "--check" and not args:
        return guarded(None, lambda: None)
    if len(args) != 3:
        print("Usage: python3 branch.py <type> <KEY> '<Summary>'  |  python3 branch.py --check [<type> <KEY> '<Summary>']  |  python3 branch.py --ready <type> <KEY> '<Summary>'  |  python3 branch.py --merge <type> <KEY> '<Summary>'  |  python3 branch.py --worktree <type> <KEY> '<Summary>'  |  python3 branch.py --discard [--dry-run] <type> <KEY> '<Summary>'", file=sys.stderr)
        return 2
    kind, key, summary = args
    if not slug(summary):
        print("The Summary has no letters or digits to name the branch with", file=sys.stderr)
        return 2
    branch = f"{kind}/{key}/{slug(summary)}"
    if mode == "--merge":
        return guarded(branch, lambda: merge_into_develop(branch), mergeable)
    if mode == "--discard":
        return guarded(branch, lambda: discard(branch, key, dry_run), lambda _: None)
    if mode == "--worktree":
        return guarded(branch, lambda: open_worktree(branch, key), lambda _: check(None))
    if mode == "--ready":
        return guarded(branch, lambda: None, ready)
    return guarded(branch, (lambda: None) if mode else (lambda: switch_to(branch)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
