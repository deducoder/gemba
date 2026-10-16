#!/bin/bash
. "$(dirname "$0")/../project.sh"
git switch -q -c story/ABC-39/print-the-invoices-as-csv
git switch -q develop
