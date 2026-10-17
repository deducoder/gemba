#!/usr/bin/env python3
"""Checks the findings of a spike against the template and converts them to the live doc
that Confluence takes: the title and the body as an ADF document.

Usage: python3 findings.py --site <site> --key <KEY> < draft.md

The draft comes on stdin: the title on its first line, `<KEY> <Summary>`; one paragraph
that is the question of the spike with the decision that waits on its answer; then the
`### Answer`, `### Evidence` and `### Next` sections, in that order. The Answer opens
with sí, no or inconclusa. The Evidence holds each `ran:` or `read:` line, and after it
the script or the output it printed in a fenced block, kept literal. A spike's Done when,
Out of scope, time-box, time worked and status live in Jira, so the draft has no section
for them.

Lines are written and converted as the plugin's scripts/draft.py says.

When the draft follows the template, prints {"title": ..., "body": <ADF>} as JSON: the link
to the issue as a smart link alone on the first line, the question, and the three sections.
Otherwise prints one line per problem to stderr, prints nothing to stdout and exits 1.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from draft import FENCE, TRAIL, check_sections, check_summary, doc, heading, inline, split, unclosed  # noqa: E402

SECTIONS = ["Answer", "Evidence", "Next"]
VERDICT = re.compile(r"^(sí|no|inconclusa)[.,:;]", re.IGNORECASE)


def paragraphs(lines):
    """Groups the lines outside fenced blocks into paragraphs and the fenced blocks into
    (language, code) pairs, in order."""
    blocks, text, code, fence, language = [], [], [], None, ""
    for line in lines:
        opener = FENCE.match(line)
        if fence is None and opener:
            if text:
                blocks.append(" ".join(text))
                text = []
            fence, language = opener.group(1), line[len(opener.group(1)):].strip()
        elif fence is not None and line.strip() == fence:
            blocks.append((language, "\n".join(code)))
            fence, language, code = None, "", []
        elif fence is not None:
            code.append(line)
        elif line.strip():
            if text and line.startswith(TRAIL):
                blocks.append(" ".join(text))
                text = []
            text.append(line.strip())
        elif text:
            blocks.append(" ".join(text))
            text = []
    if text:
        blocks.append(" ".join(text))
    return blocks


def problems(draft, key):
    """Returns what doesn't follow the template, and the content of the draft when it does."""
    fence = unclosed(draft)
    if fence:
        return ["Evidence: close the code block opened with " + fence], None
    title, intro, sections, subsections, repeated = split(draft)
    found = []
    if not title.startswith(f"{key} "):
        found.append(f"title: start the first line with the key and a space: {key} <Summary>")
    else:
        check_summary(title[len(key) + 1:], found)
    question = paragraphs(intro)
    if len(question) != 1 or not isinstance(question[0], str):
        found.append("question: write one paragraph: the question of the spike and the decision that waits on its answer")
    if subsections:
        found.append("sections: write no #### headings")
    if not check_sections(sections, SECTIONS, repeated, found):
        return found, None
    answer, evidence, nxt = (paragraphs(sections[name]) for name in SECTIONS)
    if not answer or not isinstance(answer[0], str) or not VERDICT.match(answer[0]):
        found.append("Answer: open with sí, no o inconclusa, then the sentence that supports it")
    if not any(isinstance(block, str) and block.startswith(TRAIL) for block in evidence):
        found.append("Evidence: write at least one line that starts with 'ran:' or 'read:'")
    if not nxt:
        found.append("Next: write at least one paragraph")
    for name, blocks in (("Answer", answer), ("Next", nxt)):
        if any(not isinstance(block, str) for block in blocks):
            found.append(f"{name}: write no code blocks; they belong in the Evidence")
    if found:
        return found, None
    return found, {"title": title, "question": question[0], "answer": answer, "evidence": evidence, "next": nxt}


def paragraph(text):
    return {"type": "paragraph", "content": inline(text)}


def verdict(text):
    """Returns the Answer paragraph with its yes, no or inconclusive in bold."""
    first = VERDICT.match(text)
    nodes = inline(text[first.end():])
    return {"type": "paragraph", "content": [
        {"type": "text", "text": text[:first.end()], "marks": [{"type": "strong"}]}, *nodes]}


def labelled(text):
    """Returns a ran: or read: line with its label in bold."""
    label = text.split(":", 1)[0] + ": "
    return {"type": "paragraph", "content": [
        {"type": "text", "text": label, "marks": [{"type": "strong"}]}, *inline(text[len(label):])]}


def evidence(block):
    if isinstance(block, tuple):
        language, code = block
        return {"type": "codeBlock", "attrs": {"language": language} if language else {},
                **({"content": [{"type": "text", "text": code}]} if code else {})}
    return labelled(block) if block.startswith(TRAIL) else paragraph(block)


def body(content, site, key):
    """Returns the live doc as an ADF document."""
    link = {"type": "inlineCard", "attrs": {"url": f"https://{site}/browse/{key}"}}
    return doc([
        {"type": "paragraph", "content": [link]},
        paragraph(content["question"]),
        heading("Answer", 2),
        verdict(content["answer"][0]),
        *[paragraph(block) for block in content["answer"][1:]],
        heading("Evidence", 2),
        *[evidence(block) for block in content["evidence"]],
        heading("Next", 2),
        *[paragraph(block) for block in content["next"]],
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--site", required=True, help="the Atlassian site, e.g. example.atlassian.net")
    parser.add_argument("--key", required=True, help="the key of the spike, e.g. ABC-7")
    args = parser.parse_args()
    found, content = problems(sys.stdin.read(), args.key)
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    print(json.dumps({"title": content["title"], "body": body(content, args.site, args.key)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
