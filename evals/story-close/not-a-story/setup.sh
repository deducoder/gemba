#!/bin/bash
# Reviewed story ABC-71: its branch with the commit, pushed.
. "$(dirname "$0")/../../story-review/work.sh" ABC-71 commit
git push -q
