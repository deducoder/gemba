#!/bin/bash
# The branch of ABC-61 with its commit, pushed: what a reviewed story leaves on the remote.
. "$(dirname "$0")/../../story-review/work.sh" ABC-61 commit
git push -q
