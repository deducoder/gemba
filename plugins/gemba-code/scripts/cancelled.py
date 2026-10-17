#!/usr/bin/env python3
"""Checks a cancellation comment against its template and converts it to ADF for Jira.

Usage: python3 cancelled.py --site <site> < comment.md

The comment comes on stdin: the heading `### Cancelled`, then one `* ` bullet per
line, `Reason:`, `Found:` and `Replaced by:`, in that order. `Found:` starts with
`ran:` or `read:`, and `Replaced by:` holds only the key of the work item that
replaces it, which becomes a link to the issue on the site, or the text saying none does.
`code` becomes a code mark.

When the comment follows the template, prints its ADF document as JSON. Otherwise
prints one line per problem to stderr, prints nothing to stdout and exits 1.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from draft import KEY, bullets, check_trail, doc, filled, heading, inline, items  # noqa: E402

HEADING = "### Cancelled"
LABELS = ["Reason", "Found", "Replaced by"]
MENTION = re.compile(r"\b[A-Za-z][A-Za-z0-9_]+-\d+\b")


def problems(text):
    """Returns what doesn't follow the template, and the value of each line when it does."""
    found = []
    lines = filled(text.strip("\n").splitlines())
    if not lines or lines[0].strip() != HEADING:
        found.append(f"heading: start the comment with {HEADING}")
        return found, None
    pairs = [(label.strip(), value.strip()) for label, _, value in
             (line.partition(":") for line in items("Cancelled", lines[1:], found))]
    values = dict(pairs)
    if [label for label, _ in pairs] != LABELS:
        found.append(f"lines: write {', '.join(LABELS)}, in that order, once each")
        return found, None
    for label in LABELS:
        if not values[label]:
            found.append(f"{label}: write what goes after the colon")
    if values["Found"]:
        check_trail("Found", [values["Found"]], found)
    replaced = values["Replaced by"]
    if MENTION.search(replaced) and not KEY.match(replaced):
        found.append(f"Replaced by: write only the key of the work item that replaces it: {replaced}")
    return found, values


def comment(values, site):
    """Returns the comment as an ADF document, with the key of `Replaced by` as a link to the issue."""
    replaced = values["Replaced by"]
    last = inline("Replaced by: ") + [{"type": "inlineCard", "attrs": {"url": f"https://{site}/browse/{replaced}"}}] \
        if KEY.match(replaced) else inline(f"Replaced by: {replaced}")
    return doc([heading("Cancelled"), bullets([
        inline(f"Reason: {values['Reason']}"), inline(f"Found: {values['Found']}"), last,
    ])])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--site", required=True, help="the Atlassian site, e.g. example.atlassian.net")
    site = parser.parse_args().site
    found, values = problems(sys.stdin.read())
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    print(json.dumps(comment(values, site), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
