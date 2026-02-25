---
id: java-06-custom-starter
domain: java
difficulty: medium
timeout: 300
description: Custom Spring Boot auto-configuration starter
---

Write a custom Spring Boot auto-configuration that provides an audit logging facility.

Requirements:

1. `AuditProperties` (`@ConfigurationProperties(prefix = "audit")`):
   - `enabled` (boolean, default true), `logLevel` (String, default "INFO")
   - `includeRequestBody` (boolean, default false), `excludePaths` (List<String>)

2. `AuditEvent` record: `timestamp`, `method`, `path`, `statusCode`, `durationMs`, `requestBody` (nullable)

3. `AuditService`: stores events in memory, exposes `record(AuditEvent)`, `getRecent(int n)`, `getByPath(String path)`

4. `AuditFilter` (`OncePerRequestFilter`): intercepts all requests, creates and records `AuditEvent`

5. `AuditAutoConfiguration`:
   - `@AutoConfiguration`
   - `@ConditionalOnWebApplication`
   - `@ConditionalOnProperty(prefix = "audit", name = "enabled", havingValue = "true", matchIfMissing = true)`
   - `@ConditionalOnMissingBean` on each declared bean

Requirements:
- All `jakarta.*` imports, constructor injection everywhere
- Show the `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` entry as a comment
