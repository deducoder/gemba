"""Checks version-close's script that writes what a released version taught on its page: the
edit it builds, where it goes and what it rejects."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/skills/version-close/scripts/learned.py"

PAGE = ('<p data-local-id="a1">'
        '<span data-local-id="a2" data-type="status" data-color="green" data-status-style="bold">Released</span>'
        ' · <time data-local-id="a3" datetime="2026-11-15">2026-11-15</time>'
        '</p>'
        '<h2 data-local-id="a4">Outcome</h2>'
        '<p data-local-id="a5">La meta.</p>'
        '<h2 data-local-id="a6">Work items</h2>'
        '<div data-local-id="a7" data-type="extension"></div>')

DRAFT = "* El conector guarda tarde: leer antes de seguir.\n* `merge.py` no inserta al final.\n"


def run(payload):
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run([sys.executable, str(SCRIPT)], input=text, capture_output=True, text=True)


def learned(page, draft=DRAFT):
    result = run({"page": page, "draft": draft})
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)["edits"]


def rejected(payload, *words):
    result = run(payload)
    assert result.returncode == 1, result.stdout
    assert result.stdout == ""
    for word in words:
        assert word in result.stderr, result.stderr
    return result


class Learned(unittest.TestCase):
    def test_a_single_append_at_the_end_with_no_localId(self):
        found = learned(PAGE)
        self.assertEqual(found, [{"name": "appendNodeToEnd",
                                   "value": "<h2>Learned</h2><ul><li><p>El conector guarda tarde: leer antes de seguir."
                                            "</p></li><li><p><code>merge.py</code> no inserta al final.</p></li></ul>"}])


class LearnedRejects(unittest.TestCase):
    def test_a_version_not_released_yet(self):
        for state in ("Planned", "In progress"):
            page = PAGE.replace(">Released<", f">{state}<")
            rejected({"page": page, "draft": DRAFT}, "release it first")

    def test_a_page_without_the_stamp(self):
        rejected({"page": "<h2>Outcome</h2>", "draft": DRAFT}, "release it first")

    def test_a_page_that_already_has_learned(self):
        page = PAGE + "<h2>Learned</h2><ul><li><p>Ya.</p></li></ul>"
        rejected({"page": page, "draft": DRAFT}, "Learned")

    def test_a_draft_without_lessons(self):
        rejected({"page": PAGE, "draft": "\n"}, "Learned")

    def test_a_line_that_is_not_a_bullet(self):
        rejected({"page": PAGE, "draft": "* Una.\nOtra suelta.\n"}, "Otra suelta.")

    def test_a_draft_with_headings_or_code_blocks(self):
        rejected({"page": PAGE, "draft": "### Learned\n* Una.\n"}, "### Learned")
        rejected({"page": PAGE, "draft": "```\n* Una.\n```\n"}, "code")

    def test_a_page_that_is_not_a_string(self):
        result = rejected({"page": {"not": "a string"}, "draft": DRAFT}, "input")
        self.assertNotIn("Traceback", result.stderr)

    def test_a_draft_that_is_not_a_string(self):
        result = rejected({"page": PAGE, "draft": ["x"]}, "input")
        self.assertNotIn("Traceback", result.stderr)

    def test_input_that_is_not_json(self):
        rejected("not json", "JSON")


if __name__ == "__main__":
    unittest.main()
