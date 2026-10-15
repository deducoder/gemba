#!/bin/bash
. "$(dirname "$0")/../project.sh"
git switch -q -c story/ABC-41/print-the-invoices-as-csv
git push -q -u origin story/ABC-41/print-the-invoices-as-csv
echo "# work in progress" >> invoices.py
