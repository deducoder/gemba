"""Checks the Jira mocks of the evals against the real responses saved by evals/save_response.py:
each key of a mock's JSON exists, with the same type, in the real response of its tool. Mocks
that instruct an agent (`type: agent`) or raise the tool's error (`error: true`) are left out."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOCKS = sorted(ROOT.glob("evals/**/mocks/atlassian/*.md"))
RESPONSES = ROOT / "tests/fixtures/atlassian-responses"


def split(mock):
    """Returns the frontmatter and the body of a mock."""
    return re.match(r"^---\n(.*?)\n---\n(.*)$", mock.read_text(encoding="utf-8"), re.S).groups()


def compared(mock):
    frontmatter, _ = split(mock)
    return not re.search(r"^(type: agent|error: true)$", frontmatter, re.M)


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


def saved(tool):
    return json.loads((RESPONSES / f"{tool}.json").read_text(encoding="utf-8"))


class Mocks(unittest.TestCase):
    longMessage = False

    def test_every_mocked_tool_has_a_saved_real_response(self):
        for tool in sorted({mock.stem for mock in MOCKS}):
            with self.subTest(tool=tool):
                self.assertTrue((RESPONSES / f"{tool}.json").is_file(), f"no saved real response for {tool}")

    def test_every_key_of_a_mock_is_in_the_real_response_of_its_tool(self):
        """A tool without a saved response fails the test above, not each of its mocks."""
        for mock in filter(compared, MOCKS):
            if not (RESPONSES / f"{mock.stem}.json").is_file():
                continue
            name = mock.relative_to(ROOT)
            with self.subTest(mock=str(name)):
                real = paths(saved(mock.stem))
                for path, type_ in paths(json.loads(split(mock)[1])).items():
                    self.assertIn(path, real, f"{name}: {path} is not in the real response of {mock.stem}")
                    self.assertEqual(type_, real[path], f"{name}: {path} is a {type_} and in the real response of {mock.stem} a {real[path]}")

    def test_saved_responses_hold_no_personal_data_or_project_key(self):
        responses = sorted(RESPONSES.glob("*.json"))
        self.assertTrue(responses, f"no saved real responses in {RESPONSES.relative_to(ROOT)}")
        for response in responses:
            with self.subTest(response=response.name):
                text = response.read_text(encoding="utf-8")
                self.assertNotRegex(text, r"[\w.+-]+@[\w-]+\.[\w.]+")
                self.assertNotRegex(text, r'"(accountId|emailAddress|displayName|avatarUrls)"')
                self.assertNotRegex(text, r"https?://\S*avatar")
                self.assertEqual({key for key in re.findall(r"\b([A-Z][A-Z0-9]+)-\d+\b", text)} - {"ABC"}, set())


if __name__ == "__main__":
    unittest.main()
