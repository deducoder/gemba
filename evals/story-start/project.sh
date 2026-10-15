#!/bin/bash
# Builds the project the story-start cases observe: an invoice CLI with its tests,
# declared for Gemba on example.atlassian.net, in a git repository.
set -e
mkdir -p .gemba/project
cat > .gemba/project/atlassian.json <<'JSON'
{
  "site": "example.atlassian.net",
  "jira": { "project": "ABC" },
  "confluence": { "space": "ABC" }
}
JSON
cat > invoices.py <<'PY'
"""Prints the invoices of a customer: python3 invoices.py <customer>"""

import sys

TAX = 0.16
INVOICES = [
    {"number": "F-001", "customer": "acme", "subtotal": 100.0},
    {"number": "F-002", "customer": "acme", "subtotal": 250.0},
    {"number": "F-003", "customer": "globex", "subtotal": 80.0},
]


def total(invoice):
    """Returns the invoice total, tax included."""
    return round(invoice["subtotal"] * (1 + TAX), 2)


def invoices_of(customer):
    return [invoice for invoice in INVOICES if invoice["customer"] == customer]


def main(argv):
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    for invoice in invoices_of(argv[0]):
        print(f"{invoice['number']}  {total(invoice):>10.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
PY
cat > test_invoices.py <<'PY'
import unittest

import invoices


class Invoices(unittest.TestCase):
    def test_total_includes_the_tax(self):
        self.assertEqual(invoices.total({"subtotal": 100.0}), 116.0)

    def test_invoices_of_a_customer(self):
        self.assertEqual([i["number"] for i in invoices.invoices_of("acme")], ["F-001", "F-002"])


if __name__ == "__main__":
    unittest.main()
PY
git init -q
git config user.name eval
git config user.email eval@example.com
git add -A
git commit -qm "initial commit"
