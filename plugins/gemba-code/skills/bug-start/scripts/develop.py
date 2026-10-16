#!/usr/bin/env python3
"""Opens origin/develop in a worktree, to reproduce a failure there, and closes it.
The branch, the uncommitted changes and the untracked files of the project stay as
they were, because nothing runs in its working tree.

Usage: python3 develop.py open    (from the project)
       python3 develop.py close

`open` fetches origin first, as branch.py does, so a local develop that is behind
does not matter, and prints the path of the worktree: inside the repository's git
directory, so that `git status` never shows it. It replaces one a stopped run left
behind. Without origin/develop it prints the reason to stderr and exits 1.
`close` removes the worktree with everything a run left in it, and succeeds when
there is none.
"""

import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from branch import DEVELOP, git, has_ref  # noqa: E402

NAME = "gemba-develop"


def worktree():
    return Path(git("rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()) / NAME


def close(path):
    if path.exists():
        subprocess.run(["git", "worktree", "remove", "--force", str(path)], capture_output=True)
    git("worktree", "prune")


def main(argv):
    if argv not in (["open"], ["close"]):
        print(__doc__, file=sys.stderr)
        return 2
    path = worktree()
    close(path)
    if argv == ["close"]:
        return 0
    subprocess.run(["git", "fetch", "-q", "--prune", "origin"], capture_output=True)
    if not has_ref(f"refs/remotes/{DEVELOP}"):
        print(f"develop.py: {DEVELOP} does not exist, so there is no develop to reproduce the failure on", file=sys.stderr)
        return 1
    git("worktree", "add", "--detach", str(path), DEVELOP)
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
