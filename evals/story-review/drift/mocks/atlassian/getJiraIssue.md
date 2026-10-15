---
expect:
  cloudId: string
  issueIdOrKey: ABC-57
---

{"issues": {"nodes": [{"id": "57", "key": "ABC-57", "fields": {"summary": "Print the invoices as CSV", "description": "Como cliente, quiero ver mis facturas en CSV, para abrirlas en una hoja de cálculo.\n\n### Done when\n\n* `python3 invoices.py acme --csv` imprime una línea `number,total` por factura.\n\n### Out of scope\n\n* Otros formatos.", "status": {"name": "Implement"}, "issuetype": {"name": "Story"}, "issuelinks": [], "comment": {"comments": [{"id": "1", "body": "### Evidence\n\n* ran: `python3 invoices.py acme` → F-001 999.00 and F-002 999.00"}]}}, "webUrl": "https://example.atlassian.net/browse/ABC-57"}]}}
