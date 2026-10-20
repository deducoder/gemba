"""Checks project-create's vision script: what it accepts, what it rejects and the HTML it
prints for the live doc of a product's vision."""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/skills/project-create/scripts/vision.py"
ACCOUNT = "712020:4aaa7bc9-95d7-410b-af7f-956435d83f8f"
FIRST = "Tours reúne en un solo lugar la venta de tours, su agenda y la hoja de servicio."

DRAFT = f"""{FIRST} [Client]

La venta se captura una vez y cada etapa trabaja sobre los mismos datos.

A futuro cubre la agenda, la hoja de servicio y los gastos del operador.

### Problem

Ventas y Operaciones no pueden pasar una venta a la hoja de servicio sin recapturar datos.
Today: una hoja de cálculo y mensajes de WhatsApp.

### Users

* **Ventas** registra las ventas de tours.
* **Operador** consulta su hoja de servicio.

### Success

Si hoy una venta se captura de nuevo en cada etapa, entonces se registra una vez para Ventas. Se mide con:
* El tiempo para registrar una venta con varios tours.
Baseline: desconocido. Target: menos de 2 minutos.

### Constraints

* Los montos van en MXN.

### Risks

* **Ventas sigue armando las hojas fuera del sistema** [Value] [Evidence]
  Validation: contar las hojas emitidas desde el sistema en el primer mes.
  Threshold: el 80 % de las hojas sale del sistema.
* **El operador no puede abrir su hoja en el teléfono** [Usability] [Hypothesis]
  Validation: observar a tres operadores abrir su hoja en campo.
  Threshold: los tres la abren sin ayuda.

### Decision

Go to validate: construir Tours v0.1.0 para validar el riesgo de valor.
Decided by: {ACCOUNT} · 2026-10-18
"""


def run(draft, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=draft, capture_output=True, text=True)


def page(draft):
    result = run(draft)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)["body"]


def rejected(draft, *words):
    result = run(draft)
    assert result.returncode == 1, result.stdout
    assert result.stdout == ""
    for word in words:
        assert word in result.stderr, result.stderr
    return result.stderr


def flat(html):
    return re.sub(r"<[^>]+>", "", html)


def headings(body, level=2):
    return re.findall(rf"<h{level}>(.+?)</h{level}>", body)


def panels(body):
    """Returns (kind, inner html) for every panel, in order. Panel content here never
    nests a <div>, so the next literal </div> always closes the one that opened."""
    result = []
    for match in re.finditer(r'<div data-type="panel-(\w+)">', body):
        kind, start = match.group(1), match.end()
        end = body.index("</div>", start)
        result.append((kind, body[start:end]))
    return result


def statuses(html):
    return re.findall(r'<span data-type="status" data-color="(\w+)">([^<]*)</span>', html)


class VisionDraft(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run(DRAFT)
        cls.page = json.loads(cls.result.stdout) if cls.result.returncode == 0 else {}
        cls.body = cls.page.get("body", "")

    def test_a_draft_that_follows_the_template_passes(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr)
        self.assertEqual(self.result.stderr, "")

    def test_the_title_is_vision(self):
        self.assertEqual(self.page["title"], "Vision")

    def test_the_origin_is_a_lozenge_at_the_end_of_the_first_line(self):
        first = re.match(r"<p>(.*?)</p>", self.body).group(1)
        self.assertTrue(first.endswith('<span data-type="status" data-color="neutral">Client</span>'))
        without_status = re.sub(r'<span data-type="status"[^>]*>[^<]*</span>$', "", first)
        self.assertEqual(flat(without_status).strip(), FIRST)

    def test_the_two_paragraphs_follow_the_first_line(self):
        paragraphs = re.findall(r"<p>(.*?)</p>", self.body)[1:3]
        self.assertEqual(paragraphs, [
            "La venta se captura una vez y cada etapa trabaja sobre los mismos datos.",
            "A futuro cubre la agenda, la hoja de servicio y los gastos del operador.",
        ])

    def test_the_headings_are_the_sections_in_order(self):
        self.assertEqual(headings(self.body), ["Problem", "Users", "Success", "Constraints", "Risks", "Decision"])

    def test_today_is_an_info_panel(self):
        info = [content for kind, content in panels(self.body) if kind == "info"]
        self.assertEqual(len(info), 1)
        self.assertTrue(flat(info[0]).startswith("Today:"))

    def test_each_risk_carries_its_kind_and_evidence_lozenges_and_a_note_panel(self):
        lozenges = [statuses(p) for p in re.findall(r'<p>((?:(?!</?p>)[\s\S])*?)</p>(?=<div data-type="panel-note">)', self.body)]
        self.assertEqual([[text for _, text in loz] for loz in lozenges], [["Value", "Evidence"], ["Usability", "Hypothesis"]])
        notes = [content for kind, content in panels(self.body) if kind == "note"]
        self.assertEqual([flat(n).split(":")[0] for n in notes[:1] for _ in [0]], ["Validation"])
        self.assertEqual(len(notes), 2)

    def test_evidence_is_green_and_hypothesis_neutral(self):
        colors = dict((text, color) for color, text in statuses(self.body))
        self.assertEqual((colors["Evidence"], colors["Hypothesis"]), ("green", "neutral"))

    def test_go_to_validate_is_a_warning_panel_with_the_category_as_level_three_heading(self):
        kind, content = panels(self.body)[-1]
        self.assertEqual(kind, "warning")
        self.assertTrue(content.startswith("<h3>Go to validate</h3>"))

    def test_the_decision_text_is_a_quote_under_the_heading(self):
        _, content = panels(self.body)[-1]
        self.assertIn("<blockquote><p>construir Tours v0.1.0 para validar el riesgo de valor.</p></blockquote>", content)

    def test_decided_by_is_a_mention_and_the_date_a_date_node(self):
        _, content = panels(self.body)[-1]
        self.assertIn(f'<span data-type="mention" data-user-id="{ACCOUNT}">@{ACCOUNT}</span>', content)
        self.assertIn('<time datetime="2026-10-18">2026-10-18</time>', content)


class VisionDecision(unittest.TestCase):
    def test_go_to_build_is_a_success_panel(self):
        body = page(DRAFT.replace("Go to validate:", "Go to build:"))
        self.assertEqual(panels(body)[-1][0], "success")

    def test_no_go_is_an_error_panel(self):
        body = page(DRAFT.replace("Go to validate:", "No-go:"))
        self.assertEqual(panels(body)[-1][0], "error")

    def test_without_a_decision_the_page_has_no_decision_heading_and_no_panel(self):
        body = page(DRAFT[:DRAFT.index("### Decision")])
        self.assertNotIn("Decision", headings(body))
        self.assertEqual([kind for kind, _ in panels(body)], ["info", "note", "note"])

    def test_go_to_build_with_a_value_risk_in_hypothesis(self):
        draft = DRAFT.replace("[Value] [Evidence]", "[Value] [Hypothesis]").replace("Go to validate:", "Go to build:")
        rejected(draft, "Go to build", "Value")

    def test_go_to_build_with_a_viability_risk_in_hypothesis(self):
        draft = DRAFT.replace("[Usability] [Hypothesis]", "[Viability] [Hypothesis]").replace("Go to validate:", "Go to build:")
        rejected(draft, "Go to build", "Viability")

    def test_a_decision_state_that_is_not_one_of_the_three(self):
        rejected(DRAFT.replace("Go to validate:", "Maybe:"), "Decision")

    def test_decided_by_without_a_date(self):
        rejected(DRAFT.replace(" · 2026-10-18", ""), "Decided by")

    def test_decided_by_with_a_name_instead_of_an_account_id(self):
        rejected(DRAFT.replace(ACCOUNT, "Daniel Domínguez"), "Decided by")


class VisionRejects(unittest.TestCase):
    def test_a_first_line_without_the_origin(self):
        rejected(DRAFT.replace(" [Client]", ""), "origin")

    def test_an_origin_that_is_not_one_of_the_four(self):
        rejected(DRAFT.replace("[Client]", "[Startup]"), "origin")

    def test_without_the_two_paragraphs_after_the_first_line(self):
        rejected(DRAFT.replace("A futuro cubre la agenda, la hoja de servicio y los gastos del operador.\n\n", ""), "paragraphs")

    def test_sections_in_another_order(self):
        rejected(DRAFT.replace("### Users", "### Usuarios"), "sections")

    def test_a_problem_without_today(self):
        rejected(DRAFT.replace("Today: una hoja de cálculo y mensajes de WhatsApp.\n", ""), "Today")

    def test_a_user_without_a_bold_role(self):
        rejected(DRAFT.replace("* **Ventas** registra", "* Ventas registra"), "Users")

    def test_success_without_baseline_and_target(self):
        rejected(DRAFT.replace("Baseline: desconocido. Target: menos de 2 minutos.\n", ""), "Baseline")

    def test_a_risk_with_a_kind_that_is_not_one_of_the_four(self):
        rejected(DRAFT.replace("[Value] [Evidence]", "[Cost] [Evidence]"), "Risks", "Cost")

    def test_a_risk_without_evidence_or_hypothesis(self):
        rejected(DRAFT.replace("[Value] [Evidence]", "[Value]"), "Risks")

    def test_a_risk_without_validation(self):
        rejected(DRAFT.replace("  Validation: contar las hojas emitidas desde el sistema en el primer mes.\n", ""), "Validation")

    def test_a_risk_without_threshold(self):
        rejected(DRAFT.replace("  Threshold: el 80 % de las hojas sale del sistema.\n", ""), "Threshold")

    def test_without_risks(self):
        start, end = DRAFT.index("* **Ventas sigue"), DRAFT.index("### Decision")
        rejected(DRAFT[:start] + DRAFT[end:], "Risks")


class VisionReview(unittest.TestCase):
    def test_an_empty_bullet_in_success(self):
        rejected(DRAFT.replace("* El tiempo", "*\n* El tiempo"), "Success", "empty bullet")

    def test_an_indented_metric_is_still_a_metric(self):
        body = page(DRAFT.replace("* El tiempo", "  * El tiempo"))
        success = re.search(r"<h2>Success</h2>(.*?)<h2>", body, re.DOTALL).group(1)
        self.assertIn("<ul>", success)

    def test_text_after_today(self):
        rejected(DRAFT.replace("mensajes de WhatsApp.\n", "mensajes de WhatsApp.\nY correos.\n"), "Today")

    def test_code_in_the_decision_is_a_code_mark(self):
        body = page(DRAFT.replace("construir Tours v0.1.0", "construir `tours` v0.1.0"))
        self.assertIn("<code>tours</code>", panels(body)[-1][1])

    def test_a_malformed_risk_is_reported_once(self):
        errors = rejected(DRAFT.replace("* **Ventas sigue armando las hojas fuera del sistema** [Value]", "* Ventas sigue armando las hojas fuera del sistema [Value]"), "Risks")
        self.assertEqual(len(errors.strip().splitlines()), 1, errors)


class VisionRequirementsLink(unittest.TestCase):
    URL = "https://example.atlassian.net/wiki/spaces/ABC/pages/1007/Requirements"
    UNKNOWN = DRAFT.replace("Baseline: desconocido.", "Baseline: desconocido (Question 1).")

    def baseline(self, *args):
        result = run(self.UNKNOWN, *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        body = json.loads(result.stdout)["body"]
        return next(p for p in re.findall(r"<p>(.*?)</p>", body) if "Baseline:" in p)

    def test_a_question_in_the_baseline_links_to_the_requirements_page(self):
        line = self.baseline("--requirements", self.URL)
        self.assertIn(f'<a href="{self.URL}">Question 1</a>', line)

    def test_a_question_inside_code_stays_code(self):
        result = run(DRAFT.replace("Baseline: desconocido.", "Baseline: desconocido `(Question 1)`."), "--requirements", self.URL)
        self.assertEqual(result.returncode, 0, result.stderr)
        body = json.loads(result.stdout)["body"]
        line = next(p for p in re.findall(r"<p>(.*?)</p>", body) if "Baseline:" in p)
        self.assertIn("<code>(Question 1)</code>", line)

    def test_without_the_page_the_question_stays_text(self):
        line = self.baseline()
        self.assertIn("Question 1", flat(line))
        self.assertNotIn("<a ", line)


class VisionOptional(unittest.TestCase):
    def test_without_constraints_the_page_has_no_constraints_heading(self):
        body = page(DRAFT.replace("* Los montos van en MXN.\n", ""))
        self.assertNotIn("Constraints", headings(body))


if __name__ == "__main__":
    unittest.main()
