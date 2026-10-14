"""Checks what session-close's handoff.py does, by running it in a throwaway repository."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "plugins/gemba/skills/session-close/scripts/handoff.py"
VALID = "# Session 2026-10-14 01:10 — demo\n\n## Done\n\n- x\n\n## Decided\n\n- y — why: z\n\n## Open\n\n## Next\n\nEdit a file\n"
SAVED = ".gemba/sessions/2026-10-14-0110-demo-run.md"
ENV = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}  # keep git inside the temp repo


class Handoff(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, env=ENV, check=True)

    def save(self, text, slug="demo-run", cwd=None):
        return subprocess.run(
            [sys.executable, SCRIPT, slug], input=text, capture_output=True, text=True, cwd=cwd or self.repo, env=ENV
        )

    def test_saves_the_handoff_out_of_git_status(self):
        result = self.save(VALID)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.repo / SAVED).is_file())
        status = subprocess.run(["git", "status", "--short"], cwd=self.repo, env=ENV, capture_output=True, text=True)
        self.assertEqual(status.stdout, "")

    def test_rejects_a_name_that_already_exists(self):
        self.assertEqual(self.save(VALID).returncode, 0)
        self.assertEqual(self.save(VALID).returncode, 1)

    def test_reports_every_problem_at_once_and_writes_nothing(self):
        result = self.save("# Session today\n\n## Done\n\n## Next\n\n- a\n- b\n", slug="X")
        self.assertEqual(result.returncode, 1)
        for problem in ("slug", "title:", "sections:", "Done:", "Next:"):
            self.assertIn(problem, result.stderr)
        self.assertFalse((self.repo / ".gemba").exists())

    def test_accepts_an_empty_decided(self):
        result = self.save(VALID.replace("- y — why: z\n\n", ""))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_keeps_an_edited_sessions_gitignore(self):
        ignore = self.repo / ".gemba/sessions/.gitignore"
        ignore.parent.mkdir(parents=True)
        ignore.write_text("*\n!keep.md\n", encoding="utf-8")
        self.assertEqual(self.save(VALID).returncode, 0)
        self.assertEqual(ignore.read_text(encoding="utf-8"), "*\n!keep.md\n")

    def test_saves_at_the_repository_root_from_a_subdirectory(self):
        subdirectory = self.repo / "src"
        subdirectory.mkdir()
        self.assertEqual(self.save(VALID, cwd=subdirectory).returncode, 0)
        self.assertTrue((self.repo / SAVED).is_file())


if __name__ == "__main__":
    unittest.main()
