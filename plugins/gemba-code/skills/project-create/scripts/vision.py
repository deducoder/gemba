#!/usr/bin/env python3
"""Checks the vision of a product against the template and converts it to the live doc
that Confluence takes: the title and the body as an ADF document.

Usage: python3 vision.py < draft.md

The draft comes on stdin: what the product is in one sentence, ending in its origin as
`[Client]`, `[Market]`, `[Internal]` or `[Platform]`; two paragraphs, how it changes the
work of its users and where it goes; then the `### Problem`, `### Users`, `### Success`,
`### Constraints` and `### Risks` sections, and `### Decision` once the person decides.

- Problem: a paragraph and a `Today: ...` line.
- Users: bullets `* **Role** what they do or need`.
- Success: a paragraph, the metrics as bullets and a `Baseline: ... Target: ...` line.
- Constraints: bullets, or none.
- Risks: bullets `* **Risk** [Kind] [Evidence|Hypothesis]`, Kind one of Value, Usability,
  Feasibility or Viability, each followed by `Validation: ...` and `Threshold: ...` lines.
- Decision: `Go to build|Go to validate|No-go: what is decided` and
  `Decided by: <accountId> · YYYY-MM-DD`. Go to build needs Evidence in every Value and
  Viability risk.

Prints {"title": "Vision", "body": <ADF>} as JSON when the draft follows the template.
Otherwise prints one line per problem to stderr, prints nothing to stdout and exits 1.
"""

import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from draft import FENCE, bullets, check_sections, doc, filled, heading, inline, items, paragraphs, split  # noqa: E402

SECTIONS = ["Problem", "Users", "Success", "Constraints", "Risks"]
ORIGINS = ("Client", "Market", "Internal", "Platform")
KINDS = {"Value": "purple", "Usability": "yellow", "Feasibility": "red", "Viability": "blue"}
PROOF = {"Evidence": "green", "Hypothesis": "neutral"}
PANELS = {"Go to build": "success", "Go to validate": "warning", "No-go": "error"}
FIRST = re.compile(r"^(.+?) \[([^\]]+)\]$")
NAMED = re.compile(r"^\*\*(.+?)\*\* (.+)$")
RISK = re.compile(r"^\*\*(.+?)\*\* \[([^\]]+)\] \[([^\]]+)\]$")
TODAY = re.compile(r"^Today: (.+)$")
BASELINE = re.compile(r"^Baseline: (.+?) Target: (.+)$")
FIELD = re.compile(r"^(Validation|Threshold): (.+)$")
DECISION = re.compile(r"^(.+?): (.+)$")
DECIDED = re.compile(r"^Decided by: ([A-Za-z0-9:_-]+) · (\d{4}-\d{2}-\d{2})$")


def problem(lines, found):
    lines = filled(lines)
    today = TODAY.match(lines[-1].strip()) if lines else None
    text = paragraphs(lines[:-1])
    if len(text) != 1:
        found.append("Problem: write one paragraph: who cannot do what, because of what")
    if not today or any(line.strip().startswith("Today:") for line in lines[:-1]):
        found.append("Problem: end with one 'Today: ...' line with what is used today in its place")
        return None
    return text[0] if text else "", today.group(1)


def users(lines, found):
    roles = []
    for item in items("Users", lines, found):
        match = NAMED.match(item)
        if match:
            roles.append(match.groups())
        else:
            found.append(f"Users: write each as '* **Role** what they do or need': {item}")
    return roles


def success(lines, found):
    lines = [line.strip() for line in lines]
    statement = paragraphs([line for line in lines if not line.startswith("*") and not line.startswith("Baseline:")])
    metrics = items("Success", [line for line in lines if line.startswith("*")], found)
    baseline = [BASELINE.match(line) for line in lines if line.startswith("Baseline:")]
    if len(statement) != 1:
        found.append("Success: write one paragraph: if current state, then signal for whom")
    if len(baseline) != 1 or not baseline[0]:
        found.append("Success: write one 'Baseline: ... Target: ...' line")
        return None
    return statement[0] if statement else "", metrics, baseline[0].groups()


def risks(lines, found):
    found_risks, current, count = [], None, 0
    for line in filled(lines):
        if line.startswith("* "):
            count += 1
            current = {"name": None}
            match = RISK.match(line[2:].strip())
            if not match:
                found.append(f"Risks: write each as '* **Risk** [Kind] [Evidence|Hypothesis]': {line.strip()}")
                continue
            name, kind, proof = match.groups()
            if kind not in KINDS:
                found.append(f"Risks: {kind} is not a kind; use {', '.join(KINDS)}: {name}")
            if proof not in PROOF:
                found.append(f"Risks: {proof} is neither Evidence nor Hypothesis: {name}")
            current = {"name": name, "kind": kind, "proof": proof}
            found_risks.append(current)
            continue
        field = FIELD.match(line.strip())
        if current and current["name"] is None:
            continue
        if not field or current is None:
            found.append(f"Risks: write 'Validation: ...' and 'Threshold: ...' under each risk: {line.strip()}")
        elif field.group(1) in current:
            found.append(f"Risks: write {field.group(1)} once for {current['name']}")
        else:
            current[field.group(1)] = field.group(2)
    for risk in found_risks:
        for name in ("Validation", "Threshold"):
            if name not in risk:
                found.append(f"Risks: {risk['name']} needs its '{name}: ...' line")
    if not count:
        found.append("Risks: write at least one risk")
    return found_risks


def decision(lines, found_risks, found):
    lines = [line.strip() for line in filled(lines)]
    if len(lines) != 2:
        found.append("Decision: write the decision line and the 'Decided by: <accountId> · YYYY-MM-DD' line, or leave the section out")
        return None
    match, decided = DECISION.match(lines[0]), DECIDED.match(lines[1])
    if not match or match.group(1) not in PANELS:
        found.append(f"Decision: start with {', '.join(PANELS)} and a colon: {lines[0]}")
        match = None
    if not decided:
        found.append(f"Decided by: write the accountId of who decided and the date as 'Decided by: <accountId> · YYYY-MM-DD': {lines[1]}")
    else:
        try:
            date.fromisoformat(decided.group(2))
        except ValueError:
            found.append(f"Decided by: {decided.group(2)} is not a date")
            decided = None
    if match and match.group(1) == "Go to build":
        for risk in found_risks:
            if risk["kind"] in ("Value", "Viability") and risk["proof"] == "Hypothesis":
                found.append(f"Decision: Go to build needs Evidence in every Value and Viability risk; {risk['kind']} is a Hypothesis: {risk['name']}")
    if not match or not decided:
        return None
    return match.group(1), match.group(2), decided.group(1), decided.group(2)


def problems(draft):
    """Returns what doesn't follow the template, and the content of the draft when it does."""
    if any(FENCE.match(line) for line in draft.splitlines()):
        return ["draft: write no code blocks"], None
    first, intro, sections, subsections, repeated = split(draft)
    found = []
    origin = FIRST.match(first)
    if not origin or origin.group(2) not in ORIGINS:
        found.append(f"origin: end the first line with one of {', '.join(f'[{o}]' for o in ORIGINS)}")
    if len(paragraphs(intro)) != 2:
        found.append("paragraphs: write two paragraphs after the first line: how it changes the work of its users and where it goes")
    for section, sub in subsections:
        found.append(f"{section}: write no '####' headings: {sub}")
    expected = SECTIONS + (["Decision"] if "Decision" in sections else [])
    if not check_sections(sections, expected, repeated, found):
        return found, None
    content = {
        "what": origin.group(1) if origin else "", "origin": origin.group(2) if origin else "",
        "intro": paragraphs(intro),
        "problem": problem(sections["Problem"], found),
        "users": users(sections["Users"], found),
        "success": success(sections["Success"], found),
        "constraints": items("Constraints", sections["Constraints"], found) if filled(sections["Constraints"]) else [],
    }
    content["risks"] = risks(sections["Risks"], found)
    content["decision"] = decision(sections["Decision"], content["risks"], found) if "Decision" in sections else None
    return (found, None) if found else (found, content)


def status(text, color):
    return {"type": "status", "attrs": {"text": text, "color": color, "style": "bold"}}


def strong(text):
    return {"type": "text", "text": text, "marks": [{"type": "strong"}]}


def space():
    return {"type": "text", "text": " "}


def paragraph(*content):
    return {"type": "paragraph", "content": list(content)}


def panel(kind, *content):
    return {"type": "panel", "attrs": {"panelType": kind}, "content": list(content)}


def label(name, text):
    return paragraph(strong(f"{name}:"), space(), *inline(text))


def timestamp(day):
    """Returns the date as the milliseconds of its midnight in UTC, as a date node takes it."""
    moment = datetime.combine(date.fromisoformat(day), datetime.min.time(), tzinfo=timezone.utc)
    return str(int(moment.timestamp() * 1000))


def body(content):
    """Returns the live doc as an ADF document."""
    text, today = content["problem"]
    statement, metrics, (baseline, target) = content["success"]
    nodes = [
        paragraph(*inline(content["what"]), space(), status(content["origin"], "neutral")),
        *[paragraph(*inline(block)) for block in content["intro"]],
        heading("Problem", 2), paragraph(*inline(text)), panel("info", label("Today", today)),
        heading("Users", 2), bullets([[strong(role), space(), *inline(need)] for role, need in content["users"]]),
        heading("Success", 2), paragraph(*inline(statement)), bullets([inline(metric) for metric in metrics]),
        paragraph(strong("Baseline:"), space(), *inline(baseline), space(), strong("Target:"), space(), *inline(target)),
    ]
    if content["constraints"]:
        nodes += [heading("Constraints", 2), bullets([inline(item) for item in content["constraints"]])]
    nodes.append(heading("Risks", 2))
    for risk in content["risks"]:
        nodes += [
            paragraph(strong(risk["name"]), space(), status(risk["kind"], KINDS[risk["kind"]]),
                      space(), status(risk["proof"], PROOF[risk["proof"]])),
            panel("note", label("Validation", risk["Validation"]), label("Threshold", risk["Threshold"])),
        ]
    if content["decision"]:
        state, what, account, day = content["decision"]
        nodes += [heading("Decision", 2), panel(
            PANELS[state], {"type": "heading", "attrs": {"level": 3}, "content": inline(what)},
            paragraph(strong("Decided by:"), space(), {"type": "mention", "attrs": {"id": account}},
                      {"type": "text", "text": " · "}, {"type": "date", "attrs": {"timestamp": timestamp(day)}}),
        )]
    return doc(nodes)


def main():
    found, content = problems(sys.stdin.read())
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    print(json.dumps({"title": "Vision", "body": body(content)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
