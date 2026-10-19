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

Prints {"title": ..., "body": <HTML>} as JSON when the draft follows the template.
Otherwise prints one line per problem to stderr, prints nothing to stdout and exits 1.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from draft import CODE, FENCE, KEY, check_sections, esc, heading, inline, paragraphs, split, unclosed  # noqa: E402

SECTIONS = ["Answer", "Method", "Findings", "Sources", "Next"]
FINDING = re.compile(r"^(\d+)\.(\d+) (\S+?): (.+)$")
STATES = ("Documented", "Inferred", "Unverified")
SOURCE = re.compile(r"^\[(\d+)\] (https?://\S+) \((official|spec|source|secondary), (\d{4}-\d{2}-\d{2})\): (.+)$")
CITE = re.compile(r"\[(\d+)\]")
FROM = re.compile(r"\(from \d+\.\d+(, \d+\.\d+)*\)\s*$")
CITED = re.compile(r"\[Finding (\d+\.\d+)\]")
TOPIC = re.compile(r"^(\d+)\. \S")


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
    blocks = {name: paragraphs(sections[name]) for name in ("Answer", "Method", "Next")}
    for name, paragraph_list in blocks.items():
        if not paragraph_list:
            found.append(f"{name}: write at least one paragraph")
    if [line for line in sections["Findings"] if line.strip()]:
        found.append("Findings: write each line under a '#### n. Topic' heading")

    sources = []
    for line in (line for line in sections["Sources"] if line.strip()):
        match = SOURCE.match(line)
        if not match:
            found.append(f"Sources: write each as '[n] <URL> (official|spec|source|secondary, YYYY-MM-DD): what it is': {line}")
        elif int(match.group(1)) != len(sources) + 1:
            found.append(f"Sources: number them from 1, in order: {line}")
        else:
            sources.append(match.groups()[1:])
    if not sources:
        found.append("Sources: write at least one source")
    kinds = [source[1] for source in sources]
    if "secondary" in kinds and any(kind in ("official", "spec") for kind in kinds[kinds.index("secondary"):]):
        found.append("Sources: a secondary source goes after every official and spec one")

    topics = []
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
            numbers = [int(n) for n in CITE.findall(CODE.sub("", text))]
            if state == "Unverified":
                if numbers:
                    found.append(f"Findings: {name} Unverified cites no source")
            else:
                if state == "Documented" and not numbers:
                    found.append(f"Findings: {name} Documented needs the number of its source as [n]")
                for n in numbers:
                    if not 1 <= n <= len(sources):
                        found.append(f"Findings: {name} cites the source {n}, which Sources does not have")
            if state == "Inferred":
                follows = FROM.search(text)
                if not follows:
                    found.append(f"Findings: {name} Inferred names what it follows from, ending in (from n.m)")
                known = {earlier for _, items in topics for earlier, *_ in items}
                for ref in (re.findall(r"\d+\.\d+", follows.group(0)) if follows else []):
                    if ref not in known:
                        found.append(f"Findings: {name} Inferred follows {ref}, which is not a finding before it")
            topics[-1][1].append((name, state, text))
        if not count:
            found.append(f"Findings: {topic} needs at least one finding")
    if not topics:
        found.append("Findings: write at least one '#### 1. Topic' with its findings")

    ids = {name for _, items in topics for name, *_ in items}
    cited = CITED.findall(" ".join(blocks["Answer"]))
    if not cited:
        found.append("Answer: cite at least one finding as [Finding n.m]")
    for name in cited:
        if name not in ids:
            found.append(f"Answer: cites [Finding {name}], which Findings does not have")
    if found:
        return found, None
    return found, {"title": title, "decision": decision[0], "answer": blocks["Answer"],
                   "method": blocks["Method"], "topics": topics, "sources": sources, "next": blocks["Next"]}


def paragraph(text):
    return f"<p>{inline(text)}</p>"


def cited(text, sources):
    """Returns the text with each [n] as a link to the source n, without a card."""
    parts = []
    for i, chunk in enumerate(CODE.split(text)):
        if i % 2:
            parts.append(inline(f"`{chunk}`"))
            continue
        out = []
        for j, part in enumerate(CITE.split(chunk)):
            if j % 2:
                out.append(f'<a href="{esc(sources[int(part) - 1][0])}">[{part}]</a>')
            elif part:
                out.append(inline(part))
        parts.append("".join(out))
    return "".join(parts)


def finding(name, state, text, sources):
    return f"<p><strong>{esc(name)} {esc(state)}:</strong> {cited(text, sources)}</p>"


def source(number, url, kind, date, what):
    return f'<p>[{number}] <a href="{esc(url)}" data-card-appearance="inline"></a>{inline(f" ({kind}, {date}): {what}")}</p>'


def body(content, site, key):
    """Returns the live doc as HTML."""
    link = f'<p><a href="https://{site}/browse/{key}" data-card-appearance="inline"></a></p>' if key else ""
    sources = content["sources"]
    return (link
            + paragraph(content["decision"])
            + heading("Answer", 2) + "".join(paragraph(block) for block in content["answer"])
            + heading("Method", 2) + "".join(paragraph(block) for block in content["method"])
            + heading("Findings", 2)
            + "".join(heading(topic, 3) + "".join(finding(*item, sources) for item in findings)
                      for topic, findings in content["topics"])
            + heading("Sources", 2) + "".join(source(n, *values) for n, values in enumerate(sources, 1))
            + heading("Next", 2) + "".join(paragraph(block) for block in content["next"]))


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
