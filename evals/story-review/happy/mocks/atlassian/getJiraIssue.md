---
expect:
  cloudId: string
  issueIdOrKey: ABC-31
---

{"issues": {"nodes": [{"id": "31", "key": "ABC-31", "fields": {"summary": "Print the invoices as CSV", "description": "Como cliente, quiero ver mis facturas en CSV, para abrirlas en una hoja de cálculo.\n\n### Done when\n\n* `python3 invoices.py acme --csv` imprime una línea `number,total` por factura.\n\n### Out of scope\n\n* Otros formatos.", "status": {"name": "Implement"}, "issuetype": {"name": "Story"}, "issuelinks": [], "comment": {"comments": [{"id": "1", "body": "### Evidence\n\n* ran: `python3 invoices.py acme` → F-001 116.00 and F-002 290.00"}]}}, "webUrl": "https://example.atlassian.net/browse/ABC-31"}]}}
