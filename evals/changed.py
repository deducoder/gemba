#!/usr/bin/env python3
"""Runs the evals of the skills a change touches, with one run per case, instead of the
whole set.

Usage: python3 evals/changed.py [--dry-run]    (from the repository)

The change is every file that differs from where the branch left origin/develop,
committed or not, plus the untracked ones. Each file picks evals by its path:
- what every case shares (evals/mocks/, tests/fixtures/atlassian-stub/, the context/,
  hooks/ and references/ of a plugin, and a plugin script no SKILL.md names) picks them all;
- a plugin script picks the skills whose SKILL.md names it;
- plugins/<plugin>/skills/<skill>/ picks that skill;
- evals/<skill>/ picks that skill and, through the scripts that load the file from
  other folders of evals/, theirs.
Each picked skill with evals is one `claude plugin eval` with `--case '<skill>-*'`; when
everything is picked, it is a single one without `--case`. Each command is printed and run
from the repository; `--dry-run` only prints them. With nothing picked it says so. The exit
status is the worst of the runs.
"""

import re
import shlex
import subprocess
import sys
from pathlib import Path

SHARED = ("evals/mocks/", "tests/fixtures/atlassian-stub/")
SHARED_IN_PLUGIN = ("context", "hooks", "references")
LOADED = re.compile(r"\.\./([a-z-]+)/([\w-]+\.sh)")


def evaluate(*case):
    """The `claude plugin eval` command of the README with one run per case, for `case`."""
    return ["claude", "plugin", "eval", ".", "--scaffold", "--runs", "1", *case,
            "--allow-tools", "Bash(python3:*)", "Bash(git:*)", "Edit", "Write"]


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def changed_files():
    base = git("merge-base", "origin/develop", "HEAD").strip()
    return set(git("diff", "--name-only", base).split()) | set(git("ls-files", "--others", "--exclude-standard").split())


def loaders(root):
    """Maps each file of evals/ that another one loads through `../<folder>/<name>.sh` to the
    files that load it."""
    loaded_by = {}
    for folder in (root / "evals").iterdir():
        if folder.is_dir() and folder.name != "results":
            for path in [*folder.glob("**/*.sh"), *folder.glob("**/*.yaml")]:
                for loaded, name in LOADED.findall(path.read_text(encoding="utf-8")):
                    loaded_by.setdefault(f"evals/{loaded}/{name}", set()).add(path.relative_to(root).as_posix())
    return loaded_by


def picked_by(path, root, loaded_by):
    """Returns the skills a changed file picks, or None when it picks them all."""
    parts = path.split("/")
    if path.startswith(SHARED):
        return None
    if parts[0] == "plugins" and len(parts) > 3:
        if parts[2] in SHARED_IN_PLUGIN:
            return None
        if parts[2] == "scripts":
            naming = {skill.parent.name for skill in root.glob("plugins/*/skills/*/SKILL.md")
                      if f"scripts/{parts[3]}" in skill.read_text(encoding="utf-8")}
            return naming or None
        if parts[2] == "skills" and len(parts) > 4:
            return {parts[3]}
    if parts[0] == "evals" and len(parts) > 2:
        seen, pending = set(), [path]
        while pending:
            current = pending.pop()
            if current not in seen:
                seen.add(current)
                pending += loaded_by.get(current, ())
        return {file.split("/")[1] for file in seen}
    return set()


def commands(root):
    loaded_by = loaders(root)
    skills = set()
    for path in sorted(changed_files()):
        picked = picked_by(path, root, loaded_by)
        if picked is None:
            return [evaluate()]
        skills |= picked
    runs = []
    for skill in sorted(skills):
        folder = root / "evals" / skill
        if any(folder.glob("*/case.yaml")) or any(folder.glob("*/prompt.md")):
            runs.append(evaluate("--case", f"{skill}-*"))
        elif (folder / "case.yaml").exists() or (folder / "prompt.md").exists():
            runs.append(evaluate("--case", skill))
    return runs


def main():
    dry_run = "--dry-run" in sys.argv[1:]
    root = Path(git("rev-parse", "--show-toplevel").strip())
    runs = commands(root)
    if not runs:
        print("No evals cover the changed files.")
        return 0
    status = 0
    for command in runs:
        print(shlex.join(command), flush=True)
        if not dry_run:
            status = max(status, subprocess.run(command, cwd=root).returncode)
    return status


if __name__ == "__main__":
    sys.exit(main())
