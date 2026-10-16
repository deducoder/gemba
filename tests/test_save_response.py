"""Checks the script that saves a real Jira response for the mock tests: what it leaves out of
the response it writes and how it hides the project it was captured from."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "evals/save_response.py"
RESPONSE = {
    "issues": {"nodes": [{
        "id": "10", "key": "XYZ-7", "self": "https://api.atlassian.com/ex/jira/1/rest/api/3/issue/10",
        "fields": {
            "summary": "Mention XYZ-6 and the XYZ board",
            "project": {"key": "XYZ", "avatarUrls": {"48x48": "https://example.com/avatar/1"}},
            "assignee": {"accountId": "712020:abc", "emailAddress": "someone@example.com",
                         "displayName": "Someone", "avatarUrls": {"16x16": "https://example.com/avatar/2"}},
            "status": {"name": "Backlog", "iconUrl": "https://example.com/avatar/3"},
            "comment": {"comments": [{"id": "1", "author": {"accountId": "712020:abc"}}]},
        },
        "webUrl": "https://example.atlassian.net/browse/XYZ-7",
    }]},
    "context": {"atlassianAccountId": "712020:abc", "toolName": "getJiraIssue"},
}


class SaveResponse(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        (self.root / "evals").mkdir()
        shutil.copy(SCRIPT, self.root / "evals")

    def save(self, response, tool="getJiraIssue", project="XYZ"):
        result = subprocess.run([sys.executable, self.root / "evals/save_response.py", tool, project],
                                input=json.dumps(response), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads((self.root / f"tests/fixtures/atlassian-responses/{tool}.json").read_text(encoding="utf-8"))

    def test_leaves_out_personal_data_at_any_depth(self):
        saved = json.dumps(self.save(RESPONSE))
        for key in ("accountId", "atlassianAccountId", "emailAddress", "avatarUrls", "iconUrl", "self"):
            with self.subTest(key=key):
                self.assertNotIn(f'"{key}"', saved)
        self.assertNotIn("avatar", saved)

    def test_keeps_the_other_keys(self):
        node = self.save(RESPONSE)["issues"]["nodes"][0]
        self.assertEqual(node["fields"]["assignee"], {"displayName": "Someone"})
        self.assertEqual(node["fields"]["status"], {"name": "Backlog"})
        self.assertEqual(node["fields"]["comment"]["comments"], [{"id": "1", "author": {}}])

    def test_names_the_project_abc(self):
        node = self.save(RESPONSE)["issues"]["nodes"][0]
        self.assertEqual(node["key"], "ABC-7")
        self.assertEqual(node["fields"]["project"], {"key": "ABC"})
        self.assertEqual(node["fields"]["summary"], "Mention ABC-6 and the ABC board")
        self.assertEqual(node["webUrl"], "https://example.atlassian.net/browse/ABC-7")

    def test_writes_one_file_per_tool(self):
        self.save({"id": "1", "timeSpent": "1h"}, tool="addWorklogToJiraIssue")
        self.save({"id": "2", "body": "x"}, tool="addCommentToJiraIssue")
        saved = sorted(p.name for p in (self.root / "tests/fixtures/atlassian-responses").iterdir())
        self.assertEqual(saved, ["addCommentToJiraIssue.json", "addWorklogToJiraIssue.json"])


if __name__ == "__main__":
    unittest.main()
