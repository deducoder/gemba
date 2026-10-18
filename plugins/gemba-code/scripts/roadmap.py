#!/usr/bin/env python3
"""Checks the roadmap of a product against the template and converts it to the live doc
that Confluence takes: the title and the body as an ADF document.

Usage: python3 roadmap.py < draft.md

The draft comes on stdin with the `### Now`, `### Next`, `### Later` and `### Released`
sections, in that order. Now is one paragraph while no version is in progress, or the
versions in progress, each a bullet
`* [<Product> vX.Y.Z](<link to its page>) [Planned|In progress] · YYYY-MM-DD goal Target: measurable goal`.
Released is one paragraph while no version is released, or the released versions, newest
first, each a bullet `* [<Product> vX.Y.Z](<link to its page>) [Released] goal Target: measurable goal`,
without a date. Next holds at least one entry, or none once its entry became
the version in Now, and Later any number, each a bullet `* **Unnumbered** goal`.

Prints {"title": "Roadmap", "body": <ADF>} as JSON when the draft follows the template.
Otherwise prints one line per problem to stderr, prints nothing to stdout and exits 1.
"""

import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from draft import FENCE, STATES, VERSION_NAME, bullets, check_sections, doc, filled, heading, inline, is_day, items, paragraph, paragraphs, space, split, stamp, status, strong  # noqa: E402

SECTIONS = ["Now", "Next", "Later", "Released"]
ENTRY = re.compile(r"^\*\*Unnumbered\*\* (.+)$")
VERSION = re.compile(rf"^\[({VERSION_NAME})\]\((https?://\S+)\) \[([^\]]+)\] · (\S+) (.+)$")
RELEASED = re.compile(rf"^\[({VERSION_NAME})\]\((https?://\S+)\) \[([^\]]+)\] (.+)$")
CURRENT = ("Planned", "In progress")
VERSION_FORM = "'* [<Product> vX.Y.Z](<link>) [Planned] · YYYY-MM-DD goal Target: measurable goal'"
RELEASED_FORM = "'* [<Product> vX.Y.Z](<link>) [Released] goal Target: measurable goal'"


def entries(name, lines, found, optional=False):
    goals = []
    for item in items(name, lines, found, optional):
        match = ENTRY.match(item)
        if match:
            goals.append(match.group(1))
        else:
            found.append(f"{name}: write each entry as '* **Unnumbered** goal'; versions are added by version-start: {item}")
    return goals


def versions(lines, found):
    """Returns the versions in progress, each (name, link, state, day, goal, target)."""
    listed = []
    for item in items("Now", lines, found):
        match = VERSION.match(item)
        if not match:
            found.append(f"Now: write each version as {VERSION_FORM}: {item}")
            continue
        name, link, state, day, rest = match.groups()
        if state not in CURRENT:
            found.append(f"Now: {name} is {state}; a version in Now is {' or '.join(CURRENT)}, and a released one goes to Released")
            continue
        if not is_day(day):
            found.append(f"Now: {name} has {day}, which is not a date")
            continue
        if " Target: " not in rest:
            found.append(f"Now: {name} needs its goal and then 'Target: measurable goal'")
            continue
        goal, target = rest.split(" Target: ", 1)
        listed.append((name, link, state, day, goal, target))
    return listed


def released(lines, found):
    """Returns the released versions, each (name, link, state, None, goal, target)."""
    listed = []
    for item in items("Released", lines, found):
        match = RELEASED.match(item)
        if not match:
            found.append(f"Released: write each version as {RELEASED_FORM}: {item}")
            continue
        name, link, state, rest = match.groups()
        if state != "Released":
            found.append(f"Released: {name} is {state}; a version in Released is Released, and one in progress goes to Now")
            continue
        if " Target: " not in rest:
            found.append(f"Released: {name} needs its goal and then 'Target: measurable goal'")
            continue
        goal, target = rest.split(" Target: ", 1)
        listed.append((name, link, state, None, goal, target))
    return listed


def listed(lines):
    return any(line.startswith("* ") for line in lines)


def single(name, lines, found):
    """Returns the one paragraph of a section that has no version."""
    text = paragraphs(lines)
    if len(text) != 1:
        found.append(f"{name}: write one paragraph saying there is no version yet")
    return text[0] if text else ""


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
    in_progress = listed(sections["Now"])
    content = {
        "Now": versions(sections["Now"], found) if in_progress else single("Now", sections["Now"], found),
        "Released": released(sections["Released"], found) if listed(sections["Released"]) else single("Released", sections["Released"], found),
        "Next": entries("Next", sections["Next"], found, optional=in_progress),
    }
    content["Later"] = entries("Later", sections["Later"], found, optional=True)
    return (found, None) if found else (found, content)


def entry(goal):
    return [strong("Unnumbered"), {"type": "hardBreak"}, *inline(goal)]


def version(name, link, state, day, goal, target):
    lozenge = stamp(state, day) if day else [status(state, STATES[state])]
    return [{"type": "text", "text": name, "marks": [{"type": "link", "attrs": {"href": link}}]}, space(),
            *lozenge, {"type": "hardBreak"},
            *inline(goal), {"type": "hardBreak"}, strong("Target:"), space(), *inline(target)]


def body(content):
    """Returns the live doc as an ADF document."""
    nodes = []
    for name in SECTIONS:
        nodes.append(heading(name, 2))
        if isinstance(content[name], str):
            nodes.append(paragraph(*inline(content[name])))
        elif name in ("Now", "Released"):
            nodes.append(bullets([version(*listed) for listed in content[name]]))
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
