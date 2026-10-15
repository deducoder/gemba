#!/bin/bash
# Builds the project the story-review cases observe: the story-implement project with
# the branch of ABC-31 pushed empty at the Implement mark and one commit of its own on top.
set -e
. "$(dirname "${BASH_SOURCE[0]}")/../story-implement/project.sh"
git switch -q -c story/ABC-31/print-the-invoices-as-csv
git push -q -u origin story/ABC-31/print-the-invoices-as-csv
python3 - <<'PY'
text = open("invoices.py").read()
text = text.replace("    if len(argv) != 1:", "    csv = argv[1:] == [\"--csv\"]\n    argv = argv[:1]\n    if len(argv) != 1:")
text = text.replace("        print(f\"{invoice['number']}  {total(invoice):>10.2f}\")",
                    "        if csv:\n            print(f\"{invoice['number']},{total(invoice):.2f}\")\n        else:\n            print(f\"{invoice['number']}  {total(invoice):>10.2f}\")")
open("invoices.py", "w").write(text)
PY
git commit -qam "feat(invoices): print the invoices as csv"
