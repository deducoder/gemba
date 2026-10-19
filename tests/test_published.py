"""Checks published's HTML parsing: splitting a published page into its top-level nodes and
their sections, by data-local-id."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plugins/gemba-code/scripts"))

from published import sections, top_level_nodes  # noqa: E402


class TopLevelNodes(unittest.TestCase):
    def test_splits_siblings_by_their_own_tag(self):
        html = '<p data-local-id="a1">Uno</p><h2 data-local-id="a2">Dos</h2>'
        self.assertEqual(top_level_nodes(html), [
            ("a1", '<p data-local-id="a1">Uno</p>', "p"),
            ("a2", '<h2 data-local-id="a2">Dos</h2>', "h2"),
        ])

    def test_a_node_without_a_local_id_has_none(self):
        self.assertEqual(top_level_nodes("<p>Sin id</p>"), [(None, "<p>Sin id</p>", "p")])

    def test_nested_tags_of_the_same_name_do_not_end_the_node_early(self):
        html = '<div data-local-id="a1" data-type="panel-info"><ul><li><p>a</p></li><li><p>b</p></li></ul></div>'
        nodes = top_level_nodes(html)
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0][0], "a1")
        self.assertEqual(nodes[0][2], "div")

    def test_a_void_element_is_its_own_node_with_no_closing_tag(self):
        html = '<p data-local-id="a1">a</p><br><p data-local-id="a2">b</p>'
        nodes = top_level_nodes(html)
        self.assertEqual([tag for _, _, tag in nodes], ["p", "br", "p"])

    def test_a_full_uuid_local_id_is_read_too(self):
        html = '<span data-local-id="54e857d6-18db-4c4b-99a7-dc7308c76b2e">x</span>'
        self.assertEqual(top_level_nodes(html)[0][0], "54e857d6-18db-4c4b-99a7-dc7308c76b2e")


class Sections(unittest.TestCase):
    def test_the_head_of_the_page_is_the_section_without_a_name(self):
        html = '<p data-local-id="a1">Intro</p><h2 data-local-id="a2">Problem</h2><p data-local-id="a3">Texto</p>'
        found = sections(html)
        self.assertEqual([name for name, _, _ in found], ["", "Problem"])
        self.assertEqual(found[0][1], None)
        self.assertEqual([lid for lid, _ in found[0][2]], ["a1"])
        self.assertEqual(found[1][1], "a2")
        self.assertEqual([lid for lid, _ in found[1][2]], ["a3"])

    def test_a_section_with_several_body_nodes_keeps_them_all(self):
        html = '<h2 data-local-id="a1">Risks</h2><p data-local-id="a2">Uno</p><p data-local-id="a3">Dos</p>'
        found = sections(html)
        self.assertEqual([lid for lid, _ in found[1][2]], ["a2", "a3"])

    def test_an_empty_head_has_no_body_nodes(self):
        html = '<h2 data-local-id="a1">Problem</h2><p data-local-id="a2">Texto</p>'
        found = sections(html)
        self.assertEqual(found[0], ("", None, []))


if __name__ == "__main__":
    unittest.main()
