#!/usr/bin/env python3
"""Checks the page of a product version against the template and converts it to the live
doc that Confluence takes: the title and the body as an ADF document.

Usage: python3 version.py --project <KEY> --site <host> --cloud-id <uuid> --requirements <url> [--first] < draft.md

The draft comes on stdin: the version name `<Product> vX.Y.Z` on the first line, then the
paragraph `[Planned] · YYYY-MM-DD` with its release date and the paragraph of its goal,
then these sections, in this order:

- `### MVP criterion`, in the first version, given with --first, and in no other:
  `Risk validated: <Kind>, «risk». why`, with a Kind among Value, Usability, Feasibility
  and Viability.
- `### Outcome`: the statement, then `Baseline: <...> Target: <...>`.
- `### Requirements`: a bullet `* **R-nn** requirement` for each one of the version.
- `### Open questions`: one paragraph with the numbers of the questions that blocked the
  version; each `Question n` links to the Requirements page given in --requirements.

The page ends with `## Work items`: a Jira issues data source table of the children of the
version given in --project, epics left out since they only group. The draft does not write
it, nor `Learned`, which version-close adds.

Prints {"title": "<Product> vX.Y.Z", "body": <HTML>} as JSON when the draft follows the
template. Otherwise prints one line per problem to stderr, prints nothing to stdout and exits 1.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from draft import BASELINE, FENCE, VERSION_NAME, attr_esc, bullets, check_sections, esc, heading, inline, is_day, items, label, linked, paragraph, paragraphs, space, split, stamp, strong  # noqa: E402

TITLE = re.compile(rf"^{VERSION_NAME}$")
STATUS = re.compile(r"^\[([^\]]+)\] · (\S+)$")
KINDS = ("Value", "Usability", "Feasibility", "Viability")
RISK = re.compile(r"^Risk validated: ((\w+), «.+?».*)$")
REQUIREMENT = re.compile(r"^\*\*(R-\d+)\*\* (.+)$")
SECTIONS = ["Outcome", "Requirements", "Open questions"]
LEFT_OUT = {"Work items": "the script writes the Jira issues table", "Learned": "version-close writes it"}
DATASOURCE_ID = "d8b75300-dfda-4519-b6cd-e49abbd50401"  # Confluence's built-in Jira issues datasource provider
COLUMNS = ("issuetype", "key", "summary", "priority", "status")
PROJECT = re.compile(r"^[A-Z][A-Z0-9_]+$")


def intro(lines, found):
    """Returns the release date and the goal of the version."""
    text = paragraphs(lines)
    match = STATUS.match(text[0]) if text else None
    if not match:
        found.append("draft: after the title write '[Planned] · YYYY-MM-DD' with the release date")
        return None
    state, day = match.groups()
    if state != "Planned":
        found.append(f"draft: a version starts Planned, not {state}")
    if not is_day(day):
        found.append(f"draft: the release date {day} is not a date")
    if len(text) != 2:
        found.append("draft: write the goal of the version in one paragraph after the release date")
        return None
    return day, text[1]


def mvp(lines, found):
    text = paragraphs(lines)
    match = RISK.match(text[0]) if len(text) == 1 else None
    if not match:
        found.append("MVP criterion: write one paragraph 'Risk validated: <Kind>, «risk». why'")
        return None
    if match.group(2) not in KINDS:
        found.append(f"MVP criterion: the Kind is one of {', '.join(KINDS)}, not {match.group(2)}")
        return None
    return match.group(1)


def outcome(lines, found):
    text = paragraphs(lines)
    match = BASELINE.match(text[1]) if len(text) == 2 else None
    if not match:
        found.append("Outcome: write the statement, then 'Baseline: <...> Target: <...>'")
        return None
    return text[0], *match.groups()


def requirements(lines, found):
    listed = []
    for item in items("Requirements", lines, found):
        match = REQUIREMENT.match(item)
        if match:
            listed.append(match.groups())
        else:
            found.append(f"Requirements: write each as '* **R-nn** requirement': {item}")
    return listed


def problems(draft, first=False):
    """Returns what doesn't follow the template, and the content of the draft when it does."""
    if any(FENCE.match(line) for line in draft.splitlines()):
        return ["draft: write no code blocks"], None
    title, lines, sections, subsections, repeated = split(draft)
    found = []
    if not TITLE.match(title):
        found.append(f"title: write the version name '<Product> vX.Y.Z' on the first line: {title}")
    for section, sub in subsections:
        found.append(f"{section}: write no '####' headings: {sub}")
    for name, why in LEFT_OUT.items():
        if name in sections:
            found.append(f"{name}: leave it out; {why}")
            sections.pop(name)
    if first and "MVP criterion" not in sections:
        found.append("MVP criterion: the first version names the risk it validates")
    elif not first and "MVP criterion" in sections:
        found.append("MVP criterion: only the first version has it; leave it out")
        sections.pop("MVP criterion")
    expected = (["MVP criterion"] if "MVP criterion" in sections else []) + SECTIONS
    if not check_sections(sections, expected, repeated, found):
        return found, None
    content = {
        "title": title,
        "intro": intro(lines, found),
        "mvp": mvp(sections["MVP criterion"], found) if "MVP criterion" in sections else None,
        "outcome": outcome(sections["Outcome"], found),
        "requirements": requirements(sections["Requirements"], found),
    }
    questions = paragraphs(sections["Open questions"])
    if len(questions) != 1:
        found.append("Open questions: write one paragraph with the numbers of the questions that blocked the version, or say none did")
    content["questions"] = questions[0] if questions else ""
    return (found, None) if found else (found, content)


def macro(project, version, site, cloud_id):
    quoted = version.replace("\\", "\\\\").replace('"', '\\"')
    jql = f'project = {project} AND fixVersion = "{quoted}" AND issuetype NOT IN (Epic, Sub-task) ORDER BY key'
    url = f"https://{site}/issues/?jql=" + quote(jql)
    datasource = json.dumps({
        "id": DATASOURCE_ID,
        "parameters": {"cloudId": cloud_id, "jql": jql},
        "views": [{"type": "table", "properties": {"columns": [{"key": column} for column in COLUMNS]}}],
    })
    escaped_url = attr_esc(url)
    return (f'<div data-type="block-card" data-url="{escaped_url}" data-datasource="{attr_esc(datasource)}">'
            f'<a href="{escaped_url}">{esc(url)}</a></div>')


def body(content, project, site, cloud_id, requirements):
    """Returns the live doc as HTML."""
    day, goal = content["intro"]
    parts = [paragraph(stamp("Planned", day)), paragraph(inline(goal))]
    if content["mvp"]:
        parts += [heading("MVP criterion", 2), label("Risk validated", content["mvp"])]
    statement, baseline, target = content["outcome"]
    parts += [heading("Outcome", 2), paragraph(inline(statement)),
              paragraph(strong("Baseline:") + space() + inline(baseline) + space() + strong("Target:") + space() + inline(target))]
    parts += [heading("Requirements", 2), bullets([strong(rid) + space() + inline(text) for rid, text in content["requirements"]])]
    parts += [heading("Open questions", 2), paragraph(linked(content["questions"], requirements))]
    parts += [heading("Work items", 2), macro(project, content["title"], site, cloud_id)]
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", required=True, help="the key of the Jira project")
    parser.add_argument("--site", required=True, help="the Jira/Confluence site hostname, for the Work items fallback link")
    parser.add_argument("--cloud-id", required=True, help="the Atlassian cloudId, for the Work items data source")
    parser.add_argument("--requirements", required=True, help="the URL of the Requirements page")
    parser.add_argument("--first", action="store_true", help="the version is the first of the product")
    args = parser.parse_args()
    if not PROJECT.match(args.project):
        print(f"--project: {args.project} is not the key of a Jira project, like ABC", file=sys.stderr)
        return 1
    found, content = problems(sys.stdin.read(), args.first)
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    body_html = body(content, args.project, args.site, args.cloud_id, args.requirements)
    print(json.dumps({"title": content["title"], "body": body_html}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
