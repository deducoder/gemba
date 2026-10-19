"""Checks project-create's merge script: the `edits` it builds to keep every section of a
published page as it is, nodes and local IDs included, taking from the new page only the
sections the person accepted."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/scripts/merge.py"

LIVE = ('<p data-local-id="a1">Primera línea publicada</p>'
        '<h2 data-local-id="a2">Problem</h2><p data-local-id="a3">Problema publicado</p>'
        '<h2 data-local-id="a4">Risks</h2><p data-local-id="a5">Riesgo publicado</p>'
        '<h2 data-local-id="a6">Decision</h2><p data-local-id="a7">Decisión publicada</p>')

NEW = ('<p>Primera línea regenerada</p>'
       '<h2>Problem</h2><p>Problema regenerado</p>'
       '<h2>Risks</h2><p>Riesgo nuevo</p>'
       '<h2>Decision</h2><p>Decisión nueva</p>')


def run(replace, live=LIVE, new=NEW):
    data = json.dumps({"live": live, "new": new, "replace": replace})
    return subprocess.run([sys.executable, str(SCRIPT)], input=data, capture_output=True, text=True)


def edits(replace, **kwargs):
    result = run(replace, **kwargs)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)["edits"]


class Merge(unittest.TestCase):
    def test_without_sections_nothing_changes(self):
        self.assertEqual(edits([]), [])

    def test_only_the_body_of_the_accepted_section_changes(self):
        found = edits(["Decision"])
        self.assertEqual(found, [
            {"name": "replaceNode", "localId": "a6", "value": "<h2>Decision</h2><p>Decisión nueva</p>"},
            {"name": "deleteNode", "localId": "a7"},
        ])

    def test_the_head_of_the_page_is_the_section_without_heading(self):
        found = edits([""])
        self.assertEqual(found, [
            {"name": "replaceNode", "localId": "a1", "value": "<p>Primera línea regenerada</p>"},
        ])

    def test_a_new_section_goes_after_the_nearest_earlier_kept_section(self):
        new = NEW.replace("<h2>Decision</h2>", "<h2>Withdrawn</h2><p>R-02 retirado</p><h2>Decision</h2>")
        found = edits(["Withdrawn"], new=new)
        self.assertEqual(found, [
            {"name": "insertNodeAfter", "localId": "a5", "value": "<h2>Withdrawn</h2><p>R-02 retirado</p>"},
        ])

    def test_a_new_section_with_nothing_earlier_kept_goes_before_the_first_live_node(self):
        live = LIVE[LIVE.index("<h2"):]
        new = NEW.replace("<h2>Problem</h2>", "<h2>Withdrawn</h2><p>R-02 retirado</p><h2>Problem</h2>")
        found = edits(["Withdrawn"], live=live, new=new)
        self.assertEqual(found, [
            {"name": "insertNodeBefore", "localId": "a2", "value": "<h2>Withdrawn</h2><p>R-02 retirado</p>"},
        ])

    def test_two_consecutive_new_sections_insert_in_their_own_order(self):
        new = NEW.replace("<h2>Decision</h2>", "<h2>Withdrawn</h2><p>uno</p><h2>Removed</h2><p>dos</p><h2>Decision</h2>")
        found = edits(["Withdrawn", "Removed"], new=new)
        self.assertEqual(found, [
            {"name": "insertNodeAfter", "localId": "a5", "value": "<h2>Withdrawn</h2><p>uno</p><h2>Removed</h2><p>dos</p>"},
        ])

    def test_an_accepted_section_the_new_page_drops_is_removed(self):
        new = NEW.split("<h2>Decision</h2>")[0]
        found = edits(["Decision"], new=new)
        self.assertEqual(found, [
            {"name": "deleteNode", "localId": "a6"},
            {"name": "deleteNode", "localId": "a7"},
        ])

    def test_a_section_with_several_body_nodes_deletes_each_one(self):
        live = LIVE.replace('<p data-local-id="a7">Decisión publicada</p>',
                             '<p data-local-id="a7">Decisión publicada</p><p data-local-id="a8">Más texto</p>')
        found = edits(["Decision"], live=live)
        self.assertEqual(found, [
            {"name": "replaceNode", "localId": "a6", "value": "<h2>Decision</h2><p>Decisión nueva</p>"},
            {"name": "deleteNode", "localId": "a7"},
            {"name": "deleteNode", "localId": "a8"},
        ])

    def test_an_empty_head_in_live_but_a_new_head_inserts_before_the_first_heading(self):
        live = LIVE[LIVE.index("<h2"):]
        found = edits([""], live=live, new=NEW)
        self.assertEqual(found, [
            {"name": "insertNodeBefore", "localId": "a2", "value": "<p>Primera línea regenerada</p>"},
        ])

    def test_a_section_neither_page_has(self):
        result = run(["Users"])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("Users", result.stderr)


if __name__ == "__main__":
    unittest.main()
