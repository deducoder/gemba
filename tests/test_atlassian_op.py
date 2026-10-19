"""Checks the script that resolves an Atlassian operation name to the connector tool(s), tier,
key parameters and format of plugins/gemba-code/references/atlassian.json."""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/scripts/atlassian_op.py"


def run(*names):
    return subprocess.run([sys.executable, str(SCRIPT), *names], capture_output=True, text=True)


class AtlassianOperation(unittest.TestCase):
    def test_a_primary_operation_resolves_its_tool_tier_params_and_format(self):
        result = run("getJiraIssue")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("getJiraIssue (primaria)", result.stdout)
        self.assertIn("params:", result.stdout)
        self.assertIn("format:", result.stdout)

    def test_an_executeread_and_an_executewrite_operation_resolve(self):
        result = run("getTransitionsForJiraIssue", "addWorklogToJiraIssue")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("listJiraIssueTransitions (executeRead)", result.stdout)
        self.assertIn("addOrEditJiraIssueWorklog (executeWrite)", result.stdout)

    def test_an_operation_with_two_tools_lists_both_with_their_tier(self):
        result = run("lookupJiraAccountId")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("lookupJiraAccountId (executeRead)", result.stdout)
        self.assertIn("atlassianUserInfo (primaria)", result.stdout)

    def test_an_unknown_operation_says_so_instead_of_failing(self):
        result = run("notAnOperation")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("notAnOperation: operación no encontrada", result.stdout)

    def test_several_operations_each_print_their_own_line(self):
        result = run("getJiraIssue", "manageJiraProjectVersion")
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 2)


if __name__ == "__main__":
    unittest.main()
