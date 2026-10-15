#!/usr/bin/env python3
"""Creates the branch of a work item from origin/develop, or switches to it when it exists.

Usage: python3 branch.py <type> <KEY> '<Summary>'
       python3 branch.py --check [<type> <KEY> '<Summary>']   (from the project root)

The branch is `<type>/<KEY>/<summary>`, with the Summary in lowercase kebab-case.
It starts from origin/develop after fetching, so a develop that is behind does not
matter; when the branch already exists, locally or on origin, it switches to it.
Prints the branch name. Both forms first refuse, touching nothing, when origin/develop
does not exist or when a file with tracking has uncommitted changes (untracked files do
not count), unless the work is already on that branch: changes made on it are the
same work and may continue. `--check` only does the check, with the branch of the work
item when given. It never pushes: the push is a command of its own, visible to
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


def switch_to(branch):
    if has_ref(f"refs/heads/{branch}") or has_ref(f"refs/remotes/origin/{branch}"):
        git("switch", "-q", branch)
    else:
        git("switch", "-q", "-c", branch, "--no-track", DEVELOP)
    print(branch)


def guarded(branch, action):
    """Runs the action once the project passes the check for the branch; returns the exit status."""
    try:
        reason = check(branch)
        if reason:
            print(reason, file=sys.stderr)
            return 1
        action()
    except subprocess.CalledProcessError as error:
        print(error.stderr.strip(), file=sys.stderr)
        return 1
    return 0


def main(argv):
    checking = argv[:1] == ["--check"]
    args = argv[1:] if checking else argv
    if checking and not args:
        return guarded(None, lambda: None)
    if len(args) != 3:
        print("Usage: python3 branch.py <type> <KEY> '<Summary>'  |  python3 branch.py --check [<type> <KEY> '<Summary>']", file=sys.stderr)
        return 2
    kind, key, summary = args
    if not slug(summary):
        print("The Summary has no letters or digits to name the branch with", file=sys.stderr)
        return 2
    branch = f"{kind}/{key}/{slug(summary)}"
    return guarded(branch, (lambda: None) if checking else (lambda: switch_to(branch)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
