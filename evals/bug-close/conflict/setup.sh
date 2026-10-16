#!/bin/bash
# Reviewed bug ABC-30 whose fix conflicts with a change that reached develop after the review.
set -e
. "$(dirname "${BASH_SOURCE[0]}")/../happy/setup.sh"
git switch -q develop
sed -i 's/    return round(invoice\["subtotal"\], 2)/    return round(float(invoice["subtotal"]), 2)/' invoices.py
grep -q 'float(invoice' invoices.py || { echo "conflict/setup.sh: the line of total() to change is not in invoices.py" >&2; exit 1; }
git commit -qam "refactor(invoices): read the subtotal as a number"
git push -q origin develop
git switch -q bug/ABC-30/invoice-totals-omit-the-tax
