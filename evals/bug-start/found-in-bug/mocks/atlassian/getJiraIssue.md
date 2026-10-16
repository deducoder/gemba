---
expect:
  cloudId: string
  issueIdOrKey: ABC-12
---

{"issues": {"nodes": [{"id": "12", "key": "ABC-12", "fields": {"summary": "Crash on a customer with no invoices", "status": {"name": "Implement"}, "issuetype": {"name": "Bug"}, "project": {"key": "ABC"}}, "webUrl": "https://example.atlassian.net/browse/ABC-12"}]}}
