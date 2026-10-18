"""What the draft scripts of every work item type share: splitting the draft into its
sections, the checks of the Summary, the bullets, the == marks, the evidence lines
and the Out of scope arrows, and the conversion of their lines to ADF for Jira.
`code` becomes a code mark, a Done when criterion wrapped in `==` turns orange, and
a work item key after `→` becomes a link to the issue on the site."""

import re

ORANGE = {"type": "textColor", "attrs": {"color": "#ff991f"}}
KEY = re.compile(r"^[A-Z][A-Z0-9_]+-\d+$")
CODE = re.compile(r"`([^`]+)`")
HEADING = re.compile(r"^(#{3,4}) (.+?)\s*$")
FENCE = re.compile(r"^(`{3,}|~{3,})")
TRAIL = ("ran:", "read:")


def split(text, titled=True):
    """Returns the Summary, the lines before the first `###` section, the lines of each
    section, the lines of each `####` subsection keyed by (section, subsection) and the
    headings written twice. A heading inside a fenced block is part of the block. A draft
    that is not titled has no Summary line: it is returned empty."""
    lines = text.strip("\n").splitlines()
    summary = lines[0].strip() if lines and titled else ""
    intro, sections, subsections, repeated = [], {}, {}, []
    target, current, fence = intro, None, None
    for line in lines[1:] if titled else lines:
        heading = HEADING.match(line) if fence is None else None
        if heading and len(heading.group(1)) == 3:
            current = heading.group(2)
            if current in sections:
                repeated.append(current)
            target = sections.setdefault(current, [])
            continue
        if heading and current is not None:
            key = (current, heading.group(2))
            if key in subsections:
                repeated.append(" ".join(key))
            target = subsections.setdefault(key, [])
            continue
        opener = FENCE.match(line)
        if fence is None and opener:
            fence = opener.group(1)
        elif fence is not None and line.strip() == fence:
            fence = None
        target.append(line)
    return summary, intro, sections, subsections, repeated


def unclosed(text):
    """Returns the fence that a fenced block opened and never closed, or None."""
    fence = None
    for line in text.splitlines():
        opener = FENCE.match(line)
        if fence is None and opener:
            fence = opener.group(1)
        elif fence is not None and line.strip() == fence:
            fence = None
    return fence


def filled(lines):
    return [line for line in lines if line.strip()]


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


def prose(line):
    """Returns a line without its `code`, where == and → are literal."""
    return CODE.sub("", line)


def wrapped(line):
    """Tells whether a Done when criterion is wrapped in == as deduced."""
    return line.startswith("==") and line.endswith("==") and len(line) > 4


def check_summary(summary, found):
    if not summary or len(summary) > 64:
        found.append("Summary: write it on the first line, 64 characters at most")
    elif summary.endswith(".") or not summary[0].isupper():
        found.append("Summary: sentence case, with no final period")


def check_sections(sections, expected, repeated, found):
    """Reports the headings written twice; returns whether the sections are the expected ones, in order."""
    for name in repeated:
        found.append(f"{name}: write the section once")
    if list(sections) != expected:
        found.append(f"sections: expected {', '.join(expected)}, in that order; found {', '.join(sections) or 'none'}")
        return False
    return True


def items(name, lines, found, optional=False):
    """Returns the bullets of a section and reports the lines that are not bullets, and an
    empty section unless it is optional."""
    lines = filled(lines)
    if not lines and not optional:
        found.append(f"{name}: write at least one item")
    bullets = []
    for line in lines:
        if line.strip() == "*":
            found.append(f"{name}: remove the empty bullet")
        elif line.startswith("* "):
            bullets.append(line[2:].strip())
        else:
            found.append(f"{name}: write each item as a '* ' bullet on one line: {line.strip()}")
    return bullets


def check_unmarked(name, text, found):
    """Reports == in a text that only Done when criteria may carry."""
    if "==" in prose(text):
        found.append(f"{name}: only Done when criteria are wrapped in ==: {text}")


def check_trail(name, lines, found):
    for line in lines:
        if not line.startswith(TRAIL):
            found.append(f"{name}: start each line with 'ran:' or 'read:': {line}")


def check_criteria(criteria, found):
    for line in criteria:
        inner = line[2:-2] if wrapped(line) else line
        if "==" in prose(inner):
            found.append(f"Done when: wrap the whole criterion in ==, or none of it: {line}")
        elif wrapped(line) and not prose(inner).strip():
            found.append(f"Done when: a deduced criterion needs words outside `code` to show in orange: {line}")


def check_scope(scope, found):
    for line in scope:
        if "→" in prose(line) and not KEY.match(line.rsplit("→", 1)[1].strip()):
            found.append(f"Out of scope: keep the arrow only for the key of an existing work item: {line}")


def inline(text, marks=()):
    """Splits text into ADF text nodes, with `code` as a code mark and no other mark on it."""
    nodes = []
    for i, part in enumerate(CODE.split(text)):
        if not part:
            continue
        if i % 2:
            nodes.append({"type": "text", "text": part, "marks": [{"type": "code"}]})
        else:
            nodes.append({"type": "text", "text": part, **({"marks": list(marks)} if marks else {})})
    return nodes


def criterion(line):
    return inline(line[2:-2], [ORANGE]) if wrapped(line) else inline(line)


def excluded(line, site):
    if "→" not in prose(line):
        return inline(line)
    what, key = (part.strip() for part in line.rsplit("→", 1))
    return inline(f"{what} → ") + [{"type": "inlineCard", "attrs": {"url": f"https://{site}/browse/{key}"}}]


def strong(text):
    return {"type": "text", "text": text, "marks": [{"type": "strong"}]}


def space():
    return {"type": "text", "text": " "}


def status(text, color):
    """Returns a lozenge."""
    return {"type": "status", "attrs": {"text": text, "color": color, "style": "bold"}}


def heading(name, level=3):
    return {"type": "heading", "attrs": {"level": level}, "content": [{"type": "text", "text": name}]}


def bullets(items):
    return {"type": "bulletList", "content": [
        {"type": "listItem", "content": [{"type": "paragraph", "content": item}]} for item in items
    ]}


def section(name, items):
    return [heading(name), bullets(items)]


def doc(content):
    return {"type": "doc", "version": 1, "content": content}
