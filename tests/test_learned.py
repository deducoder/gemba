"""Checks version-close's script that writes what a released version taught on its page: where
Learned goes, what it keeps and what it rejects."""

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/skills/version-close/scripts/learned.py"

PAGE = {"type": "doc", "version": 1, "content": [
    {"type": "paragraph", "attrs": {"localId": "p1"}, "content": [
        {"type": "status", "attrs": {"text": "Released", "color": "green", "style": "bold", "localId": "s1"}},
        {"type": "text", "text": " · "},
        {"type": "date", "attrs": {"timestamp": "1794960000000", "localId": "d1"}},
    ]},
    {"type": "heading", "attrs": {"level": 2, "localId": "h1"}, "content": [{"type": "text", "text": "Outcome"}]},
    {"type": "paragraph", "attrs": {"localId": "p2"}, "content": [{"type": "text", "text": "La meta."}]},
    {"type": "heading", "attrs": {"level": 2, "localId": "h2"}, "content": [{"type": "text", "text": "Work items"}]},
    {"type": "extension", "attrs": {"extensionKey": "jira", "localId": "e1"}},
]}

DRAFT = "* El conector guarda tarde: leer antes de seguir.\n* `merge.py` no inserta al final.\n"


def run(payload):
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run([sys.executable, str(SCRIPT)], input=text, capture_output=True, text=True)


def learned(page, draft=DRAFT):
    result = run({"page": page, "draft": draft})
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def rejected(payload, *words):
    result = run(payload)
    assert result.returncode == 1, result.stdout
    assert result.stdout == ""
    for word in words:
        assert word in result.stderr, result.stderr
    return result


def flat(node):
    return "".join(n.get("text", "") for n in node.get("content", []))


class Learned(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = learned(PAGE)
        cls.added = cls.doc["content"][len(PAGE["content"]):]

    def test_learned_is_a_level_two_heading_after_work_items(self):
        heading = self.added[0]
        self.assertEqual((heading["type"], heading["attrs"]["level"], flat(heading)), ("heading", 2, "Learned"))

    def test_each_lesson_is_a_bullet(self):
        self.assertEqual(len(self.added), 2)
        items = self.added[1]["content"]
        self.assertEqual(self.added[1]["type"], "bulletList")
        self.assertEqual([flat(item["content"][0]) for item in items],
                         ["El conector guarda tarde: leer antes de seguir.", "merge.py no inserta al final."])

    def test_code_keeps_its_mark(self):
        first = self.added[1]["content"][1]["content"][0]["content"][0]
        self.assertEqual(first, {"type": "text", "text": "merge.py", "marks": [{"type": "code"}]})

    def test_the_rest_of_the_page_stays_as_it_was(self):
        self.assertEqual(self.doc["content"][:len(PAGE["content"])], PAGE["content"])
        self.assertEqual({k: v for k, v in self.doc.items() if k != "content"}, {"type": "doc", "version": 1})


class LearnedRejects(unittest.TestCase):
    def test_a_version_not_released_yet(self):
        for state in ("Planned", "In progress"):
            page = copy.deepcopy(PAGE)
            page["content"][0]["content"][0]["attrs"]["text"] = state
            rejected({"page": page, "draft": DRAFT}, "release it first")

    def test_a_page_without_the_stamp(self):
        page = {"type": "doc", "version": 1, "content": PAGE["content"][1:]}
        rejected({"page": page, "draft": DRAFT}, "release it first")

    def test_a_page_that_already_has_learned(self):
        page = Learned.doc
        rejected({"page": page, "draft": DRAFT}, "Learned")

    def test_a_draft_without_lessons(self):
        rejected({"page": PAGE, "draft": "\n"}, "Learned")

    def test_a_line_that_is_not_a_bullet(self):
        rejected({"page": PAGE, "draft": "* Una.\nOtra suelta.\n"}, "Otra suelta.")

    def test_a_draft_with_headings_or_code_blocks(self):
        rejected({"page": PAGE, "draft": "### Learned\n* Una.\n"}, "### Learned")
        rejected({"page": PAGE, "draft": "```\n* Una.\n```\n"}, "code")

    def test_a_page_that_is_not_an_adf_object(self):
        result = rejected({"page": json.dumps(PAGE), "draft": DRAFT}, "input")
        self.assertNotIn("Traceback", result.stderr)

    def test_input_that_is_not_json(self):
        rejected("not json", "JSON")


if __name__ == "__main__":
    unittest.main()
