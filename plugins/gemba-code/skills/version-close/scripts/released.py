#!/usr/bin/env python3
"""Marks the published page of a product version Released: its stamp, the first paragraph
`[Planned|In progress] · <release date>`, becomes `[Released] · <the day of the release>`.

Usage: python3 released.py < input.json

The input is {"page": <the published ADF of the version page>, "day": "YYYY-MM-DD"}. The
rest of the page stays as it is, nodes and local IDs included.

Prints the ADF document as JSON. When the page has no stamp of a version in progress, or
the day is not a date, prints the problem to stderr, nothing to stdout and exits 1.
"""

import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from draft import CURRENT, is_day, stamp  # noqa: E402


def problem(page, day):
    """Returns what keeps the page from being released, or None."""
    if not is_day(day):
        return f"day: {day} is not a date YYYY-MM-DD"
    first = (page.get("content") or [{}])[0]
    lozenge = (first.get("content") or [{}])[0] if first.get("type") == "paragraph" else {}
    state = lozenge.get("attrs", {}).get("text") if lozenge.get("type") == "status" else None
    if state == "Released":
        return "page: the version is already Released"
    if state not in CURRENT:
        return f"page: the first paragraph is not the stamp '[{' | '.join(CURRENT)}] · YYYY-MM-DD' of the version"
    return None


def main():
    try:
        data = json.loads(sys.stdin.read())
        page, day = data["page"], data["day"]
    except (ValueError, KeyError, TypeError):
        print('input: write {"page": <ADF>, "day": "YYYY-MM-DD"} as JSON', file=sys.stderr)
        return 1
    found = problem(page, day)
    if found:
        print(found, file=sys.stderr)
        return 1
    page["content"][0]["content"] = stamp("Released", day)
    print(json.dumps(page, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
