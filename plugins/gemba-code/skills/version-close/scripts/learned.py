#!/usr/bin/env python3
"""Builds the edit that writes what a released product version taught on its published
page: a level two heading `Learned` at the end of the page, after `Work items`, with one
bullet per lesson.

Usage: python3 learned.py < input.json

The input is {"page": <the published HTML of the version page>, "draft": "<the lessons the
person accepted, one `* ` bullet per line>"}. The rest of the page stays as it is, nodes and
local IDs included.

Prints {"edits": [<the single appendNodeToEnd edit>]} as JSON. When the version is not
released yet, the page already has `Learned` or the draft is not a list of lessons, prints
each problem to stderr, nothing to stdout and exits 1.
"""

import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

sys.path.insert(0, str(Path(__file__).resolve().parent))

from draft import FENCE, HEADING, bullets, heading, inline, items  # noqa: E402
from released import stamp_state  # noqa: E402

TITLE = "Learned"
HAS_LEARNED = re.compile(r"<h2[^>]*>Learned</h2>")


def problems(page, draft):
    """Returns what keeps the lessons from being written, and the lessons when nothing does."""
    found = []
    if stamp_state(page) != "Released":
        found.append("page: the version is not Released; release it first")
    elif HAS_LEARNED.search(page):
        found.append(f"page: the version already has {TITLE}")
    lines = draft.splitlines()
    if any(FENCE.match(line) for line in lines):
        return found + [f"{TITLE}: write no code blocks"], []
    headings = [line.strip() for line in lines if HEADING.match(line)]
    if headings:
        return found + [f"{TITLE}: write only the bullets, without headings: {', '.join(headings)}"], []
    return found, items(TITLE, lines, found)


def main():
    try:
        data = json.loads(sys.stdin.read())
        page, draft = data["page"], data["draft"]
        if not isinstance(page, str) or not isinstance(draft, str):
            raise TypeError
    except (ValueError, KeyError, TypeError):
        print('input: write {"page": "<html>", "draft": "* lesson"} as JSON', file=sys.stderr)
        return 1
    found, lessons = problems(page, draft)
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    value = heading(TITLE, 2) + bullets([inline(lesson) for lesson in lessons])
    print(json.dumps({"edits": [{"name": "appendNodeToEnd", "value": value}]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
