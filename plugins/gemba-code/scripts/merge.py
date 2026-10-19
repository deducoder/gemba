#!/usr/bin/env python3
"""Builds the `edits` that merge a reviewed page into the published one: it keeps every
section of the published page as it is, nodes and local IDs included, and takes from the
new page only the sections the person accepted.

Usage: python3 merge.py < input.json

The input is {"live": <published HTML>, "new": <HTML the page script printed>, "replace":
[<section>, ...]}. A section is a level two heading with everything up to the next one; the
nodes before the first heading are the section "". A replaced section the published page
lacks goes where the new page puts it, and one the new page lacks is removed.

Prints {"edits": [<the updateConfluenceContent edits by localId>, ...]} as JSON. A section
neither page has is printed to stderr, with nothing on stdout and exit status 1.
"""

import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from published import sections  # noqa: E402


def first_node(live):
    """Returns the localId of the very first node of the page, heading or body."""
    for _, heading_id, _, body in live:
        if heading_id:
            return heading_id
        if body:
            return body[0][0]
    return None


def anchor(order, names, live, index):
    """Returns the localId to `insertNodeAfter`: the last node of the nearest earlier
    section both pages share, or None when none of them has one to anchor on."""
    for earlier in reversed(order[:index]):
        if earlier in names:
            _, heading_id, _, body = live[names.index(earlier)]
            return (body[-1][0] if body else heading_id) or None
    return None


def edits(live_html, new_html, replace):
    """Returns the edits that replace only the accepted sections, and the sections that
    neither page has."""
    live, new = sections(live_html), sections(new_html)
    names = [name for name, _, _, _ in live]
    order = [name for name, _, _, _ in new]
    found, missing = [], []
    for name in replace:
        if name not in order:
            if name not in names:
                missing.append(name)
                continue
            _, heading_id, _, body = live[names.index(name)]
            if heading_id:
                found.append({"name": "deleteNode", "localId": heading_id})
            found += [{"name": "deleteNode", "localId": local} for local, _ in body]
            continue
        _, _, new_heading, new_body = new[order.index(name)]
        value = (new_heading or "") + "".join(raw for _, raw in new_body)
        if name in names:
            _, heading_id, _, body = live[names.index(name)]
            if heading_id:
                found.append({"name": "replaceNode", "localId": heading_id, "value": value})
                found += [{"name": "deleteNode", "localId": local} for local, _ in body]
            elif body:
                found.append({"name": "replaceNode", "localId": body[0][0], "value": value})
                found += [{"name": "deleteNode", "localId": local} for local, _ in body[1:]]
            else:
                found.append({"name": "insertNodeBefore", "localId": first_node(live), "value": value})
            continue
        target = anchor(order, names, live, order.index(name))
        if target:
            found.append({"name": "insertNodeAfter", "localId": target, "value": value})
        else:
            found.append({"name": "insertNodeBefore", "localId": first_node(live), "value": value})
    return found, missing


def main():
    data = json.load(sys.stdin)
    found, missing = edits(data["live"], data["new"], data["replace"])
    if missing:
        print("\n".join(f"replace: {name} is a section of neither page" for name in missing), file=sys.stderr)
        return 1
    print(json.dumps({"edits": found}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
