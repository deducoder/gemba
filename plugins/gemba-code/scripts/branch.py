#!/usr/bin/env python3
"""Creates the branch of a work item from origin/develop, or switches to it when it exists.

Usage: python3 branch.py <type> <KEY> '<Summary>'
       python3 branch.py --check                    (from the project root)

The branch is `<type>/<KEY>/<summary>`, with the Summary in lowercase kebab-case.
It starts from origin/develop after fetching, so a develop that is behind does not
matter; when the branch already exists, locally or on origin, it switches to it.
Prints the branch name. Both forms first check the project and refuse, without
touching anything, when a file with tracking has uncommitted changes or origin/develop
does not exist; untracked files do not count. `--check` only does that check. It
never pushes: the push is a command of its own, visible to whoever gates it.
"""

import re
import subprocess
import sys

DEVELOP = "origin/develop"


def slug(summary):
    return re.sub(r"[^a-z0-9]+", "-", summary.lower()).strip("-")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True)


def check():
    """Returns the reason the project cannot take a work item branch, or None."""
    git("fetch", "-q", "--prune", "origin")
    changes = git("status", "--porcelain", "--untracked-files=no").stdout.strip()
    if changes:
        return f"Uncommitted changes in files with tracking:\n{changes}"
    if subprocess.run(["git", "rev-parse", "--verify", "-q", DEVELOP], capture_output=True).returncode:
        return f"{DEVELOP} does not exist"
    return None


def exists(branch):
    return any(
        subprocess.run(["git", "rev-parse", "--verify", "-q", ref], capture_output=True).returncode == 0
        for ref in (branch, f"origin/{branch}")
    )


def main(argv):
    checking = argv == ["--check"]
    if not checking and len(argv) != 3:
        print("Usage: python3 branch.py <type> <KEY> '<Summary>'  |  python3 branch.py --check", file=sys.stderr)
        return 2
    if not checking:
        kind, key, summary = argv
        if not slug(summary):
            print("The Summary has no letters or digits to name the branch with", file=sys.stderr)
            return 2
        branch = f"{kind}/{key}/{slug(summary)}"
    try:
        reason = check()
        if reason:
            print(reason, file=sys.stderr)
            return 1
        if not checking:
            if exists(branch):
                git("switch", "-q", branch)
            else:
                git("switch", "-q", "-c", branch, "--no-track", DEVELOP)
            print(branch)
    except subprocess.CalledProcessError as error:
        print(error.stderr.strip(), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
