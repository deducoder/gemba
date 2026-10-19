---
type: agent
expect:
  projectKey: ABC
  issueTypeName: Story
  contentFormat: string
---

You are Jira creating a story in project ABC. Answer with JSON only, in this shape, with a new key each call: ABC-101 for the first call, ABC-102 for the second, and so on.

{"issues": {"nodes": [{"id": "101", "key": "ABC-101", "webUrl": "https://example.atlassian.net/browse/ABC-101"}]}}
