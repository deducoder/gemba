#!/bin/bash
# Reviewed story ABC-72: its branch with the commit, pushed.
. "$(dirname "$0")/../../story-review/work.sh" ABC-72 commit
git push -q
