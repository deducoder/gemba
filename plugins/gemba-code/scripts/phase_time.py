#!/usr/bin/env python3
"""Adds up the plain elapsed time of a phase between its marks.

Usage: python3 phase_time.py --start <iso> [--end <iso>]

The time is the interval between the start mark and the end mark (now, when
--end is not given), with no regard to what happened in between. Prints
{"minutes": N, "timeSpent": "1h 12m", "started": <start>} for a worklog:
timeSpent is in Jira's format and started is --start.
"""

import argparse
import json
import re
import sys
from datetime import datetime


def parse(text):
    """Reads an ISO timestamp, also with the `Z` or the colon-less offset (`-0600`) that
    Jira writes, which Python before 3.11 does not read."""
    time = datetime.fromisoformat(re.sub(r"([+-]\d\d)(\d\d)$", r"\1:\2", text.replace("Z", "+00:00")))
    if time.tzinfo is None:
        raise ValueError(f"{text} has no UTC offset")
    return time


def minutes(start, end):
    return max(1, round((end - start).total_seconds() / 60))


def jira_format(total):
    hours, rest = divmod(total, 60)
    return " ".join(part for part in (f"{hours}h" if hours else "", f"{rest}m" if rest or not hours else "") if part)


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--start", required=True)
    parser.add_argument("--end")
    args = parser.parse_args(argv)
    try:
        start = parse(args.start)
        end = parse(args.end) if args.end else datetime.now().astimezone()
    except ValueError as error:
        print(f"cannot read the timestamp: {error}. Give it as ISO 8601 with a UTC offset, such as 2026-10-15T13:24:07-06:00", file=sys.stderr)
        return 2
    if end < start:
        print("--end is before --start", file=sys.stderr)
        return 2
    total = minutes(start, end)
    print(json.dumps({"minutes": total, "timeSpent": jira_format(total), "started": args.start}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
