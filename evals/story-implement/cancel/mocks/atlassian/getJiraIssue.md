---
expect:
  cloudId: string
  issueIdOrKey: ABC-40
---

{"issues": {"nodes": [{"id": "40", "key": "ABC-40", "fields": {"summary": "Print the invoices as CSV", "description": "Como cliente, quiero ver mis facturas en CSV, para abrirlas en una hoja de c\u00e1lculo.\n\n### Done when\n\n* `python3 invoices.py acme --csv` imprime una l\u00ednea `number,total` por factura.\n\n### Out of scope\n\n* Otros formatos.", "status": {"name": "Backlog"}, "issuetype": {"name": "Story"}, "issuelinks": [], "comment": {"comments": [{"id": "1", "body": "### Evidence\n\n* ran: `python3 invoices.py acme` \u2192 F-001 999.00 and F-002 999.00"}]}}, "webUrl": "https://example.atlassian.net/browse/ABC-40"}]}}
