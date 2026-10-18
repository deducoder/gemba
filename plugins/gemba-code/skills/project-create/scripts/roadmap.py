#!/usr/bin/env python3
"""Checks the roadmap of a product before its first version against the template and
converts it to the live doc that Confluence takes: the title and the body as an ADF document.

Usage: python3 roadmap.py < draft.md

The draft comes on stdin with the `### Now`, `### Next`, `### Later` and `### Released`
sections, in that order. Now and Released are one paragraph each, since no version exists
yet. Next holds at least one entry and Later any number, each a bullet
`* **Unnumbered** goal`.

Prints {"title": "Roadmap", "body": <ADF>} as JSON when the draft follows the template.
Otherwise prints one line per problem to stderr, prints nothing to stdout and exits 1.
"""

import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from draft import FENCE, bullets, check_sections, doc, filled, heading, inline, items, paragraphs, split, strong  # noqa: E402

SECTIONS = ["Now", "Next", "Later", "Released"]
ENTRY = re.compile(r"^\*\*Unnumbered\*\* (.+)$")


def entries(name, lines, found, optional=False):
    goals = []
    for item in items(name, lines, found, optional):
        match = ENTRY.match(item)
        if match:
            goals.append(match.group(1))
        else:
            found.append(f"{name}: write each entry as '* **Unnumbered** goal'; versions are added by version-start: {item}")
    return goals


def problems(draft):
    """Returns what doesn't follow the template, and the content of the draft when it does."""
    if any(FENCE.match(line) for line in draft.splitlines()):
        return ["draft: write no code blocks"], None
    _, intro, sections, subsections, repeated = split(draft, titled=False)
    found = []
    if filled(intro):
        found.append("draft: start with the '### Now' section")
    for section, sub in subsections:
        found.append(f"{section}: write no '####' headings: {sub}")
    if not check_sections(sections, SECTIONS, repeated, found):
        return found, None
    content = {}
    for name in ("Now", "Released"):
        text = paragraphs(sections[name])
        if len(text) != 1:
            found.append(f"{name}: write one paragraph saying there is no version yet")
        content[name] = text[0] if text else ""
    content["Next"] = entries("Next", sections["Next"], found)
    content["Later"] = entries("Later", sections["Later"], found, optional=True)
    return (found, None) if found else (found, content)


def entry(goal):
    return [strong("Unnumbered"), {"type": "hardBreak"}, *inline(goal)]


def body(content):
    """Returns the live doc as an ADF document."""
    nodes = []
    for name in SECTIONS:
        nodes.append(heading(name, 2))
        if name in ("Now", "Released"):
            nodes.append({"type": "paragraph", "content": inline(content[name])})
        elif content[name]:
            nodes.append(bullets([entry(goal) for goal in content[name]]))
    return doc(nodes)


def main():
    found, content = problems(sys.stdin.read())
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    print(json.dumps({"title": "Roadmap", "body": body(content)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
