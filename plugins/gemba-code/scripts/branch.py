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
It prints the branch and, on a second line, what it found and did, staying on develop:
`already pushed` when origin/develop already holds origin/<branch> (it only updates
develop); `merged, not pushed` when develop's only commit of its own is that merge (it
merges nothing again, and refuses naming the commits when origin/develop has any develop
lacks); otherwise `merged`: it updates develop (`git pull --ff-only`) and merges
origin/<branch> with `--no-ff` and the message `Merge branch '<branch>' into develop`.
On conflicts it aborts the merge, goes back to the branch it came from and names
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
    if has_ref("refs/heads/develop") and not is_ancestor("develop", DEVELOP) and not merged_locally(branch):
        return f"develop does not fast-forward to {DEVELOP}"
    return None


def merged_locally(branch):
    """Whether develop holds origin/<branch> and its only commit of its own is the merge at its tip."""
    if not has_ref("refs/heads/develop") or not is_ancestor(f"origin/{branch}", "develop"):
        return False
    own = git("rev-list", "develop", f"^{DEVELOP}", f"^origin/{branch}").stdout.split()
    return own == [git("rev-parse", "develop").stdout.strip()]


def merge_into_develop(branch):
    if is_ancestor(f"origin/{branch}", DEVELOP):
        git("switch", "-q", "develop")
        git("pull", "-q", "--ff-only")
        print(branch, "already pushed", sep="\n")
        return None
    if merged_locally(branch):
        missing = git("log", "--oneline", f"develop..{DEVELOP}").stdout.rstrip()
        if missing:
            return f"develop has the merge of {branch} unpushed and {DEVELOP} has commits it lacks:\n{missing}"
        git("switch", "-q", "develop")
        print(branch, "merged, not pushed", sep="\n")
        return None
    current = current_branch()
    try:
        git("switch", "-q", "develop")
        git("pull", "-q", "--ff-only")
        git("merge", "-q", "--no-ff", "-m", f"Merge branch '{branch}' into develop", f"origin/{branch}")
    except subprocess.CalledProcessError:
        conflicts = git("diff", "--name-only", "--diff-filter=U").stdout.split()
        if conflicts:
            git("merge", "--abort")
        if current:
            subprocess.run(["git", "switch", "-q", current], capture_output=True)
        if conflicts:
            return f"Merge conflicts in: {', '.join(conflicts)}"
        raise
    print(branch, "merged", sep="\n")


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
