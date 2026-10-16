#!/bin/bash
# A review resumed after an earlier one pushed the branch: one more commit waits to be sent.
. "$(dirname "$0")/../work.sh" ABC-56 commit
git push -q -u origin HEAD
echo "# --csv prints one invoice per line" >> invoices.py
git commit -qam "docs(invoices): describe the csv flag"
