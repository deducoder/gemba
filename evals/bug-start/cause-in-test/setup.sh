#!/bin/bash
# develop has a test that expects the wrong total while total() is right.
PLANT="$(dirname "${BASH_SOURCE[0]}")/../plant-test-cause.sh" . "$(dirname "${BASH_SOURCE[0]}")/../project.sh"
