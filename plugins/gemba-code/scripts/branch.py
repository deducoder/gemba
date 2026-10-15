#!/usr/bin/env python3
"""Creates the branch of a work item from origin/develop and switches to it.

Usage: python3 branch.py <type> <KEY> '<Summary>'   (from the project root)

The branch is `<type>/<KEY>/<summary>`, with the Summary in lowercase kebab-case.
It starts from origin/develop after fetching, so a develop that is behind does not
matter. Prints the branch name. It neither pushes nor sets an upstream: the push
is a command of its own, visible to whoever gates it.
"""

import re
import subprocess
import sys

DEVELOP = "origin/develop"


def slug(summary):
    return re.sub(r"[^a-z0-9]+", "-", summary.lower()).strip("-")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True)


def main(argv):
    if len(argv) != 3:
        print("Usage: python3 branch.py <type> <KEY> '<Summary>'", file=sys.stderr)
        return 2
    kind, key, summary = argv
    branch = f"{kind}/{key}/{slug(summary)}"
    try:
        git("fetch", "-q", "origin")
        git("switch", "-q", "-c", branch, "--no-track", DEVELOP)
    except subprocess.CalledProcessError as error:
        print(error.stderr.strip() or f"git {error.cmd[1]} failed", file=sys.stderr)
        return 1
    print(branch)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
