"""Checks the script that converts the cancellation comment of the implement skills
to HTML: what it accepts, what it rejects and the smart link of `Replaced by`."""

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


class CancellationComment(unittest.TestCase):
    def test_a_comment_that_follows_the_template_prints_its_html(self):
        result = run(COMMENT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("<h3>Cancelled</h3>"))
        self.assertIn("Reason: el CSV ya lo entrega otra story.", result.stdout)
        self.assertIn("<code>python3 invoices.py acme --csv</code>", result.stdout)

    def test_replaced_by_a_key_is_a_smart_link_to_the_issue(self):
        result = run(COMMENT)
        self.assertIn(f'Replaced by: <a href="https://{SITE}/browse/ABC-99" data-card-appearance="inline">', result.stdout)

    def test_replaced_by_nothing_stays_as_text(self):
        result = run(COMMENT.replace("ABC-99", "Ninguno."))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Replaced by: Ninguno.", result.stdout)
        self.assertNotIn("data-card-appearance", result.stdout)

    def test_replaced_by_holds_only_the_key_when_a_key_replaces_it(self):
        for value in ("ABC-99.", "ABC-99 (la story del CSV)", "abc-99"):
            with self.subTest(value=value):
                result = run(COMMENT.replace("ABC-99", value))
                self.assertEqual(result.returncode, 1)
                self.assertIn("Replaced by", result.stderr)

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
