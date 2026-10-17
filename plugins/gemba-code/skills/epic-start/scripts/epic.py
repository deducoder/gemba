#!/usr/bin/env python3
"""Checks an epic draft against the template and converts it to what Jira
takes: the Summary and the description as an ADF document.

Usage: python3 epic.py --site <site> < draft.md

The draft comes on stdin: the Summary on its first line, the opening paragraph,
then the `### Done when` and `### Out of scope` sections, with one `* ` bullet
per line, and at most 8 Done when criteria. An epic has no Evidence: each of its
children carries its own. `code` becomes a code mark, a Done when criterion
wrapped in `==` turns orange, and a work item key after `→` in Out of scope
becomes a link to the issue on the site.

When the draft follows the template, prints {"summary": ..., "description":
<ADF>} as JSON. Otherwise prints one line per problem to stderr, prints nothing
to stdout and exits 1.
"""

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from draft import (  # noqa: E402
    check_criteria, check_scope, check_sections, check_summary, check_unmarked, criterion, doc, excluded, filled,
    inline, items, section, split,
)

SECTIONS = ["Done when", "Out of scope"]
MAX_CRITERIA = 8


def problems(summary, intro, sections, subsections, repeated):
    """Returns what doesn't follow the template, and the bullets of each section when it does."""
    found = []
    check_summary(summary, found)
    intro = filled(intro)
    if len(intro) != 1 or not intro[0].strip().endswith("."):
        found.append("opening paragraph: write one paragraph that says what the epic delivers, for whom, and what they can do")
    for name, text in (("Summary", summary), ("opening paragraph", " ".join(intro))):
        check_unmarked(name, text, found)
    if subsections:
        found.append("sections: write no #### headings")
    if "Evidence" in sections:
        found.append("Evidence: an epic has no Evidence; each of its children carries its own")
    if not check_sections(sections, SECTIONS, repeated, found):
        return found, None
    criteria, scope = (items(name, sections[name], found) for name in SECTIONS)
    if len(criteria) > MAX_CRITERIA:
        found.append(f"Done when: {len(criteria)} criteria; an epic has {MAX_CRITERIA} at most")
    check_criteria(criteria, found)
    for line in scope:
        check_unmarked("Out of scope", line, found)
    check_scope(scope, found)
    return found, {"summary": summary, "intro": intro[0].strip() if intro else "", "criteria": criteria, "scope": scope}


def description(content, site):
    """Returns the description as an ADF document: the opening paragraph, Done when and Out of scope."""
    return doc([
        {"type": "paragraph", "content": inline(content["intro"])},
        *section("Done when", [criterion(line) for line in content["criteria"]]),
        *section("Out of scope", [excluded(line, site) for line in content["scope"]]),
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--site", required=True, help="the Atlassian site, e.g. example.atlassian.net")
    site = parser.parse_args().site
    found, content = problems(*split(sys.stdin.read()))
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    print(json.dumps({"summary": content["summary"], "description": description(content, site)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
