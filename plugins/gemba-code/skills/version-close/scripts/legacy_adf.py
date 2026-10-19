#!/usr/bin/env python3
"""ADF node builders for the version page while it is still ADF: learned.py and released.py
both mutate that page by slicing its content list, so they share these instead of draft.py's
HTML builders. GEMBA-92 moves the page to HTML and the edits that target it by localId; once
it does, this module is removed along with its two callers' ADF-only code."""

import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from draft import CODE, STATES  # noqa: E402


def adf_inline(text):
    """Returns text as ADF text nodes, with `code` as a code mark."""
    nodes = []
    for i, part in enumerate(CODE.split(text)):
        if not part:
            continue
        nodes.append({"type": "text", "text": part, **({"marks": [{"type": "code"}]} if i % 2 else {})})
    return nodes


def adf_heading(name, level=2):
    return {"type": "heading", "attrs": {"level": level}, "content": [{"type": "text", "text": name}]}


def adf_bullets(items):
    return {"type": "bulletList", "content": [
        {"type": "listItem", "content": [{"type": "paragraph", "content": item}]} for item in items
    ]}


def adf_stamp(state, day):
    """Returns the ADF nodes of a version's lozenge, ` · ` and its release date."""
    moment = datetime.combine(date.fromisoformat(day), datetime.min.time(), tzinfo=timezone.utc)
    return [
        {"type": "status", "attrs": {"text": state, "color": STATES[state], "style": "bold"}},
        {"type": "text", "text": " · "},
        {"type": "date", "attrs": {"timestamp": str(int(moment.timestamp() * 1000))}},
    ]
