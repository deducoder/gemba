---
expect:
  cloudId: string
  issueIdOrKey: ABC-30
---

{"issues": {"nodes": [{"id": "30", "key": "ABC-30", "fields": {"summary": "Check whether the billing API lists the invoices of a customer", "description": "\u00bfPuede un script traer las facturas de un cliente desde `https://billing.example.org/api/invoices`, un API que pide un contacto (correo o nombre de quien lo llama) en el `User-Agent`? De la respuesta depende si la historia de sincronizar facturas lee del API o de `invoices.py`.\n\n### Done when\n\n* La respuesta es s\u00ed, no o inconclusa, con la salida de un script de prueba que llama al API.\n\n### Out of scope\n\n* Sincronizar las facturas \u2192 ABC-40", "status": {"name": "Backlog"}, "issuetype": {"name": "Spike"}, "issuelinks": [], "comment": {"comments": [{"id": "1", "body": "### Evidence\n\n* ran: `python3 invoices.py acme` \u2192 F-001 116.00 and F-002 290.00"}]}}, "webUrl": "https://example.atlassian.net/browse/ABC-30"}]}}
