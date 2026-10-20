#!/usr/bin/env python3
"""Checks the catalog of a product's requirements against the template and converts it to
the live doc that Confluence takes: the title and the body as an ADF document.

Usage: python3 requirements.py [--existing R-01,R-02,...] < draft.md

The draft comes on stdin with its sections in this order: one per version that version-start
named, as `### <Product> vX.Y.Z`; `### Unassigned`, where every requirement is born and
which may be empty only when a version or a withdrawn requirement exists; `### Withdrawn`, which is optional;
and `### Assumptions and open questions`, which may be empty.

- A requirement: `* **R-nn** requirement [Type] Source: origin [Hypothesis]`, Type one of
  Functional, Business rule, Non-functional or Constraint, origin one of Interview, Material,
  Research or Vision. Source and Hypothesis are each optional, but not both absent: a
  requirement with nothing external to back it carries only `[Hypothesis]`. Each ID is used
  once in the page and goes upward within its section; a gap is a proposal the person removed.
- A withdrawn requirement: `* ~~**R-nn** requirement~~ reason · YYYY-MM-DD`, in the order
  they were withdrawn.
- A question: `* **Question n.** question Assumption: assumption Affects R-nn. [Open|Answered]`,
  numbered from 1; `Affects` is optional and names requirements of the page.

With --existing, the IDs the published page has: each of them stays in the draft, since a
requirement is withdrawn and never deleted, and each new ID goes above the highest of them,
so no number is reused.

Prints {"title": "Requirements", "body": <HTML>} as JSON when the draft follows the template.
Otherwise prints one line per problem to stderr, prints nothing to stdout and exits 1.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from draft import FENCE, GREY, STRIKE, STRONG, VERSION_NAME, bullets, check_sections, filled, heading, inline, is_day, items, space, split, status, strong, date_node  # noqa: E402

TYPES = {"Functional": "neutral", "Business rule": "blue", "Non-functional": "purple", "Constraint": "yellow"}
SOURCES = ("Interview", "Material", "Research", "Vision")
STATES = {"Open": "blue", "Answered": "green"}
QUESTIONS = "Assumptions and open questions"
REQUIREMENT = re.compile(r"^\*\*(R-\d+)\*\* (.+)$")
VERSION = re.compile(rf"^{VERSION_NAME}$")
WITHDRAWN = re.compile(r"^~~\*\*(R-\d+)\*\* (.+?)~~ (.+) · (\d{4}-\d{2}-\d{2})$")
TAIL = re.compile(r"^(.*?) \[([^\]]+)\](?: Source: (\w+))?( \[Hypothesis\])?$")
QUESTION = re.compile(r"^\*\*Question (\d+)\.\*\* (.+?) Assumption: (.+) \[([^\]]+)\]$")


def numbered(name, rid, ids, last, found):
    """Reports an ID used before in the page or not going upward in its section; a last of
    None skips the order, as in Withdrawn, kept in the order of withdrawal."""
    if rid in ids or (last is not None and int(rid[2:]) <= last):
        found.append(f"{name}: {rid} breaks the series; number the requirements upward from R-01, never reusing one")
    ids.add(rid)
    return None if last is None else max(last, int(rid[2:]))


def requirements(name, lines, ids, found, optional=False):
    """Returns the requirements of a section, adding each ID written, valid or not, so one bad
    line reports once."""
    catalog, last = [], 0
    for item in items(name, lines, found, optional):
        match = REQUIREMENT.match(item)
        if not match:
            found.append(f"{name}: write each as '* **R-nn** requirement. Source: origin [Type]': {item}")
            continue
        rid, rest = match.groups()
        last = numbered(name, rid, ids, last, found)
        tail = TAIL.match(rest)
        if not tail or tail.group(2) not in TYPES:
            found.append(f"{name}: {rid} carries its Type right after the sentence, one of {', '.join(TYPES)}, then its optional Source and [Hypothesis]: {rest}")
            continue
        sentence, kind, source, hypothesis = tail.group(1), tail.group(2), tail.group(3), bool(tail.group(4))
        if source is None and not hypothesis:
            found.append(f"{name}: {rid} needs its 'Source: origin' or [Hypothesis], or both")
            continue
        if source is not None and source not in SOURCES:
            found.append(f"{name}: {rid}'s Source is one of {', '.join(SOURCES)}, not {source}")
            continue
        catalog.append((rid, sentence, source, kind, hypothesis))
    return catalog


def withdrawn(lines, ids, found):
    listed = []
    for item in items("Withdrawn", lines, found, optional=True):
        rid = re.search(r"R-\d+", item)
        if rid:
            numbered("Withdrawn", rid.group(0), ids, None, found)
        match = WITHDRAWN.match(item)
        if not match:
            found.append(f"Withdrawn: write each as '* ~~**R-nn** requirement~~ reason · YYYY-MM-DD': {item}")
            continue
        if not is_day(match.group(4)):
            found.append(f"Withdrawn: {match.group(1)} has {match.group(4)}, which is not a date")
            continue
        listed.append(match.groups())
    return listed


def questions(lines, ids, found):
    listed = []
    for item in items(QUESTIONS, lines, found, optional=True):
        match = QUESTION.match(item)
        if not match:
            found.append(f"{QUESTIONS}: write each as '* **Question n.** question Assumption: assumption [Open|Answered]': {item}")
            continue
        number, question, assumption, state = match.groups()
        name = f"Question {number}"
        if int(number) != len(listed) + 1:
            found.append(f"{QUESTIONS}: {name} breaks the series; number the questions from 1")
        if state not in STATES:
            found.append(f"{QUESTIONS}: {name} is {state}; use Open or Answered")
        for rid in re.findall(r"R-\d+", assumption.split("Affects", 1)[1]) if "Affects" in assumption else []:
            if rid not in ids:
                found.append(f"{QUESTIONS}: {name} affects {rid}, which the page does not have")
        listed.append((name, question, assumption, state))
    return listed


def problems(draft, existing=None):
    """Returns what doesn't follow the template, and the content of the draft when it does."""
    if any(FENCE.match(line) for line in draft.splitlines()):
        return ["draft: write no code blocks"], None
    _, intro, sections, subsections, repeated = split(draft, titled=False)
    found = []
    if filled(intro):
        found.append("draft: start with a version section or '### Unassigned'")
    for section, sub in subsections:
        found.append(f"{section}: write no '####' headings: {sub}")
    versions = [name for name in sections if VERSION.match(name)]
    expected = versions + ["Unassigned"] + (["Withdrawn"] if "Withdrawn" in sections else []) + [QUESTIONS]
    if not check_sections(sections, expected, repeated, found):
        return found, None
    ids = set()
    groups = [(name, requirements(name, sections[name], ids, found)) for name in versions]
    groups.append(("Unassigned", requirements("Unassigned", sections["Unassigned"], ids, found,
                                               optional=bool(versions) or "Withdrawn" in sections)))
    gone = withdrawn(sections.get("Withdrawn", []), ids, found)
    listed = questions(sections[QUESTIONS], ids, found)
    if existing is not None:
        for rid in sorted(existing - ids):
            found.append(f"draft: {rid} is published; withdraw it instead of deleting it")
        top = max((int(rid[2:]) for rid in existing), default=0)
        for rid in sorted(ids - existing):
            if int(rid[2:]) <= top:
                found.append(f"draft: {rid} is new, so it takes a number above R-{top:02d}, the highest published")
    return (found, None) if found else (found, {"groups": groups, "withdrawn": gone, "questions": listed})


def body(content):
    """Returns the live doc as HTML."""
    parts = []
    for name, catalog in content["groups"]:
        lines = []
        for rid, sentence, source, kind, hypothesis in catalog:
            marks = space() + status(kind, TYPES[kind])
            if source:
                marks += space() + inline(f"Source: {source}", (GREY,))
            if hypothesis:
                marks += space() + status("Hypothesis", "neutral")
            lines.append(strong(rid) + space() + inline(sentence) + marks)
        parts.append(heading(name, 2) + (bullets(lines) if lines else ""))
    if content["withdrawn"]:
        parts.append(heading("Withdrawn", 2) + bullets([
            inline(rid, (STRONG, STRIKE)) + inline(f" {sentence}", (STRIKE,))
            + space() + inline(f"{reason} · ", (GREY,)) + date_node(day)
            for rid, sentence, reason, day in content["withdrawn"]]))
    if content["questions"]:
        parts.append(heading(QUESTIONS, 2) + bullets([
            strong(f"{name}.") + space() + inline(question) + space() + strong("Assumption:") + space()
            + inline(assumption) + space() + status(state, STATES[state])
            for name, question, assumption, state in content["questions"]]))
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--existing", help="the IDs of the published page, comma separated")
    args = parser.parse_args()
    existing = {rid.strip() for rid in args.existing.split(",") if rid.strip()} if args.existing is not None else None
    wrong = sorted(rid for rid in existing or () if not re.match(r"^R-\d+$", rid))
    if wrong:
        print(f"existing: {', '.join(wrong)} is not an ID like R-01", file=sys.stderr)
        return 1
    found, content = problems(sys.stdin.read(), existing)
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    print(json.dumps({"title": "Requirements", "body": body(content)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
