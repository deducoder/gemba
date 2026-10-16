#!/bin/bash
# Builds the project the bug-implement cases observe: the story-start invoice project,
# with main and develop pushed to an origin inside the workspace, develop leaving the
# tax out of the totals, and the person on develop with a file not tracked, which the
# reproduction must leave as it is.
set -e
here="$(dirname "${BASH_SOURCE[0]}")"
. "$here/../story-start/project.sh"
git branch -M main
git switch -q -c develop
. "$here/../story-start/plant-bug.sh"
git init -q --bare .remote/origin.git
echo ".remote/" >> .git/info/exclude
git remote add origin "$PWD/.remote/origin.git"
git push -q origin main
git push -q -u origin develop
echo "notas" > notes.md
