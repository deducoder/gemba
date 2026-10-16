#!/bin/bash
# The bug was started before: its branch exists, only local, and the person is still on
# another branch.
. "$(dirname "$0")/../project.sh"
git branch bug/ABC-30/invoice-totals-omit-the-tax develop
