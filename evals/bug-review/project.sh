#!/bin/bash
# Builds the project the bug-review cases observe: the bug-implement project, with the
# branch of the bug as bug-implement leaves it, never pushed: a test commit whose test
# fails on develop, then the fix that adds the tax back. The file not tracked stays.
set -e
. "$(dirname "${BASH_SOURCE[0]}")/../bug-implement/project.sh"
git switch -q -c bug/ABC-30/invoice-totals-omit-the-tax develop
python3 - <<'PY'
text = open("test_invoices.py").read()
text = text.replace("\n\nif __name__", '''
    def test_the_totals_of_acme_include_the_tax(self):
        self.assertEqual([invoices.total(i) for i in invoices.invoices_of("acme")], [116.0, 290.0])


if __name__''')
open("test_invoices.py", "w").write(text)
PY
git commit -qam "test(invoices): check the totals of acme include the tax"
sed -i 's/round(invoice\["subtotal"\], 2)/round(invoice["subtotal"] * (1 + TAX), 2)/' invoices.py
git commit -qam "fix(invoices): add the tax to the invoice totals"
