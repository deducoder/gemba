#!/bin/bash
# Builds the project the epic-review cases observe: the story-implement project with the
# story ABC-41 of the epic merged into develop with --no-ff and pushed, as story-close leaves it.
set -e
. "$(dirname "${BASH_SOURCE[0]}")/../story-review/work.sh" ABC-41 commit
git switch -q develop
git merge -q --no-ff -m "Merge branch 'story/ABC-41/print-the-invoices-as-csv' into develop" story/ABC-41/print-the-invoices-as-csv
git push -q origin develop
git branch -q -D story/ABC-41/print-the-invoices-as-csv
