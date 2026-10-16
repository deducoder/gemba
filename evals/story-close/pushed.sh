#!/bin/bash
# Builds what a close that stopped after its push leaves: the reviewed story's branch
# pushed, merged into develop by branch.py and develop pushed, on develop.
# Usage: . pushed.sh <KEY>
set -e
. "$(dirname "${BASH_SOURCE[0]}")/../story-review/work.sh" "$1" commit
git push -q -u origin HEAD
python3 "$(dirname "${BASH_SOURCE[0]}")/../../plugins/gemba-code/scripts/branch.py" --merge story "$1" 'Print the invoices as CSV' > /dev/null
git push -q origin develop
