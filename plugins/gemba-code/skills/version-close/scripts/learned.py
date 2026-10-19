#!/usr/bin/env python3
"""Writes what a released product version taught on its published page: a level two heading
`Learned` at the end of the page, after `Work items`, with one bullet per lesson.

Usage: python3 learned.py < input.json

The input is {"page": <the published ADF of the version page>, "draft": "<the lessons the
person accepted, one `* ` bullet per line>"}. The rest of the page stays as it is, nodes and
local IDs included.

Prints the ADF document as JSON. When the version is not released yet, the page already has
`Learned` or the draft is not a list of lessons, prints each problem to stderr, nothing to
stdout and exits 1.
"""

import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

sys.path.insert(0, str(Path(__file__).resolve().parent))

from draft import FENCE, HEADING, items  # noqa: E402
from legacy_adf import adf_bullets, adf_heading, adf_inline  # noqa: E402
from released import stamp_state  # noqa: E402

TITLE = "Learned"


def has_learned(page):
    return any(node.get("type") == "heading" and node.get("attrs", {}).get("level") == 2
               and "".join(part.get("text", "") for part in node.get("content", [])) == TITLE
               for node in page.get("content", []))


def problems(page, draft):
    """Returns what keeps the lessons from being written, and the lessons when nothing does."""
    found = []
    if stamp_state(page) != "Released":
        found.append("page: the version is not Released; release it first")
    elif has_learned(page):
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
        if not isinstance(page, dict) or not isinstance(draft, str):
            raise TypeError
        if not isinstance(page.get("content", []), list) or not all(isinstance(node, dict) for node in page.get("content", [])):
            raise TypeError
    except (ValueError, KeyError, TypeError):
        print('input: write {"page": <ADF>, "draft": "* lesson"} as JSON', file=sys.stderr)
        return 1
    found, lessons = problems(page, draft)
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    page["content"] = page.get("content", []) + [adf_heading(TITLE, 2), adf_bullets([adf_inline(lesson) for lesson in lessons])]
    print(json.dumps(page, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
