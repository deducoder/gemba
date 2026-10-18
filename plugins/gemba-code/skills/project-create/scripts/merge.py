#!/usr/bin/env python3
"""Merges a reviewed page into the published one: it keeps every section of the published
page as it is, nodes and local IDs included, and the heading of each replaced one, and takes from the new page only the sections
the person accepted.

Usage: python3 merge.py < input.json

The input is {"live": <published ADF>, "new": <ADF the page script printed>, "replace":
[<section>, ...]}. A section is a level two heading with everything up to the next one; the
nodes before the first heading are the section "". A replaced section the published page
lacks goes where the new page puts it.

Prints the merged ADF document as JSON. A section neither page has is printed to stderr,
with nothing on stdout and exit status 1.
"""

import json
import sys


def sections(doc):
    """Returns the sections of a document as an ordered list of (name, nodes)."""
    found = [("", [])]
    for node in doc.get("content", []):
        if node.get("type") == "heading" and node.get("attrs", {}).get("level") == 2:
            name = "".join(part.get("text", "") for part in node.get("content", []))
            found.append((name, [node]))
        else:
            found[-1][1].append(node)
    return found


def merge(live, new, replace):
    """Returns the merged document and the sections that neither page has."""
    result, fresh = sections(live), dict(sections(new))
    order = [name for name, _ in sections(new)]
    missing = [name for name in replace if name not in fresh and name not in dict(result)]
    for name in replace:
        if name not in fresh:
            continue
        names = [current for current, _ in result]
        if name in names:
            heading = result[names.index(name)][1][:1] if name else []
            result[names.index(name)] = (name, heading + fresh[name][1 if name else 0:])
            continue
        before = [earlier for earlier in order[:order.index(name)] if earlier in names]
        result.insert(names.index(before[-1]) + 1 if before else 1, (name, fresh[name]))
    return {**live, "content": [node for _, nodes in result for node in nodes]}, missing


def main():
    data = json.load(sys.stdin)
    doc, missing = merge(data["live"], data["new"], data["replace"])
    if missing:
        print("\n".join(f"replace: {name} is a section of neither page" for name in missing), file=sys.stderr)
        return 1
    print(json.dumps(doc, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
