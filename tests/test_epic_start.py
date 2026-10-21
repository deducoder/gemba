"""Checks epic-start's draft script: what it accepts, what it rejects and the
HTML it prints for Jira."""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/skills/epic-start/scripts/epic.py"
SITE = "example.atlassian.net"

DRAFT = """Customers manage their invoices from the CLI

Quien factura puede consultar, exportar y enviar sus facturas desde la CLI, sin abrir la base de datos.

### Done when

* `invoices.py` lista las facturas de un cliente con su total.
* ==Un cliente sin facturas recibe un mensaje y el código 1.==

### Out of scope

* Facturas de otros clientes
* Exportar a PDF → ABC-7
"""


def run(draft, requirements=None):
    args = [sys.executable, str(SCRIPT), "--site", SITE]
    if requirements:
        args += ["--requirements", requirements]
    return subprocess.run(args, input=draft, capture_output=True, text=True)


def criteria(count):
    return "".join(f"* El criterio {i} se cumple.\n" for i in range(count))


def with_criteria(count):
    return DRAFT.split("### Done when")[0] + f"### Done when\n\n{criteria(count)}\n### Out of scope\n\n* Nada\n"


class EpicDraft(unittest.TestCase):
    def test_a_draft_that_follows_the_template_prints_the_summary_and_the_html(self):
        result = run(DRAFT)
        self.assertEqual(result.returncode, 0, result.stderr)
        epic = json.loads(result.stdout)
        self.assertEqual(set(epic), {"summary", "description"})
        self.assertEqual(epic["summary"], "Customers manage their invoices from the CLI")
        import re
        self.assertEqual(re.findall(r"<h3>(.+?)</h3>", epic["description"]), ["Done when", "Out of scope"])

    def test_more_than_8_criteria_are_rejected(self):
        result = run(with_criteria(9))
        self.assertEqual(result.returncode, 1)
        self.assertIn("8", result.stderr)
        self.assertEqual(run(with_criteria(8)).returncode, 0)

    def test_an_evidence_section_is_rejected(self):
        draft = DRAFT.replace("### Out of scope", "### Evidence\n\n* read: `invoices.py:1`\n* read: `invoices.py:2`\n\n### Out of scope")
        result = run(draft)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Evidence", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_the_opening_is_a_single_paragraph(self):
        draft = DRAFT.replace("sin abrir la base de datos.\n", "sin abrir la base de datos.\n\nOtro párrafo.\n")
        result = run(draft)
        self.assertEqual(result.returncode, 1)
        self.assertIn("paragraph", result.stderr)


class EpicRequirements(unittest.TestCase):
    REQUIREMENTS = f"https://{SITE}/wiki/spaces/ABC/pages/1/Requirements"

    def test_each_requirement_a_merged_criterion_cites_links_to_the_requirements_page(self):
        draft = DRAFT.replace(
            "* ==Un cliente sin facturas recibe un mensaje y el código 1.==",
            "* ==Un cliente sin facturas recibe un mensaje y el código 1 (R-15, R-16).==",
        )
        result = run(draft, requirements=self.REQUIREMENTS)
        self.assertEqual(result.returncode, 0, result.stderr)
        description = json.loads(result.stdout)["description"]
        self.assertIn(f'<a href="{self.REQUIREMENTS}">R-15</a>', description)
        self.assertIn(f'<a href="{self.REQUIREMENTS}">R-16</a>', description)

    def test_without_the_page_the_requirement_stays_text(self):
        draft = DRAFT.replace(
            "* ==Un cliente sin facturas recibe un mensaje y el código 1.==",
            "* ==Un cliente sin facturas recibe un mensaje y el código 1 (R-15).==",
        )
        result = run(draft)
        self.assertEqual(result.returncode, 0, result.stderr)
        description = json.loads(result.stdout)["description"]
        self.assertIn("R-15", description)
        self.assertIsNone(re.search(r'<a href="[^"]*">R-15</a>', description))


if __name__ == "__main__":
    unittest.main()
