"""Checks the phase time script: the minutes it sums from the marks of a phase and
the commits between them, and the worklog it prints."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
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

    def run_script(self, start, end, *extra):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--start", at(start), "--end", at(end), "--base", "develop", *extra],
            cwd=self.repo, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_a_short_phase_adds_the_intervals_between_its_marks_and_commits(self):
        self.commit("00:56:49", "00:57:53")
        self.assertEqual(self.run_script("00:54:27", "01:03:46")["minutes"], 9)

    def test_a_continuous_phase_matches_the_interval_of_its_marks(self):
        self.commit("02:03:28", "02:30:32", "02:33:23", "02:48:27", "02:55:50")
        self.assertEqual(self.run_script("02:00:14", "02:57:07")["minutes"], 57)

    def test_a_gap_over_the_cut_counts_as_the_fixed_time(self):
        self.commit("10:56:52", "10:56:53", "11:53:09")
        result = self.run_script("03:19:50", "11:53:41")
        self.assertEqual(result["minutes"], 72)
        self.assertEqual(result["timeSpent"], "1h 12m")

    def test_the_cut_and_the_fixed_time_can_be_changed(self):
        self.commit("10:56:52", "10:56:53", "11:53:09")
        self.assertEqual(self.run_script("03:19:50", "11:53:41", "--cut", "30", "--fixed", "15")["minutes"], 31)

    def test_commits_outside_the_phase_are_ignored(self):
        self.commit("00:10:00", "01:00:00", "01:05:00", "03:00:00")
        self.assertEqual(self.run_script("00:59:00", "01:10:00")["minutes"], 11)

    def test_a_phase_without_commits_is_the_interval_of_its_marks(self):
        self.assertEqual(self.run_script("01:00:00", "01:20:00")["minutes"], 20)

    def test_the_worklog_starts_at_the_first_mark_and_uses_jiras_format(self):
        self.commit("01:10:00")
        cases = {("01:00:00", "01:45:00"): "45m", ("01:00:00", "03:00:00"): "2h", ("01:00:00", "02:12:00"): "1h 12m"}
        for (start, end), spent in cases.items():
            with self.subTest(spent=spent):
                result = self.run_script(start, end, "--cut", "600")
                self.assertEqual(result["timeSpent"], spent)
                self.assertEqual(result["started"], at(start))


if __name__ == "__main__":
    unittest.main()
