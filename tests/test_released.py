"""Checks version-close's script that marks the page of a product version Released: the
stamp it writes, what it keeps and what it rejects."""

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/skills/version-close/scripts/released.py"

PAGE = {"type": "doc", "version": 1, "content": [
    {"type": "paragraph", "attrs": {"localId": "p1"}, "content": [
        {"type": "status", "attrs": {"text": "Planned", "color": "neutral", "style": "bold", "localId": "s1"}},
        {"type": "text", "text": " · "},
        {"type": "date", "attrs": {"timestamp": "1795132800000", "localId": "d1"}},
    ]},
    {"type": "paragraph", "attrs": {"localId": "p2"}, "content": [{"type": "text", "text": "La meta."}]},
    {"type": "heading", "attrs": {"level": 2, "localId": "h1"}, "content": [{"type": "text", "text": "Outcome"}]},
]}


def run(payload):
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run([sys.executable, str(SCRIPT)], input=text, capture_output=True, text=True)


def released(page, day="2026-11-18"):
    result = run({"page": page, "day": day})
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def rejected(payload, *words):
    result = run(payload)
    assert result.returncode == 1, result.stdout
    assert result.stdout == ""
    for word in words:
        assert word in result.stderr, result.stderr


class Released(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = released(PAGE)
        cls.stamp = cls.doc["content"][0]["content"]

    def test_the_lozenge_is_released_in_green(self):
        self.assertEqual((self.stamp[0]["type"], self.stamp[0]["attrs"]["text"], self.stamp[0]["attrs"]["color"]), ("status", "Released", "green"))

    def test_the_date_is_the_day_of_the_release(self):
        self.assertEqual(self.stamp[1]["text"], " · ")
        self.assertEqual(self.stamp[2], {"type": "date", "attrs": {"timestamp": "1794960000000"}})

    def test_the_rest_of_the_page_stays_as_it_was(self):
        self.assertEqual(self.doc["content"][1:], PAGE["content"][1:])
        self.assertEqual(self.doc["content"][0]["attrs"], {"localId": "p1"})
        self.assertEqual({k: v for k, v in self.doc.items() if k != "content"}, {"type": "doc", "version": 1})

    def test_a_version_in_progress_is_released_too(self):
        page = copy.deepcopy(PAGE)
        page["content"][0]["content"][0]["attrs"]["text"] = "In progress"
        self.assertEqual(released(page)["content"][0]["content"][0]["attrs"]["text"], "Released")


class ReleasedRejects(unittest.TestCase):
    def test_a_version_already_released(self):
        page = copy.deepcopy(PAGE)
        page["content"][0]["content"][0]["attrs"]["text"] = "Released"
        rejected({"page": page, "day": "2026-11-18"}, "Released")

    def test_a_page_without_the_stamp(self):
        rejected({"page": {"type": "doc", "version": 1, "content": PAGE["content"][1:]}, "day": "2026-11-18"}, "Planned")

    def test_a_day_that_is_not_a_date(self):
        rejected({"page": PAGE, "day": "2026-13-40"}, "2026-13-40")

    def test_input_that_is_not_json(self):
        rejected("not json", "JSON")


if __name__ == "__main__":
    unittest.main()
