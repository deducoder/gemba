"""Checks project-create's requirements script: what it accepts, what it rejects and the HTML
it prints for the live doc that holds the catalog of a product's requirements."""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/scripts/requirements.py"

DRAFT = """### Unassigned

* **R-01** Ventas registra una venta con varios tours en menos de 2 minutos. [Functional] Source: Material
* **R-02** El folio de venta es único. [Business rule] Source: Interview
* **R-03** El operador abre su hoja desde el teléfono. [Non-functional] Source: Research [Hypothesis]
* **R-04** Los montos van en MXN. [Constraint] Source: Vision

### Assumptions and open questions

* **Question 1.** ¿Cuántas ventas se recapturan hoy por semana? Assumption: unas 20. [Open]
* **Question 2.** ¿El operador captura gastos? Assumption: solo lee su hoja. Affects R-03. [Open]
"""


def run(draft, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=draft, capture_output=True, text=True)


def page(draft, *args):
    result = run(draft, *args)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)["body"]


def rejected(draft, *words, args=()):
    result = run(draft, *args)
    assert result.returncode == 1, result.stdout
    assert result.stdout == ""
    for word in words:
        assert word in result.stderr, result.stderr
    return result.stderr


def flat(html):
    return re.sub(r"<[^>]+>", "", html)


def headings(body):
    return re.findall(r"<h2>(.+?)</h2>", body)


def section(body, title):
    """Returns the HTML of the <ul> list right after the <h2>title</h2> heading, or "" without one."""
    match = re.search(rf"<h2>{re.escape(title)}</h2>(<ul>.*?</ul>)?", body, re.DOTALL)
    return match.group(1) or ""


def lines(body, title):
    """Returns the inner HTML of each bullet of the list under a level two heading."""
    return re.findall(r"<li><p>(.*?)</p></li>", section(body, title), re.DOTALL)


def statuses(line):
    return re.findall(r'<span data-type="status" data-color="(\w+)">([^<]*)</span>', line)


class RequirementsDraft(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run(DRAFT)
        cls.page = json.loads(cls.result.stdout) if cls.result.returncode == 0 else {}
        cls.body = cls.page.get("body", "")

    def test_a_draft_that_follows_the_template_passes(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr)

    def test_the_title_is_requirements(self):
        self.assertEqual(self.page["title"], "Requirements")

    def test_the_headings_are_unassigned_and_the_questions(self):
        self.assertEqual(headings(self.body), ["Unassigned", "Assumptions and open questions"])

    def test_each_requirement_opens_with_its_id_in_bold(self):
        first = [re.match(r"<strong>(.+?)</strong>", line).group(1) for line in lines(self.body, "Unassigned")]
        self.assertEqual(first, ["R-01", "R-02", "R-03", "R-04"])

    def test_the_source_is_grey_after_the_type(self):
        line = lines(self.body, "Unassigned")[0]
        type_pos = line.index('<span data-type="status" data-color="neutral">Functional</span>')
        source_pos = line.index('<span style="color: #97a0af">Source: Material</span>')
        self.assertLess(type_pos, source_pos)
        self.assertTrue(line.rstrip().endswith("Source: Material</span>"))

    def test_the_hypothesis_lozenge_closes_the_line_after_source(self):
        line = lines(self.body, "Unassigned")[2]
        source_pos = line.index('<span style="color: #97a0af">Source: Research</span>')
        hypothesis_pos = line.index('<span data-type="status" data-color="neutral">Hypothesis</span>')
        self.assertLess(source_pos, hypothesis_pos)
        self.assertTrue(line.rstrip().endswith("Hypothesis</span>"))

    def test_the_type_is_a_lozenge_with_its_color(self):
        types = [statuses(line) for line in lines(self.body, "Unassigned")]
        self.assertEqual(types, [
            [("neutral", "Functional")], [("blue", "Business rule")],
            [("purple", "Non-functional"), ("neutral", "Hypothesis")], [("yellow", "Constraint")],
        ])

    def test_each_question_carries_its_assumption_and_its_state(self):
        questions = lines(self.body, "Assumptions and open questions")
        self.assertEqual([re.match(r"<strong>(.+?)</strong>", q).group(1) for q in questions], ["Question 1.", "Question 2."])
        self.assertTrue(all("Assumption:" in flat(q) for q in questions))
        self.assertEqual([statuses(q)[-1][1] for q in questions], ["Open", "Open"])


class RequirementsOptional(unittest.TestCase):
    def test_without_questions_the_page_has_no_questions_heading(self):
        body = page(DRAFT[:DRAFT.index("### Assumptions")] + "### Assumptions and open questions\n")
        self.assertEqual(headings(body), ["Unassigned"])

    def test_an_answered_question(self):
        page(DRAFT.replace("unas 20. [Open]", "unas 20. [Answered]"))


class RequirementsReview(unittest.TestCase):
    def test_a_gap_left_by_a_removed_proposal_passes(self):
        page(DRAFT.replace("**R-03**", "**R-05**").replace("**R-04**", "**R-06**").replace("Affects R-03.", "Affects R-05."))

    def test_a_malformed_requirement_does_not_cascade(self):
        errors = rejected(DRAFT.replace(" Source: Material", ""), "R-01")
        self.assertEqual(len(errors.strip().splitlines()), 1, errors)

    def test_affects_with_any_separator_checks_every_id(self):
        rejected(DRAFT.replace("Affects R-03.", "Affects R-03; R-09."), "R-09")


REVIEWED = DRAFT.replace("""### Unassigned

* **R-01**""", """### Tours v0.1.0

* **R-01**""").replace("""* **R-02** El folio""", """### Unassigned

* **R-02** El folio""").replace("""### Assumptions and open questions""", """* **R-06** Ventas imprime la hoja de servicio. [Functional] Source: Interview

### Withdrawn

* ~~**R-05** El operador ve un mapa de la ruta.~~ La persona lo descartó. · 2026-10-18

### Assumptions and open questions""")
EXISTING = ("--existing", "R-01,R-02,R-03,R-04,R-05")


class RequirementsReviewMode(unittest.TestCase):
    def test_a_reviewed_catalog_passes(self):
        page(REVIEWED, *EXISTING)

    def test_a_version_group_comes_before_unassigned(self):
        self.assertEqual(headings(page(REVIEWED)), ["Tours v0.1.0", "Unassigned", "Withdrawn", "Assumptions and open questions"])

    def test_a_withdrawn_requirement_is_struck_with_its_reason_and_date(self):
        line = lines(page(REVIEWED), "Withdrawn")[0]
        self.assertTrue(line.startswith("<s><strong>R-05</strong></s><s> El operador ve un mapa de la ruta.</s>"))
        self.assertIn("La persona lo descartó.", flat(line))
        self.assertRegex(line, r'<time datetime="2026-10-18">2026-10-18</time>$')

    def test_a_published_requirement_that_disappears(self):
        rejected(REVIEWED.replace("* ~~**R-05** El operador ve un mapa de la ruta.~~ La persona lo descartó. · 2026-10-18\n", ""),
                 "R-05", args=EXISTING)

    def test_a_new_requirement_that_reuses_a_withdrawn_number(self):
        rejected(REVIEWED.replace("**R-06** Ventas imprime", "**R-05** Ventas imprime"), "R-05", args=EXISTING)

    def test_a_new_requirement_below_the_highest_published(self):
        rejected(REVIEWED.replace("**R-06** Ventas imprime", "**R-04** Ventas imprime").replace("* **R-04** Los montos van en MXN. [Constraint] Source: Vision\n", ""),
                 "R-04", args=("--existing", "R-01,R-02,R-03,R-05"))

    def test_a_withdrawn_line_without_its_date(self):
        rejected(REVIEWED.replace(" · 2026-10-18", ""), "Withdrawn", "R-05")


class RequirementsReviewEdges(unittest.TestCase):
    def test_an_impossible_withdrawn_date_is_reported(self):
        rejected(REVIEWED.replace("2026-10-18", "2026-13-45"), "Withdrawn", "2026-13-45")

    def test_withdrawn_in_the_order_they_were_withdrawn(self):
        draft = """### Unassigned

* **R-01** Algo. [Functional] Source: Interview

### Withdrawn

* ~~**R-05** Otra cosa.~~ Ya no aplica. · 2026-10-01
* ~~**R-02** Una más.~~ La cubre R-01. · 2026-10-18

### Assumptions and open questions
"""
        page(draft, "--existing", "R-01,R-02,R-05")

    def test_a_malformed_withdrawn_line_reports_once(self):
        errors = rejected(REVIEWED.replace("* ~~**R-05** El operador", "* R-05 ~~El operador"), "Withdrawn", args=EXISTING)
        self.assertEqual(len(errors.strip().splitlines()), 1, errors)

    def test_an_empty_unassigned_with_withdrawn_requirements(self):
        draft = """### Unassigned

### Withdrawn

* ~~**R-01** Algo.~~ Ya no aplica. · 2026-10-18

### Assumptions and open questions
"""
        page(draft, "--existing", "R-01")

    def test_existing_ids_that_are_not_ids(self):
        rejected(REVIEWED, "existing", "Rx", args=("--existing", "R-01,Rx"))


class RequirementsRejects(unittest.TestCase):
    def test_ids_out_of_order(self):
        rejected(DRAFT.replace("**R-02**", "**R-07**"), "R-03")

    def test_a_repeated_id(self):
        rejected(DRAFT.replace("**R-02**", "**R-01**"), "R-01")

    def test_a_type_outside_the_closed_list(self):
        rejected(DRAFT.replace("[Constraint]", "[Preference]"), "Preference")

    def test_a_requirement_without_source_or_hypothesis(self):
        rejected(DRAFT.replace(" Source: Interview", ""), "Source", "R-02")

    def test_a_hypothesis_without_source_passes(self):
        page(DRAFT.replace(" Source: Research", ""))

    def test_a_source_outside_the_closed_list(self):
        rejected(DRAFT.replace("Source: Material", "Source: Notes"), "Source", "Notes")

    def test_a_requirement_without_type(self):
        rejected(DRAFT.replace(" [Business rule]", ""), "R-02")

    def test_a_section_that_is_not_of_the_page(self):
        rejected(DRAFT.replace("### Unassigned", "### Backlog"), "sections")

    def test_without_requirements(self):
        start, end = DRAFT.index("* **R-01**"), DRAFT.index("### Assumptions")
        rejected(DRAFT[:start] + DRAFT[end:], "Unassigned")

    def test_a_question_without_assumption(self):
        rejected(DRAFT.replace(" Assumption: unas 20.", ""), "Question 1", "Assumption")

    def test_a_question_out_of_its_series(self):
        rejected(DRAFT.replace("**Question 2.**", "**Question 3.**"), "Question 3")

    def test_a_question_that_affects_a_missing_requirement(self):
        rejected(DRAFT.replace("Affects R-03.", "Affects R-09."), "R-09")

    def test_a_question_with_another_state(self):
        rejected(DRAFT.replace("unas 20. [Open]", "unas 20. [Pending]"), "Pending")


if __name__ == "__main__":
    unittest.main()
