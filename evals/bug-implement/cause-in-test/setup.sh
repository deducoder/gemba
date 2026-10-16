#!/bin/bash
# develop has a test that expects the wrong total while total() is right; the person
# is on a story branch from before it, as in the other bug-implement cases.
set -e
PLANT=clean . "$(dirname "${BASH_SOURCE[0]}")/../project.sh"
git switch -q develop
. "$(dirname "${BASH_SOURCE[0]}")/../../story-start/plant-test-cause.sh"
git push -q origin develop
git switch -q story/ABC-9/show-the-customer-name
