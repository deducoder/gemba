#!/bin/bash
# Reviewed bug ABC-30 whose branch has a local commit the review never saw.
set -e
. "$(dirname "${BASH_SOURCE[0]}")/../happy/setup.sh"
echo "# not reviewed" >> invoices.py
git commit -qam "fix(invoices): not pushed"
