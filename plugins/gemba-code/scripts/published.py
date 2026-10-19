#!/usr/bin/env python3
"""Splits an already-published page's HTML into its top-level sibling nodes and, from them,
its level-two sections, each node keeping the `data-local-id` the connector gave it."""

import re

VOID = {"br", "hr", "img", "input", "meta", "link"}
OPEN_TAG = re.compile(r'<(\w+)((?:\s+[\w:-]+="[^"]*")*)\s*/?>')
WHITESPACE = re.compile(r"\s+")
LOCAL_ID = re.compile(r'data-local-id="([0-9a-fA-F-]+)"')
TAGS = re.compile(r"<[^>]+>")


def top_level_nodes(html):
    """Returns the top-level sibling nodes of a page's HTML as (localId or None, raw html,
    tag name), each raw html including its nested content whole. Whitespace between
    siblings is skipped, not kept as a node of its own."""
    nodes, pos, length = [], 0, len(html)
    while pos < length:
        gap = WHITESPACE.match(html, pos)
        if gap:
            pos = gap.end()
            continue
        opener = OPEN_TAG.match(html, pos)
        tag, attrs = opener.group(1), opener.group(2)
        if tag in VOID:
            end = opener.end()
        else:
            opens = re.compile(rf"<{tag}(?=[ >])")
            closes = re.compile(rf"</{tag}>")
            depth, cursor = 1, opener.end()
            while depth:
                next_open, next_close = opens.search(html, cursor), closes.search(html, cursor)
                if next_close and (not next_open or next_close.start() < next_open.start()):
                    depth, cursor = depth - 1, next_close.end()
                else:
                    depth, cursor = depth + 1, next_open.end()
            end = cursor
        local = LOCAL_ID.search(attrs)
        nodes.append((local.group(1) if local else None, html[pos:end], tag))
        pos = end
    return nodes


def sections(html):
    """Returns the sections of a page's HTML as an ordered list of (name, headingLocalId,
    headingRaw, body), body a list of (localId, raw html); the heading-less section "" is
    always first and its headingLocalId and headingRaw are None."""
    found = [("", None, None, [])]
    for local, raw, tag in top_level_nodes(html):
        if tag == "h2":
            found.append((TAGS.sub("", raw), local, raw, []))
        else:
            found[-1][3].append((local, raw))
    return found
