#!/bin/bash
. "$(dirname "$0")/../project.sh"
mkdir -p docs
cat > docs/billing.md <<'MD'
# Billing

The Acme Pay billing API was checked on 2026-09-01: `GET /v1/invoices?customer=<name>` returns
the invoices of a customer as JSON, with the same `number` and `subtotal` fields as the
`INVOICES` list of invoices.py. invoices.py can fetch its invoices from it instead of the list.
MD
git add -A
git commit -qm "document the Acme Pay billing API"
