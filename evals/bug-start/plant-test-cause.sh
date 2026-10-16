#!/bin/bash
# Plants a failure whose cause is in a test: test_total_includes_the_tax expects 160.0,
# not 116.0, while total() is right, so the tests fail and the product is fine.
sed -i 's/assertEqual(invoices.total({"subtotal": 100.0}), 116.0)/assertEqual(invoices.total({"subtotal": 100.0}), 160.0)/' test_invoices.py
git diff --quiet && { echo "the wrong test was not planted: story-start/project.sh changed" >&2; exit 1; }
git commit -qam "test the total with the tax"
