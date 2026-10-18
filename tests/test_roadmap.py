"""Checks project-create's roadmap script: what it accepts, what it rejects and the ADF it
prints for the live doc of a product's roadmap before its first version."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/skills/project-create/scripts/roadmap.py"

DRAFT = """### Now

Ninguna versión en curso.

### Next

* **Unnumbered** Validar que 3 equipos adoptan Gemba.

### Later

* **Unnumbered** Soporte para otros trackers.
* **Unnumbered** Soporte para macOS.

### Released

Ninguna versión liberada.
"""


def run(draft):
    return subprocess.run([sys.executable, str(SCRIPT)], input=draft, capture_output=True, text=True)


def rejected(draft, *words):
    result = run(draft)
    assert result.returncode == 1, result.stdout
    assert result.stdout == ""
    for word in words:
        assert word in result.stderr, result.stderr


def flat(node):
    return "".join(n["text"] if n["type"] == "text" else "" for n in node.get("content", []))


class RoadmapDraft(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run(DRAFT)
        cls.page = json.loads(cls.result.stdout) if cls.result.returncode == 0 else {}
        cls.body = cls.page.get("body", {}).get("content", [])

    def test_a_draft_that_follows_the_template_passes(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr)

    def test_the_title_is_roadmap(self):
        self.assertEqual(self.page["title"], "Roadmap")

    def test_the_headings_are_the_four_horizons_in_order(self):
        self.assertEqual([flat(n) for n in self.body if n["type"] == "heading"], ["Now", "Next", "Later", "Released"])

    def test_now_and_released_are_a_paragraph(self):
        self.assertEqual((self.body[1]["type"], flat(self.body[1])), ("paragraph", "Ninguna versión en curso."))
        self.assertEqual(self.body[-1]["type"], "paragraph")

    def test_each_entry_is_unnumbered_in_bold_then_its_goal_on_a_new_line(self):
        entries = [item["content"][0]["content"] for n in self.body if n["type"] == "bulletList" for item in n["content"]]
        self.assertEqual(len(entries), 3)
        for entry in entries:
            self.assertEqual(entry[0], {"type": "text", "text": "Unnumbered", "marks": [{"type": "strong"}]})
            self.assertEqual(entry[1]["type"], "hardBreak")
        self.assertEqual(entries[0][2]["text"], "Validar que 3 equipos adoptan Gemba.")


class RoadmapRejects(unittest.TestCase):
    def test_sections_in_another_order(self):
        rejected(DRAFT.replace("### Next", "### Soon"), "sections")

    def test_an_entry_that_is_not_unnumbered(self):
        rejected(DRAFT.replace("* **Unnumbered** Validar", "* Gemba v0.1.0 Validar"), "Next", "Unnumbered")

    def test_now_without_its_paragraph(self):
        rejected(DRAFT.replace("Ninguna versión en curso.\n", ""), "Now")

    def test_next_without_entries(self):
        rejected(DRAFT.replace("* **Unnumbered** Validar que 3 equipos adoptan Gemba.\n", ""), "Next")


class RoadmapOptional(unittest.TestCase):
    def test_later_may_be_empty(self):
        start, end = DRAFT.index("* **Unnumbered** Soporte para otros"), DRAFT.index("### Released")
        result = run(DRAFT[:start] + DRAFT[end:])
        self.assertEqual(result.returncode, 0, result.stderr)
        body = json.loads(result.stdout)["body"]["content"]
        self.assertEqual([flat(n) for n in body if n["type"] == "heading"], ["Now", "Next", "Later", "Released"])


if __name__ == "__main__":
    unittest.main()
