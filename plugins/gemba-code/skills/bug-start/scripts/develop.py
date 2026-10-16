#!/usr/bin/env python3
"""Opens the local develop branch in a worktree, to reproduce a failure there, and
closes it. The branch, the uncommitted changes and the untracked files of the
project stay as they were, because nothing runs in its working tree.

Usage: python3 develop.py open    (from the project)
       python3 develop.py close

`open` prints the path of the worktree, inside the repository's git directory so
that `git status` never shows it, and replaces one a stopped run left behind.
Without a local develop branch it prints the reason to stderr and exits 1.
`close` removes the worktree with everything a run left in it, and succeeds when
there is none.
"""

import subprocess
import sys
from pathlib import Path

NAME = "gemba-develop"


def git(*args, check=True):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=check)


def worktree():
    common = Path(git("rev-parse", "--git-common-dir").stdout.strip())
    return (common if common.is_absolute() else Path.cwd() / common).resolve() / NAME


def close(path):
    if path.exists():
        git("worktree", "remove", "--force", str(path), check=False)
    git("worktree", "prune")


def main(argv):
    if argv not in (["open"], ["close"]):
        print(__doc__, file=sys.stderr)
        return 2
    path = worktree()
    if argv == ["close"]:
        close(path)
        return 0
    if git("rev-parse", "--verify", "--quiet", "refs/heads/develop", check=False).returncode != 0:
        print("develop.py: there is no local develop branch to reproduce the failure on", file=sys.stderr)
        return 1
    close(path)
    git("worktree", "add", "--detach", str(path), "develop")
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
