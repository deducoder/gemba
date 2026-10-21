#!/usr/bin/env python3
"""Checks the answer to a question against the template and converts it to the live doc
that Confluence takes: the title and the body as an ADF document.

Usage: python3 research.py --site <site> [--key <KEY>] < draft.md

The draft comes on stdin: a short closed question on its first line, ending in `?`, it is
the title of the page; one sentence with the decision or doubt that prompted it and who
waits on it; a `Detail: ...?` line with the question as asked, in full; an
`Asked by: <accountId> · YYYY-MM-DD` line; then the `### Answer`, `### Method`,
`### Findings`, `### Sources` and `### Next` sections, in that order. The Answer cites the
findings it rests on as `[Finding 1.1]`. The Findings are `#### n. Topic` headings with
lines `n.m Documented|Inferred|Unverified: text`: a Documented finding ends with the number
of its source as `[n]`, an Inferred one names what it follows from as `(from n.m)` and an
Unverified one cites nothing. Each Sources line is
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

from draft import (  # noqa: E402
    CODE, FENCE, KEY, attr_esc, check_sections, dated, esc, filled, heading, inline, is_day, label, paragraph,
    paragraphs, space, split, strong, unclosed,
)

SECTIONS = ["Answer", "Method", "Findings", "Sources", "Next"]
FINDING = re.compile(r"^(\d+)\.(\d+) (\S+?): (.+)$")
STATES = ("Documented", "Inferred", "Unverified")
SOURCE = re.compile(r"^\[(\d+)\] (https?://\S+) \((official|spec|source|secondary), (\d{4}-\d{2}-\d{2})\): (.+)$")
CITE = re.compile(r"\[(\d+)\]")
FROM = re.compile(r"\(from \d+\.\d+(, \d+\.\d+)*\)\s*$")
CITED = re.compile(r"\[Finding (\d+\.\d+)\]")
TOPIC = re.compile(r"^(\d+)\. \S")
DETAIL = re.compile(r"^Detail: (.+)$")
ASKED = re.compile(r"^Asked by: ([A-Za-z0-9:_-]+) · (\d{4}-\d{2}-\d{2})$")


def intro_lines(lines, found):
    """Returns the decision sentence, the Detail text and the Asked by accountId and date, or
    None when the intro does not follow the template. The decision sentence may wrap across
    several lines; the Detail and Asked by lines may not."""
    lines = [line.strip() for line in filled(lines)]
    if len(lines) < 3:
        found.append("Detail: write the decision sentence, then a 'Detail: ...?' line and an "
                      "'Asked by: <accountId> · YYYY-MM-DD' line")
        return None
    *decision_lines, detail_line, asked_line = lines
    decision = " ".join(decision_lines)
    detail = DETAIL.match(detail_line)
    asked = ASKED.match(asked_line)
    if not detail or not detail.group(1).strip().endswith("?"):
        found.append(f"Detail: write the question as asked, in full, ending in ?: {detail_line}")
        detail = None
    if not asked:
        found.append(f"Asked by: write the accountId of who asked and the date as 'Asked by: <accountId> · YYYY-MM-DD': {asked_line}")
    elif not is_day(asked.group(2)):
        found.append(f"Asked by: {asked.group(2)} is not a date")
        asked = None
    if not detail or not asked:
        return None
    return decision, detail.group(1).strip(), asked.group(1), asked.group(2)


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
        found.append("title: write a short closed question on the first line, ending in ?")
    asked = intro_lines(intro, found)
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
    decision, detail, account, day = asked
    return found, {"title": title, "decision": decision, "detail": detail, "account": account, "day": day,
                   "answer": blocks["Answer"], "method": blocks["Method"], "topics": topics, "sources": sources,
                   "next": blocks["Next"]}


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
                out.append(f'<a href="{attr_esc(sources[int(part) - 1][0])}">[{part}]</a>')
            elif part:
                out.append(inline(part))
        parts.append("".join(out))
    return "".join(parts)


def finding(name, state, text, sources):
    return f"<p><strong>{esc(name)} {esc(state)}:</strong> {cited(text, sources)}</p>"


def source(number, url, kind, date, what):
    return f'<p>[{number}] <a href="{attr_esc(url)}" data-card-appearance="inline"></a>{inline(f" ({kind}, {date}): {what}")}</p>'


def mention(account):
    return f'<span data-type="mention" data-user-id="{attr_esc(account)}">@{esc(account)}</span>'


def body(content, site, key):
    """Returns the live doc as HTML."""
    link = f'<p><a href="https://{site}/browse/{key}" data-card-appearance="inline"></a></p>' if key else ""
    sources = content["sources"]
    return (link
            + paragraph(inline(content["decision"]))
            + label("Detail", content["detail"])
            + paragraph(strong("Asked by:") + space() + mention(content["account"]) + dated(content["day"]))
            + heading("Answer", 2) + "".join(paragraph(inline(block)) for block in content["answer"])
            + heading("Method", 2) + "".join(paragraph(inline(block)) for block in content["method"])
            + heading("Findings", 2)
            + "".join(heading(topic, 3) + "".join(finding(*item, sources) for item in findings)
                      for topic, findings in content["topics"])
            + heading("Sources", 2) + "".join(source(n, *values) for n, values in enumerate(sources, 1))
            + heading("Next", 2) + "".join(paragraph(inline(block)) for block in content["next"]))


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
