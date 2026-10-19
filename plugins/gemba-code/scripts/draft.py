"""What the draft scripts of every work item type share: splitting the draft into its
sections, the checks of the Summary, the bullets, the == marks, the evidence lines
and the Out of scope arrows, and the conversion of their lines to HTML for the
Atlassian connector. `code` becomes a `<code>` span, a Done when criterion wrapped in
`==` turns orange, and a work item key after `→` becomes a smart link to the issue on
the site."""

import html as html_lib
import re
from datetime import date

ORANGE = ('<span style="color: #ff991f">', "</span>")
GREY = ('<span style="color: #97a0af">', "</span>")
STRIKE = ("<s>", "</s>")
STRONG = ("<strong>", "</strong>")
KEY = re.compile(r"^[A-Z][A-Z0-9_]+-\d+$")
CODE = re.compile(r"`([^`]+)`")
HEADING = re.compile(r"^(#{3,4}) (.+?)\s*$")
FENCE = re.compile(r"^(`{3,}|~{3,})")
TRAIL = ("ran:", "read:")
VERSION_NAME = r".+ v\d+\.\d+\.\d+"
STATES = {"Planned": "neutral", "In progress": "blue", "Released": "green"}
CURRENT = ("Planned", "In progress")
BASELINE = re.compile(r"^Baseline: (.+?) Target: (.+)$")


def esc(text):
    return html_lib.escape(text, quote=False)


def attr_esc(text):
    """Escapes text for an HTML attribute value, where esc() alone would let a `"` in the
    text close the attribute early."""
    return html_lib.escape(text, quote=True)


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
    """Returns text as HTML, with `code` as a `<code>` span and no other mark on it; the
    other runs carry each mark in order, innermost first."""
    parts = []
    for i, part in enumerate(CODE.split(text)):
        if not part:
            continue
        if i % 2:
            parts.append(f"<code>{esc(part)}</code>")
        else:
            run = esc(part)
            for open_tag, close_tag in marks:
                run = f"{open_tag}{run}{close_tag}"
            parts.append(run)
    return "".join(parts)


def linked(text, url):
    """Returns the text as HTML, with each `Question n` outside code linking to the
    Requirements page."""
    if not url:
        return inline(text)
    parts = []
    for i, chunk in enumerate(CODE.split(text)):
        if i % 2:
            parts.append(inline(f"`{chunk}`"))
            continue
        for j, part in enumerate(re.split(r"(Question \d+)", chunk)):
            if j % 2:
                parts.append(f'<a href="{attr_esc(url)}">{esc(part)}</a>')
            elif part:
                parts.append(inline(part))
    return "".join(parts)


def criterion(line):
    return inline(line[2:-2], (ORANGE,)) if wrapped(line) else inline(line)


def excluded(line, site):
    if "→" not in prose(line):
        return inline(line)
    what, key = (part.strip() for part in line.rsplit("→", 1))
    return inline(f"{what} → ") + f'<a href="https://{site}/browse/{key}" data-card-appearance="inline"></a>'


def strong(text):
    return f"<strong>{esc(text)}</strong>"


def space():
    return " "


def status(text, color):
    """Returns a lozenge."""
    return f'<span data-type="status" data-color="{color}">{esc(text)}</span>'


def date_node(day):
    """Returns a YYYY-MM-DD day as a date node."""
    date.fromisoformat(day)
    return f'<time datetime="{day}">{day}</time>'


def heading(name, level=3):
    return f"<h{level}>{esc(name)}</h{level}>"


def bullets(items):
    return "<ul>" + "".join(f"<li><p>{item}</p></li>" for item in items) + "</ul>"


def section(name, items):
    return heading(name) + bullets(items)


DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_day(day):
    """Tells whether a text is a day written YYYY-MM-DD, the only ISO form the templates take."""
    if not isinstance(day, str) or not DAY.match(day):
        return False
    try:
        date.fromisoformat(day)
    except ValueError:
        return False
    return True


def paragraph(*content):
    return f"<p>{''.join(content)}</p>"


def label(name, text):
    """Returns a paragraph with the label in bold, then its text."""
    return paragraph(strong(f"{name}:"), space(), inline(text))


def dated(day):
    """Returns ` · ` and the day as a date node."""
    return " · " + date_node(day)


def stamp(state, day):
    """Returns the lozenge of a version state, ` · ` and its release date."""
    return status(state, STATES[state]) + dated(day)
