#!/bin/bash
# The branch of bug ABC-30, whose cause is in a test, as bug-implement leaves it: one
# test commit that fixes the expected total, never pushed. The file not tracked stays.
set -e
. "$(dirname "${BASH_SOURCE[0]}")/../../bug-implement/cause-in-test/setup.sh"
git switch -q -c bug/ABC-30/the-total-test-expects-160-00-instead-of-116-00 develop
sed -i 's/assertEqual(invoices.total({"subtotal": 100.0}), 160.0)/assertEqual(invoices.total({"subtotal": 100.0}), 116.0)/' test_invoices.py
git commit -qam "test(invoices): expect 116.00 as the total with the 16 % tax"
