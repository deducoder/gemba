#!/usr/bin/env python3
"""Checks the catalog of a product's requirements against the template and converts it to
the live doc that Confluence takes: the title and the body as an ADF document.

Usage: python3 requirements.py < draft.md

The draft comes on stdin with the `### Unassigned` section, where every requirement is born,
and the `### Assumptions and open questions` section, which may be empty.

- Unassigned: bullets `* **R-nn** requirement. Source: origin [Type]`, with an optional
  `[Hypothesis]` after the Type. The IDs go upward from R-01 and are never reused; a gap is a proposal the person removed, and the
  Type is Functional, Business rule, Non-functional or Constraint.
- Assumptions and open questions: bullets
  `* **Question n.** question Assumption: assumption Affects R-nn. [Open|Answered]`,
  numbered from 1; `Affects` is optional and names existing requirements.

Prints {"title": "Requirements", "body": <ADF>} as JSON when the draft follows the template.
Otherwise prints one line per problem to stderr, prints nothing to stdout and exits 1.
"""

import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from draft import FENCE, bullets, check_sections, doc, filled, heading, inline, items, space, split, status, strong  # noqa: E402

GREY = {"type": "textColor", "attrs": {"color": "#97a0af"}}
TYPES = {"Functional": "neutral", "Business rule": "blue", "Non-functional": "purple", "Constraint": "yellow"}
STATES = {"Open": "blue", "Answered": "green"}
QUESTIONS = "Assumptions and open questions"
REQUIREMENT = re.compile(r"^\*\*(R-\d+)\*\* (.+)$")
TAIL = re.compile(r"^(.*?) \[([^\]]+)\]( \[Hypothesis\])?$")
QUESTION = re.compile(r"^\*\*Question (\d+)\.\*\* (.+?) Assumption: (.+) \[([^\]]+)\]$")


def requirements(lines, found):
    """Returns the catalog and the IDs written, valid or not, so one bad line reports once."""
    catalog, ids, last = [], set(), 0
    for item in items("Unassigned", lines, found):
        match = REQUIREMENT.match(item)
        if not match:
            found.append(f"Unassigned: write each as '* **R-nn** requirement. Source: origin [Type]': {item}")
            continue
        rid, rest = match.groups()
        number = int(rid[2:])
        if rid in ids or number <= last:
            found.append(f"Unassigned: {rid} breaks the series; number the requirements upward from R-01, never reusing one")
        ids.add(rid)
        last = max(last, number)
        tail = TAIL.match(rest)
        if not tail or tail.group(2) not in TYPES:
            found.append(f"Unassigned: {rid} ends with its Type, one of {', '.join(TYPES)}, and optionally [Hypothesis]: {rest}")
            continue
        text, kind, hypothesis = tail.group(1), tail.group(2), bool(tail.group(3))
        if " Source: " not in text:
            found.append(f"Unassigned: {rid} needs its 'Source: origin' before the Type")
            continue
        sentence, source = text.rsplit(" Source: ", 1)
        catalog.append((rid, sentence, source, kind, hypothesis))
    return catalog, ids


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
                found.append(f"{QUESTIONS}: {name} affects {rid}, which Unassigned does not have")
        listed.append((name, question, assumption, state))
    return listed


def problems(draft):
    """Returns what doesn't follow the template, and the content of the draft when it does."""
    if any(FENCE.match(line) for line in draft.splitlines()):
        return ["draft: write no code blocks"], None
    _, intro, sections, subsections, repeated = split(draft, titled=False)
    found = []
    if filled(intro):
        found.append("draft: start with the '### Unassigned' section")
    for section, sub in subsections:
        found.append(f"{section}: write no '####' headings: {sub}")
    if not check_sections(sections, ["Unassigned", QUESTIONS], repeated, found):
        return found, None
    catalog, ids = requirements(sections["Unassigned"], found)
    listed = questions(sections[QUESTIONS], ids, found)
    return (found, None) if found else (found, {"catalog": catalog, "questions": listed})


def body(content):
    """Returns the live doc as an ADF document."""
    lines = []
    for rid, sentence, source, kind, hypothesis in content["catalog"]:
        marks = [space(), status(kind, TYPES[kind])] + ([space(), status("Hypothesis", "neutral")] if hypothesis else [])
        lines.append([strong(rid), space(), *inline(sentence), space(), *inline(f"Source: {source}", [GREY]), *marks])
    nodes = [heading("Unassigned", 2), bullets(lines)]
    if content["questions"]:
        nodes += [heading(QUESTIONS, 2), bullets([
            [strong(f"{name}."), space(), *inline(question), space(), strong("Assumption:"), space(),
             *inline(assumption), space(), status(state, STATES[state])]
            for name, question, assumption, state in content["questions"]])]
    return doc(nodes)


def main():
    found, content = problems(sys.stdin.read())
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    print(json.dumps({"title": "Requirements", "body": body(content)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
