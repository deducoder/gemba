---
expect:
  cloudId: string
  issueIdOrKey: ABC-60
---

{"issues": {"nodes": [{"id": "60", "key": "ABC-60", "fields": {"summary": "Customers manage their invoices on their own", "issuetype": {"name": "Epic"}, "status": {"name": "Review"}, "issuelinks": [{"id": "10501", "type": {"id": "10003", "name": "Relates", "inward": "relates to", "outward": "relates to"}, "inwardIssue": {"id": "70", "key": "ABC-70", "fields": {"summary": "The invoice export drops the accents", "status": {"name": "Backlog"}, "issuetype": {"name": "Bug"}}}}]}, "webUrl": "https://example.atlassian.net/browse/ABC-60"}]}}
