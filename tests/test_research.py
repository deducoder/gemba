"""Checks research's draft script: what it accepts, what it rejects and the HTML it prints
for the live doc that holds the answer to a question."""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "plugins/gemba-code/skills/research"
SCRIPT = SKILL / "scripts/research.py"
SITE = "example.atlassian.net"
URL_ONE = "https://www.sqlite.org/partialindex.html"
URL_TWO = "https://example.com/blog/partial-indexes"

QUESTION = "¿Puede SQLite garantizar con un índice parcial una sola bias activa por idol?"

DRAFT = f"""{QUESTION}

Decide el esquema de la historia de liberar biases y lo espera quien la implementa.

### Answer

Sí. Un índice único parcial rechaza la segunda fila activa [Finding 1.1] y funciona desde SQLite 3.8.0 [Finding 1.2].

### Method

Se leyó la documentación oficial de SQLite y un artículo de apoyo.

### Findings

#### 1. Índices parciales

1.1 Documented: un índice parcial solo indexa las filas que cumplen su `WHERE`, y si es único solo restringe esas filas [1]
1.2 Inferred: la versión mínima es la que introdujo los índices parciales (from 1.1)
1.3 Unverified: el rendimiento con millones de filas

### Sources

[1] {URL_ONE} (official, 2026-10-17): la página de índices parciales de la documentación de SQLite
[2] {URL_TWO} (secondary, 2026-10-17): un artículo que repite el ejemplo

### Next

Declarar la historia de liberar biases con el índice parcial.
"""


def run(draft, *args):
    return subprocess.run([sys.executable, str(SCRIPT), "--site", SITE, *args], input=draft, capture_output=True, text=True)


def rejected(draft, *words, args=()):
    result = run(draft, *args)
    assert result.returncode == 1, result.stdout
    assert result.stdout == ""
    for word in words:
        assert word in result.stderr, result.stderr
    return result.stderr


def headings(html, level=2):
    return re.findall(rf"<h{level}>(.+?)</h{level}>", html)


class ResearchDraft(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run(DRAFT)
        cls.page = json.loads(cls.result.stdout) if cls.result.returncode == 0 else {}
        cls.body = cls.page.get("body", "")

    def test_a_draft_that_follows_the_template_passes(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr)
        self.assertEqual(self.result.stderr, "")

    def test_the_title_is_the_question(self):
        self.assertEqual(self.page["title"], QUESTION)

    def test_without_a_key_the_page_opens_with_the_decision_sentence(self):
        self.assertTrue(self.body.startswith("<p>Decide el esquema de la historia de liberar biases y lo espera quien la implementa.</p>"))

    def test_the_headings_are_the_five_sections_in_order(self):
        self.assertEqual(headings(self.body), ["Answer", "Method", "Findings", "Sources", "Next"])

    def test_the_topics_are_level_three_headings(self):
        self.assertEqual(headings(self.body, 3), ["1. Índices parciales"])

    def test_the_citation_number_of_a_finding_links_to_its_source(self):
        self.assertIn(f'<a href="{URL_ONE}">[1]</a>', self.body)

    def test_a_number_inside_a_code_span_is_code_and_not_a_citation(self):
        draft = DRAFT.replace("su `WHERE`,", "su `WHERE`, como `arr[1]`,")
        result = run(draft)
        self.assertEqual(result.returncode, 0, result.stderr)
        body = json.loads(result.stdout)["body"]
        self.assertIn("<code>arr[1]</code>", body)
        self.assertEqual(re.findall(r'<a href="[^"]+">(\[\d+\])</a>', body), ["[1]"])

    def test_the_state_of_each_finding_is_bold(self):
        self.assertEqual(
            re.findall(r"<strong>(\d\.\d (?:Documented|Inferred|Unverified)):</strong>", self.body),
            ["1.1 Documented", "1.2 Inferred", "1.3 Unverified"],
        )

    def test_each_source_is_a_smart_link_followed_by_its_kind_and_date(self):
        cards = re.findall(r'<p>\[\d+\] <a href="([^"]+)" data-card-appearance="inline"></a>(.+?)</p>', self.body)
        self.assertEqual([url for url, _ in cards], [URL_ONE, URL_TWO])
        self.assertIn("(official, 2026-10-17)", cards[0][1])

    def test_the_finding_citations_of_the_answer_stay_plain_text(self):
        answer = re.search(r"<p>(Sí\..+?\[Finding 1\.2\]\.)</p>", self.body).group(1)
        self.assertNotIn("<a ", answer)


class ResearchKey(unittest.TestCase):
    def test_a_key_opens_the_page_with_a_smart_link_to_the_issue(self):
        result = run(DRAFT, "--key", "ABC-7")
        self.assertEqual(result.returncode, 0, result.stderr)
        body = json.loads(result.stdout)["body"]
        self.assertTrue(body.startswith(f'<p><a href="https://{SITE}/browse/ABC-7" data-card-appearance="inline"></a></p>'))

    def test_a_key_that_is_not_a_work_item_key(self):
        rejected(DRAFT, "key", args=("--key", "abc7"))


class ResearchRejects(unittest.TestCase):
    def test_a_title_that_is_not_a_question(self):
        rejected(DRAFT.replace("por idol?", "por idol."), "title", "?")

    def test_a_draft_without_sources(self):
        draft = DRAFT[:DRAFT.index("[1] https")] + DRAFT[DRAFT.index("### Next"):]
        rejected(draft, "Sources")

    def test_an_answer_that_cites_no_finding(self):
        rejected(DRAFT.replace("[Finding 1.1]", "").replace("[Finding 1.2]", ""), "Answer")

    def test_an_answer_that_cites_a_finding_that_does_not_exist(self):
        rejected(DRAFT.replace("[Finding 1.2]", "[Finding 9.9]"), "Answer", "9.9")

    def test_a_documented_finding_without_a_source(self):
        rejected(DRAFT.replace(" [1]\n1.2", "\n1.2"), "1.1", "Documented")

    def test_a_documented_finding_that_cites_a_source_that_does_not_exist(self):
        rejected(DRAFT.replace(" [1]\n1.2", " [7]\n1.2"), "1.1", "7")

    def test_an_inferred_finding_that_does_not_say_what_it_follows_from(self):
        rejected(DRAFT.replace(" (from 1.1)", ""), "1.2", "Inferred")

    def test_an_inferred_finding_that_cites_a_source_that_does_not_exist(self):
        rejected(DRAFT.replace("los índices parciales (from 1.1)", "los índices parciales [5] (from 1.1)"), "1.2", "5")

    def test_an_inferred_finding_that_follows_a_finding_that_does_not_exist(self):
        rejected(DRAFT.replace("(from 1.1)", "(from 9.9)"), "1.2", "9.9")

    def test_an_unverified_finding_with_a_source(self):
        rejected(DRAFT.replace("millones de filas", "millones de filas [1]"), "1.3", "Unverified")

    def test_a_state_that_is_not_documented_inferred_or_unverified(self):
        rejected(DRAFT.replace("1.3 Unverified", "1.3 Observed"), "1.3")

    def test_a_secondary_source_before_an_official_one(self):
        swapped = DRAFT.replace(f"[1] {URL_ONE} (official", f"[1] {URL_TWO} (secondary", 1).replace(
            f"[2] {URL_TWO} (secondary", f"[2] {URL_ONE} (official", 1)
        rejected(swapped, "secondary")

    def test_a_url_with_a_quote_does_not_break_out_of_its_href(self):
        quoted_url = 'https://example.com/x"onmouseover="alert(1)'
        draft = DRAFT.replace(URL_ONE, quoted_url)
        result = run(draft)
        body = json.loads(result.stdout)["body"]
        self.assertIn('href="https://example.com/x&quot;onmouseover=&quot;alert(1)"', body)
        self.assertNotIn('href="https://example.com/x"onmouseover="alert(1)"', body)

    def test_a_source_without_its_kind_and_date(self):
        rejected(DRAFT.replace("(official, 2026-10-17)", ""), "Sources")

    def test_sections_in_another_order(self):
        rejected(DRAFT.replace("### Method", "### Sources2"), "sections")

    def test_a_section_without_content(self):
        rejected(DRAFT.replace("Declarar la historia de liberar biases con el índice parcial.\n", ""), "Next")
