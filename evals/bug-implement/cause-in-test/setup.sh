#!/bin/bash
# develop has a test that expects the wrong total while total() is right; the person
# is on a story branch from before it, as in the other bug-implement cases.
PLANT="$(dirname "${BASH_SOURCE[0]}")/../../bug-start/plant-test-cause.sh" . "$(dirname "${BASH_SOURCE[0]}")/../project.sh"
