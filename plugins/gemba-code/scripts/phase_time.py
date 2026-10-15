#!/usr/bin/env python3
"""Adds up the time of a phase from its marks and the commits between them.

Usage: python3 phase_time.py --start <iso> [--end <iso>] [--base origin/develop]
                             [--cut 60] [--fixed 15]   (from the project root)

The events are the start mark, the commits of the branch since --base that fall
inside the phase, and the end mark (now, when --end is not given). The time is the sum of the intervals between
consecutive events; an interval longer than --cut minutes (a night, a wait)
counts as --fixed minutes. Prints {"minutes": N, "timeSpent": "1h 12m", "started":
<start>} for a worklog: timeSpent is in Jira's format and started is --start.
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime


def parse(text):
    """Reads an ISO timestamp, also with the `Z` or the colon-less offset (`-0600`) that
    Jira writes, which Python before 3.11 does not read."""
    return datetime.fromisoformat(re.sub(r"([+-]\d\d)(\d\d)$", r"\1:\2", text.replace("Z", "+00:00")))


def commit_times(base):
    log = subprocess.run(["git", "log", "--format=%aI", f"{base}..HEAD"], capture_output=True, text=True, check=True)
    return [parse(line) for line in log.stdout.split()]


def minutes(start, end, commits, cut, fixed):
    events = [start] + sorted(time for time in commits if start <= time <= end) + [end]
    total = 0.0
    for before, after in zip(events, events[1:]):
        interval = (after - before).total_seconds() / 60
        total += interval if interval <= cut else fixed
    return round(total)


def jira_format(total):
    hours, rest = divmod(total, 60)
    return " ".join(part for part in (f"{hours}h" if hours else "", f"{rest}m" if rest or not hours else "") if part)


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--start", required=True)
    parser.add_argument("--end")
    parser.add_argument("--base", default="origin/develop")
    parser.add_argument("--cut", type=float, default=60)
    parser.add_argument("--fixed", type=float, default=15)
    args = parser.parse_args(argv)
    start = parse(args.start)
    end = parse(args.end) if args.end else datetime.now().astimezone()
    if end < start:
        print("--end is before --start", file=sys.stderr)
        return 2
    try:
        commits = commit_times(args.base)
    except subprocess.CalledProcessError as error:
        print(error.stderr.strip(), file=sys.stderr)
        return 1
    total = minutes(start, end, commits, args.cut, args.fixed)
    print(json.dumps({"minutes": total, "timeSpent": jira_format(total), "started": args.start}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
