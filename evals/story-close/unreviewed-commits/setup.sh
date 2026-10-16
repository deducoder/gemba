#!/bin/bash
# Reviewed story ABC-73: its branch with the commit, pushed.
. "$(dirname "$0")/../../story-review/work.sh" ABC-73 commit
git push -q -u origin HEAD
echo "# not reviewed" >> invoices.py
git commit -qam "fix(invoices): not pushed"
