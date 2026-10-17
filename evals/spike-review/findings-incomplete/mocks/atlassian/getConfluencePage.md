---
expect:
  cloudId: string
  pageId: "1006"
---

{"content": {"totalCount": 1, "nodes": [{"id": "1006", "type": "page", "subtype": "live", "status": "current", "title": "ABC-35 Check whether invoices can be listed as JSON", "lastModified": "1 minute ago", "summary": "Findings.", "space": {"key": "ABC", "name": "ABC"}, "_links": {"webui": "/spaces/ABC/pages/1006/p"}, "author": {"displayName": "", "avatarUrls": {"48x48": ""}}, "body": "[ABC-35](https://example.atlassian.net/browse/ABC-35)\n\n\u00bfPuede la biblioteca est\u00e1ndar de Python imprimir una lista de facturas como JSON? De la respuesta depende si la historia de exportar facturas usa JSON o CSV.\n\n## Answer\n\n**S\u00ed.** El m\u00f3dulo `json` de la biblioteca est\u00e1ndar imprime una lista de facturas como JSON v\u00e1lido, con los totales como n\u00fameros.\n\n## Next\n\nLa historia de exportar facturas puede usar JSON.\n", "webUrl": "https://example.atlassian.net/wiki/spaces/ABC/pages/1006/p"}]}}
