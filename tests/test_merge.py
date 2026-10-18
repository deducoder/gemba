"""Checks project-create's merge script: it keeps every section of a published page as it is
and takes from the new page only the sections the person accepted."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/skills/project-create/scripts/merge.py"


def h2(name, local):
    return {"type": "heading", "attrs": {"level": 2, "localId": local}, "content": [{"type": "text", "text": name}]}


def p(text, local=None):
    return {"type": "paragraph", **({"attrs": {"localId": local}} if local else {}), "content": [{"type": "text", "text": text}]}


LIVE = {"type": "doc", "version": 1, "content": [
    p("Primera línea publicada", "a1"),
    h2("Problem", "a2"), p("Problema publicado", "a3"),
    h2("Risks", "a4"), p("Riesgo publicado", "a5"),
    h2("Decision", "a6"), p("Decisión publicada", "a7"),
]}

NEW = {"type": "doc", "version": 1, "content": [
    p("Primera línea regenerada"),
    h2("Problem", None), p("Problema regenerado"),
    h2("Risks", None), p("Riesgo nuevo"),
    h2("Decision", None), p("Decisión nueva"),
]}


def run(replace, live=LIVE, new=NEW):
    data = json.dumps({"live": live, "new": new, "replace": replace})
    return subprocess.run([sys.executable, str(SCRIPT)], input=data, capture_output=True, text=True)


def merged(replace, **kwargs):
    result = run(replace, **kwargs)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def texts(doc):
    return [n["content"][0]["text"] for n in doc["content"]]


class Merge(unittest.TestCase):
    def test_without_sections_the_page_stays_as_published(self):
        self.assertEqual(merged([]), LIVE)

    def test_only_the_accepted_section_changes(self):
        doc = merged(["Decision"])
        self.assertEqual(doc["content"][:6], LIVE["content"][:6])
        self.assertEqual(texts(doc)[6:], ["Decision", "Decisión nueva"])

    def test_the_head_of_the_page_is_the_section_without_heading(self):
        doc = merged([""])
        self.assertEqual(texts(doc)[0], "Primera línea regenerada")
        self.assertEqual(doc["content"][1:], LIVE["content"][1:])

    def test_a_new_section_goes_where_the_new_page_puts_it(self):
        new = {"type": "doc", "version": 1, "content": NEW["content"][:5] + [h2("Withdrawn", None), p("R-02 retirado")] + NEW["content"][5:]}
        doc = merged(["Withdrawn"], new=new)
        self.assertEqual(texts(doc), ["Primera línea publicada", "Problem", "Problema publicado", "Risks", "Riesgo publicado",
                                      "Withdrawn", "R-02 retirado", "Decision", "Decisión publicada"])

    def test_a_section_neither_page_has(self):
        result = run(["Users"])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("Users", result.stderr)


if __name__ == "__main__":
    unittest.main()
