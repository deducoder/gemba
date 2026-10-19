"""Checks story-start's draft script: what it accepts, what it rejects and the
HTML it prints for Jira."""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "plugins/gemba-code/skills/story-start"
SCRIPT = SKILL / "scripts/story.py"
SITE = "example.atlassian.net"

DRAFT = """Let customers download their invoices

Como cliente, quiero descargar mis facturas, para llevar mis cuentas.

### Done when

* La página de facturas ofrece `Download` para cada factura.
* ==Si la factura no existe, la descarga responde 404.==

### Evidence

* read: `app/invoices.py:12`
* ran: `curl -i /invoices/0` → 404

### Out of scope

* Facturas de otros clientes
* Exportar a PDF → ABC-7
"""


def run(draft):
    return subprocess.run([sys.executable, str(SCRIPT), "--site", SITE], input=draft, capture_output=True, text=True)


class StoryDraft(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run(DRAFT)
        cls.story = json.loads(cls.result.stdout) if cls.result.returncode == 0 else {}

    def test_a_draft_that_follows_the_template_prints_the_summary_and_the_html(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr)
        story = self.story
        self.assertEqual(story["summary"], "Let customers download their invoices")
        headings = re.findall(r"<h3>(.+?)</h3>", story["description"])
        self.assertEqual(headings, ["Done when", "Out of scope"])

    def test_the_evidence_goes_to_a_comment_with_one_line_per_criterion(self):
        story = self.story
        lines = re.findall(r"<li><p>(.+?)</p></li>", story["comment"])
        self.assertEqual(lines, ["read: <code>app/invoices.py:12</code>", "ran: <code>curl -i /invoices/0</code> → 404"])

    def test_more_than_8_criteria_ask_to_split_the_story(self):
        criteria = "".join(f"* El criterio {i} se cumple.\n" for i in range(9))
        evidence = "".join(f"* read: `app.py:{i}`\n" for i in range(9))
        draft = DRAFT.split("### Done when")[0] + f"### Done when\n\n{criteria}\n### Evidence\n\n{evidence}\n### Out of scope\n\n* Nada\n"
        result = run(draft)
        self.assertEqual(result.returncode, 1)
        self.assertIn("split", result.stderr)
        self.assertEqual(run(draft.replace("* El criterio 8 se cumple.\n", "").replace("* read: `app.py:8`\n", "")).returncode, 0)

    def test_a_criterion_in_equals_reaches_jira_in_orange_except_its_code(self):
        description = self.story["description"]
        self.assertIn('<span style="color: #ff991f">Si la factura no existe, la descarga responde 404.</span>', description)
        self.assertNotIn("==", self.result.stdout)

    def test_code_in_backticks_becomes_a_code_mark(self):
        self.assertIn("<code>Download</code>", self.story["description"])

    def test_an_out_of_scope_key_becomes_a_link_to_the_issue(self):
        self.assertIn(f'<a href="https://{SITE}/browse/ABC-7" data-card-appearance="inline"></a>', self.story["description"])

    def test_the_opening_sentence_may_name_a_domain_or_a_version(self):
        draft = DRAFT.replace("para llevar mis cuentas.", "para llevar mis cuentas en claude.ai v1.2.")
        result = run(draft)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_code_may_hold_equals_and_arrows_and_keys_may_hold_underscores(self):
        draft = DRAFT.replace("* ran: `curl -i /invoices/0` → 404", "* ran: `python3 -c 'print(1 == 1)'` → True")
        draft = draft.replace("* Facturas de otros clientes", "* Renombrar `a → b`").replace("→ ABC-7", "→ MY_PROJ-7")
        result = run(draft)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"https://{SITE}/browse/MY_PROJ-7", result.stdout)

    def test_the_template_has_the_sections_the_script_expects(self):
        template = (SKILL / "assets/story.md").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"^### (.+)$", template, re.MULTILINE), ["Done when", "Evidence", "Out of scope"])

    def test_a_draft_off_the_template_exits_1_with_one_line_per_problem(self):
        cases = {
            "summary over 64": DRAFT.replace("Let customers download their invoices", "L" + "x" * 64),
            "summary with a final period": DRAFT.replace("their invoices\n", "their invoices.\n", 1),
            "a missing section": DRAFT.replace("### Evidence", "### Proof"),
            "evidence that does not match the criteria": DRAFT.replace("* ran: `curl -i /invoices/0` → 404\n", ""),
            "evidence without ran or read": DRAFT.replace("* read: `app/invoices.py:12`", "* see the code"),
            "an arrow to something that is not a key": DRAFT.replace("→ ABC-7", "→ a story of its own"),
            "equals outside Done when": DRAFT.replace("* Facturas de otros clientes", "* ==Facturas de otros clientes=="),
            "a repeated section": DRAFT + "\n### Out of scope\n\n* Otra cosa\n",
            "a partly wrapped criterion": DRAFT.replace("* ==Si la factura no existe, la descarga responde 404.==", "* ==Si la factura no existe== responde 404."),
            "equals in the Summary": DRAFT.replace("Let customers download", "Let ==customers== download"),
            "an empty bullet": DRAFT.replace("* Facturas de otros clientes", "* "),
            "a deduced criterion with only code": DRAFT.replace("* ==Si la factura no existe, la descarga responde 404.==", "* ==`--json`=="),
            "a line that is not a bullet": DRAFT.replace("* Facturas de otros clientes", "Facturas de otros clientes"),
            "two opening paragraphs": DRAFT.replace("para llevar mis cuentas.", "para llevar mis cuentas.\n\nOtra frase."),
            "no criteria": DRAFT.replace("* La página de facturas ofrece `Download` para cada factura.\n", "").replace(
                "* ==Si la factura no existe, la descarga responde 404.==\n", ""
            ),
        }
        for name, draft in cases.items():
            with self.subTest(case=name):
                result = run(draft)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.strip())


if __name__ == "__main__":
    unittest.main()
