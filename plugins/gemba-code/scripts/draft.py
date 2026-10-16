"""What the draft scripts of every work item type share: the checks of the Summary,
the == marks and the Out of scope arrows, and the conversion of their lines to ADF
for Jira. `code` becomes a code mark, a Done when criterion wrapped in `==` turns
orange, and a work item key after `→` becomes a link to the issue on the site."""

import re

ORANGE = {"type": "textColor", "attrs": {"color": "#ff991f"}}
KEY = re.compile(r"^[A-Z][A-Z0-9_]+-\d+$")
CODE = re.compile(r"`([^`]+)`")


def prose(line):
    """Returns a line without its `code`, where == and → are literal."""
    return CODE.sub("", line)


def check_summary(summary, found):
    if not summary or len(summary) > 64:
        found.append("Summary: write it on the first line, 64 characters at most")
    elif summary.endswith(".") or not summary[0].isupper():
        found.append("Summary: sentence case, with no final period")


def check_unmarked(name, text, found):
    """Reports == in a text that only Done when criteria may carry."""
    if "==" in prose(text):
        found.append(f"{name}: only Done when criteria are wrapped in ==")


def check_criteria(criteria, found):
    for line in criteria:
        wrapped = line.startswith("==") and line.endswith("==") and len(line) > 4
        inner = line[2:-2] if wrapped else line
        if "==" in prose(inner):
            found.append(f"Done when: wrap the whole criterion in ==, or none of it: {line}")
        elif wrapped and not prose(inner).strip():
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
    if line.startswith("==") and line.endswith("==") and len(line) > 4:
        return inline(line[2:-2], [ORANGE])
    return inline(line)


def excluded(line, site):
    if "→" not in prose(line):
        return inline(line)
    what, key = (part.strip() for part in line.rsplit("→", 1))
    return inline(f"{what} → ") + [{"type": "inlineCard", "attrs": {"url": f"https://{site}/browse/{key}"}}]


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
