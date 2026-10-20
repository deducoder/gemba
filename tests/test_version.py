"""Checks version-start's version script: what it accepts, what it rejects and the HTML it
prints for the live doc of a product version, with its Jira macro of work items."""

import json
import re
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


SITE = "example.atlassian.net"
CLOUD_ID = "60bceecb-ff67-4e42-ad74-e1b4da07354e"
LATER = ("--project", "ABC", "--site", SITE, "--cloud-id", CLOUD_ID, "--requirements", REQUIREMENTS)
FIRST = LATER + ("--first",)


def run(draft, *args):
    args = args or FIRST
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=draft, capture_output=True, text=True)


def page(draft, *args):
    result = run(draft, *args)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def rejected(draft, *words, args=()):
    result = run(draft, *args)
    assert result.returncode != 0, result.stdout
    assert result.stdout == ""
    for word in words:
        assert word in result.stderr, result.stderr


def flat(html):
    return re.sub(r"<[^>]+>", "", html)


def headings(body, level=2):
    return re.findall(rf"<h{level}>(.+?)</h{level}>", body)


def section(body, title):
    """Returns the raw HTML right after the <h2>title</h2> heading, up to the next heading."""
    match = re.search(rf"<h2>{re.escape(title)}</h2>(.*?)(?=<h2>|$)", body, re.DOTALL)
    return match.group(1)


def items(section_html):
    return re.findall(r"<li><p>(.*?)</p></li>", section_html, re.DOTALL)


class VersionPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = page(DRAFT)
        cls.body = cls.page["body"]

    def test_the_title_is_the_version(self):
        self.assertEqual(self.page["title"], "Gemba v0.1.0")

    def test_the_sections_follow_the_version_template(self):
        self.assertEqual(headings(self.body), ["MVP criterion", "Outcome", "Requirements", "Open questions", "Work items"])

    def test_the_first_line_is_the_status_lozenge_and_the_release_date(self):
        first = re.match(r"<p>(.*?)</p>", self.body).group(1)
        self.assertTrue(first.startswith('<span data-type="status" data-color="neutral">Planned</span>'))
        self.assertTrue(first.endswith('<time datetime="2026-11-20">2026-11-20</time>'))

    def test_the_goal_is_the_paragraph_after_it(self):
        self.assertIn("<p>Validar que 3 equipos adoptan Gemba en un proyecto activo.</p>", self.body)

    def test_the_mvp_criterion_starts_with_its_label(self):
        mvp = section(self.body, "MVP criterion")
        self.assertTrue(mvp.startswith("<p><strong>Risk validated:</strong>"))

    def test_baseline_and_target_are_labels(self):
        outcome = section(self.body, "Outcome")
        self.assertIn("<strong>Baseline:</strong>", outcome)
        self.assertIn("<strong>Target:</strong>", outcome)

    def test_each_requirement_carries_its_id_in_bold(self):
        listed = items(section(self.body, "Requirements"))
        self.assertEqual([re.match(r"<strong>(.+?)</strong>", item).group(1) for item in listed], ["R-01", "R-04"])
        self.assertIn("<code>story-review</code>", listed[1])

    def test_each_open_question_links_to_requirements(self):
        questions = section(self.body, "Open questions")
        links = re.findall(rf'<a href="{re.escape(REQUIREMENTS)}">(.+?)</a>', questions)
        self.assertEqual(links, ["Question 2", "Question 3"])

    def test_work_items_is_the_jira_issues_data_source_of_the_version(self):
        macro = section(self.body, "Work items")
        self.assertIn('data-type="block-card"', macro)
        datasource = json.loads(re.search(r'data-datasource="([^"]*(?:&quot;[^"]*)*)"', macro).group(1).replace("&quot;", '"'))
        self.assertEqual(datasource["id"], "d8b75300-dfda-4519-b6cd-e49abbd50401")
        self.assertEqual(datasource["parameters"]["cloudId"], CLOUD_ID)
        self.assertEqual(datasource["parameters"]["jql"],
                          'project = ABC AND fixVersion = "Gemba v0.1.0" AND issuetype != Epic ORDER BY key')
        self.assertEqual(datasource["views"][0]["properties"]["columns"],
                          [{"key": "issuetype"}, {"key": "key"}, {"key": "summary"}, {"key": "priority"}, {"key": "status"}])

    def test_work_items_carries_a_fallback_link_with_the_percent_encoded_jql(self):
        macro = section(self.body, "Work items")
        url = f"https://{SITE}/issues/?jql=project%20%3D%20ABC%20AND%20fixVersion%20%3D%20%22Gemba%20v0.1.0%22%20AND%20issuetype%20%21%3D%20Epic%20ORDER%20BY%20key"
        self.assertEqual(re.search(r'data-url="([^"]*)"', macro).group(1), url)
        self.assertIn(f'<a href="{url}">{url}</a>', macro)


class VersionOptional(unittest.TestCase):
    def test_quotes_in_the_version_name_are_escaped_in_the_jql(self):
        body = page(DRAFT.replace("Gemba v0.1.0", 'Ga"b v0.1.0'))["body"]
        macro = section(body, "Work items")
        datasource = json.loads(re.search(r'data-datasource="([^"]*(?:&quot;[^"]*)*)"', macro).group(1).replace("&quot;", '"'))
        self.assertIn('fixVersion = "Ga\\"b v0.1.0"', datasource["parameters"]["jql"])

    def test_a_later_version_has_no_mvp_criterion(self):
        start, end = DRAFT.index("### MVP criterion"), DRAFT.index("### Outcome")
        body = page(DRAFT[:start] + DRAFT[end:].replace("Gemba v0.1.0", "Gemba v0.2.0"), *LATER)["body"]
        self.assertEqual(headings(body)[0], "Outcome")


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

    def test_a_release_date_in_another_iso_form(self):
        rejected(DRAFT.replace("2026-11-20", "20261120"), "20261120")

    def test_a_project_that_is_not_a_jira_key(self):
        rejected(DRAFT, "--project", args=("--project", 'ABC" OR project = X', "--site", SITE, "--cloud-id", CLOUD_ID, "--requirements", REQUIREMENTS))

    def test_the_first_version_needs_its_mvp_criterion(self):
        start, end = DRAFT.index("### MVP criterion"), DRAFT.index("### Outcome")
        rejected(DRAFT[:start] + DRAFT[end:], "MVP criterion")

    def test_a_later_version_has_none(self):
        rejected(DRAFT, "MVP criterion", args=LATER)

    def test_without_project_or_requirements_link(self):
        rejected(DRAFT, "--project", args=("--requirements", REQUIREMENTS))
        rejected(DRAFT, "--requirements", args=("--project", "ABC"))


if __name__ == "__main__":
    unittest.main()
