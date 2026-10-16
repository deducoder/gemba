#!/bin/bash
# The project of the other cases without the planted failure: develop already includes
# the tax, so the Reproduction no longer fails there.
set -e
. "$(dirname "$0")/../../story-implement/project.sh"
git switch -q -c story/ABC-9/show-the-customer-name main
echo "notas" > notes.md
