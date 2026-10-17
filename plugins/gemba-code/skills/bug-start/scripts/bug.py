#!/usr/bin/env python3
"""Checks a bug draft against the template and converts it to what Jira takes:
the Summary, the description and the Evidence comment as ADF documents.

Usage: python3 bug.py --site <site> < draft.md

The draft comes on stdin: the Summary on its first line, the paragraph of the
failure, then the sections of the template in order:

- `### Root cause`: the one sentence that names the cause.
- `### Neighboring inputs`: a table headed `| Input | Current behavior |`.
- `### Done when`: one `* ` bullet per criterion.
- `### Evidence`: `#### Reproduction`, one fenced block with the literal command
  and its output, then `#### Cause trail`, one `* ran:` or `* read:` bullet per line.
- `### Out of scope`: one `* ` bullet per line.

Lines are written and converted as the plugin's scripts/draft.py says.

When the draft follows the template, prints {"summary": ..., "description":
<ADF>, "comment": <ADF>} as JSON: the description holds the failure, Root cause,
Neighboring inputs, Done when and Out of scope, and the comment holds the
Evidence. Otherwise prints one line per problem to stderr, prints nothing to
stdout and exits 1.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from draft import (  # noqa: E402
    CODE, FENCE, bullets, check_criteria, check_scope, check_sections, check_summary, check_trail, check_unmarked,
    criterion, doc, excluded, filled, heading, inline, items, section, split,
)

SECTIONS = ["Root cause", "Neighboring inputs", "Done when", "Evidence", "Out of scope"]
EVIDENCE = [("Evidence", "Reproduction"), ("Evidence", "Cause trail")]
HEADER = ["Input", "Current behavior"]
TABLE = f"| {' | '.join(HEADER)} |"
SEPARATOR = re.compile(r"^\|(\s*:?-+:?\s*\|)+$")


def cells(row):
    """Splits a table row on the pipes outside `code`."""
    masked = CODE.sub(lambda match: "x" * len(match.group(0)), row)
    bounds = [i for i, char in enumerate(masked) if char == "|"]
    return [row[start + 1:end].strip() for start, end in zip(bounds, bounds[1:])]


def check_table(lines, found):
    """Returns the rows of Neighboring inputs, without the header, split into cells."""
    rows = [line.strip() for line in filled(lines)]
    if not rows or not all(row.startswith("|") and row.endswith("|") for row in rows):
        found.append(f"Neighboring inputs: write a table headed {TABLE}")
        return []
    if cells(rows[0]) != HEADER or len(rows) < 2 or not SEPARATOR.match(rows[1]):
        found.append(f"Neighboring inputs: head the table with {TABLE} and its separator row")
        return []
    body = [cells(row) for row in rows[2:]]
    if not body:
        found.append("Neighboring inputs: add one row per neighboring input")
    for row in body:
        if len(row) != len(HEADER) or not all(row):
            found.append(f"Neighboring inputs: give each row an input and its current behavior: | {' | '.join(row)} |")
    return body


def check_reproduction(lines, found):
    """Returns the literal text of the Reproduction block, or None."""
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    opener = FENCE.match(lines[0]) if lines else None
    if not opener or len(lines) < 2 or lines[-1].strip() != opener.group(1):
        found.append("Evidence: write the Reproduction as one fenced block with the literal command and its output")
        return None
    body = "\n".join(lines[1:-1])
    if not body.strip():
        found.append("Evidence: the Reproduction block needs the command and its output")
        return None
    return body


def problems(summary, intro, sections, subsections, repeated):
    """Returns what doesn't follow the template, and the parsed content when it does."""
    found = []
    check_summary(summary, found)
    paragraph = filled(intro)
    if len(paragraph) != 1:
        found.append("failure: write one paragraph that says what fails, when or where, and who it affects")
    for name, text in (("Summary", summary), ("failure", " ".join(paragraph))):
        check_unmarked(name, text, found)
    if not check_sections(sections, SECTIONS, repeated, found):
        return found, None
    if list(subsections) != EVIDENCE or filled(sections["Evidence"]):
        subsections_named = " and ".join(f"#### {name}" for _, name in EVIDENCE)
        found.append(f"Evidence: write the subsections {subsections_named}, in that order, and nothing else")
        return found, None

    cause = filled(sections["Root cause"])
    if len(cause) != 1 or cause[0].startswith(("* ", "ran:", "read:")):
        found.append("Root cause: write the one sentence that names the cause; its ran: and read: lines go in Evidence")
    rows = check_table(sections["Neighboring inputs"], found)
    criteria = items("Done when", sections["Done when"], found)
    check_criteria(criteria, found)
    reproduction = check_reproduction(subsections[EVIDENCE[0]], found)
    trail = items("Evidence Cause trail", subsections[EVIDENCE[1]], found)
    check_trail("Evidence Cause trail", trail, found)
    scope = items("Out of scope", sections["Out of scope"], found)
    check_scope(scope, found)
    for name, lines in (("Root cause", cause), ("Neighboring inputs", [cell for row in rows for cell in row]),
                        ("Evidence", trail), ("Out of scope", scope)):
        for line in lines:
            check_unmarked(name, line, found)
    if found:
        return found, None
    return found, {"summary": summary, "intro": paragraph[0].strip(), "cause": cause[0].strip(), "rows": rows,
                   "criteria": criteria, "reproduction": reproduction, "trail": trail, "scope": scope}


def table(rows):
    def row(values, kind):
        return {"type": "tableRow", "content": [
            {"type": kind, "attrs": {}, "content": [{"type": "paragraph", "content": inline(value)}]} for value in values
        ]}
    return {"type": "table", "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
            "content": [row(HEADER, "tableHeader")] + [row(values, "tableCell") for values in rows]}


def description(content, site):
    """Returns the description: the failure, Root cause, Neighboring inputs, Done when and Out of scope."""
    return doc([
        {"type": "paragraph", "content": inline(content["intro"])},
        heading("Root cause"),
        {"type": "paragraph", "content": inline(content["cause"])},
        heading("Neighboring inputs"),
        table(content["rows"]),
        *section("Done when", [criterion(line) for line in content["criteria"]]),
        *section("Out of scope", [excluded(line, site) for line in content["scope"]]),
    ])


def comment(content):
    """Returns the Evidence comment: the Reproduction block and the Cause trail."""
    return doc([
        heading("Evidence"),
        heading("Reproduction", 4),
        {"type": "codeBlock", "content": [{"type": "text", "text": content["reproduction"]}]},
        heading("Cause trail", 4),
        bullets([inline(line) for line in content["trail"]]),
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--site", required=True, help="the Atlassian site, e.g. example.atlassian.net")
    site = parser.parse_args().site
    found, content = problems(*split(sys.stdin.read()))
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    bug = {"summary": content["summary"], "description": description(content, site), "comment": comment(content)}
    print(json.dumps(bug, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
