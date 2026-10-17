#!/usr/bin/env python3
"""Checks the answer to a question against the template and converts it to the live doc
that Confluence takes: the title and the body as an ADF document.

Usage: python3 research.py --site <site> [--key <KEY>] < draft.md

The draft comes on stdin: the question on its first line, ending in `?`; one sentence with
the decision or doubt that prompted it and who waits on it; then the `### Answer`,
`### Method`, `### Findings`, `### Sources` and `### Next` sections, in that order. The
Answer cites the findings it rests on as `[Finding 1.1]`. The Findings are `#### n. Topic`
headings with lines `n.m Documented|Inferred|Unverified: text`: a Documented finding ends
with the number of its source as `[n]`, an Inferred one names what it follows from as
`(from n.m)` and an Unverified one cites nothing. Each Sources line is
`[n] <URL> (official|spec|source|secondary, YYYY-MM-DD): what it is`, and a secondary
source never goes before an official or a spec one.

The related work item is not in the draft: --key adds a smart link to it as the first
line of the page, and must look like a work item key.

Prints {"title": ..., "body": <ADF>} as JSON when the draft follows the template.
Otherwise prints one line per problem to stderr, prints nothing to stdout and exits 1.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from draft import FENCE, KEY, check_sections, doc, heading, inline, split, unclosed  # noqa: E402

SECTIONS = ["Answer", "Method", "Findings", "Sources", "Next"]
FINDING = re.compile(r"^(\d+)\.(\d+) (\S+?): (.+)$")
STATES = ("Documented", "Inferred", "Unverified")
SOURCE = re.compile(r"^\[(\d+)\] (https?://\S+) \((official|spec|source|secondary), (\d{4}-\d{2}-\d{2})\): (.+)$")
CITE = re.compile(r"\[(\d+)\]")
FROM = re.compile(r"\(from \d+\.\d+(, \d+\.\d+)*\)\s*$")
CITED = re.compile(r"\[Finding (\d+\.\d+)\]")
TOPIC = re.compile(r"^(\d+)\. \S")


def paragraphs(lines):
    """Groups the lines into paragraphs, separated by blank lines."""
    blocks, text = [], []
    for line in lines:
        if line.strip():
            text.append(line.strip())
        elif text:
            blocks.append(" ".join(text))
            text = []
    if text:
        blocks.append(" ".join(text))
    return blocks


def problems(draft):
    """Returns what doesn't follow the template, and the content of the draft when it does."""
    fence = unclosed(draft)
    if fence:
        return ["draft: close the code block opened with " + fence], None
    if any(FENCE.match(line) for line in draft.splitlines()):
        return ["draft: write no code blocks"], None
    title, intro, sections, subsections, repeated = split(draft)
    found = []
    if not title.endswith("?"):
        found.append("title: write the question on the first line, ending in ?")
    decision = paragraphs(intro)
    if len(decision) != 1:
        found.append("decision: write one sentence under the question: the decision or doubt that prompted it and who waits on it")
    if not check_sections(sections, SECTIONS, repeated, found):
        return found, None
    for name in ("Answer", "Method", "Next"):
        if not paragraphs(sections[name]):
            found.append(f"{name}: write at least one paragraph")
    if [line for line in sections["Findings"] if line.strip()]:
        found.append("Findings: write each line under a '#### n. Topic' heading")

    sources = {}
    for line in (line for line in sections["Sources"] if line.strip()):
        match = SOURCE.match(line)
        if not match:
            found.append(f"Sources: write each as '[n] <URL> (official|spec|source|secondary, YYYY-MM-DD): what it is': {line}")
        elif int(match.group(1)) != len(sources) + 1:
            found.append(f"Sources: number them from 1, in order: {line}")
        else:
            sources[int(match.group(1))] = match.groups()[1:]
    if not sources:
        found.append("Sources: write at least one source")
    kinds = [source[1] for source in sources.values()]
    if "secondary" in kinds and any(kind in ("official", "spec") for kind in kinds[kinds.index("secondary"):]):
        found.append("Sources: a secondary source goes after every official and spec one")

    topics, ids = [], []
    for (section, topic), lines in subsections.items():
        number = TOPIC.match(topic)
        if section != "Findings" or not number or int(number.group(1)) != len(topics) + 1:
            found.append(f"Findings: write '#### n. Topic' headings under Findings, numbered from 1: {topic}")
            continue
        topics.append((topic, []))
        count = 0
        for line in (line for line in lines if line.strip()):
            match = FINDING.match(line)
            count += 1
            if not match or (int(match.group(1)), int(match.group(2))) != (len(topics), count):
                found.append(f"Findings: write '{len(topics)}.{count} Documented|Inferred|Unverified: text': {line}")
                continue
            state, text = match.group(3), match.group(4)
            name = f"{len(topics)}.{count}"
            if state not in STATES:
                found.append(f"Findings: {name} is {state}; use Documented, Inferred or Unverified")
                continue
            numbers = [int(n) for n in CITE.findall(text)]
            if state == "Documented":
                if not numbers:
                    found.append(f"Findings: {name} Documented needs the number of its source as [n]")
                for n in numbers:
                    if n not in sources:
                        found.append(f"Findings: {name} cites the source {n}, which Sources does not have")
            elif state == "Inferred" and not FROM.search(text):
                found.append(f"Findings: {name} Inferred names what it follows from, ending in (from n.m)")
            elif state == "Unverified" and numbers:
                found.append(f"Findings: {name} Unverified cites no source")
            ids.append(name)
            topics[-1][1].append((name, state, text))
        if not count:
            found.append(f"Findings: {topic} needs at least one finding")
    if not topics:
        found.append("Findings: write at least one '#### 1. Topic' with its findings")

    answer = " ".join(paragraphs(sections["Answer"]))
    cited = CITED.findall(answer)
    if not cited:
        found.append("Answer: cite at least one finding as [Finding n.m]")
    for name in cited:
        if name not in ids:
            found.append(f"Answer: cites [Finding {name}], which Findings does not have")
    if found:
        return found, None
    return found, {"title": title, "decision": decision[0], "answer": paragraphs(sections["Answer"]),
                   "method": paragraphs(sections["Method"]), "topics": topics, "sources": sources,
                   "next": paragraphs(sections["Next"])}


def paragraph(text):
    return {"type": "paragraph", "content": inline(text)}


def cited(text, sources):
    """Returns the text with each [n] as a link to the source n, without a card."""
    nodes = []
    for i, part in enumerate(CITE.split(text)):
        if i % 2:
            nodes.append({"type": "text", "text": f"[{part}]",
                          "marks": [{"type": "link", "attrs": {"href": sources[int(part)][0]}}]})
        elif part:
            nodes.extend(inline(part))
    return nodes


def finding(name, state, text, sources):
    return {"type": "paragraph", "content": [
        {"type": "text", "text": f"{name} {state}:", "marks": [{"type": "strong"}]},
        {"type": "text", "text": " "}, *cited(text, sources)]}


def source(number, url, kind, date, what):
    return {"type": "paragraph", "content": [
        {"type": "text", "text": f"[{number}] "}, {"type": "inlineCard", "attrs": {"url": url}},
        *inline(f" ({kind}, {date}): {what}")]}


def body(content, site, key):
    """Returns the live doc as an ADF document."""
    link = [{"type": "paragraph", "content": [{"type": "inlineCard", "attrs": {"url": f"https://{site}/browse/{key}"}}]}] if key else []
    sources = content["sources"]
    return doc([
        *link,
        paragraph(content["decision"]),
        heading("Answer", 2), *[paragraph(block) for block in content["answer"]],
        heading("Method", 2), *[paragraph(block) for block in content["method"]],
        heading("Findings", 2),
        *[node for topic, findings in content["topics"]
          for node in (heading(topic, 3), *[finding(*item, sources) for item in findings])],
        heading("Sources", 2), *[source(n, *values) for n, values in sources.items()],
        heading("Next", 2), *[paragraph(block) for block in content["next"]],
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--site", required=True, help="the Atlassian site, e.g. example.atlassian.net")
    parser.add_argument("--key", help="the key of the related work item, e.g. ABC-7")
    args = parser.parse_args()
    if args.key is not None and not KEY.match(args.key):
        print(f"key: {args.key} is not a work item key like ABC-7", file=sys.stderr)
        return 1
    found, content = problems(sys.stdin.read())
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    print(json.dumps({"title": content["title"], "body": body(content, args.site, args.key)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
