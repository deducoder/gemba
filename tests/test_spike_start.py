"""Checks spike-start's draft script: what it accepts, what it rejects and the ADF it
prints for Jira, the description and the Evidence comment."""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "plugins/gemba-code/skills/spike-start"
SCRIPT = SKILL / "scripts/spike.py"
SITE = "example.atlassian.net"
ORANGE = {"type": "textColor", "attrs": {"color": "#ff991f"}}

QUESTION = "¿La API de Acme Pay entrega las facturas de un cliente en JSON?"
DECISION = "De la respuesta depende si `invoices.py` deja la lista `INVOICES` por la API."

DRAFT = f"""Check whether Acme Pay returns a customer's invoices as JSON

{QUESTION} {DECISION}

### Done when

* La respuesta es sí, no o inconclusa, con la respuesta de la API a una consulta de prueba.
* ==Cada afirmación lleva su `ran:` o su fuente.==

### Evidence

* read: `invoices.py:6` → las facturas viven en la lista `INVOICES`
* ran: `grep -ri "acme pay" .` → sin resultados

### Out of scope

* Reemplazar la lista por la API → ABC-7
"""


def run(draft):
    return subprocess.run([sys.executable, str(SCRIPT), "--site", SITE], input=draft, capture_output=True, text=True)


def texts(node):
    """Yields every inline node of an ADF document, in order."""
    for child in node.get("content", []):
        if child["type"] in ("text", "inlineCard"):
            yield child
        yield from texts(child)


def paragraph(node):
    return "".join(n["text"] for n in node["content"])


class SpikeDraft(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run(DRAFT)
        cls.spike = json.loads(cls.result.stdout) if cls.result.returncode == 0 else {}
        cls.nodes = list(texts(cls.spike.get("description", {})))

    def test_a_draft_that_follows_the_template_prints_the_summary_and_the_adf(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr)
        self.assertEqual(self.spike["summary"], "Check whether Acme Pay returns a customer's invoices as JSON")
        description = self.spike["description"]
        self.assertEqual(description["type"], "doc")
        headings = [n["content"][0]["text"] for n in description["content"] if n["type"] == "heading"]
        self.assertEqual(headings, ["Done when", "Out of scope"])

    def test_the_question_opens_the_description_followed_by_the_decision(self):
        first = self.spike["description"]["content"][0]
        self.assertEqual(first["type"], "paragraph")
        self.assertEqual(paragraph(first), f"{QUESTION} {DECISION}".replace("`", ""))

    def test_the_evidence_goes_to_a_single_comment(self):
        comment = self.spike["comment"]
        self.assertEqual(comment["type"], "doc")
        self.assertEqual(comment["content"][0]["content"][0]["text"], "Evidence")
        lines = [paragraph(item["content"][0]) for item in comment["content"][1]["content"]]
        self.assertEqual(lines, [
            "read: invoices.py:6 → las facturas viven en la lista INVOICES",
            'ran: grep -ri "acme pay" . → sin resultados',
        ])
        self.assertNotIn("Evidence", [n.get("text") for n in self.nodes])

    def test_the_evidence_need_not_match_the_number_of_criteria(self):
        result = run(DRAFT.replace('* ran: `grep -ri "acme pay" .` → sin resultados\n', ""))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_criterion_in_equals_reaches_jira_in_orange_except_its_code(self):
        orange = [n["text"] for n in self.nodes if ORANGE in n.get("marks", [])]
        self.assertEqual(orange, ["Cada afirmación lleva su ", " o su fuente."])
        for node in self.nodes:
            marks = [m["type"] for m in node.get("marks", [])]
            self.assertFalse("code" in marks and "textColor" in marks, node)
        self.assertNotIn("==", self.result.stdout)

    def test_an_out_of_scope_key_becomes_a_link_to_the_issue(self):
        self.assertIn({"type": "inlineCard", "attrs": {"url": f"https://{SITE}/browse/ABC-7"}}, self.nodes)

    def test_a_question_mark_inside_code_does_not_count(self):
        result = run(DRAFT.replace(DECISION, "De la respuesta depende si `invoices.py?` deja la lista."))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_the_template_has_the_sections_the_script_expects(self):
        template = (SKILL / "assets/spike.md").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"^### (.+)$", template, re.MULTILINE), ["Done when", "Evidence", "Out of scope"])

    def test_a_draft_off_the_template_exits_1_with_one_line_per_problem(self):
        cases = {
            "no question": DRAFT.replace(QUESTION, "La API de Acme Pay entrega las facturas en JSON."),
            "the question as the second sentence": DRAFT.replace(QUESTION, "Acme Pay tiene una API. " + QUESTION),
            "two questions": DRAFT.replace(DECISION, "¿Y en XML? " + DECISION),
            "no decision after the question": DRAFT.replace(" " + DECISION, ""),
            "two opening paragraphs": DRAFT.replace(" " + DECISION, "\n\n" + DECISION),
            "summary over 64": DRAFT.replace("Check whether Acme Pay returns a customer's invoices as JSON", "C" + "x" * 64),
            "a missing section": DRAFT.replace("### Evidence", "### Proof"),
            "a subsection": DRAFT.replace("### Evidence\n", "### Evidence\n\n#### Sources\n"),
            "no evidence": DRAFT.replace("* read: `invoices.py:6` → las facturas viven en la lista `INVOICES`\n", "").replace(
                '* ran: `grep -ri "acme pay" .` → sin resultados\n', ""
            ),
            "evidence without ran or read": DRAFT.replace("* read: `invoices.py:6`", "* see `invoices.py:6`"),
            "an arrow to something that is not a key": DRAFT.replace("→ ABC-7", "→ a story of its own"),
            "equals outside Done when": DRAFT.replace("* Reemplazar la lista", "* ==Reemplazar la lista=="),
            "a partly wrapped criterion": DRAFT.replace("* ==Cada afirmación lleva su `ran:` o su fuente.==", "* ==Cada afirmación== lleva su fuente."),
            "equals in the question": DRAFT.replace("¿La API", "¿La ==API=="),
            "more than 8 criteria": DRAFT.replace("### Evidence", "".join(f"* El criterio {i} se cumple.\n" for i in range(8)) + "\n### Evidence"),
        }
        for name, draft in cases.items():
            with self.subTest(case=name):
                result = run(draft)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.strip())


if __name__ == "__main__":
    unittest.main()
