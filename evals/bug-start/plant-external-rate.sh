#!/bin/bash
# Plants a failure whose cause is not in the repository: develop takes the tax rate
# from a rates service, a command outside the tracked code, which answers no tax.
mkdir -p .remote/bin
printf '#!/bin/sh\necho 0.0\n' > .remote/bin/invoice-rates
chmod +x .remote/bin/invoice-rates
sed -i "s|^TAX = 0.16$|TAX = float(__import__('subprocess').check_output(['$PWD/.remote/bin/invoice-rates'], text=True))|" invoices.py
git diff --quiet && { echo "the rate was not planted: story-start/project.sh changed" >&2; exit 1; }
git commit -qam "take the tax rate from the rates service"
