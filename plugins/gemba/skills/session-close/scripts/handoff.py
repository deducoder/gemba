#!/usr/bin/env python3
"""Checks a handoff against the template and saves it.

Usage: python3 handoff.py <slug> < handoff.md   (from the project root)

The handoff comes on stdin. When it follows the template, the script writes it
to .gemba/sessions/<YYYY-MM-DD-HHMM>-<slug>.md, with the date taken from its
title, creates that folder with a .gitignore that ignores everything in it,
and prints the path.

When something doesn't follow the template, it prints one line per problem to
stderr, writes nothing and exits 1.
"""

import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

SESSIONS = Path(".gemba/sessions")
SECTIONS = ["Done", "Decided", "Open", "Next"]
OPTIONAL_LAST = "State"

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){1,2}$")
TITLE = re.compile(r"^# Session (\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}) [—–-] \S.*$")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")


def sections(text):
    """Returns the ## sections of a handoff as (heading, body) pairs, in order."""
    parts = re.split(r"^## (.+?)\s*$", text, flags=re.MULTILINE)
    return [(parts[i], parts[i + 1].strip()) for i in range(1, len(parts), 2)]


def problems(slug, text):
    """Returns what doesn't follow the template; empty when the handoff does."""
    found = []
    if not SLUG.match(slug):
        found.append(f"slug {slug!r}: use 2 or 3 lowercase words joined by hyphens")

    first_line = text.lstrip().splitlines()[0] if text.strip() else ""
    if not TITLE.match(first_line):
        found.append("title: the first line must be '# Session <YYYY-MM-DD HH:MM> — <focus>'")

    parsed = sections(text)
    headings = [heading for heading, _ in parsed]
    if headings not in (SECTIONS, SECTIONS + [OPTIONAL_LAST]):
        found.append(
            f"sections: expected {', '.join(SECTIONS)} and optionally {OPTIONAL_LAST}, "
            f"in that order; found {', '.join(headings) or 'none'}"
        )
        return found

    body = dict(parsed)
    if not body["Done"]:
        found.append("Done: name at least one outcome")
    for line in body["Decided"].splitlines():
        if LIST_ITEM.match(line) and "why:" not in line.lower():
            found.append(f"Decided: give this decision its why: {line.strip()}")
    if not body["Next"]:
        found.append("Next: write one concrete action")
    elif any(LIST_ITEM.match(line) for line in body["Next"].splitlines()) or "\n\n" in body["Next"]:
        found.append("Next: write a single action, not a list or several paragraphs")
    if OPTIONAL_LAST in body and not body[OPTIONAL_LAST]:
        found.append(f"{OPTIONAL_LAST}: leave the section out when there is nothing to name")
    return found


def target(slug, text):
    """Returns the handoff's path, with the date from its title."""
    year, month, day, hour, minute = TITLE.match(text.lstrip().splitlines()[0]).groups()
    return SESSIONS / f"{year}-{month}-{day}-{hour}{minute}-{slug}.md"


def main(argv):
    if len(argv) != 2:
        print("usage: handoff.py <slug> < handoff.md", file=sys.stderr)
        return 1
    slug, text = argv[1], sys.stdin.read()

    found = problems(slug, text)
    path = None if found else target(slug, text)
    if path is not None and path.exists():
        found.append(f"{path.as_posix()} already exists: choose another slug")
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1

    try:
        SESSIONS.mkdir(parents=True, exist_ok=True)
        (SESSIONS / ".gitignore").write_text("*\n", encoding="utf-8")
        path.write_text(text.strip() + "\n", encoding="utf-8")
    except OSError as error:
        print(f"handoff.py: {error}", file=sys.stderr)
        return 1

    print(path.as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
