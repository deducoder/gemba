#!/bin/bash
# Plants a failure whose cause is not in the repository: the tax rate comes from a
# compiled library whose source is never committed, and a later commit replaces the
# library with one that returns no tax, so neither the code nor the history says why.
library() {
  local src
  src="$(mktemp -d)"
  printf 'double rate(void) { return %s; }\n' "$1" > "$src/rates.c"
  gcc -shared -fPIC -o librates.so "$src/rates.c"
  rm -rf "$src"
}
library 0.16
python3 - <<'PY'
from pathlib import Path
p = Path("invoices.py")
t = p.read_text()
t = t.replace("import sys\n", "import ctypes\nimport sys\nfrom pathlib import Path\n", 1)
t = t.replace("TAX = 0.16\n", "_rates = ctypes.CDLL(str(Path(__file__).with_name(\"librates.so\")))\n_rates.rate.restype = ctypes.c_double\nTAX = _rates.rate()\n", 1)
p.write_text(t)
PY
git add invoices.py librates.so
git commit -qm "read the tax rate from the rates library"
library 0.0
git commit -qam "update the rates library"
