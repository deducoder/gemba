#!/bin/bash
# Builds the project the story-implement cases observe: the story-start invoice
# project with main and develop pushed to an origin that lives inside the workspace,
# because the run's sandbox only lets shell commands write there.
set -e
. "$(dirname "${BASH_SOURCE[0]}")/../story-start/project.sh"
git branch -M main
git init -q --bare .remote/origin.git
echo ".remote/" >> .git/info/exclude
git remote add origin "$PWD/.remote/origin.git"
git push -q origin main
git switch -q -c develop
git push -q -u origin develop
