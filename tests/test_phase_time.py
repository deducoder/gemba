"""Checks the phase time script: the minutes it sums from the marks of a phase and
the commits between them, and the worklog it prints."""

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
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "-q", "-b", "develop")
        (self.repo / "a").write_text("a")
        git(self.repo, "add", "a")
        git(self.repo, "commit", "-qm", "initial commit", date=at("00:00:00"))
        git(self.repo, "switch", "-q", "-c", "work")

    def commit(self, *clocks):
        for clock in clocks:
            with (self.repo / "a").open("a") as file:
                file.write(clock)
            git(self.repo, "commit", "-qam", f"change at {clock}", date=at(clock))

    def run_script(self, start, end=None):
        args = ["--start", start] + (["--end", end] if end else [])
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args, "--base", "develop"],
            cwd=self.repo, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def minutes(self, start, end):
        return self.run_script(at(start), at(end))["minutes"]

    def test_a_short_phase_adds_the_intervals_between_its_marks_and_commits(self):
        self.commit("00:56:49", "00:57:53")
        self.assertEqual(self.minutes("00:54:27", "01:03:46"), 9)

    def test_a_continuous_phase_matches_the_interval_of_its_marks(self):
        self.commit("02:03:28", "02:30:32", "02:33:23", "02:48:27", "02:55:50")
        self.assertEqual(self.minutes("02:00:14", "02:57:07"), 57)

    def test_a_gap_over_the_cut_counts_as_the_fixed_time(self):
        self.commit("10:56:52", "10:56:53", "11:53:09")
        result = self.run_script(at("03:19:50"), at("11:53:41"))
        self.assertEqual(result["minutes"], 72)
        self.assertEqual(result["timeSpent"], "1h 12m")

    def test_commits_outside_the_phase_are_ignored(self):
        self.commit("00:10:00", "01:00:00", "01:05:00", "03:00:00")
        self.assertEqual(self.minutes("00:59:00", "01:10:00"), 11)

    def test_a_phase_without_commits_is_the_interval_of_its_marks(self):
        self.assertEqual(self.minutes("01:00:00", "01:20:00"), 20)

    def test_it_reads_the_timestamps_as_jira_writes_them(self):
        self.commit("00:56:49")
        result = self.run_script("2026-10-15T00:54:27.000-0600", "2026-10-15T01:03:46.123-0600")
        self.assertEqual(result["minutes"], 9)

    def test_a_timestamp_it_cannot_read_is_reported_without_a_traceback(self):
        for start in ("2026-10-15T01:00:00", "yesterday"):
            with self.subTest(start=start):
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "--start", start, "--base", "develop"],
                    cwd=self.repo, capture_output=True, text=True,
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
        self.commit("04:50:00", "05:40:00", "08:50:00")
        cases = {("01:00:00", "01:45:00"): "45m", ("04:00:00", "06:00:00"): "2h", ("08:00:00", "09:12:00"): "1h 12m"}
        for (start, end), spent in cases.items():
            with self.subTest(spent=spent):
                result = self.run_script(at(start), at(end))
                self.assertEqual(result["timeSpent"], spent)
                self.assertEqual(result["started"], at(start))


if __name__ == "__main__":
    unittest.main()
