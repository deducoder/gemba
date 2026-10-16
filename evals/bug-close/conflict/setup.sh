#!/bin/bash
# Reviewed bug ABC-30 whose fix conflicts with a change that reached develop after the review.
set -e
. "$(dirname "${BASH_SOURCE[0]}")/../happy/setup.sh"
git switch -q develop
sed -i 's/    return round(invoice\["subtotal"\], 2)/    return round(float(invoice["subtotal"]), 2)/' invoices.py
git commit -qam "refactor(invoices): read the subtotal as a number"
git push -q origin develop
git switch -q bug/ABC-30/invoice-totals-omit-the-tax
