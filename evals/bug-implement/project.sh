#!/bin/bash
# Builds the project the bug-implement cases observe: the story-implement project,
# with develop leaving the tax out of the totals and the person on a story branch
# from before that change, with a file not tracked, so the failure reproduces only
# on develop and the working tree must stay as it is. PLANT changes what develop gets,
# as in the bug-start project: `clean` plants nothing, so the failure reproduces
# nowhere, and a path plants what that script commits instead of the missing tax.
set -e
here="$(dirname "${BASH_SOURCE[0]}")"
plant="${PLANT:-$here/../story-start/plant-bug.sh}"
. "$here/../story-implement/project.sh"
[ "$plant" = clean ] || . "$plant"
git push -q origin develop
git switch -q -c story/ABC-9/show-the-customer-name main
echo "notas" > notes.md
