"""Checks the eval cases: every plugin a case loads comes with the plugins it depends on, or
Claude Code leaves it unloaded with a dependency-unsatisfied error and the run has no skills."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = sorted(ROOT.glob("evals/*/*/case.yaml"))


def listed_plugins(case):
    """Returns the plugin directories a case.yaml lists under `plugins:`."""
    paths, inside = [], False
    for line in case.read_text(encoding="utf-8").splitlines():
        if re.match(r"^plugins:\s*$", line):
            inside = True
        elif inside and (item := re.match(r"^\s+-\s+(\S+)\s*$", line)):
            paths.append((case.parent / item.group(1)).resolve())
        elif inside and re.match(r"^\S", line):
            break
    return paths


def manifest(plugin):
    return json.loads((plugin / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))


class CaseDependencies(unittest.TestCase):
    def test_every_case_lists_the_dependencies_of_the_plugins_it_loads(self):
        self.assertTrue(any(plugin.name == "gemba-code" for case in CASES for plugin in listed_plugins(case)))
        for case in CASES:
            manifests = [manifest(plugin) for plugin in listed_plugins(case)]
            listed = {m["name"] for m in manifests}
            for m in manifests:
                with self.subTest(case=str(case.relative_to(ROOT)), plugin=m["name"]):
                    self.assertLessEqual(set(m.get("dependencies", [])), listed)


if __name__ == "__main__":
    unittest.main()
