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
a version in Now or in Released, and Later any number, each a bullet `* **Unnumbered** goal`.

Prints {"title": "Roadmap", "body": <HTML>} as JSON when the draft follows the template.
Otherwise prints one line per problem to stderr, prints nothing to stdout and exits 1.
"""

import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from draft import CURRENT, FENCE, STATES, VERSION_NAME, attr_esc, bullets, check_sections, esc, filled, heading, inline, is_day, items, paragraph, paragraphs, space, split, stamp, status, strong  # noqa: E402

SECTIONS = ["Now", "Next", "Later", "Released"]
ENTRY = re.compile(r"^\*\*Unnumbered\*\* (.+)$")
VERSION = re.compile(rf"^\[({VERSION_NAME})\]\((https?://\S+)\) \[([^\]]+)\](?: · (\S+))? (.+)$")
# Per section: the states its versions may have, whether they carry the release date, and the form to write.
VERSION_SECTIONS = {
    "Now": (CURRENT, True, "'* [<Product> vX.Y.Z](<link>) [Planned] · YYYY-MM-DD goal Target: measurable goal'"),
    "Released": (("Released",), False, "'* [<Product> vX.Y.Z](<link>) [Released] goal Target: measurable goal'"),
}
OTHER = {"Now": "a released one goes to Released", "Released": "one in progress goes to Now"}
NEXT_PLACEHOLDER = "Se decide al cerrar la versión en curso, con lo aprendido."


def entries(name, lines, found, optional=False):
    goals = []
    for item in items(name, lines, found, optional):
        match = ENTRY.match(item)
        if match:
            goals.append(match.group(1))
        else:
            found.append(f"{name}: write each entry as '* **Unnumbered** goal'; versions are added by version-start: {item}")
    return goals


def versions(section, lines, found):
    """Returns the versions of Now or Released, each (name, link, state, day, goal, target),
    the day None in Released."""
    states, dated, form = VERSION_SECTIONS[section]
    listed = []
    for item in items(section, lines, found):
        match = VERSION.match(item)
        if not match:
            found.append(f"{section}: write each version as {form}: {item}")
            continue
        name, link, state, day, rest = match.groups()
        if state not in states:
            found.append(f"{section}: {name} is {state}; a version in {section} is {' or '.join(states)}, and {OTHER[section]}")
        elif dated and not day:
            found.append(f"{section}: {name} needs ' · YYYY-MM-DD', its release date, after its status")
        elif dated and not is_day(day):
            found.append(f"{section}: {name} has {day}, which is not a date")
        elif not dated and day:
            found.append(f"{section}: {name} is released; write it without a date")
        elif " Target: " not in rest:
            found.append(f"{section}: {name} needs its goal and then 'Target: measurable goal'")
        else:
            listed.append((name, link, state, day, *rest.split(" Target: ", 1)))
    return listed


def has_versions(lines):
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
    started = has_versions(sections["Now"]) or has_versions(sections["Released"])
    content = {
        name: versions(name, sections[name], found) if has_versions(sections[name]) else single(name, sections[name], found)
        for name in VERSION_SECTIONS
    }
    content["Next"] = entries("Next", sections["Next"], found, optional=started)
    content["Later"] = entries("Later", sections["Later"], found, optional=True)
    return (found, None) if found else (found, content)


def entry(goal):
    return strong("Unnumbered") + "<br>" + inline(goal)


def version(name, link, state, day, goal, target):
    lozenge = stamp(state, day) if day else status(state, STATES[state])
    return (f'<a href="{attr_esc(link)}">{esc(name)}</a>' + space() + lozenge + "<br>"
            + inline(goal) + "<br>" + strong("Target:") + space() + inline(target))


def body(content):
    """Returns the live doc as HTML."""
    parts = []
    started = not isinstance(content["Now"], str) or not isinstance(content["Released"], str)
    for name in SECTIONS:
        parts.append(heading(name, 2))
        if isinstance(content[name], str):
            parts.append(paragraph(inline(content[name])))
        elif name in VERSION_SECTIONS:
            parts.append(bullets([version(*listed) for listed in content[name]]))
        elif content[name]:
            parts.append(bullets([entry(goal) for goal in content[name]]))
        elif name == "Next" and started:
            parts.append(paragraph(inline(NEXT_PLACEHOLDER)))
    return "".join(parts)


def main():
    found, content = problems(sys.stdin.read())
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    print(json.dumps({"title": "Roadmap", "body": body(content)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
