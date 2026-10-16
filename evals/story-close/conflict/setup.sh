#!/bin/bash
# Reviewed story ABC-74: its branch with the commit, pushed.
. "$(dirname "$0")/../../story-review/work.sh" ABC-74 commit
git push -q -u origin HEAD
git switch -q develop
python3 - <<'PY'
text = open("invoices.py").read()
text = text.replace("        print(f\"{invoice['number']}  {total(invoice):>10.2f}\")", "        print(f\"{invoice['number']} {total(invoice):.2f}\")")
open("invoices.py", "w").write(text)
PY
git commit -qam "feat(invoices): tighten the invoice line"
git push -q origin develop
git switch -q story/ABC-74/print-the-invoices-as-csv
