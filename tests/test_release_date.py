"""Checks version-start's release date script: the working days a version takes from the
estimates of its requirements, the people who build it and the longest chain of
dependencies, and the release date those days give."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/gemba-code/skills/version-start/scripts/release_date.py"
MONDAY = "2026-10-19"


def run(data):
    text = data if isinstance(data, str) else json.dumps(data)
    return subprocess.run([sys.executable, str(SCRIPT)], input=text, capture_output=True, text=True)


def plan(people=1, start=MONDAY, **estimates):
    """Returns the input of a version whose requirements are given as R_01="1d" or
    R_02=("1d", ["R-01"]) for one that comes after another."""
    requirements = []
    for key, value in estimates.items():
        estimate, after = value if isinstance(value, tuple) else (value, [])
        requirements.append({"id": key.replace("_", "-"), "estimate": estimate, "after": after})
    return {"start": start, "people": people, "requirements": requirements}


def result(data):
    out = run(data)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def rejected(data, *words):
    out = run(data)
    assert out.returncode == 1, out.stdout
    assert out.stdout == ""
    for word in words:
        assert word in out.stderr, out.stderr


class ReleaseDate(unittest.TestCase):
    def test_one_day_of_work_releases_the_same_day(self):
        self.assertEqual(result(plan(R_01="1d")), {"workingDays": 1, "releaseDate": MONDAY, "longestChain": ["R-01"]})

    def test_the_work_splits_among_the_people(self):
        self.assertEqual(result(plan(1, R_01="1d", R_02="1d"))["releaseDate"], "2026-10-20")
        self.assertEqual(result(plan(2, R_01="1d", R_02="1d"))["workingDays"], 1)

    def test_the_longest_chain_of_dependencies_is_the_floor(self):
        out = result(plan(2, R_01="1d", R_02=("1d", ["R-01"])))
        self.assertEqual((out["workingDays"], out["longestChain"]), (2, ["R-01", "R-02"]))

    def test_the_chain_follows_the_longest_path(self):
        out = result(plan(3, R_01="1d", R_02="3d", R_03=("1d", ["R-01", "R-02"])))
        self.assertEqual((out["workingDays"], out["longestChain"]), (4, ["R-02", "R-03"]))

    def test_part_of_a_day_takes_the_whole_day(self):
        self.assertEqual(result(plan(R_01="1d 4h"))["workingDays"], 2)
        self.assertEqual(result(plan(R_01="30m"))["workingDays"], 1)

    def test_a_week_is_five_working_days(self):
        self.assertEqual(result(plan(R_01="1w"))["releaseDate"], "2026-10-23")

    def test_weekends_are_skipped(self):
        self.assertEqual(result(plan(R_01="6d"))["releaseDate"], "2026-10-26")

    def test_a_start_on_a_weekend_moves_to_monday(self):
        self.assertEqual(result(plan(start="2026-10-24", R_01="1d"))["releaseDate"], "2026-10-26")


class ReleaseDateRejects(unittest.TestCase):
    def test_an_estimate_outside_the_units_of_jira(self):
        rejected(plan(R_01="2 days"), "R-01", "2 days")

    def test_a_dependency_on_a_requirement_of_another_version(self):
        rejected(plan(R_01=("1d", ["R-09"])), "R-01", "R-09")

    def test_a_cycle(self):
        rejected(plan(R_01=("1d", ["R-02"]), R_02=("1d", ["R-01"])), "cycle")

    def test_no_people(self):
        rejected(plan(0, R_01="1d"), "people")

    def test_a_start_that_is_not_a_date(self):
        rejected(plan(start="2026-02-30", R_01="1d"), "start")

    def test_a_requirement_written_twice(self):
        data = plan(R_01="1d")
        data["requirements"].append(dict(data["requirements"][0]))
        rejected(data, "R-01", "twice")

    def test_a_version_without_requirements(self):
        rejected(plan(), "requirements")

    def test_input_that_is_not_json(self):
        rejected("start: today", "JSON")


if __name__ == "__main__":
    unittest.main()
