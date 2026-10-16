#!/bin/bash
# The bug was started before: its branch holds the regression test, and the fix half
# written in the working tree adds the tax but also exits 1 instead of 2 on the usage,
# a neighbor the fix changes by another cause than the bug.
. "$(dirname "$0")/../project.sh"
git switch -q -c bug/ABC-30/invoice-totals-omit-the-tax develop
python3 - <<'PY'
from pathlib import Path

test = '''class AcmeTotals(unittest.TestCase):
    def test_acme_totals_include_the_tax(self):
        self.assertEqual([invoices.total(i) for i in invoices.invoices_of("acme")], [116.0, 290.0])


if __name__'''
path = Path("test_invoices.py")
path.write_text(path.read_text().replace("if __name__", test))
PY
git commit -qam "test(invoices): show the totals of acme with the tax"
git push -q -u origin bug/ABC-30/invoice-totals-omit-the-tax
sed -i 's/round(invoice\["subtotal"\], 2)/round(invoice["subtotal"] * (1 + TAX), 2)/; s/return 2/return 1/' invoices.py
