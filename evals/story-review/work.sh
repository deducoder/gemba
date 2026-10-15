#!/bin/bash
# Builds the project the story-review and story-close cases observe: the story-implement
# project with the branch of the story pushed empty at the Implement mark. With "commit"
# it adds the one commit of its own that builds the story.
# Usage: . work.sh <KEY> [commit]
set -e
. "$(dirname "${BASH_SOURCE[0]}")/../story-implement/project.sh"
git switch -q -c "story/$1/print-the-invoices-as-csv"
git push -q -u origin "story/$1/print-the-invoices-as-csv"
if [ "$2" = commit ]; then
python3 - <<'PY'
text = open("invoices.py").read()
text = text.replace("    if len(argv) != 1:", "    csv = \"--csv\" in argv\n    argv = [arg for arg in argv if arg != \"--csv\"]\n    if len(argv) != 1:")
text = text.replace("        print(f\"{invoice['number']}  {total(invoice):>10.2f}\")",
                    "        if csv:\n            print(f\"{invoice['number']},{total(invoice):.2f}\")\n        else:\n            print(f\"{invoice['number']}  {total(invoice):>10.2f}\")")
open("invoices.py", "w").write(text)
PY
git commit -qam "feat(invoices): print the invoices as csv"
fi
