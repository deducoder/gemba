#!/usr/bin/env python3
"""Creates the branch of a work item from origin/develop, or switches to it when it exists.

Usage: python3 branch.py <type> <KEY> '<Summary>'
       python3 branch.py --check                    (from the project root)

The branch is `<type>/<KEY>/<summary>`, with the Summary in lowercase kebab-case.
It starts from origin/develop after fetching, so a develop that is behind does not
matter; when the branch already exists, locally or on origin, it switches to it.
Prints the branch name. Both forms first refuse, touching nothing, when a file with
tracking has uncommitted changes or origin/develop does not exist (untracked files do
not count); `--check` only does that. It never pushes: the push is a command of its
own, visible to whoever gates it.
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


def check():
    """Returns the reason the project cannot take a work item branch, or None."""
    git("fetch", "-q", "--prune", "origin")
    changes = git("status", "--porcelain", "--untracked-files=no").stdout.rstrip()
    if changes:
        return f"Uncommitted changes in files with tracking:\n{changes}"
    if not has_ref(DEVELOP):
        return f"{DEVELOP} does not exist"
    return None


def switch_to(branch):
    if has_ref(branch) or has_ref(f"origin/{branch}"):
        git("switch", "-q", branch)
    else:
        git("switch", "-q", "-c", branch, "--no-track", DEVELOP)
    print(branch)


def guarded(action):
    """Runs the action once the project passes the check; returns the exit status."""
    try:
        reason = check()
        if reason:
            print(reason, file=sys.stderr)
            return 1
        action()
    except subprocess.CalledProcessError as error:
        print(error.stderr.strip(), file=sys.stderr)
        return 1
    return 0


def main(argv):
    if argv == ["--check"]:
        return guarded(lambda: None)
    if len(argv) != 3:
        print("Usage: python3 branch.py <type> <KEY> '<Summary>'  |  python3 branch.py --check", file=sys.stderr)
        return 2
    kind, key, summary = argv
    if not slug(summary):
        print("The Summary has no letters or digits to name the branch with", file=sys.stderr)
        return 2
    return guarded(lambda: switch_to(f"{kind}/{key}/{slug(summary)}"))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
