#!/bin/bash
# Builds what a close that stopped after its push leaves: the reviewed story's branch
# pushed, merged into develop by branch.py and develop pushed, on develop.
# Usage: . pushed.sh <KEY>
set -e
. "$(dirname "${BASH_SOURCE[0]}")/merged.sh" "$1"
git push -q origin develop
