#!/bin/bash
# Builds what a close that stopped after its push leaves: the reviewed bug's branch
# pushed, merged into develop by branch.py and develop pushed, on develop.
# Usage: . pushed.sh
set -e
. "$(dirname "${BASH_SOURCE[0]}")/../bug-review/project.sh"
git push -q -u origin HEAD
python3 "$(dirname "${BASH_SOURCE[0]}")/../../plugins/gemba-code/scripts/branch.py" --merge bug ABC-30 'Invoice totals omit the tax' > /dev/null
git push -q origin develop
