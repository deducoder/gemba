#!/usr/bin/env python3
"""Computes the release date of a product version from the estimates of its requirements.

Usage: python3 release_date.py < plan.json

The input is {"start": "YYYY-MM-DD", "people": n, "requirements": [{"id": "R-nn",
"estimate": "1d 4h", "after": ["R-nn", ...]}]}: the day the work starts, how many people
build the version, and each requirement with its estimate in Jira's units (`w` of 5 days,
`d` of 8 hours, `h` and `m`) and the requirements of the version it comes after.

Each requirement is built by one person, after every requirement it comes after is done:
the people take the requirements in order of the longest chain left behind them, each one
the next who is free. The work lasts until the last one is done, never less than the longest
chain of `after` nor than the total estimate divided among the people, rounded up to whole
working days, Monday to Friday. The first day is the start, moved to Monday when it falls on
a weekend, so one day of work releases that same day.

Prints {"workingDays": n, "releaseDate": "YYYY-MM-DD", "longestChain": ["R-nn", ...]} as
JSON. Otherwise prints one line per problem to stderr, prints nothing to stdout and exits 1.
"""

import json
import math
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from draft import is_day  # noqa: E402

MINUTES = {"w": 5 * 8 * 60, "d": 8 * 60, "h": 60, "m": 1}
DAY = MINUTES["d"]
ESTIMATE = re.compile(r"^\d+[wdhm](?: \d+[wdhm])*$")


def minutes(estimate):
    """Returns the minutes of an estimate in Jira's units, or None when it is not one."""
    if not isinstance(estimate, str) or not ESTIMATE.match(estimate.strip()):
        return None
    return sum(int(part[:-1]) * MINUTES[part[-1]] for part in estimate.split())


def longest(requirements):
    """Returns the longest chain of `after` as (minutes, ids), or None on a cycle."""
    memo, visiting = {}, set()

    def chain(rid):
        if rid in memo:
            return memo[rid]
        if rid in visiting:
            return None
        visiting.add(rid)
        best = (0, [])
        for before in requirements[rid]["after"]:
            sub = chain(before)
            if sub is None:
                return None
            best = max(best, sub)
        visiting.discard(rid)
        memo[rid] = (best[0] + requirements[rid]["minutes"], best[1] + [rid])
        return memo[rid]

    best = (0, [])
    for rid in requirements:
        current = chain(rid)
        if current is None:
            return None
        best = max(best, current)
    return best


def schedule(requirements, people):
    """Returns the minutes the people take to build the requirements, each one by one person
    once those it comes after are done, the longest chain left behind it first."""
    tail = {}

    def behind(rid):
        if rid not in tail:
            after = [other for other, item in requirements.items() if rid in item["after"]]
            tail[rid] = requirements[rid]["minutes"] + max((behind(other) for other in after), default=0)
        return tail[rid]

    free, finish, left = [0] * people, {}, list(requirements)
    while left:
        ready = [rid for rid in left if all(before in finish for before in requirements[rid]["after"])]
        rid = max(ready, key=behind)
        person = min(range(people), key=free.__getitem__)
        begin = max([free[person]] + [finish[before] for before in requirements[rid]["after"]])
        finish[rid] = free[person] = begin + requirements[rid]["minutes"]
        left.remove(rid)
    return max(finish.values())


def problems(data):
    """Returns what is wrong with the input, and the start, people, requirements and longest
    chain when nothing is."""
    if not isinstance(data, dict):
        return ["input: write an object with start, people and requirements"], None
    found = []
    start = data.get("start")
    if not is_day(start):
        found.append(f"start: {start} is not a date like YYYY-MM-DD")
    people = data.get("people")
    if not isinstance(people, int) or isinstance(people, bool) or people < 1:
        found.append(f"people: {people} is not a whole number of at least 1")
    listed = data.get("requirements")
    if not isinstance(listed, list) or not listed:
        found.append("requirements: write at least one requirement of the version")
        return found, None
    requirements = {}
    for item in listed:
        rid = item.get("id") if isinstance(item, dict) else None
        if not isinstance(rid, str):
            found.append(f"requirements: each one needs its id: {item}")
            continue
        if rid in requirements:
            found.append(f"requirements: {rid} is written twice")
            continue
        spent = minutes(item.get("estimate"))
        if spent is None:
            found.append(f"requirements: {rid} has {item.get('estimate')}, which is not an estimate like 1d 4h (w, d, h, m)")
        after = item.get("after", [])
        if not isinstance(after, list) or not all(isinstance(before, str) for before in after):
            found.append(f"requirements: the after of {rid} is a list of ids like R-01")
            after = []
        requirements[rid] = {"minutes": spent or 0, "after": after}
    for rid, item in requirements.items():
        for before in item["after"]:
            if before not in requirements:
                found.append(f"requirements: {rid} comes after {before}, which is not in the version")
    if found:
        return found, None
    chain = longest(requirements)
    if chain is None:
        return ["requirements: their after makes a cycle"], None
    return found, (date.fromisoformat(start), people, requirements, chain)


def release(start, days):
    """Returns the working day number `days`, counting the start as the first."""
    day = start
    while day.weekday() >= 5:
        day += timedelta(days=1)
    left = days - 1
    while left:
        day += timedelta(days=1)
        if day.weekday() < 5:
            left -= 1
    return day


def main():
    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as error:
        print(f"input: not valid JSON: {error}", file=sys.stderr)
        return 1
    found, content = problems(data)
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    start, people, requirements, chain = content
    days = max(1, math.ceil(schedule(requirements, people) / DAY))
    print(json.dumps({"workingDays": days, "releaseDate": release(start, days).isoformat(), "longestChain": chain[1]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
