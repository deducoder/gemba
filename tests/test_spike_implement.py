"""Checks spike-implement's findings script: what it accepts, what it rejects and the HTML it
prints for the live doc that holds the findings of a spike."""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "plugins/gemba-code/skills/spike-implement"
SCRIPT = SKILL / "scripts/findings.py"
SITE = "example.atlassian.net"
KEY = "ABC-7"

QUESTION = "¿Puede SQLite garantizar con un índice parcial una sola bias activa por idol? De la respuesta depende el esquema de la historia de liberar biases."
OUTPUT = "1. primer apartado activo: ok\n2. mismo apartado activo: IntegrityError"

DRAFT = f"""ABC-7 Check a partial unique index for one active bias per idol

{QUESTION}

### Answer

Sí. Con SQLite 3.46.1, el índice parcial rechaza el segundo apartado activo con `sqlite3.IntegrityError`.

### Evidence

ran: `python3 probe.py` con este script, en un directorio temporal fuera del repositorio:

```python
print("probe")
```

Salida (exit 0):

```
{OUTPUT}
```

read: `invoices.py:6` → las facturas viven en la lista `INVOICES`

### Next

La historia de liberar biases cambia la restricción por el índice parcial.
"""


def run(draft, key=KEY):
    return subprocess.run([sys.executable, str(SCRIPT), "--site", SITE, "--key", key], input=draft, capture_output=True, text=True)


def rejected(draft, *words):
    result = run(draft)
    assert result.returncode == 1, result.stdout
    assert result.stdout == ""
    for word in words:
        assert word in result.stderr, result.stderr
    return result.stderr


def headings(html):
    return [(int(level), name) for level, name in re.findall(r"<h(\d)>(.+?)</h\1>", html)]


class FindingsDraft(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run(DRAFT)
        cls.page = json.loads(cls.result.stdout) if cls.result.returncode == 0 else {}
        cls.body = cls.page.get("body", "")

    def test_a_draft_that_follows_the_template_passes(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr)
        self.assertEqual(self.result.stderr, "")

    def test_the_title_is_the_key_and_the_summary(self):
        self.assertEqual(self.page["title"], "ABC-7 Check a partial unique index for one active bias per idol")

    def test_the_first_line_is_the_link_to_the_issue_as_a_smart_link_and_nothing_else(self):
        self.assertTrue(self.body.startswith(f'<p><a href="https://{SITE}/browse/{KEY}" data-card-appearance="inline"></a></p>'))

    def test_the_question_follows_without_a_heading(self):
        self.assertIn(f"<p>{QUESTION}</p>", self.body)

    def test_the_headings_are_answer_evidence_and_next_in_that_order(self):
        self.assertEqual(headings(self.body), [(2, "Answer"), (2, "Evidence"), (2, "Next")])

    def test_the_verdict_of_the_answer_is_bold(self):
        self.assertIn("<p><strong>Sí.</strong>", self.body)

    def test_evidence_keeps_each_script_and_output_literal_in_code_blocks(self):
        blocks = re.findall(r"<pre><code(?: class=\"language-(\w+)\")?>(.*?)</code></pre>", self.body, re.DOTALL)
        self.assertEqual([code for _, code in blocks], ['print("probe")', OUTPUT])
        self.assertEqual(blocks[0][0], "python")

    def test_a_language_with_a_quote_does_not_break_out_of_its_class_attribute(self):
        draft = DRAFT.replace('```python\nprint("probe")\n```', '```python"onmouseover="alert(1)\nprint("probe")\n```')
        result = run(draft)
        body = json.loads(result.stdout)["body"]
        self.assertIn('class="language-python&quot;onmouseover=&quot;alert(1)"', body)

    def test_each_ran_and_read_line_starts_with_its_label_in_bold(self):
        labels = re.findall(r"<p><strong>(ran: |read: )</strong>", self.body)
        self.assertEqual(labels, ["ran: ", "read: "])

    def test_it_writes_no_done_when_out_of_scope_time_or_status(self):
        for word in ("Done when", "Out of scope", "Status", "time-box"):
            self.assertNotIn(word, self.body)


class FindingsEvidence(unittest.TestCase):
    def test_an_empty_output_becomes_a_code_block_without_text(self):
        result = run(DRAFT.replace(OUTPUT, ""))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("<pre><code></code></pre>", json.loads(result.stdout)["body"])

    def test_consecutive_ran_and_read_lines_are_one_paragraph_each(self):
        draft = DRAFT.replace("read: `invoices.py:6`", "read: `a.py:1` → una\nread: `invoices.py:6`")
        result = run(draft)
        self.assertEqual(result.returncode, 0, result.stderr)
        labels = re.findall(r"<p><strong>(read: )</strong>", json.loads(result.stdout)["body"])
        self.assertEqual(len(labels), 2)


class FindingsRejects(unittest.TestCase):
    def test_a_title_that_does_not_start_with_the_key(self):
        rejected(DRAFT.replace("ABC-7 Check", "ABC-8 Check", 1), "title", "ABC-7")

    def test_a_question_that_is_not_one_paragraph(self):
        rejected(DRAFT.replace(QUESTION, QUESTION + "\n\nOtro párrafo."), "question")

    def test_sections_in_another_order(self):
        rejected(DRAFT.replace("### Next", "### Answer2"), "sections", "Answer, Evidence, Next")

    def test_a_done_when_section(self):
        rejected(DRAFT + "\n### Done when\n\n* Algo.\n", "sections")

    def test_an_answer_that_does_not_open_with_yes_no_or_inconclusive(self):
        rejected(DRAFT.replace("Sí. Con SQLite", "Quizá. Con SQLite"), "Answer", "sí, no o inconclusa")

    def test_an_answer_that_starts_with_a_word_that_is_not_a_verdict(self):
        for lead in ("No se pudo medir, pero", "Si el índice rechaza, entonces"):
            with self.subTest(lead=lead):
                rejected(DRAFT.replace("Sí. Con SQLite", f"{lead} con SQLite"), "Answer", "sí, no o inconclusa")

    def test_an_inconclusive_answer_passes(self):
        result = run(DRAFT.replace("Sí. Con SQLite", "Inconclusa. Con SQLite"))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_an_evidence_without_a_ran_or_read_line(self):
        draft = DRAFT.replace("ran: `python3 probe.py` con", "Corrí `python3 probe.py` con").replace("read: `invoices.py:6`", "Leí `invoices.py:6`")
        rejected(draft, "Evidence", "ran:")

    def test_an_unclosed_code_block(self):
        rejected(DRAFT.replace('print("probe")\n```', 'print("probe")\n'), "Evidence", "code block")

    def test_a_code_block_in_the_answer_or_in_next(self):
        rejected(DRAFT.replace("Sí. Con SQLite", "Sí.\n\n```\ncódigo\n```\n\nCon SQLite"), "Answer", "code blocks")
        rejected(DRAFT.replace("La historia de liberar", "```\ncódigo\n```\n\nLa historia de liberar"), "Next", "code blocks")

    def test_an_empty_next(self):
        rejected(DRAFT.replace("La historia de liberar biases cambia la restricción por el índice parcial.\n", ""), "Next")


if __name__ == "__main__":
    unittest.main()
