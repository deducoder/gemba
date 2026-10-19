"""Checks the Jira mocks of the evals against the real responses saved by evals/save_response.py:
each key of a mock's JSON exists, with the same type, in the real response of its tool. Mocks
that instruct an agent (`type: agent`) or raise the tool's error (`error: true`) are left out.

An operation resolved behind executeRead, executeWrite or executeDestructive is mocked through
one shared dispatcher file (`executeRead.md`, etc.) whose body is a `{{file:fixtures/{input.name}
.json}}` template, not a literal response, plus one `fixtures/<tool>.json` per operation next to
it holding that operation's canned response. The three dispatcher files are left out of both
checks below (their stem names no tool to save a response for); their fixtures are checked the
same way a mock's body is."""

import functools
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DISPATCHERS = {"executeRead", "executeWrite", "executeDestructive"}
MOCKS = sorted(m for m in ROOT.glob("evals/**/mocks/atlassian/*.md") if m.stem not in DISPATCHERS)
FIXTURES = sorted(ROOT.glob("evals/**/mocks/atlassian/fixtures/*.json"))
RESPONSES = ROOT / "tests/fixtures/atlassian-responses"
SPEC = importlib.util.spec_from_file_location("save_response", ROOT / "evals/save_response.py")
SAVE_RESPONSE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SAVE_RESPONSE)


def split(mock):
    """Returns the frontmatter and the body of a mock."""
    return re.match(r"^---\n(.*?)\n---\n(.*)$", mock.read_text(encoding="utf-8"), re.S).groups()


def kind(value):
    return "number" if type(value) in (int, float) else type(value).__name__


def paths(value, prefix=""):
    """Maps each key path of a JSON value to its type; a list is `[]`, with the keys of all its items."""
    found = {prefix: kind(value)} if prefix else {}
    if isinstance(value, dict):
        for key, item in value.items():
            found.update(paths(item, f"{prefix}.{key}"))
    elif isinstance(value, list):
        for item in value:
            found.update(paths(item, f"{prefix}[]"))
    return found


def texts(value, personal=False):
    """Yields each text of a JSON value with whether it sits under a key of PERSONAL."""
    if isinstance(value, dict):
        for key, item in value.items():
            yield from texts(item, personal or key in SAVE_RESPONSE.PERSONAL)
    elif isinstance(value, list):
        for item in value:
            yield from texts(item, personal)
    elif isinstance(value, str):
        yield value, personal


def response(tool):
    return RESPONSES / f"{tool}.json"


@functools.cache
def real_paths(tool):
    return paths(json.loads(response(tool).read_text(encoding="utf-8")))


def entries():
    """Yields (name, tool, body, skip) for every mock and every dispatcher fixture, `skip`
    marking a mock that instructs an agent or raises an error, which carries no real body."""
    for mock in MOCKS:
        frontmatter, body = split(mock)
        skip = bool(re.search(r"^(type: agent|error: true)$", frontmatter, re.M))
        yield mock.relative_to(ROOT), mock.stem, body, skip
    for fixture in FIXTURES:
        yield fixture.relative_to(ROOT), fixture.stem, fixture.read_text(encoding="utf-8"), False


class Mocks(unittest.TestCase):
    longMessage = False

    def test_every_mocked_tool_has_a_saved_real_response(self):
        tools = {mock.stem for mock in MOCKS} | {fixture.stem for fixture in FIXTURES}
        for tool in sorted(tools):
            with self.subTest(tool=tool):
                self.assertTrue(response(tool).is_file(), f"no saved real response for {tool}")

    def test_every_key_of_a_mock_is_in_the_real_response_of_its_tool(self):
        """A tool without a saved response fails the test above, not each of its mocks."""
        for name, tool, body, skip in entries():
            if skip or not response(tool).is_file():
                continue
            with self.subTest(mock=str(name)):
                real = real_paths(tool)
                for path, type_ in paths(json.loads(body)).items():
                    self.assertIn(path, real, f"{name}: {path} is not in the real response of {tool}")
                    self.assertEqual(type_, real[path], f"{name}: {path} is a {type_} and in the real response of {tool} a {real[path]}")

    def test_saved_responses_hold_no_personal_data_or_project_key(self):
        responses = sorted(RESPONSES.glob("*.json"))
        self.assertTrue(responses, f"no saved real responses in {RESPONSES.relative_to(ROOT)}")
        for response in responses:
            with self.subTest(response=response.name):
                found = list(texts(json.loads(response.read_text(encoding="utf-8"))))
                self.assertEqual([text for text, personal in found if personal and text], [])
                text = "\n".join(text for text, _ in found)
                self.assertNotRegex(text, r"[\w.+-]+@[\w-]+\.[\w.]+")
                self.assertNotRegex(text, r"https?://\S*avatar")
                self.assertLessEqual(set(re.findall(r"(?<!\w)([A-Z][A-Z0-9]+)-\d+(?!\w)", text)), {"ABC"})


if __name__ == "__main__":
    unittest.main()
