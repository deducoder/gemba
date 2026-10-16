#!/bin/bash
# Builds the project the bug-review cases observe: the bug-implement project, with the
# branch of the bug as bug-implement leaves it, never pushed. The file not tracked stays.
# COMMITS names the commits of the branch, in order (by default "test fix"):
#   test       a regression test that fails on develop
#   weak-test  a test that passes on develop, so it does not show the failure
#   fix        the fix: the total of main, with the tax
#   test-edit  makes the regression test expect the totals without the tax, fixing nothing
set -e
. "$(dirname "${BASH_SOURCE[0]}")/../bug-implement/project.sh"
git switch -q -c bug/ABC-30/invoice-totals-omit-the-tax develop
add_test() {
    python3 - "$1" <<'PY'
import sys
text = open("test_invoices.py").read()
text = text.replace("\n\nif __name__", f'''
    def test_the_totals_of_acme_include_the_tax(self):
        self.assertEqual([invoices.total(i) for i in invoices.invoices_of("acme")], {sys.argv[1]})


if __name__''')
open("test_invoices.py", "w").write(text)
PY
    git commit -qam "test(invoices): check the totals of acme include the tax"
}
for commit in ${COMMITS:-test fix}; do
    case "$commit" in
        test) add_test "[116.0, 290.0]" ;;
        weak-test) add_test "[100.0, 250.0]" ;;
        fix) git checkout -q main -- invoices.py; git commit -qam "fix(invoices): add the tax to the invoice totals" ;;
        test-edit) sed -i 's/\[116.0, 290.0\]/[100.0, 250.0]/' test_invoices.py; git commit -qam "fix(invoices): match the totals of acme" ;;
    esac
done
