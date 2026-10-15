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
Done when and Out of scope, and the comment holds the Evidence. Otherwise prints one line per problem to stderr, prints nothing
to stdout and exits 1.
"""

import argparse
import json
import re
import sys

SECTIONS = ["Done when", "Evidence", "Out of scope"]
MAX_CRITERIA = 8
ORANGE = {"type": "textColor", "attrs": {"color": "#ff991f"}}
KEY = re.compile(r"^[A-Z][A-Z0-9]+-\d+$")
CODE = re.compile(r"`([^`]+)`")


def parse(text):
    """Returns the Summary, the opening sentence and the bullets of each section."""
    lines = text.strip().splitlines()
    summary = lines[0].strip() if lines else ""
    intro, sections, current = [], {}, None
    for line in lines[1:]:
        heading = re.match(r"^### (.+?)\s*$", line)
        if heading:
            current = heading.group(1)
            sections[current] = []
        elif current is None:
            if line.strip():
                intro.append(line.strip())
        elif line.startswith("* "):
            sections[current].append(line[2:].strip())
        elif line.strip():
            sections[current].append(None)
    return summary, intro, sections


def problems(summary, intro, sections):
    """Returns what doesn't follow the template; empty when the draft does."""
    found = []
    if not summary or len(summary) > 64:
        found.append("Summary: write it on the first line, 64 characters at most")
    elif summary.endswith(".") or not summary[0].isupper():
        found.append("Summary: sentence case, with no final period")
    if len(intro) != 1 or not intro[0].endswith("."):
        found.append("opening sentence: write one sentence that says who wants what and why")
    if list(sections) != SECTIONS:
        found.append(f"sections: expected {', '.join(SECTIONS)}, in that order; found {', '.join(sections) or 'none'}")
        return found
    for name, bullets in sections.items():
        if None in bullets:
            found.append(f"{name}: write each item as a '* ' bullet on one line")
        if not bullets:
            found.append(f"{name}: write at least one item")
    criteria, evidence, scope = (sections[name] for name in SECTIONS)
    if len(criteria) > MAX_CRITERIA:
        found.append(f"Done when: {len(criteria)} criteria; split the story into stories of {MAX_CRITERIA} criteria at most")
    if len(evidence) != len(criteria):
        found.append(f"Evidence: give one line per Done when criterion, in order ({len(criteria)} criteria, {len(evidence)} lines)")
    for line in filter(None, evidence):
        if not line.startswith(("ran:", "read:")):
            found.append(f"Evidence: start with 'ran:' or 'read:': {line}")
    for name in ("Evidence", "Out of scope"):
        for line in filter(None, sections[name]):
            if "==" in line:
                found.append(f"{name}: only Done when criteria are wrapped in ==: {line}")
    for line in filter(None, scope):
        if "→" in line and not KEY.match(line.rsplit("→", 1)[1].strip()):
            found.append(f"Out of scope: keep the arrow only for the key of an existing work item: {line}")
    return found


def inline(text, marks=()):
    """Splits text into ADF text nodes, with `code` as a code mark and no other mark on it."""
    nodes = []
    for i, part in enumerate(CODE.split(text)):
        if not part:
            continue
        if i % 2:
            nodes.append({"type": "text", "text": part, "marks": [{"type": "code"}]})
        else:
            nodes.append({"type": "text", "text": part, **({"marks": list(marks)} if marks else {})})
    return nodes


def criterion(line):
    if line.startswith("==") and line.endswith("==") and len(line) > 4:
        return inline(line[2:-2], [ORANGE])
    return inline(line)


def excluded(line, site):
    if "→" not in line:
        return inline(line)
    what, key = (part.strip() for part in line.rsplit("→", 1))
    return inline(f"{what} → ") + [{"type": "inlineCard", "attrs": {"url": f"https://{site}/browse/{key}"}}]


def section(name, items):
    return [
        {"type": "heading", "attrs": {"level": 3}, "content": [{"type": "text", "text": name}]},
        {"type": "bulletList", "content": [
            {"type": "listItem", "content": [{"type": "paragraph", "content": item}]} for item in items
        ]},
    ]


def doc(content):
    return {"type": "doc", "version": 1, "content": content}


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
    summary, intro, sections = parse(sys.stdin.read())
    found = problems(summary, intro, sections)
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    story = {"summary": summary, "description": description(intro, sections, site), "comment": comment(sections)}
    print(json.dumps(story, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
