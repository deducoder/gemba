---
error: true
expect:
  cloudId: string
  issueIdOrKey: ABC-99
---

{"error":true,"message":"{\"errorMessages\":[\"Issue does not exist or you do not have permission to see it.\"],\"errors\":{}}","rateLimit":{"limit":400,"remaining":399,"headers":{"x-ratelimit-limit":"400","x-ratelimit-remaining":"399"}},"statusCode":404}
