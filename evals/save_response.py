"""Saves a real response of an Atlassian tool, the one its mocks are compared against, without
the personal data of whoever captured it and with its project named ABC, as the mocks name it.

Usage: python3 evals/save_response.py <tool> <PROJECT> < response.json

It empties every text under the keys in PERSONAL, at any depth, keeping the keys so the response
keeps Jira's shape; it replaces with ABC, in every other text, each word <PROJECT> and the name
of the project whose `key` is <PROJECT>. It writes the result to
tests/fixtures/atlassian-responses/<tool>.json.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PERSONAL = {"emailAddress", "accountId", "atlassianAccountId", "displayName", "avatarUrls", "iconUrl", "self"}
USAGE = "Usage: python3 evals/save_response.py <tool> <PROJECT> < response.json"


def emptied(value):
    """Keeps the keys and the non-text values of a value and empties its texts."""
    if isinstance(value, dict):
        return {k: emptied(v) for k, v in value.items()}
    if isinstance(value, list):
        return [emptied(v) for v in value]
    return "" if isinstance(value, str) else value


def project_names(value, project):
    """Returns the names of the dicts whose `key` is the project's."""
    if isinstance(value, dict):
        own = {value["name"]} if value.get("key") == project and isinstance(value.get("name"), str) else set()
        return own.union(*(project_names(v, project) for v in value.values()))
    if isinstance(value, list):
        return set().union(*(project_names(v, project) for v in value))
    return set()


def anonymized(value, words):
    """Empties the personal data of a value and replaces each match of `words` with ABC in its texts."""
    if isinstance(value, dict):
        return {k: emptied(v) if k in PERSONAL else anonymized(v, words) for k, v in value.items()}
    if isinstance(value, list):
        return [anonymized(v, words) for v in value]
    return words.sub("ABC", value) if isinstance(value, str) else value


def main():
    args = sys.argv[1:]
    if len(args) != 2 or not all(re.fullmatch(r"\w+", arg) for arg in args):
        print(USAGE, file=sys.stderr)
        sys.exit(2)
    tool, project = args
    response = json.load(sys.stdin)
    names = sorted(project_names(response, project) | {project}, key=len, reverse=True)
    words = re.compile("|".join(rf"(?<!\w){re.escape(name)}(?!\w)" for name in names))
    out = ROOT / "tests/fixtures/atlassian-responses" / f"{tool}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(anonymized(response, words), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
