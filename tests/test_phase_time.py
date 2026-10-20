"""Checks the phase time script: the plain elapsed minutes between the marks of a phase
and the worklog it prints."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/scripts/phase_time.py"
DAY = "2026-10-15T"
ZONE = "-06:00"


def at(clock):
    return f"{DAY}{clock}{ZONE}"


def git(cwd, *args, date=None):
    env = dict(os.environ, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date) if date else None
    return subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", *args],
        cwd=cwd, capture_output=True, text=True, check=True, env=env,
    ).stdout.strip()


class PhaseTime(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cwd = Path(self.tmp.name)

    def run_script(self, start, end=None):
        args = ["--start", start] + (["--end", end] if end else [])
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=self.cwd, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def minutes(self, start, end):
        return self.run_script(at(start), at(end))["minutes"]

    def test_a_phase_is_the_plain_interval_of_its_marks(self):
        self.assertEqual(self.minutes("00:54:27", "01:03:46"), 9)

    def test_a_long_phase_is_still_its_plain_interval(self):
        self.assertEqual(self.minutes("03:19:50", "11:53:41"), 514)

    def test_commits_between_the_marks_do_not_change_the_result(self):
        git(self.cwd, "init", "-q", "-b", "develop")
        (self.cwd / "a").write_text("a")
        git(self.cwd, "add", "a")
        git(self.cwd, "commit", "-qam", "change at 00:56:49", date=at("00:56:49"))
        self.assertEqual(self.minutes("00:54:27", "01:03:46"), 9)

    def test_outside_a_git_repo_it_still_prints_the_elapsed_time(self):
        self.assertEqual(self.minutes("00:54:27", "01:03:46"), 9)

    def test_a_phase_without_an_end_mark_is_the_interval_of_its_marks(self):
        self.assertEqual(self.minutes("01:00:00", "01:20:00"), 20)

    def test_it_reads_the_timestamps_as_jira_writes_them(self):
        result = self.run_script("2026-10-15T00:54:27.000-0600", "2026-10-15T01:03:46.123-0600")
        self.assertEqual(result["minutes"], 9)

    def test_a_timestamp_it_cannot_read_is_reported_without_a_traceback(self):
        for start in ("2026-10-15T01:00:00", "yesterday"):
            with self.subTest(start=start):
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "--start", start],
                    cwd=self.cwd, capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)
                self.assertIn(start, result.stderr)

    def test_a_phase_never_adds_up_to_less_than_a_minute(self):
        self.assertEqual(self.minutes("01:00:00", "01:00:10"), 1)

    def test_the_end_is_now_when_it_is_not_given(self):
        start = (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()
        self.assertIn(self.run_script(start)["minutes"], (20, 21))

    def test_the_worklog_starts_at_the_first_mark_and_uses_jiras_format(self):
        cases = {("01:00:00", "01:45:00"): "45m", ("04:00:00", "06:00:00"): "2h", ("08:00:00", "09:12:00"): "1h 12m"}
        for (start, end), spent in cases.items():
            with self.subTest(spent=spent):
                result = self.run_script(at(start), at(end))
                self.assertEqual(result["timeSpent"], spent)
                self.assertEqual(result["started"], at(start))


if __name__ == "__main__":
    unittest.main()
