"""Checks version-start's version script: what it accepts, what it rejects and the ADF it
prints for the live doc of a product version, with its Jira macro of work items."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/skills/version-start/scripts/version.py"
REQUIREMENTS = "https://example.atlassian.net/wiki/spaces/ABC/pages/1011/Requirements"

DRAFT = """Gemba v0.1.0

[Planned] · 2026-11-20

Validar que 3 equipos adoptan Gemba en un proyecto activo.

### MVP criterion

Risk validated: Value, «Los equipos no adoptan Gemba». Recorta al ciclo de una story y deja fuera los epics.

### Outcome

Si un equipo revierte cambios del agente por supuestos, entonces sigue usando Gemba, medido por proyectos activos a 4 semanas.

Baseline: 0 equipos. Target: 3 equipos.

### Requirements

* **R-01** La persona declara una story en menos de 5 minutos.
* **R-04** La persona revisa una story con `story-review`.

### Open questions

Question 2 y Question 3, ya respondidas.
"""


def run(draft, *args):
    args = args or ("--project", "ABC", "--requirements", REQUIREMENTS)
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=draft, capture_output=True, text=True)


def page(draft):
    result = run(draft)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def rejected(draft, *words, args=()):
    result = run(draft, *args)
    assert result.returncode != 0, result.stdout
    assert result.stdout == ""
    for word in words:
        assert word in result.stderr, result.stderr


def flat(node):
    return "".join(n.get("text", "") for n in node.get("content", []))


class VersionPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = page(DRAFT)
        cls.body = cls.page["body"]["content"]

    def test_the_title_is_the_version(self):
        self.assertEqual(self.page["title"], "Gemba v0.1.0")

    def test_the_sections_follow_the_version_template(self):
        self.assertEqual([flat(n) for n in self.body if n["type"] == "heading"],
                         ["MVP criterion", "Outcome", "Requirements", "Open questions", "Work items"])
        self.assertTrue(all(n["attrs"]["level"] == 2 for n in self.body if n["type"] == "heading"))

    def test_the_first_line_is_the_status_lozenge_and_the_release_date(self):
        first = self.body[0]["content"]
        self.assertEqual(first[0]["type"], "status")
        self.assertEqual(first[0]["attrs"]["text"], "Planned")
        self.assertEqual(first[-1], {"type": "date", "attrs": {"timestamp": "1795132800000"}})

    def test_the_goal_is_the_paragraph_after_it(self):
        self.assertEqual(flat(self.body[1]), "Validar que 3 equipos adoptan Gemba en un proyecto activo.")

    def test_the_mvp_criterion_starts_with_its_label(self):
        mvp = self.body[3]["content"]
        self.assertEqual(mvp[0], {"type": "text", "text": "Risk validated:", "marks": [{"type": "strong"}]})

    def test_baseline_and_target_are_labels(self):
        outcome = self.body[6]["content"]
        labels = [n["text"] for n in outcome if n.get("marks") == [{"type": "strong"}]]
        self.assertEqual(labels, ["Baseline:", "Target:"])

    def test_each_requirement_carries_its_id_in_bold(self):
        listed = [item["content"][0]["content"] for item in self.body[8]["content"]]
        self.assertEqual([entry[0]["text"] for entry in listed], ["R-01", "R-04"])
        self.assertIn({"type": "text", "text": "story-review", "marks": [{"type": "code"}]}, listed[1])

    def test_each_open_question_links_to_requirements(self):
        links = [n for n in self.body[10]["content"] if n.get("marks", [{}])[0].get("type") == "link"]
        self.assertEqual([n["text"] for n in links], ["Question 2", "Question 3"])
        self.assertEqual(links[0]["marks"][0]["attrs"]["href"], REQUIREMENTS)

    def test_work_items_is_the_jira_macro_of_the_first_level_of_the_version(self):
        macro = self.body[-1]
        self.assertEqual((macro["type"], macro["attrs"]["extensionKey"]), ("extension", "jira"))
        self.assertEqual(macro["attrs"]["extensionType"], "com.atlassian.confluence.macro.core")
        params = macro["attrs"]["parameters"]["macroParams"]
        self.assertEqual(params["jqlQuery"]["value"],
                         'project = ABC AND fixVersion = "Gemba v0.1.0" AND (issuetype = Epic OR parent is EMPTY) ORDER BY key')
        self.assertEqual(params["columns"]["value"], "type,key,summary,priority,status,duedate")


class VersionOptional(unittest.TestCase):
    def test_a_later_version_has_no_mvp_criterion(self):
        start, end = DRAFT.index("### MVP criterion"), DRAFT.index("### Outcome")
        body = page(DRAFT[:start] + DRAFT[end:].replace("Gemba v0.1.0", "Gemba v0.2.0"))["body"]["content"]
        self.assertEqual([flat(n) for n in body if n["type"] == "heading"][0], "Outcome")


class VersionRejects(unittest.TestCase):
    def test_a_title_that_is_not_a_version(self):
        rejected(DRAFT.replace("Gemba v0.1.0", "Gemba primera versión", 1), "title")

    def test_a_status_other_than_planned(self):
        rejected(DRAFT.replace("[Planned]", "[Released]"), "Planned")

    def test_a_release_date_that_is_not_a_date(self):
        rejected(DRAFT.replace("2026-11-20", "2026-11-31"), "2026-11-31")

    def test_no_goal(self):
        rejected(DRAFT.replace("Validar que 3 equipos adoptan Gemba en un proyecto activo.\n", ""), "goal")

    def test_sections_in_another_order(self):
        start, end = DRAFT.index("### Outcome"), DRAFT.index("### Requirements")
        rejected(DRAFT[:start] + DRAFT[end:] + "\n" + DRAFT[start:end], "sections")

    def test_a_work_items_section_written_by_hand(self):
        rejected(DRAFT + "\n### Work items\n\nLa tabla.\n", "Work items")

    def test_a_learned_section_at_the_start(self):
        rejected(DRAFT + "\n### Learned\n\n* Nada aún.\n", "Learned")

    def test_a_risk_kind_outside_the_list(self):
        rejected(DRAFT.replace("Risk validated: Value", "Risk validated: Market"), "MVP criterion", "Value")

    def test_an_outcome_without_baseline_and_target(self):
        rejected(DRAFT.replace("Baseline: 0 equipos. Target: 3 equipos.", ""), "Outcome", "Baseline")

    def test_a_malformed_requirement(self):
        rejected(DRAFT.replace("* **R-04** La", "* R-04 La"), "Requirements", "R-nn")

    def test_no_requirements(self):
        start, end = DRAFT.index("* **R-01**"), DRAFT.index("### Open questions")
        rejected(DRAFT[:start] + DRAFT[end:], "Requirements")

    def test_open_questions_without_a_paragraph(self):
        rejected(DRAFT.replace("Question 2 y Question 3, ya respondidas.\n", ""), "Open questions")

    def test_without_project_or_requirements_link(self):
        rejected(DRAFT, "--project", args=("--requirements", REQUIREMENTS))
        rejected(DRAFT, "--requirements", args=("--project", "ABC"))


if __name__ == "__main__":
    unittest.main()
