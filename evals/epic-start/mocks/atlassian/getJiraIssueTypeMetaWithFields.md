---
expect:
  cloudId: string
  projectIdOrKey: ABC
---

{"startAt": 0, "maxResults": 50, "total": 3, "fields": [{"required": false, "schema": {"type": "date", "system": "duedate"}, "name": "Due date", "key": "duedate", "fieldId": "duedate"}, {"required": false, "schema": {"type": "array", "items": "version", "system": "fixVersions"}, "name": "Fix versions", "key": "fixVersions", "fieldId": "fixVersions", "allowedValues": [{"id": "1", "name": "ABC v1.0.0", "archived": false, "released": true, "releaseDate": "2026-09-30"}, {"id": "2", "name": "ABC v1.1.0", "archived": false, "released": false, "releaseDate": "2026-11-30"}]}, {"required": false, "schema": {"type": "priority", "system": "priority"}, "name": "Priority", "key": "priority", "fieldId": "priority", "allowedValues": [{"name": "Highest", "id": "1"}, {"name": "High", "id": "2"}, {"name": "Medium", "id": "3"}, {"name": "Low", "id": "4"}]}]}
