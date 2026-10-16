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
    check_criteria, check_scope, check_sections, check_summary, check_trail, check_unmarked, criterion, doc, excluded,
    filled, inline, items, section, split,
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
    criteria, evidence, scope = (items(name, sections[name], found) for name in SECTIONS)
    if len(criteria) > MAX_CRITERIA:
        found.append(f"Done when: {len(criteria)} criteria; split the story into stories of {MAX_CRITERIA} criteria at most")
    if len(evidence) != len(criteria):
        found.append(f"Evidence: give one line per Done when criterion, in order ({len(criteria)} criteria, {len(evidence)} lines)")
    check_trail("Evidence", evidence, found)
    check_criteria(criteria, found)
    for name, lines in (("Evidence", evidence), ("Out of scope", scope)):
        for line in lines:
            check_unmarked(name, line, found)
    check_scope(scope, found)
    return found, {"summary": summary, "intro": intro[0].strip() if intro else "", "criteria": criteria,
                   "evidence": evidence, "scope": scope}


def description(content, site):
    """Returns the description as an ADF document: the opening sentence, Done when and Out of scope."""
    return doc([
        {"type": "paragraph", "content": inline(content["intro"])},
        *section("Done when", [criterion(line) for line in content["criteria"]]),
        *section("Out of scope", [excluded(line, site) for line in content["scope"]]),
    ])


def comment(content):
    """Returns the Evidence as an ADF document for a comment on the story."""
    return doc(section("Evidence", [inline(line) for line in content["evidence"]]))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--site", required=True, help="the Atlassian site, e.g. example.atlassian.net")
    site = parser.parse_args().site
    found, content = problems(*split(sys.stdin.read()))
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    story = {"summary": content["summary"], "description": description(content, site), "comment": comment(content)}
    print(json.dumps(story, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
