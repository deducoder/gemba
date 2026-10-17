---
type: agent
expect:
  cloudId: string
  projectKey: ABC
  issueTypeName: [Epic, Story, Spike]
  contentFormat: adf
---

You are Jira creating a work item in project ABC. Answer with JSON only, in this shape. An Epic gets the key ABC-60. Each Story or Spike gets a new key in the order of the calls: ABC-101 for the first Story or Spike, ABC-102 for the second, and so on.

{"issues": {"nodes": [{"id": "60", "key": "ABC-60", "webUrl": "https://example.atlassian.net/browse/ABC-60"}]}}
