---
id: go-01-http-handler
domain: go
difficulty: easy
timeout: 300
description: HTTP server with logging middleware
---

Write an HTTP server in Go using only the standard library (`net/http`) that:

1. Listens on port 8080
2. Has a `/health` endpoint that returns `{"status": "ok"}` as JSON
3. Has a `/hello/{name}` endpoint that returns `{"message": "Hello, {name}!"}` as JSON
4. Wraps all routes with a logging middleware that prints the HTTP method, path, and response duration to stdout in the format: `METHOD /path 200 12.3ms`

Requirements:
- Use `http.NewServeMux()` (Go 1.22+ pattern with path parameters)
- Proper `Content-Type: application/json` header on all responses
- The logging middleware should work generically for any handler
- Include a `main()` with the server setup and a graceful shutdown on SIGINT
