---
expect:
  cloudId: string
  issueIdOrKey: ABC-30
---

{"issues": {"nodes": [{"id": "30", "key": "ABC-30", "fields": {"summary": "Print the invoices as CSV", "description": "Como cliente, quiero ver mis facturas en CSV, para abrirlas en una hoja de c\u00e1lculo.\n\n### Done when\n\n* `python3 invoices.py acme --csv` imprime una l\u00ednea `number,total` por factura.\n\n### Out of scope\n\n* Otros formatos.", "status": {"name": "Backlog"}, "issuetype": {"name": "Story"}, "issuelinks": [], "comment": {"comments": [{"id": "1", "body": "### Evidence\n\n* ran: `python3 invoices.py acme` → F-001 116.00 and F-002 290.00"}]}}, "webUrl": "https://example.atlassian.net/browse/ABC-30"}]}}
