#!/usr/bin/env python3
"""Checks a spike draft against the template and converts it to what Jira takes:
the Summary, the description and the Evidence comment as ADF documents.

Usage: python3 spike.py --site <site> [--requirements <url>] < draft.md

The draft comes on stdin: the Summary on its first line, one paragraph whose first
sentence is the closed question, the only one ending in "?", followed by the decision
that waits on its answer, then the `### Done when`, `### Evidence` and
`### Out of scope` sections, with one `* ` bullet per line and at most 8 Done when
criteria. The Evidence holds what was observed to declare the spike, so it needs
no line per criterion.

Lines are written and converted as the plugin's scripts/draft.py says. With
--requirements, each `R-nn` a Done when criterion cites links to that URL.

When the draft follows the template, prints {"summary": ..., "description":
<HTML>, "comment": <HTML>} as JSON: the description holds the question and its
decision, Done when and Out of scope, and the comment holds the Evidence.
Otherwise prints one line per problem to stderr, prints nothing to stdout and
exits 1.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from draft import (  # noqa: E402
    check_criteria, check_scope, check_sections, check_summary, check_trail, check_unmarked, criterion, excluded,
    filled, inline, items, paragraph, prose, section, split,
)

SECTIONS = ["Done when", "Evidence", "Out of scope"]
MAX_CRITERIA = 8
END = re.compile(r"[.?!](?=\s|$)")


def check_question(intro, found):
    """Reports an opening paragraph that does not start with the only question and go on with the decision."""
    if len(intro) != 1:
        found.append("question: write one paragraph: the closed question, then the decision that waits on its answer")
        return
    text = prose(intro[0]).strip()
    first = END.search(text)
    if text.count("?") != 1 or not first or first.group() != "?":
        found.append('question: open with the closed question, the only sentence ending in "?"')
    elif not text[first.end():].strip():
        found.append("question: after the question, write the decision that waits on its answer")


def problems(summary, intro, sections, subsections, repeated):
    """Returns what doesn't follow the template, and the bullets of each section when it does."""
    found = []
    check_summary(summary, found)
    intro = filled(intro)
    check_question(intro, found)
    for name, text in (("Summary", summary), ("question", " ".join(intro))):
        check_unmarked(name, text, found)
    if subsections:
        found.append("sections: write no #### headings")
    if not check_sections(sections, SECTIONS, repeated, found):
        return found, None
    criteria, evidence, scope = (items(name, sections[name], found) for name in SECTIONS)
    if len(criteria) > MAX_CRITERIA:
        found.append(f"Done when: {len(criteria)} criteria; a spike answers one question with {MAX_CRITERIA} criteria at most")
    check_trail("Evidence", evidence, found)
    check_criteria(criteria, found)
    for name, lines in (("Evidence", evidence), ("Out of scope", scope)):
        for line in lines:
            check_unmarked(name, line, found)
    check_scope(scope, found)
    return found, {"summary": summary, "intro": intro[0].strip() if intro else "", "criteria": criteria,
                   "evidence": evidence, "scope": scope}


def description(content, site, requirements=None):
    """Returns the description as HTML: the question and its decision, Done when and Out of scope."""
    return (paragraph(inline(content["intro"]))
            + section("Done when", [criterion(line, requirements) for line in content["criteria"]])
            + section("Out of scope", [excluded(line, site) for line in content["scope"]]))


def comment(content):
    """Returns the Evidence as HTML for a comment on the spike."""
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
    spike = {"summary": content["summary"], "description": description(content, args.site, args.requirements),
             "comment": comment(content)}
    print(json.dumps(spike, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
