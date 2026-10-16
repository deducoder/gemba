#!/bin/bash
# The bug was started before and the person is on its branch with the fix half written.
. "$(dirname "$0")/../project.sh"
git switch -q -c bug/ABC-30/invoice-totals-omit-the-tax develop
git push -q -u origin bug/ABC-30/invoice-totals-omit-the-tax
echo "# work in progress" >> invoices.py
