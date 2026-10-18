#!/usr/bin/env python3
"""Releases a product version in git: merges develop into main and tags the merge.

Usage: python3 release.py v<X.Y.Z>    (from the project)

It fetches origin, brings main and develop up to date with origin (fast-forward only),
merges develop into main with `--no-ff` and the message `Merge branch 'develop' into main`,
creates the annotated tag on that merge and brings develop level with main, ending on
develop. It prints the tag and, on a second line, `released`, then the commits the push of
main sends, one per line. When the tag is already on main and develop is level with it or
behind it, an earlier run released it: it only brings develop level with main and prints
`already released` instead. When the tag or that last step fails, it undoes the merge and the
tag and goes back where it was.

It refuses, touching nothing, with the first reason that fails: a tag that is not
v<X.Y.Z>, uncommitted changes in files with tracking (untracked files do not count),
origin/main or origin/develop missing, local commits of main or develop that origin lacks,
the tag already on another commit, or a develop with nothing main lacks. On conflicts it
aborts the merge, goes back where it was (a branch or a detached HEAD) and names the files;
main and develop stay brought up to date with origin. It never pushes:
each push is a command of its own, visible to whoever gates it.
"""

import re
import subprocess
import sys

TAG = re.compile(r"^v\d+\.\d+\.\d+$")
MESSAGE = "Merge branch 'develop' into main"


# The same git helpers as scripts/branch.py, kept here: a skill script that imports a plugin
# script makes evals/changed.py run every eval on each change to that script.
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


def rev(ref):
    return git("rev-parse", ref).stdout.strip()


def dirty():
    return git("status", "--porcelain", "--untracked-files=no").stdout.strip()


def already_released(tag):
    """True when the tag is on main and develop is level with it or behind it: an earlier
    run tagged the merge."""
    return (has_ref(f"refs/tags/{tag}") and has_ref("main") and has_ref("develop")
            and rev(f"{tag}^{{commit}}") == rev("main") and is_ancestor("develop", "main"))


def refusal(tag):
    """Returns why the release cannot run, or None."""
    git("fetch", "-q", "origin")
    for branch in ("main", "develop"):
        if not has_ref(f"origin/{branch}"):
            return f"origin/{branch} does not exist."
        if has_ref(branch) and not is_ancestor(branch, f"origin/{branch}"):
            return f"{branch} has commits origin/{branch} lacks: push or drop them first."
    if has_ref(f"refs/tags/{tag}"):
        return f"The tag {tag} already exists on another commit."
    if is_ancestor("origin/develop", "origin/main"):
        return "develop has nothing main lacks: there is nothing to release."
    return None


def update(branch):
    if has_ref(branch):
        git("switch", "-q", branch)
        git("merge", "-q", "--ff-only", f"origin/{branch}")
    else:
        git("switch", "-q", "-c", branch, f"origin/{branch}")


def level_develop():
    git("switch", "-q", "develop")
    git("merge", "-q", "--ff-only", "main")


def release(tag):
    branch, head = current_branch(), rev("HEAD")

    def go_back():
        succeeds("switch", "-q", *((branch,) if branch else ("--detach", head)))

    update("develop")
    update("main")
    before = rev("main")
    try:
        git("merge", "-q", "--no-ff", "-m", MESSAGE, "develop")
    except subprocess.CalledProcessError:
        conflicts = git("diff", "--name-only", "--diff-filter=U").stdout.split()
        if conflicts:
            git("merge", "--abort")
        go_back()
        if conflicts:
            return f"Merge conflicts in: {', '.join(conflicts)}"
        raise
    try:
        git("tag", "-a", tag, "-m", tag)
        level_develop()
    except subprocess.CalledProcessError:
        succeeds("tag", "-d", tag)
        succeeds("switch", "-q", "main")
        succeeds("reset", "-q", "--hard", before)
        go_back()
        raise
    return None


def main(argv):
    if len(argv) != 1:
        print(__doc__.splitlines()[2], file=sys.stderr)
        return 1
    tag = argv[0]
    if not TAG.match(tag):
        print(f"The tag {tag} is not a version: write it as v<X.Y.Z>.", file=sys.stderr)
        return 1
    try:
        if dirty():
            print("There are uncommitted changes in files with tracking: commit or discard them first.", file=sys.stderr)
            return 1
        if already_released(tag):
            state = "already released"
            level_develop()
        else:
            reason = refusal(tag) or release(tag)
            if reason:
                print(reason, file=sys.stderr)
                return 1
            state = "released"
        pending = git("log", "--format=%h %s", "origin/main..main").stdout.strip()
    except subprocess.CalledProcessError as error:
        print(error.stderr.strip(), file=sys.stderr)
        return 1
    print("\n".join(filter(None, (tag, state, pending))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
