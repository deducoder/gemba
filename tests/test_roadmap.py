"""Checks project-create's roadmap script: what it accepts, what it rejects and the ADF it
prints for the live doc of a product's roadmap before its first version."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/scripts/roadmap.py"

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


def page(draft):
    result = run(draft)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)["body"]["content"]


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


VERSION = "* [Gemba v0.1.0](https://example.atlassian.net/wiki/x/abc) [Planned] · 2026-11-20 Validar que 3 equipos adoptan Gemba. Target: 3 equipos activos a 4 semanas."

PLANNED = DRAFT.replace("Ninguna versión en curso.", VERSION).replace(
    "* **Unnumbered** Validar que 3 equipos adoptan Gemba.\n", "")


class RoadmapVersionInProgress(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.body = page(PLANNED)
        cls.entry = cls.body[1]["content"][0]["content"][0]["content"]

    def test_now_holds_the_version_as_an_entry(self):
        self.assertEqual(self.body[1]["type"], "bulletList")

    def test_the_entry_links_to_the_version_page(self):
        self.assertEqual(self.entry[0]["text"], "Gemba v0.1.0")
        self.assertEqual(self.entry[0]["marks"], [{"type": "link", "attrs": {"href": "https://example.atlassian.net/wiki/x/abc"}}])

    def test_the_entry_carries_its_status_as_a_lozenge_and_its_release_date_as_a_date(self):
        kinds = [node["type"] for node in self.entry]
        self.assertIn("status", kinds)
        self.assertEqual(next(n for n in self.entry if n["type"] == "status")["attrs"]["text"], "Planned")
        self.assertEqual(next(n for n in self.entry if n["type"] == "date")["attrs"]["timestamp"], "1795132800000")

    def test_the_goal_and_its_target_go_on_their_own_lines(self):
        breaks = [i for i, node in enumerate(self.entry) if node["type"] == "hardBreak"]
        self.assertEqual(len(breaks), 2)
        self.assertEqual(self.entry[breaks[0] + 1]["text"], "Validar que 3 equipos adoptan Gemba.")
        self.assertEqual(self.entry[breaks[1] + 1], {"type": "text", "text": "Target:", "marks": [{"type": "strong"}]})
        self.assertEqual(self.entry[-1]["text"], "3 equipos activos a 4 semanas.")

    def test_next_may_be_empty_once_its_entry_is_the_version(self):
        self.assertEqual([flat(n) for n in self.body if n["type"] == "heading"], ["Now", "Next", "Later", "Released"])
        self.assertEqual(self.body[3]["type"], "heading")

    def test_a_released_version_is_not_in_now(self):
        rejected(PLANNED.replace("[Planned]", "[Released]"), "Now", "Released")

    def test_a_release_date_in_another_iso_form(self):
        rejected(PLANNED.replace("2026-11-20", "20261120"), "Now", "20261120")

    def test_a_status_outside_the_list(self):
        rejected(PLANNED.replace("[Planned]", "[Soon]"), "Now", "Planned")

    def test_a_release_date_that_is_not_a_date(self):
        rejected(PLANNED.replace("2026-11-20", "2026-13-40"), "Now", "2026-13-40")

    def test_a_version_without_target(self):
        rejected(PLANNED.replace(" Target: 3 equipos activos a 4 semanas.", ""), "Now", "Target")

    def test_a_version_without_its_link(self):
        rejected(PLANNED.replace("[Gemba v0.1.0](https://example.atlassian.net/wiki/x/abc)", "Gemba v0.1.0"), "Now")


RELEASED_ENTRY = "* [Gemba v0.1.0](https://example.atlassian.net/wiki/x/abc) [Released] Validar que 3 equipos adoptan Gemba. Target: 3 equipos activos a 4 semanas."

RELEASED = DRAFT.replace("Ninguna versión liberada.", RELEASED_ENTRY + "\n" + RELEASED_ENTRY.replace("v0.1.0", "v0.0.1"))


class RoadmapReleasedVersions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.body = page(RELEASED)
        cls.items = cls.body[-1]["content"]
        cls.entry = cls.items[0]["content"][0]["content"]

    def test_released_holds_each_version_as_an_entry_in_its_order(self):
        self.assertEqual(self.body[-1]["type"], "bulletList")
        self.assertEqual([item["content"][0]["content"][0]["text"] for item in self.items], ["Gemba v0.1.0", "Gemba v0.0.1"])

    def test_the_entry_links_to_the_version_page(self):
        self.assertEqual(self.entry[0]["marks"], [{"type": "link", "attrs": {"href": "https://example.atlassian.net/wiki/x/abc"}}])

    def test_the_entry_carries_the_released_lozenge_and_no_date(self):
        lozenges = [n["attrs"] for n in self.entry if n["type"] == "status"]
        self.assertEqual([(s["text"], s["color"]) for s in lozenges], [("Released", "green")])
        self.assertNotIn("date", [n["type"] for n in self.entry])

    def test_the_goal_and_its_target_go_on_their_own_lines(self):
        breaks = [i for i, node in enumerate(self.entry) if node["type"] == "hardBreak"]
        self.assertEqual(len(breaks), 2)
        self.assertEqual(self.entry[breaks[0] + 1]["text"], "Validar que 3 equipos adoptan Gemba.")
        self.assertEqual(self.entry[breaks[1] + 1], {"type": "text", "text": "Target:", "marks": [{"type": "strong"}]})

    def test_a_version_in_progress_is_not_in_released(self):
        rejected(RELEASED.replace("[Released]", "[Planned]", 1), "Released", "Planned")

    def test_a_released_version_without_target(self):
        rejected(RELEASED.replace(" Target: 3 equipos activos a 4 semanas.", "", 1), "Released", "Target")

    def test_a_released_entry_that_is_not_a_version(self):
        rejected(RELEASED.replace(RELEASED_ENTRY, "* **Unnumbered** algo", 1), "Released")

    def test_a_version_moves_from_now_to_released(self):
        moved = PLANNED.replace("Ninguna versión liberada.", RELEASED_ENTRY.replace("v0.1.0", "v0.0.1"))
        self.assertEqual(page(moved)[-1]["type"], "bulletList")


class RoadmapOptional(unittest.TestCase):
    def test_later_may_be_empty(self):
        start, end = DRAFT.index("* **Unnumbered** Soporte para otros"), DRAFT.index("### Released")
        body = page(DRAFT[:start] + DRAFT[end:])
        self.assertEqual([flat(n) for n in body if n["type"] == "heading"], ["Now", "Next", "Later", "Released"])


if __name__ == "__main__":
    unittest.main()
