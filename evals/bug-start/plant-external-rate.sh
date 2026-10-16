#!/bin/bash
# Plants a failure whose cause is not in the repository: develop takes the tax rate
# from a rates service, a command installed outside the project, which answers no tax.
service="$(mktemp -d)/invoice-rates"
printf '#!/bin/sh\necho 0.0\n' > "$service"
chmod +x "$service"
SERVICE="$service" python3 - <<'PY'
import os
from pathlib import Path
p = Path("invoices.py")
t = p.read_text()
t = t.replace("import sys\n", "import subprocess\nimport sys\n", 1)
t = t.replace("TAX = 0.16\n", f"RATES = {os.environ['SERVICE']!r}\nTAX = float(subprocess.run([RATES], capture_output=True, text=True, check=True).stdout)\n", 1)
p.write_text(t)
PY
git commit -qam "take the tax rate from the rates service"
