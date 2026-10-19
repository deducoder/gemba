"""Checks version-close's script that marks the page of a product version Released: the
edit it builds for the stamp, what it keeps and what it rejects."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/skills/version-close/scripts/released.py"

PAGE = ('<p data-local-id="a1">'
        '<span data-local-id="a2" data-type="status" data-color="neutral" data-status-style="bold">Planned</span>'
        ' · <time data-local-id="a3" datetime="2026-11-15">2026-11-15</time>'
        '</p>'
        '<p data-local-id="a4">La meta.</p>'
        '<h2 data-local-id="a5">Outcome</h2>')


def run(payload):
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run([sys.executable, str(SCRIPT)], input=text, capture_output=True, text=True)


def released(page, day="2026-11-18"):
    result = run({"page": page, "day": day})
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)["edits"]


def rejected(payload, *words):
    result = run(payload)
    assert result.returncode == 1, result.stdout
    assert result.stdout == ""
    for word in words:
        assert word in result.stderr, result.stderr
    return result


class Released(unittest.TestCase):
    def test_the_whole_first_paragraph_is_replaced_by_its_own_localId(self):
        found = released(PAGE)
        self.assertEqual(found, [{"name": "replaceNode", "localId": "a1",
                                   "value": '<p><span data-type="status" data-color="green">Released</span>'
                                            ' · <time datetime="2026-11-18">2026-11-18</time></p>'}])

    def test_the_rest_of_the_page_is_not_touched(self):
        self.assertEqual(len(released(PAGE)), 1)

    def test_text_after_the_date_stays(self):
        page = PAGE.replace('</time></p>', "</time> (movida del 15)</p>", 1)
        found = released(page)
        self.assertTrue(found[0]["value"].endswith(" (movida del 15)</p>"), found[0]["value"])

    def test_a_version_in_progress_is_released_too(self):
        page = PAGE.replace(">Planned<", ">In progress<")
        self.assertIn('>Released<', released(page)[0]["value"])


class ReleasedRejects(unittest.TestCase):
    def test_a_version_already_released(self):
        page = PAGE.replace(">Planned<", ">Released<")
        rejected({"page": page, "day": "2026-11-18"}, "Released")

    def test_a_page_without_the_stamp(self):
        rejected({"page": '<p data-local-id="a6">La meta.</p>', "day": "2026-11-18"}, "stamp")

    def test_an_empty_page(self):
        rejected({"page": "", "day": "2026-11-18"}, "stamp")

    def test_a_page_whose_first_paragraph_is_not_a_stamp(self):
        page = '<p data-local-id="a6">La meta.</p>' + PAGE
        rejected({"page": page, "day": "2026-11-18"}, "stamp")

    def test_a_day_that_is_not_a_date(self):
        rejected({"page": PAGE, "day": "2026-13-40"}, "2026-13-40")

    def test_a_page_that_is_not_a_string(self):
        result = rejected({"page": {"not": "a string"}, "day": "2026-11-18"}, "input")
        self.assertNotIn("Traceback", result.stderr)

    def test_input_that_is_not_json(self):
        rejected("not json", "JSON")


if __name__ == "__main__":
    unittest.main()
