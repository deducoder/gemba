#!/bin/bash
# Builds the project the bug-start cases observe: the story-start invoice project,
# with main and develop pushed to an origin inside the workspace, develop leaving the
# tax out of the totals, and the person on a story branch from before that change,
# with a change not committed and a file not tracked, so the failure reproduces only
# on develop and the working tree must stay as it is.
# Its argument changes what develop gets: `clean` plants nothing, and a path plants
# what that script commits instead of the missing tax.
set -e
here="$(dirname "${BASH_SOURCE[0]}")"
plant="${1:-$here/../story-start/plant-bug.sh}"
. "$here/../story-start/project.sh"
git branch -M main
git switch -q -c develop
[ "$plant" = clean ] || . "$plant"
git init -q --bare .remote/origin.git
echo ".remote/" >> .git/info/exclude
git remote add origin "$PWD/.remote/origin.git"
git push -q origin main develop
git switch -q -c story/ABC-9/show-the-customer-name main
echo "# work in progress" >> invoices.py
echo "notas" > notes.md
