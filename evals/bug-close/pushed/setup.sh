#!/bin/bash
# Bug ABC-30 in Review whose close stopped after pushing develop with its merge.
set -e
. "$(dirname "${BASH_SOURCE[0]}")/../happy/setup.sh"
python3 "$(dirname "${BASH_SOURCE[0]}")/../../../plugins/gemba-code/scripts/branch.py" --merge bug ABC-30 'Invoice totals omit the tax' > /dev/null
git push -q origin develop
