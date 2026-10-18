---
expect:
  cloudId: string
  issueIdOrKey: ABC-7
---

{"issues": {"nodes": [{"id": "7", "key": "ABC-7", "fields": {"summary": "Export the invoices", "status": {"name": "Backlog"}, "issuetype": {"name": "Epic"}, "project": {"key": "ABC"}, "fixVersions": [{"id": "2", "name": "ABC v1.1.0", "archived": false, "released": false, "releaseDate": "2026-11-30"}]}, "webUrl": "https://example.atlassian.net/browse/ABC-7"}]}}
