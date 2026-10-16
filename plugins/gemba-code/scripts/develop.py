#!/usr/bin/env python3
"""Opens origin/develop in a worktree, runs commands there to reproduce a failure,
and closes it. The branch, the uncommitted changes and the untracked files of the
project stay as they were, because nothing runs in its working tree.

Usage: python3 develop.py open    (from the project)
       python3 develop.py run '<command>'
       python3 develop.py close

`open` fetches origin first, as branch.py does, so a local develop that is behind
does not matter, and prints the path of the worktree: in the temporary directory,
one per repository and Claude Code session (`CLAUDE_CODE_SESSION_ID`), so two
sessions never share it, and outside the project so that nothing the project holds
(dependencies, settings) is found from it. It replaces one a stopped run of the
same session left behind. When the fetch fails or origin/develop does not exist it prints the reason
to stderr and exits 1.
`run` runs the command with the shell inside the open worktree and passes on its
output and exit status; without an open worktree it exits 1.
`close` removes the worktree with everything a run left in it, even without write
permission, and succeeds when there is none; when it cannot, it says why and exits 1.
"""

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

from branch import DEVELOP, git, has_ref, succeeds  # noqa: E402


def worktree():
    common = git("rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    key = common + os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    return Path(tempfile.gettempdir()) / f"gemba-develop-{hashlib.sha1(key.encode()).hexdigest()[:12]}"


def writable(function, path, _):
    """Lets rmtree remove what a run left without write permission."""
    os.chmod(os.path.dirname(path), 0o700)
    function(path)


def close(path):
    """Removes the worktree; returns the reason when it cannot, or None."""
    if path.exists() and not succeeds("worktree", "remove", "--force", str(path)):
        shutil.rmtree(path, onerror=writable)
    git("worktree", "prune")
    return f"develop.py: could not remove {path}" if path.exists() else None


def main(argv):
    if argv not in (["open"], ["close"]) and not (len(argv) == 2 and argv[0] == "run"):
        print(__doc__, file=sys.stderr)
        return 2
    path = worktree()
    if argv[0] == "run":
        if not path.is_dir():
            print("develop.py: no worktree is open; run `develop.py open` first", file=sys.stderr)
            return 1
        return subprocess.run(argv[1], shell=True, cwd=path).returncode
    reason = close(path)
    if reason:
        print(reason, file=sys.stderr)
        return 1
    if argv == ["close"]:
        return 0
    if not succeeds("fetch", "-q", "--prune", "origin"):
        print("develop.py: git fetch origin failed, so develop could be behind; fix the remote and run it again", file=sys.stderr)
        return 1
    if not has_ref(f"refs/remotes/{DEVELOP}"):
        print(f"develop.py: {DEVELOP} does not exist, so there is no develop to reproduce the failure on", file=sys.stderr)
        return 1
    git("worktree", "add", "--detach", str(path), DEVELOP)
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
