---
expect:
  cloudId: string
  issueIdOrKey: ABC-35
---

{"issues": {"nodes": [{"id": "35", "key": "ABC-35", "fields": {"summary": "Check whether invoices can be listed as JSON", "description": "\u00bfPuede la biblioteca est\u00e1ndar de Python imprimir una lista de facturas como JSON? De la respuesta depende si la historia de exportar facturas usa JSON o CSV.\n\n### Done when\n\n* La respuesta es s\u00ed, no o inconclusa, con la salida de un script de prueba.\n\n### Out of scope\n\n* Cambiar `invoices.py` \u2192 ABC-40", "status": {"name": "Implement"}, "issuetype": {"name": "Spike"}, "issuelinks": [], "comment": {"comments": [{"id": "1", "body": "### Evidence\n\n* ran: `python3 invoices.py acme` \u2192 F-001 116.00 and F-002 290.00"}]}}, "webUrl": "https://example.atlassian.net/browse/ABC-35"}]}}
