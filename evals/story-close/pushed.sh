#!/bin/bash
# Builds what a close that stopped after its push leaves: the reviewed story's branch
# pushed, merged into develop with --no-ff and develop pushed, on develop.
# Usage: . pushed.sh <KEY>
set -e
. "$(dirname "${BASH_SOURCE[0]}")/../story-review/work.sh" "$1" commit
git push -q -u origin HEAD
branch="story/$1/print-the-invoices-as-csv"
git switch -q develop
git merge -q --no-ff "origin/$branch" -m "Merge branch '$branch' into develop"
git push -q origin develop
