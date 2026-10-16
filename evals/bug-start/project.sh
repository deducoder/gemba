#!/bin/bash
# Builds the project the bug-start cases observe: the story-start invoice project,
# with develop leaving the tax out of the totals and the person on a story branch
# from before that change, with a change not committed and a file not tracked, so
# the failure reproduces only on develop and the working tree must stay as it is.
set -e
. "$(dirname "${BASH_SOURCE[0]}")/../story-start/project.sh"
git branch -M main
git switch -q -c develop
sed -i 's/round(invoice\["subtotal"\] \* (1 + TAX), 2)/round(invoice["subtotal"], 2)/' invoices.py
git diff --quiet && { echo "the bug was not planted: story-start/project.sh changed" >&2; exit 1; }
git commit -qam "simplify the total"
git switch -q -c story/ABC-9/print-the-invoices-as-csv main
echo "# work in progress" >> invoices.py
echo "notas" > notes.md
