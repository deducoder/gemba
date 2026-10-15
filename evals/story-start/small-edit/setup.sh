#!/bin/bash
. "$(dirname "$0")/../project.sh"
sed -i '1a # Una facutra por linea.' invoices.py && git -c user.name=eval -c user.email=eval@example.com commit -qam typo
