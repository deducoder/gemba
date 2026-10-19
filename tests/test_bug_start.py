"""Checks bug-start's draft script: what it accepts, what it rejects and the HTML it
prints for Jira, the description and the Evidence comment."""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "plugins/gemba-code/skills/bug-start"
SCRIPT = SKILL / "scripts/bug.py"
SITE = "example.atlassian.net"

REPRODUCTION = """$ python3 invoices.py acme
F-001      100.00
### not a heading inside the fence"""

DRAFT = f"""Invoice totals leave out the tax

`python3 invoices.py acme` imprime en `develop` los totales sin el impuesto, y cada cliente ve un total menor al que paga.

### Root cause

`total()` causa totales sin impuesto porque devuelve el subtotal sin multiplicarlo por `1 + TAX`.

### Neighboring inputs

| Input | Current behavior |
| --- | --- |
| `python3 invoices.py nobody` | no imprime nada y sale con 0 |
| `python3 invoices.py` | imprime el uso y sale con 2 |

### Done when

* `python3 invoices.py acme` imprime `F-001 116.00`.
* ==El comportamiento de cada fila de Neighboring inputs no cambia.==

### Evidence

#### Reproduction

```
{REPRODUCTION}
```

#### Cause trail

* ran: `python3 -m unittest` → `FAILED (failures=1)`
* read: `invoices.py:16`

### Out of scope

* Redondear por línea → ABC-7
"""


def run(draft):
    return subprocess.run([sys.executable, str(SCRIPT), "--site", SITE], input=draft, capture_output=True, text=True)


def headings(html):
    return [(int(level), name) for level, name in re.findall(r"<h(\d)>(.+?)</h\1>", html)]


class BugDraft(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run(DRAFT)
        cls.bug = json.loads(cls.result.stdout) if cls.result.returncode == 0 else {}

    def test_a_draft_that_follows_the_template_prints_the_summary_the_description_and_the_comment(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr)
        self.assertEqual(self.bug["summary"], "Invoice totals leave out the tax")
        self.assertTrue(self.bug["description"].startswith("<p>"))
        self.assertTrue(self.bug["comment"].startswith("<h3>Evidence</h3>"))

    def test_the_description_holds_the_failure_the_cause_the_neighbors_and_the_contract(self):
        description = self.bug["description"]
        self.assertTrue(description.startswith("<p>"))
        self.assertEqual(headings(description), [(3, "Root cause"), (3, "Neighboring inputs"), (3, "Done when"), (3, "Out of scope")])
        self.assertIn("devuelve el subtotal sin multiplicarlo", description)
        self.assertNotIn("Reproduction", description)
        self.assertNotIn("ran: ", description)

    def test_the_neighboring_inputs_become_a_table_with_its_header(self):
        description = self.bug["description"]
        self.assertEqual(description.count("<table>"), 1)
        table = re.search(r"<table>(.*?)</table>", description, re.DOTALL).group(1)
        self.assertEqual(re.findall(r"<th><p>(.+?)</p></th>", table), ["Input", "Current behavior"])
        self.assertEqual(re.findall(r"<td><p>(.+?)</p></td>", table)[::2], ["<code>python3 invoices.py nobody</code>", "<code>python3 invoices.py</code>"])

    def test_the_evidence_goes_to_one_comment_with_the_reproduction_and_the_cause_trail(self):
        comment = self.bug["comment"]
        self.assertEqual(headings(comment), [(3, "Evidence"), (4, "Reproduction"), (4, "Cause trail")])
        self.assertIn(f"<pre><code>{REPRODUCTION}</code></pre>", comment)
        self.assertEqual(
            re.findall(r"<li><p>(.+?)</p></li>", comment),
            ["ran: <code>python3 -m unittest</code> → <code>FAILED (failures=1)</code>", "read: <code>invoices.py:16</code>"],
        )

    def test_a_criterion_in_equals_reaches_jira_in_orange(self):
        description = self.bug["description"]
        self.assertIn('<span style="color: #ff991f">El comportamiento de cada fila de Neighboring inputs no cambia.</span>', description)
        self.assertNotIn("==", self.result.stdout)

    def test_an_out_of_scope_key_becomes_a_link_to_the_issue(self):
        self.assertIn(f'<a href="https://{SITE}/browse/ABC-7" data-card-appearance="inline"></a>', self.bug["description"])

    def test_an_out_of_scope_with_nothing_to_exclude_is_accepted(self):
        result = run(DRAFT.replace("* Redondear por línea → ABC-7", "* Ninguno."))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_the_template_has_the_sections_the_script_expects(self):
        template = (SKILL / "assets/bug.md").read_text(encoding="utf-8")
        outside_fences = re.sub(r"^```.*?^```$", "", template, flags=re.MULTILINE | re.DOTALL)
        self.assertEqual(
            re.findall(r"^#{3,4} (.+)$", outside_fences, re.MULTILINE),
            ["Root cause", "Neighboring inputs", "Done when", "Evidence", "Reproduction", "Cause trail", "Out of scope"],
        )

    def test_a_root_cause_heading_in_the_evidence_is_rejected_asking_for_the_cause_trail(self):
        result = run(DRAFT.replace("#### Cause trail\n", "#### Root cause\n"))
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("#### Cause trail", result.stderr)

    def test_a_draft_off_the_template_exits_1_with_one_line_per_problem(self):
        cases = {
            "summary over 64": DRAFT.replace("Invoice totals leave out the tax", "I" + "x" * 64),
            "summary with a final period": DRAFT.replace("leave out the tax\n", "leave out the tax.\n", 1),
            "no failure paragraph": re.sub(r"\n`python3 invoices.py acme` imprime en[^\n]*\n", "\n", DRAFT, count=1),
            "a missing section": DRAFT.replace("### Neighboring inputs", "### Nearby"),
            "sections out of order": DRAFT.replace("### Root cause\n", "### Tmp\n", 1).replace("### Neighboring inputs", "### Root cause").replace("### Tmp", "### Neighboring inputs"),
            "a root cause of two lines": DRAFT.replace("por `1 + TAX`.", "por `1 + TAX`.\n\nY otra frase."),
            "a root cause with its evidence in the description": DRAFT.replace("por `1 + TAX`.", "por `1 + TAX`.\n\nread: `invoices.py:16`"),
            "a table with another header": DRAFT.replace("| Input | Current behavior |", "| Entrada | Comportamiento |"),
            "a table without rows": re.sub(r"\| `python3 invoices.py[^\n]*\n", "", DRAFT),
            "a row with one cell": DRAFT.replace("| `python3 invoices.py` | imprime el uso y sale con 2 |", "| `python3 invoices.py` |"),
            "a reproduction without a fenced block": DRAFT.replace("```\n" + REPRODUCTION + "\n```", REPRODUCTION.splitlines()[0]),
            "an empty reproduction": DRAFT.replace(REPRODUCTION, ""),
            "evidence without ran or read": DRAFT.replace("* read: `invoices.py:16`", "* see the code"),
            "evidence without its cause trail": DRAFT.replace("#### Cause trail\n", "#### Cause\n"),
            "an arrow to something that is not a key": DRAFT.replace("→ ABC-7", "→ a story of its own"),
            "equals outside Done when": DRAFT.replace("* Redondear por línea → ABC-7", "* ==Redondear por línea=="),
            "a partly wrapped criterion": DRAFT.replace("* ==El comportamiento de cada fila", "* ==El comportamiento== de cada fila").replace("no cambia.==", "no cambia."),
            "a line that is not a bullet": DRAFT.replace("* Redondear por línea → ABC-7", "Redondear por línea"),
            "no criteria": re.sub(r"### Done when\n\n(\* [^\n]*\n)+", "### Done when\n\n", DRAFT),
            "a repeated section": DRAFT + "\n### Out of scope\n\n* Otra cosa\n",
        }
        for name, draft in cases.items():
            with self.subTest(case=name):
                result = run(draft)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.strip())


if __name__ == "__main__":
    unittest.main()
