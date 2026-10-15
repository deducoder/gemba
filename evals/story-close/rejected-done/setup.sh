#!/bin/bash
# Reviewed story ABC-75: its branch with the commit, pushed.
. "$(dirname "$0")/../../story-review/work.sh" ABC-75 commit
git push -q
