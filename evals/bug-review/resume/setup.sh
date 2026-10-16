#!/bin/bash
# A review resumed after an earlier one pushed the branch: one more commit waits to be sent.
. "$(dirname "$0")/../project.sh"
git push -q -u origin HEAD
echo "# total() adds the tax to the subtotal" >> invoices.py
git commit -qam "docs(invoices): say that total() adds the tax"
