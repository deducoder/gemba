"""Saves a real response of an Atlassian tool, the one its mocks are compared against, without
the personal data of whoever captured it and with its project named ABC, as the mocks name it.

Usage: python3 evals/save_response.py <tool> <PROJECT> < response.json

It drops every `emailAddress`, `accountId`, `atlassianAccountId`, `avatarUrls`, `iconUrl` and
`self` key, at any depth, replaces each word <PROJECT> with ABC and writes the result to
tests/fixtures/atlassian-responses/<tool>.json.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DROPPED = {"emailAddress", "accountId", "atlassianAccountId", "avatarUrls", "iconUrl", "self"}


def without_personal_data(value):
    if isinstance(value, dict):
        return {k: without_personal_data(v) for k, v in value.items() if k not in DROPPED}
    if isinstance(value, list):
        return [without_personal_data(v) for v in value]
    return value


def main():
    tool, project = sys.argv[1:]
    text = json.dumps(without_personal_data(json.load(sys.stdin)), indent=2, ensure_ascii=False)
    out = ROOT / "tests/fixtures/atlassian-responses" / f"{tool}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(re.sub(rf"\b{re.escape(project)}\b", "ABC", text) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
