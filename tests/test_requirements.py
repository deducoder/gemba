"""Checks project-create's requirements script: what it accepts, what it rejects and the ADF
it prints for the live doc that holds the catalog of a product's requirements."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/scripts/requirements.py"

DRAFT = """### Unassigned

* **R-01** Ventas registra una venta con varios tours en menos de 2 minutos. Source: notas, punto 2 [Functional]
* **R-02** El folio de venta es único. Source: María (Ventas) [Business rule]
* **R-03** El operador abre su hoja desde el teléfono. Source: la persona [Non-functional] [Hypothesis]
* **R-04** Los montos van en MXN. Source: notas, punto 5 [Constraint]

### Assumptions and open questions

* **Question 1.** ¿Cuántas ventas se recapturan hoy por semana? Assumption: unas 20. [Open]
* **Question 2.** ¿El operador captura gastos? Assumption: solo lee su hoja. Affects R-03. [Open]
"""


def run(draft, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=draft, capture_output=True, text=True)


def page(draft, *args):
    result = run(draft, *args)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)["body"]["content"]


def rejected(draft, *words, args=()):
    result = run(draft, *args)
    assert result.returncode == 1, result.stdout
    assert result.stdout == ""
    for word in words:
        assert word in result.stderr, result.stderr
    return result.stderr


def flat(node):
    return "".join(n["text"] if n["type"] == "text" else "" for n in node.get("content", []))


def nodes(node, kind):
    found = [node] if node.get("type") == kind else []
    for child in node.get("content", []):
        found.extend(nodes(child, kind))
    return found


def lines(body, title):
    """Returns the paragraphs of the list under a level two heading."""
    start = next(i for i, n in enumerate(body) if n["type"] == "heading" and flat(n) == title)
    return [item["content"][0] for item in body[start + 1]["content"]]


class RequirementsDraft(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run(DRAFT)
        cls.page = json.loads(cls.result.stdout) if cls.result.returncode == 0 else {}
        cls.body = cls.page.get("body", {}).get("content", [])

    def test_a_draft_that_follows_the_template_passes(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr)

    def test_the_title_is_requirements(self):
        self.assertEqual(self.page["title"], "Requirements")

    def test_the_headings_are_unassigned_and_the_questions(self):
        headings = [flat(n) for n in self.body if n["type"] == "heading"]
        self.assertEqual(headings, ["Unassigned", "Assumptions and open questions"])

    def test_each_requirement_opens_with_its_id_in_bold(self):
        first = [line["content"][0] for line in lines(self.body, "Unassigned")]
        self.assertEqual([n["text"] for n in first], ["R-01", "R-02", "R-03", "R-04"])
        self.assertTrue(all(n["marks"] == [{"type": "strong"}] for n in first))

    def test_the_source_is_grey_before_the_type(self):
        line = lines(self.body, "Unassigned")[0]
        source = next(n for n in line["content"] if n["type"] == "text" and n["text"].startswith("Source:"))
        self.assertEqual(source["marks"], [{"type": "textColor", "attrs": {"color": "#97a0af"}}])
        self.assertEqual(line["content"][-1]["type"], "status")

    def test_the_type_is_a_lozenge_with_its_color(self):
        types = [[(s["attrs"]["text"], s["attrs"]["color"]) for s in nodes(line, "status")] for line in lines(self.body, "Unassigned")]
        self.assertEqual(types, [
            [("Functional", "neutral")], [("Business rule", "blue")],
            [("Non-functional", "purple"), ("Hypothesis", "neutral")], [("Constraint", "yellow")],
        ])

    def test_each_question_carries_its_assumption_and_its_state(self):
        questions = lines(self.body, "Assumptions and open questions")
        self.assertEqual([q["content"][0]["text"] for q in questions], ["Question 1.", "Question 2."])
        self.assertTrue(all("Assumption:" in flat(q) for q in questions))
        self.assertEqual([nodes(q, "status")[-1]["attrs"]["text"] for q in questions], ["Open", "Open"])


class RequirementsOptional(unittest.TestCase):
    def test_without_questions_the_page_has_no_questions_heading(self):
        body = page(DRAFT[:DRAFT.index("### Assumptions")] + "### Assumptions and open questions\n")
        self.assertEqual([flat(n) for n in body if n["type"] == "heading"], ["Unassigned"])

    def test_an_answered_question(self):
        page(DRAFT.replace("unas 20. [Open]", "unas 20. [Answered]"))


class RequirementsReview(unittest.TestCase):
    def test_a_gap_left_by_a_removed_proposal_passes(self):
        page(DRAFT.replace("**R-03**", "**R-05**").replace("**R-04**", "**R-06**").replace("Affects R-03.", "Affects R-05."))

    def test_a_malformed_requirement_does_not_cascade(self):
        errors = rejected(DRAFT.replace(" Source: notas, punto 2", ""), "R-01")
        self.assertEqual(len(errors.strip().splitlines()), 1, errors)

    def test_a_source_that_ends_in_brackets(self):
        body = page(DRAFT.replace("Source: notas, punto 2 [Functional]", "Source: notas, punto [2] [Functional]"))
        self.assertIn("Source: notas, punto [2]", flat(lines(body, "Unassigned")[0]))

    def test_affects_with_any_separator_checks_every_id(self):
        rejected(DRAFT.replace("Affects R-03.", "Affects R-03; R-09."), "R-09")


REVIEWED = DRAFT.replace("""### Unassigned

* **R-01**""", """### Tours v0.1.0

* **R-01**""").replace("""* **R-02** El folio""", """### Unassigned

* **R-02** El folio""").replace("""### Assumptions and open questions""", """* **R-06** Ventas imprime la hoja de servicio. Source: María (Ventas) [Functional]

### Withdrawn

* ~~**R-05** El operador ve un mapa de la ruta.~~ La persona lo descartó. · 2026-10-18

### Assumptions and open questions""")
EXISTING = ("--existing", "R-01,R-02,R-03,R-04,R-05")


class RequirementsReviewMode(unittest.TestCase):
    def test_a_reviewed_catalog_passes(self):
        page(REVIEWED, *EXISTING)

    def test_a_version_group_comes_before_unassigned(self):
        headings = [flat(n) for n in page(REVIEWED) if n["type"] == "heading"]
        self.assertEqual(headings, ["Tours v0.1.0", "Unassigned", "Withdrawn", "Assumptions and open questions"])

    def test_a_withdrawn_requirement_is_struck_with_its_reason_and_date(self):
        line = lines(page(REVIEWED), "Withdrawn")[0]
        struck = [n["text"] for n in line["content"] if any(m["type"] == "strike" for m in n.get("marks", []))]
        self.assertEqual(struck, ["R-05", " El operador ve un mapa de la ruta."])
        self.assertIn("La persona lo descartó.", flat(line))
        self.assertEqual([n["type"] for n in line["content"]][-1], "date")

    def test_a_published_requirement_that_disappears(self):
        rejected(REVIEWED.replace("* ~~**R-05** El operador ve un mapa de la ruta.~~ La persona lo descartó. · 2026-10-18\n", ""),
                 "R-05", args=EXISTING)

    def test_a_new_requirement_that_reuses_a_withdrawn_number(self):
        rejected(REVIEWED.replace("**R-06** Ventas imprime", "**R-05** Ventas imprime"), "R-05", args=EXISTING)

    def test_a_new_requirement_below_the_highest_published(self):
        rejected(REVIEWED.replace("**R-06** Ventas imprime", "**R-04** Ventas imprime").replace("* **R-04** Los montos van en MXN. Source: notas, punto 5 [Constraint]\n", ""),
                 "R-04", args=("--existing", "R-01,R-02,R-03,R-05"))

    def test_a_withdrawn_line_without_its_date(self):
        rejected(REVIEWED.replace(" · 2026-10-18", ""), "Withdrawn", "R-05")


class RequirementsReviewEdges(unittest.TestCase):
    def test_an_impossible_withdrawn_date_is_reported(self):
        rejected(REVIEWED.replace("2026-10-18", "2026-13-45"), "Withdrawn", "2026-13-45")

    def test_withdrawn_in_the_order_they_were_withdrawn(self):
        draft = """### Unassigned

* **R-01** Algo. Source: la persona [Functional]

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

    def test_a_requirement_without_source(self):
        rejected(DRAFT.replace(" Source: María (Ventas)", ""), "Source", "R-02")

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
