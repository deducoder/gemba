"""Checks epic-start's draft script: what it accepts, what it rejects and the
ADF it prints for Jira."""

import json
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


def run(draft):
    return subprocess.run([sys.executable, str(SCRIPT), "--site", SITE], input=draft, capture_output=True, text=True)


def criteria(count):
    return "".join(f"* El criterio {i} se cumple.\n" for i in range(count))


def with_criteria(count):
    return DRAFT.split("### Done when")[0] + f"### Done when\n\n{criteria(count)}\n### Out of scope\n\n* Nada\n"


class EpicDraft(unittest.TestCase):
    def test_a_draft_that_follows_the_template_prints_the_summary_and_the_adf(self):
        result = run(DRAFT)
        self.assertEqual(result.returncode, 0, result.stderr)
        epic = json.loads(result.stdout)
        self.assertEqual(set(epic), {"summary", "description"})
        self.assertEqual(epic["summary"], "Customers manage their invoices from the CLI")
        headings = [n["content"][0]["text"] for n in epic["description"]["content"] if n["type"] == "heading"]
        self.assertEqual(headings, ["Done when", "Out of scope"])

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


if __name__ == "__main__":
    unittest.main()
