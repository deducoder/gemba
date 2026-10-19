#!/usr/bin/env python3
"""Resolves Atlassian operation names to the connector tool(s) that back them, so a skill
names the operation it needs instead of the connector tool, and loads in context only the
operations it resolves.

Usage: python3 atlassian_op.py <operation> [<operation> ...]

Reads references/atlassian.json (sibling of this script's plugin), an object keyed by
operation name, each value {tools: [{tool, tier}], params, format}. Prints one line per
operation, in the order given, with its tool(s) and tier, its key parameters and its
format. An operation not in the catalog prints that it was not found, instead of failing.
"""

import json
import sys
from pathlib import Path

CATALOG = Path(__file__).resolve().parent.parent / "references" / "atlassian.json"


def resolve(names):
    table = json.loads(CATALOG.read_text(encoding="utf-8"))
    lines = []
    for name in names:
        row = table.get(name)
        if row is None:
            lines.append(f"{name}: operación no encontrada")
            continue
        tools = "; ".join(f"{t['tool']} ({t['tier']})" for t in row["tools"])
        lines.append(f"{name} → {tools} | params: {row['params']} | format: {row['format']}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(resolve(sys.argv[1:]))
