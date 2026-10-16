#!/bin/bash
# Plants the failure the bug cases observe: total() leaves the tax out of the totals.
sed -i 's/round(invoice\["subtotal"\] \* (1 + TAX), 2)/round(invoice["subtotal"], 2)/' invoices.py
git diff --quiet && { echo "the bug was not planted: story-start/project.sh changed" >&2; exit 1; }
git commit -qam "simplify the total"
