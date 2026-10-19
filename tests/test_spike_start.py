"""Checks spike-start's draft script: what it accepts, what it rejects and the HTML it
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


def headings(html):
    return re.findall(r"<h3>(.+?)</h3>", html)


class SpikeDraft(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run(DRAFT)
        cls.spike = json.loads(cls.result.stdout) if cls.result.returncode == 0 else {}

    def test_a_draft_that_follows_the_template_prints_the_summary_and_the_html(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr)
        self.assertEqual(self.spike["summary"], "Check whether Acme Pay returns a customer's invoices as JSON")
        self.assertEqual(headings(self.spike["description"]), ["Done when", "Out of scope"])

    def test_the_question_opens_the_description_followed_by_the_decision(self):
        description = self.spike["description"]
        self.assertTrue(description.startswith(f"<p>{QUESTION} De la respuesta depende si <code>invoices.py</code> deja"))

    def test_the_evidence_goes_to_a_single_comment(self):
        comment = self.spike["comment"]
        self.assertTrue(comment.startswith("<h3>Evidence</h3>"))
        lines = re.findall(r"<li><p>(.+?)</p></li>", comment)
        self.assertEqual(lines, [
            "read: <code>invoices.py:6</code> → las facturas viven en la lista <code>INVOICES</code>",
            'ran: <code>grep -ri "acme pay" .</code> → sin resultados',
        ])

    def test_the_evidence_need_not_match_the_number_of_criteria(self):
        result = run(DRAFT.replace('* ran: `grep -ri "acme pay" .` → sin resultados\n', ""))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_criterion_in_equals_reaches_jira_in_orange_except_its_code(self):
        description = self.spike["description"]
        self.assertIn(
            '<span style="color: #ff991f">Cada afirmación lleva su </span><code>ran:</code>'
            '<span style="color: #ff991f"> o su fuente.</span>',
            description,
        )
        self.assertNotIn("==", self.result.stdout)

    def test_an_out_of_scope_key_becomes_a_link_to_the_issue(self):
        self.assertIn(f'<a href="https://{SITE}/browse/ABC-7" data-card-appearance="inline"></a>', self.spike["description"])

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
