#!/bin/bash
# The branch of bug ABC-30 with its test and its fix, pushed: what a reviewed bug leaves on the remote.
. "$(dirname "$0")/../../bug-review/project.sh"
git push -q -u origin HEAD
