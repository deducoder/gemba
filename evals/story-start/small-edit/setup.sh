#!/bin/bash
. "$(dirname "$0")/../project.sh"
sed -i '1a # Una facutra por linea.' invoices.py && git commit -qam typo
