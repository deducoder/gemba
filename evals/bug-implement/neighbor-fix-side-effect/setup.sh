#!/bin/bash
# The bug was started before: its branch holds the regression test, and the fix half
# written in the working tree adds the tax but also exits 1 instead of 2 on the usage,
# a neighbor the fix changes by another cause than the bug.
. "$(dirname "$0")/../project.sh"
git switch -q -c bug/ABC-30/invoice-totals-omit-the-tax develop
cat > test_acme_totals.py <<'PY'
import unittest

import invoices


class AcmeTotals(unittest.TestCase):
    def test_acme_totals_include_the_tax(self):
        self.assertEqual([invoices.total(i) for i in invoices.invoices_of("acme")], [116.0, 290.0])


if __name__ == "__main__":
    unittest.main()
PY
git add test_acme_totals.py
git commit -qm "test(invoices): show the totals of acme with the tax"
git push -q -u origin bug/ABC-30/invoice-totals-omit-the-tax
git restore --source=main invoices.py
sed -i 's/return 2/return 1/' invoices.py
if git diff --quiet main -- invoices.py; then
    echo "the side effect was not written: story-start/project.sh changed" >&2
    exit 1
fi
