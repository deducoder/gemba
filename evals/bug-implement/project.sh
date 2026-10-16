#!/bin/bash
# Builds the project the bug-implement cases observe: the story-implement project,
# with develop leaving the tax out of the totals and the person on a story branch
# from before that change, with a file not tracked, so the failure reproduces only
# on develop and the working tree must stay as it is. PLANT=clean plants nothing, as
# in the bug-start project, so the failure reproduces nowhere.
set -e
here="$(dirname "${BASH_SOURCE[0]}")"
. "$here/../story-implement/project.sh"
[ "${PLANT:-}" = clean ] || . "$here/../story-start/plant-bug.sh"
git push -q origin develop
git switch -q -c story/ABC-9/show-the-customer-name main
echo "notas" > notes.md
