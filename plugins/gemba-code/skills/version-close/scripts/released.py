#!/usr/bin/env python3
"""Builds the edit that marks the published page of a product version Released: its stamp,
the first paragraph `[Planned|In progress] · <release date>`, becomes `[Released] · <the
day of the release>`.

Usage: python3 released.py < input.json

The input is {"page": <the published HTML of the version page>, "day": "YYYY-MM-DD"}. The
rest of the page stays as it is, nodes and local IDs included, also what follows the date in
that paragraph.

Prints {"edits": [<the single replaceNode edit>]} as JSON. When the page has no stamp of a
version in progress, or the day is not a date, prints the problem to stderr, nothing to
stdout and exits 1.
"""

import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from draft import CURRENT, is_day, stamp  # noqa: E402
from published import top_level_nodes  # noqa: E402

STAMP = re.compile(r'^<span[^>]*data-type="status"[^>]*>([^<]*)</span> · <time[^>]*>[^<]*</time>(.*)$', re.DOTALL)


def first_paragraph(page):
    """Returns the localId and the stamp match of the page's first paragraph, or (None, None)
    when the page has no paragraph there or it is not a stamp."""
    nodes = top_level_nodes(page)
    if not nodes or nodes[0][2] != "p":
        return None, None
    local, raw, _ = nodes[0]
    inner = re.sub(r"^<p[^>]*>", "", re.sub(r"</p>$", "", raw))
    return local, STAMP.match(inner)


def stamp_state(page):
    """Returns the state of the lozenge that opens the first paragraph of a version page, or None."""
    _, match = first_paragraph(page)
    return match.group(1) if match else None


def problem(page, day):
    """Returns what keeps the page from being released, or None."""
    if not is_day(day):
        return f"day: {day} is not a date YYYY-MM-DD"
    state = stamp_state(page)
    if state == "Released":
        return "page: the version is already Released"
    if state not in CURRENT:
        return f"page: the first paragraph is not the stamp '[{' | '.join(CURRENT)}] · YYYY-MM-DD' of the version"
    return None


def main():
    try:
        data = json.loads(sys.stdin.read())
        page, day = data["page"], data["day"]
        if not isinstance(page, str):
            raise TypeError
    except (ValueError, KeyError, TypeError):
        print('input: write {"page": "<html>", "day": "YYYY-MM-DD"} as JSON', file=sys.stderr)
        return 1
    found = problem(page, day)
    if found:
        print(found, file=sys.stderr)
        return 1
    local, match = first_paragraph(page)
    print(json.dumps({"edits": [{"name": "replaceNode", "localId": local,
                                  "value": f"<p>{stamp('Released', day)}{match.group(2)}</p>"}]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
