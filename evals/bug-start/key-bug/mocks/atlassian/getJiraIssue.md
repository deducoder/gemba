---
expect:
  cloudId: string
  issueIdOrKey: ABC-12
---

{"issues": {"nodes": [{"id": "12", "key": "ABC-12", "fields": {"summary": "Invoice totals leave out the tax", "status": {"name": "Backlog"}, "issuetype": {"name": "Bug"}, "project": {"key": "ABC"}}, "webUrl": "https://example.atlassian.net/browse/ABC-12"}]}}
