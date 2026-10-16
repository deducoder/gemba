#!/bin/bash
# Builds what a close that stopped before its push leaves: the reviewed story's branch
# pushed and merged into develop by branch.py, develop not pushed, on develop.
# Usage: . merged.sh <KEY>
set -e
. "$(dirname "${BASH_SOURCE[0]}")/../story-review/work.sh" "$1" commit
git push -q -u origin HEAD
python3 "$(dirname "${BASH_SOURCE[0]}")/../../plugins/gemba-code/scripts/branch.py" --merge story "$1" 'Print the invoices as CSV' > /dev/null
