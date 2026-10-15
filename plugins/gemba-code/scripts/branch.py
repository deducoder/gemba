#!/usr/bin/env python3
"""Creates the branch of a work item from origin/develop, or switches to it when it exists.

Usage: python3 branch.py <type> <KEY> '<Summary>'
       python3 branch.py --check [<type> <KEY> '<Summary>']   (from the project root)
       python3 branch.py --ready <type> <KEY> '<Summary>'
       python3 branch.py --merge <type> <KEY> '<Summary>'

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
Otherwise it updates develop (`git pull --ff-only`), merges origin/<branch> with `--no-ff`
and the message `Merge branch '<branch>' into develop`, stays on develop and prints the
branch; on conflicts it aborts the merge, goes back to the branch it came from and names
the files. It never pushes: the push is a command of its own, visible to
whoever gates it.
"""

import re
import subprocess
import sys

DEVELOP = "origin/develop"


def slug(summary):
    return re.sub(r"[^a-z0-9]+", "-", summary.lower()).strip("-")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True)


def has_ref(ref):
    return subprocess.run(["git", "rev-parse", "--verify", "-q", ref], capture_output=True).returncode == 0


def check(branch=None):
    """Returns the reason the project cannot take a work item branch, or None."""
    git("fetch", "-q", "--prune", "origin")
    changes = git("status", "--porcelain", "--untracked-files=no").stdout.rstrip()
    if changes and git("branch", "--show-current").stdout.strip() != branch:
        return f"Uncommitted changes in files with tracking:\n{changes}"
    if not has_ref(f"refs/remotes/{DEVELOP}"):
        return f"{DEVELOP} does not exist"
    return None


def ready(branch):
    """Returns the first reason the current branch is not ready to be reviewed, or None."""
    current = git("branch", "--show-current").stdout.strip()
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


class Refused(Exception):
    """A refusal that is not a failed git command: it carries the reason to print."""


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
    if has_ref("refs/heads/develop") and subprocess.run(["git", "merge-base", "--is-ancestor", "develop", DEVELOP]).returncode:
        return f"develop does not fast-forward to {DEVELOP}"
    return None


def merge_into_develop(branch):
    current = git("branch", "--show-current").stdout.strip()
    git("switch", "-q", "develop")
    git("pull", "-q", "--ff-only")
    try:
        git("merge", "-q", "--no-ff", "-m", f"Merge branch '{branch}' into develop", f"origin/{branch}")
    except subprocess.CalledProcessError:
        conflicts = git("diff", "--name-only", "--diff-filter=U").stdout.split()
        if not conflicts:
            raise
        git("merge", "--abort")
        if current:
            git("switch", "-q", current)
        raise Refused(f"Merge conflicts in: {', '.join(conflicts)}") from None
    print(branch)


def guarded(branch, action, verify=check):
    """Runs the action once the project passes the verification for the branch; returns the exit status."""
    try:
        reason = verify(branch)
        if reason:
            print(reason, file=sys.stderr)
            return 1
        action()
    except subprocess.CalledProcessError as error:
        print(error.stderr.strip(), file=sys.stderr)
        return 1
    except Refused as refusal:
        print(refusal, file=sys.stderr)
        return 1
    return 0


def main(argv):
    mode = argv[0] if argv[:1] in (["--check"], ["--ready"], ["--merge"]) else None
    args = argv[1:] if mode else argv
    if mode == "--check" and not args:
        return guarded(None, lambda: None)
    if len(args) != 3:
        print("Usage: python3 branch.py <type> <KEY> '<Summary>'  |  python3 branch.py --check [<type> <KEY> '<Summary>']  |  python3 branch.py --ready <type> <KEY> '<Summary>'  |  python3 branch.py --merge <type> <KEY> '<Summary>'", file=sys.stderr)
        return 2
    kind, key, summary = args
    if not slug(summary):
        print("The Summary has no letters or digits to name the branch with", file=sys.stderr)
        return 2
    branch = f"{kind}/{key}/{slug(summary)}"
    if mode == "--merge":
        return guarded(branch, lambda: merge_into_develop(branch), mergeable)
    if mode == "--ready":
        return guarded(branch, lambda: None, ready)
    return guarded(branch, (lambda: None) if mode else (lambda: switch_to(branch)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
