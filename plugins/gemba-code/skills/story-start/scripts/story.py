#!/usr/bin/env python3
"""Checks a story draft against the template and converts it to what Jira
takes: the Summary and the description as an ADF document.

Usage: python3 story.py --site <site> [--requirements <url>] < draft.md

The draft comes on stdin: the Summary on its first line, the opening sentence,
then the `### Done when`, `### Evidence` and `### Out of scope` sections, with
one `* ` bullet per line, and at most 8 Done when criteria. `code` becomes a
code mark, a Done when criterion wrapped in `==` turns orange, and a work item
key after `→` in Out of scope becomes a link to the issue on the site. With
--requirements, each `R-nn` a Done when criterion cites links to that URL, and
a criterion with no Evidence line of its own is allowed, since its only
source is the requirement it cites.

When the draft follows the template, prints {"summary": ..., "description":
<HTML>, "comment": <HTML>} as JSON: the description holds the opening sentence,
Done when and Out of scope, and the comment holds the Evidence. Otherwise
prints one line per problem to stderr, prints nothing to stdout and exits 1.
"""

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from draft import (  # noqa: E402
    check_criteria, check_scope, check_sections, check_summary, check_trail, check_unmarked, cites_requirement,
    criterion, excluded, filled, inline, items, paragraph, section, split,
)

SECTIONS = ["Done when", "Evidence", "Out of scope"]
MAX_CRITERIA = 8


def problems(summary, intro, sections, subsections, repeated):
    """Returns what doesn't follow the template, and the bullets of each section when it does."""
    found = []
    check_summary(summary, found)
    intro = filled(intro)
    if len(intro) != 1 or not intro[0].strip().endswith("."):
        found.append("opening sentence: write one sentence that says who wants what and why")
    for name, text in (("Summary", summary), ("opening sentence", " ".join(intro))):
        check_unmarked(name, text, found)
    if subsections:
        found.append("sections: write no #### headings")
    if not check_sections(sections, SECTIONS, repeated, found):
        return found, None
    criteria = items("Done when", sections["Done when"], found)
    citing = sum(1 for line in criteria if cites_requirement(line))
    evidence = items("Evidence", sections["Evidence"], found, optional=(citing == len(criteria)))
    scope = items("Out of scope", sections["Out of scope"], found)
    if len(criteria) > MAX_CRITERIA:
        found.append(f"Done when: {len(criteria)} criteria; split the story into stories of {MAX_CRITERIA} criteria at most")
    if len(evidence) > len(criteria) or len(criteria) - len(evidence) > citing:
        found.append(
            "Evidence: give one line per Done when criterion, in order, except one that only cites a requirement, "
            f"which may skip it ({len(criteria)} criteria, {citing} citing a requirement, {len(evidence)} lines)"
        )
    check_trail("Evidence", evidence, found)
    check_criteria(criteria, found)
    for name, lines in (("Evidence", evidence), ("Out of scope", scope)):
        for line in lines:
            check_unmarked(name, line, found)
    check_scope(scope, found)
    return found, {"summary": summary, "intro": intro[0].strip() if intro else "", "criteria": criteria,
                   "evidence": evidence, "scope": scope}


def description(content, site, requirements=None):
    """Returns the description as HTML: the opening sentence, Done when and Out of scope."""
    return (paragraph(inline(content["intro"]))
            + section("Done when", [criterion(line, requirements) for line in content["criteria"]])
            + section("Out of scope", [excluded(line, site) for line in content["scope"]]))


def comment(content):
    """Returns the Evidence as HTML for a comment on the story."""
    return section("Evidence", [inline(line) for line in content["evidence"]])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--site", required=True, help="the Atlassian site, e.g. example.atlassian.net")
    parser.add_argument("--requirements", help="the URL of the Requirements page")
    args = parser.parse_args()
    found, content = problems(*split(sys.stdin.read()))
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    story = {"summary": content["summary"], "description": description(content, args.site, args.requirements)}
    if content["evidence"]:
        story["comment"] = comment(content)
    print(json.dumps(story, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
