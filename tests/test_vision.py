"""Checks project-create's vision script: what it accepts, what it rejects and the ADF it
prints for the live doc of a product's vision."""

import json
import subprocess
import sys
import unittest
from datetime import datetime, timezone
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
    return json.loads(result.stdout)["body"]["content"]


def rejected(draft, *words):
    result = run(draft)
    assert result.returncode == 1, result.stdout
    assert result.stdout == ""
    for word in words:
        assert word in result.stderr, result.stderr
    return result.stderr


def flat(node):
    return "".join(n["text"] if n["type"] == "text" else "" for n in node.get("content", []))


def nodes(node, kind):
    """Returns every node of a kind inside a node, in document order."""
    found = [node] if node.get("type") == kind else []
    for child in node.get("content", []):
        found.extend(nodes(child, kind))
    return found


def h2(body):
    return [flat(n) for n in body if n["type"] == "heading" and n["attrs"]["level"] == 2]


class VisionDraft(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run(DRAFT)
        cls.page = json.loads(cls.result.stdout) if cls.result.returncode == 0 else {}
        cls.body = cls.page.get("body", {}).get("content", [])

    def test_a_draft_that_follows_the_template_passes(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr)
        self.assertEqual(self.result.stderr, "")

    def test_the_title_is_vision(self):
        self.assertEqual(self.page["title"], "Vision")

    def test_the_origin_is_a_lozenge_at_the_end_of_the_first_line(self):
        first = self.body[0]
        self.assertEqual(flat(first).strip(), FIRST)
        self.assertEqual(first["content"][-1]["type"], "status")
        self.assertEqual(first["content"][-1]["attrs"]["text"], "Client")

    def test_the_two_paragraphs_follow_the_first_line(self):
        self.assertEqual([n["type"] for n in self.body[1:3]], ["paragraph", "paragraph"])

    def test_the_headings_are_the_sections_in_order(self):
        self.assertEqual(h2(self.body), ["Problem", "Users", "Success", "Constraints", "Risks", "Decision"])

    def test_today_is_an_info_panel(self):
        panels = [n for n in self.body if n["type"] == "panel" and n["attrs"]["panelType"] == "info"]
        self.assertEqual(len(panels), 1)
        self.assertTrue(flat(panels[0]["content"][0]).startswith("Today:"))

    def test_each_risk_carries_its_kind_and_evidence_lozenges_and_a_note_panel(self):
        start = next(i for i, n in enumerate(self.body) if n["type"] == "heading" and flat(n) == "Risks")
        lozenges = [[s["attrs"]["text"] for s in nodes(n, "status")] for n in self.body[start:] if n["type"] == "paragraph"]
        self.assertEqual(lozenges, [["Value", "Evidence"], ["Usability", "Hypothesis"]])
        notes = [n for n in self.body if n["type"] == "panel" and n["attrs"]["panelType"] == "note"]
        self.assertEqual([[flat(p).split(":")[0] for p in n["content"]] for n in notes], [["Validation", "Threshold"]] * 2)

    def test_evidence_is_green_and_hypothesis_neutral(self):
        colors = {s["attrs"]["text"]: s["attrs"]["color"] for s in nodes({"content": self.body}, "status")}
        self.assertEqual((colors["Evidence"], colors["Hypothesis"]), ("green", "neutral"))

    def test_go_to_validate_is_a_warning_panel_with_the_decision_as_level_three_heading(self):
        panel = self.body[-1]
        self.assertEqual((panel["type"], panel["attrs"]["panelType"]), ("panel", "warning"))
        self.assertEqual(panel["content"][0]["type"], "heading")
        self.assertEqual(panel["content"][0]["attrs"]["level"], 3)
        self.assertEqual(flat(panel["content"][0]), "construir Tours v0.1.0 para validar el riesgo de valor.")

    def test_decided_by_is_a_mention_and_the_date_a_date_node(self):
        panel = self.body[-1]
        self.assertEqual([m["attrs"]["id"] for m in nodes(panel, "mention")], [ACCOUNT])
        stamp = datetime(2026, 10, 18, tzinfo=timezone.utc).timestamp() * 1000
        self.assertEqual([d["attrs"]["timestamp"] for d in nodes(panel, "date")], [str(int(stamp))])


class VisionDecision(unittest.TestCase):
    def test_go_to_build_is_a_success_panel(self):
        body = page(DRAFT.replace("Go to validate:", "Go to build:"))
        self.assertEqual(body[-1]["attrs"]["panelType"], "success")

    def test_no_go_is_an_error_panel(self):
        body = page(DRAFT.replace("Go to validate:", "No-go:"))
        self.assertEqual(body[-1]["attrs"]["panelType"], "error")

    def test_without_a_decision_the_page_has_no_decision_heading_and_no_panel(self):
        body = page(DRAFT[:DRAFT.index("### Decision")])
        self.assertNotIn("Decision", h2(body))
        self.assertEqual([n["attrs"]["panelType"] for n in body if n["type"] == "panel"], ["info", "note", "note"])

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
        start = next(i for i, n in enumerate(body) if n["type"] == "heading" and flat(n) == "Success")
        self.assertEqual(body[start + 2]["type"], "bulletList")

    def test_text_after_today(self):
        rejected(DRAFT.replace("mensajes de WhatsApp.\n", "mensajes de WhatsApp.\nY correos.\n"), "Today")

    def test_code_in_the_decision_is_a_code_mark(self):
        body = page(DRAFT.replace("construir Tours v0.1.0", "construir `tours` v0.1.0"))
        marks = [n.get("marks") for n in body[-1]["content"][0]["content"]]
        self.assertIn([{"type": "code"}], marks)

    def test_a_malformed_risk_is_reported_once(self):
        errors = rejected(DRAFT.replace("* **Ventas sigue armando las hojas fuera del sistema** [Value]", "* Ventas sigue armando las hojas fuera del sistema [Value]"), "Risks")
        self.assertEqual(len(errors.strip().splitlines()), 1, errors)


class VisionRequirementsLink(unittest.TestCase):
    URL = "https://example.atlassian.net/wiki/spaces/ABC/pages/1007/Requirements"
    UNKNOWN = DRAFT.replace("Baseline: desconocido.", "Baseline: desconocido (Question 1).")

    def baseline(self, *args):
        result = run(self.UNKNOWN, *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        body = json.loads(result.stdout)["body"]["content"]
        return next(n for n in body if n["type"] == "paragraph" and flat(n).startswith("Baseline:"))

    def test_a_question_in_the_baseline_links_to_the_requirements_page(self):
        links = [n for n in self.baseline("--requirements", self.URL)["content"]
                 if any(m["type"] == "link" for m in n.get("marks", []))]
        self.assertEqual([(n["text"], n["marks"][0]["attrs"]["href"]) for n in links], [("Question 1", self.URL)])

    def test_without_the_page_the_question_stays_text(self):
        line = self.baseline()
        self.assertIn("Question 1", flat(line))
        self.assertFalse(any(m["type"] == "link" for n in line["content"] for m in n.get("marks", [])))


class VisionOptional(unittest.TestCase):
    def test_without_constraints_the_page_has_no_constraints_heading(self):
        body = page(DRAFT.replace("* Los montos van en MXN.\n", ""))
        self.assertNotIn("Constraints", h2(body))


if __name__ == "__main__":
    unittest.main()
