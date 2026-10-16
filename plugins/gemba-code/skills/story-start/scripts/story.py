#!/usr/bin/env python3
"""Checks a story draft against the template and converts it to what Jira
takes: the Summary and the description as an ADF document.

Usage: python3 story.py --site <site> < draft.md

The draft comes on stdin: the Summary on its first line, the opening sentence,
then the `### Done when`, `### Evidence` and `### Out of scope` sections, with
one `* ` bullet per line, and at most 8 Done when criteria. `code` becomes a
code mark, a Done when criterion wrapped in `==` turns orange, and a work item
key after `→` in Out of scope becomes a link to the issue on the site.

When the draft follows the template, prints {"summary": ..., "description":
<ADF>, "comment": <ADF>} as JSON: the description holds the opening sentence,
Done when and Out of scope, and the comment holds the Evidence. Otherwise
prints one line per problem to stderr, prints nothing to stdout and exits 1.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from draft import (  # noqa: E402
    check_criteria, check_scope, check_summary, check_unmarked, criterion, doc, excluded, inline, prose, section,
)

SECTIONS = ["Done when", "Evidence", "Out of scope"]
MAX_CRITERIA = 8


def parse(text):
    """Returns the Summary, the opening sentence, the bullets of each section, the
    sections that have lines that are not bullets and the sections written twice."""
    lines = text.strip().splitlines()
    summary = lines[0].strip() if lines else ""
    intro, sections, loose, repeated, current = [], {}, set(), set(), None
    for line in lines[1:]:
        heading = re.match(r"^### (.+?)\s*$", line)
        if heading:
            current = heading.group(1)
            if current in sections:
                repeated.add(current)
            sections.setdefault(current, [])
        elif current is None:
            if line.strip():
                intro.append(line.strip())
        elif line.startswith("* "):
            sections[current].append(line[2:].strip())
        elif line.strip():
            loose.add(current)
    return summary, intro, sections, loose, repeated


def problems(summary, intro, sections, loose, repeated):
    """Returns what doesn't follow the template; empty when the draft does."""
    found = []
    check_summary(summary, found)
    if len(intro) != 1 or not intro[0].endswith("."):
        found.append("opening sentence: write one sentence that says who wants what and why")
    for name, text in (("Summary", summary), ("opening sentence", " ".join(intro))):
        check_unmarked(name, text, found)
    if list(sections) != SECTIONS:
        found.append(f"sections: expected {', '.join(SECTIONS)}, in that order; found {', '.join(sections) or 'none'}")
        return found
    for name, bullets in sections.items():
        if name in repeated:
            found.append(f"{name}: write the section once")
        if name in loose:
            found.append(f"{name}: write each item as a '* ' bullet on one line")
        if not bullets:
            found.append(f"{name}: write at least one item")
        if "" in bullets:
            found.append(f"{name}: remove the empty bullet")
    criteria, evidence, scope = (sections[name] for name in SECTIONS)
    if len(criteria) > MAX_CRITERIA:
        found.append(f"Done when: {len(criteria)} criteria; split the story into stories of {MAX_CRITERIA} criteria at most")
    if len(evidence) != len(criteria):
        found.append(f"Evidence: give one line per Done when criterion, in order ({len(criteria)} criteria, {len(evidence)} lines)")
    for line in evidence:
        if not line.startswith(("ran:", "read:")):
            found.append(f"Evidence: start with 'ran:' or 'read:': {line}")
    check_criteria(criteria, found)
    for name in ("Evidence", "Out of scope"):
        for line in sections[name]:
            if "==" in prose(line):
                found.append(f"{name}: only Done when criteria are wrapped in ==: {line}")
    check_scope(scope, found)
    return found


def description(intro, sections, site):
    """Returns the description as an ADF document: the opening sentence, Done when and Out of scope."""
    content = [{"type": "paragraph", "content": inline(intro[0])}]
    content += section("Done when", [criterion(line) for line in sections["Done when"]])
    content += section("Out of scope", [excluded(line, site) for line in sections["Out of scope"]])
    return doc(content)


def comment(sections):
    """Returns the Evidence as an ADF document for a comment on the story."""
    return doc(section("Evidence", [inline(line) for line in sections["Evidence"]]))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--site", required=True, help="the Atlassian site, e.g. example.atlassian.net")
    site = parser.parse_args().site
    summary, intro, sections, loose, repeated = parse(sys.stdin.read())
    found = problems(summary, intro, sections, loose, repeated)
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    story = {"summary": summary, "description": description(intro, sections, site), "comment": comment(sections)}
    print(json.dumps(story, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
