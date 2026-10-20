"""Checks project-create's license script: parsing the origin remote and the choosealicense.com
template, without hitting the network."""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/skills/project-create/scripts/license.py"

sys.path.insert(0, str(SCRIPT.parent))
from license import mit_body, owner_and_repo  # noqa: E402

MIT_TEMPLATE = """---
title: MIT License
spdx-id: MIT
---

MIT License

Copyright (c) [year] [fullname]

Permission is hereby granted.
"""


class OwnerAndRepo(unittest.TestCase):
    def test_https_url(self):
        self.assertEqual(owner_and_repo("https://github.com/deducoder/gemba"), ("deducoder", "gemba"))

    def test_https_url_with_dot_git(self):
        self.assertEqual(owner_and_repo("https://github.com/deducoder/gemba.git"), ("deducoder", "gemba"))

    def test_ssh_url(self):
        self.assertEqual(owner_and_repo("git@github.com:deducoder/gemba.git"), ("deducoder", "gemba"))

    def test_a_non_github_remote_is_none(self):
        self.assertIsNone(owner_and_repo("https://gitlab.com/deducoder/gemba.git"))


class MitBody(unittest.TestCase):
    def test_strips_the_front_matter(self):
        body = mit_body(MIT_TEMPLATE)
        self.assertTrue(body.startswith("MIT License"))
        self.assertNotIn("spdx-id", body)

    def test_keeps_the_placeholders(self):
        self.assertIn("Copyright (c) [year] [fullname]", mit_body(MIT_TEMPLATE))


class CommandLine(unittest.TestCase):
    def test_an_unknown_license_is_rejected(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "gpl-3.0"], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("gpl-3.0", result.stderr)


if __name__ == "__main__":
    unittest.main()
