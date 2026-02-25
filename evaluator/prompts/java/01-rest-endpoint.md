---
id: java-01-rest-endpoint
domain: java
difficulty: easy
timeout: 300
description: Spring Boot 3.x REST endpoint with Jakarta validation
---

Write a Spring Boot 3.x REST controller in Java that manages a `Task` resource.

Requirements:

1. `Task` record: `id` (UUID), `title` (String), `completed` (boolean), `createdAt` (Instant)
2. `TaskController` with:
   - `POST /tasks` — validates `title` is not blank (`@NotBlank`); returns 201 with the created task
   - `GET /tasks/{id}` — returns the task or 404 if not found
   - `PUT /tasks/{id}/complete` — marks a task as completed; returns 200 or 404
   - `DELETE /tasks/{id}` — deletes; returns 204 or 404
3. `TaskService` with an in-memory `ConcurrentHashMap` store
4. `GlobalExceptionHandler` with `@RestControllerAdvice` returning `ProblemDetail` for validation errors (RFC 9457)

Requirements:
- Use `jakarta.*` namespace (NOT `javax.*`)
- Constructor injection throughout (NO `@Autowired` field injection)
- `ProblemDetail` (Spring Boot 3.x native RFC 9457 support)
- Use `java.util.UUID` for IDs, `java.time.Instant` for timestamps
