---
expect:
  cloudId: string
  issueIdOrKey: ABC-55
---

{"expand": "transitions", "transitions": [{"id": "14", "name": "Cancelled", "to": {"name": "Cancelled", "id": "10079"}}, {"id": "41", "name": "to Review", "to": {"name": "Review", "id": "10077"}}, {"id": "42", "name": "to Backlog", "to": {"name": "Backlog", "id": "10074"}}]}
