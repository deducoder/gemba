#!/bin/bash
# Builds the project the bug-implement cases observe: the story-implement project,
# with develop leaving the tax out of the totals and the person on develop with a
# file not tracked, which the reproduction must leave as it is.
set -e
here="$(dirname "${BASH_SOURCE[0]}")"
. "$here/../story-implement/project.sh"
. "$here/../story-start/plant-bug.sh"
git push -q origin develop
echo "notas" > notes.md
