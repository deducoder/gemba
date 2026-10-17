"""Checks the script that converts the cancellation comment of the implement skills
to ADF: what it accepts, what it rejects and the smart link of `Replaced by`."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/scripts/cancelled.py"
SITE = "example.atlassian.net"

COMMENT = """### Cancelled

* Reason: el CSV ya lo entrega otra story.
* Found: ran: `python3 invoices.py acme --csv` → `number,total`
* Replaced by: ABC-99
"""


def run(comment):
    return subprocess.run([sys.executable, str(SCRIPT), "--site", SITE], input=comment, capture_output=True, text=True)


def lines(doc):
    """Returns the inline nodes of each bullet of the comment."""
    return [item["content"][0]["content"] for item in doc["content"][1]["content"]]


class CancellationComment(unittest.TestCase):
    def test_a_comment_that_follows_the_template_prints_its_adf(self):
        result = run(COMMENT)
        self.assertEqual(result.returncode, 0, result.stderr)
        doc = json.loads(result.stdout)
        self.assertEqual(doc["type"], "doc")
        self.assertEqual(doc["content"][0], {"type": "heading", "attrs": {"level": 3}, "content": [{"type": "text", "text": "Cancelled"}]})
        reason, found, _ = lines(doc)
        self.assertEqual("".join(n["text"] for n in reason), "Reason: el CSV ya lo entrega otra story.")
        self.assertIn({"type": "text", "text": "python3 invoices.py acme --csv", "marks": [{"type": "code"}]}, found)

    def test_replaced_by_a_key_is_a_smart_link_to_the_issue(self):
        replaced = lines(json.loads(run(COMMENT).stdout))[2]
        self.assertEqual(replaced, [
            {"type": "text", "text": "Replaced by: "},
            {"type": "inlineCard", "attrs": {"url": f"https://{SITE}/browse/ABC-99"}},
        ])

    def test_replaced_by_nothing_stays_as_text(self):
        result = run(COMMENT.replace("ABC-99", "Ninguno."))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(lines(json.loads(result.stdout))[2], [{"type": "text", "text": "Replaced by: Ninguno."}])

    def test_a_comment_without_the_heading_is_rejected(self):
        result = run(COMMENT.replace("### Cancelled\n", ""))
        self.assertEqual(result.returncode, 1)
        self.assertIn("### Cancelled", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_the_three_lines_go_in_their_order(self):
        swapped = COMMENT.replace("* Reason: el CSV ya lo entrega otra story.\n", "")
        swapped += "* Reason: el CSV ya lo entrega otra story.\n"
        result = run(swapped)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Reason, Found, Replaced by", result.stderr)

    def test_found_starts_with_ran_or_read(self):
        result = run(COMMENT.replace("Found: ran: ", "Found: "))
        self.assertEqual(result.returncode, 1)
        self.assertIn("'ran:' or 'read:'", result.stderr)

    def test_an_empty_line_is_rejected(self):
        result = run(COMMENT.replace("Reason: el CSV ya lo entrega otra story.", "Reason:"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("Reason", result.stderr)


if __name__ == "__main__":
    unittest.main()
