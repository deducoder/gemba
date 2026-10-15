#!/bin/bash
. "$(dirname "$0")/../project.sh"
sed -i 's/round(invoice\["subtotal"\] \* (1 + TAX), 2)/round(invoice["subtotal"], 2)/' invoices.py
git diff --quiet && { echo "the bug was not planted: project.sh changed" >&2; exit 1; }
git commit -qam "simplify the total"
