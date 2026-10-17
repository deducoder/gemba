---
expect:
  cloudId: string
  issueIdOrKey: ABC-33
---

{"issues": {"nodes": [{"id": "33", "key": "ABC-33", "fields": {"summary": "Check whether invoices can be listed as JSON", "description": "\u00bfPuede `invoices.py` imprimir las facturas de un cliente como JSON sin cambiar su lista `INVOICES`? De la respuesta depende si la historia de exportar facturas usa JSON o CSV.\n\n### Done when\n\n* La respuesta es s\u00ed, no o inconclusa, con la salida de un script de prueba.\n\n### Out of scope\n\n* Cambiar `invoices.py` \u2192 ABC-40", "status": {"name": "Backlog"}, "issuetype": {"name": "Spike"}, "issuelinks": [{"type": {"name": "Blocks", "inward": "is blocked by", "outward": "blocks"}, "inwardIssue": {"key": "ABC-34", "fields": {"summary": "Share the invoice model", "status": {"name": "Backlog"}, "issuetype": {"name": "Story"}}}}], "timetracking": {"originalEstimate": "2h", "originalEstimateSeconds": 7200}, "comment": {"comments": [{"id": "1", "body": "### Evidence\n\n* ran: `python3 invoices.py acme` \u2192 F-001 116.00 and F-002 290.00"}]}}, "webUrl": "https://example.atlassian.net/browse/ABC-33"}]}}
