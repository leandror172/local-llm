---
id: go-03-json-api-client
domain: go
difficulty: easy
timeout: 600
description: JSON HTTP API client with error handling and retry
---

Write a Go HTTP client (standard library only) that:

1. Defines a `Client` struct with a base URL and an `http.Client` with a configurable timeout
2. Has a `Get(path string, out any) error` method that:
   - Makes a GET request to `{baseURL}{path}`
   - Decodes the JSON response body into `out`
   - Returns a typed error distinguishing network errors, non-2xx status codes, and JSON decode failures
3. Has a `Post(path string, body any, out any) error` method that:
   - Marshals `body` to JSON, sends as POST with `Content-Type: application/json`
   - Decodes the response into `out`
4. Includes a simple retry helper `WithRetry(n int, fn func() error) error` that retries `fn` up to `n` times on error, with no delay

Requirements:
- Custom error types (not just `fmt.Errorf`)
- `context.Context` passed through all methods (add `Ctx` field or pass as parameter)
- Include a `main()` that demonstrates calling a public API (e.g., `https://httpbin.org/get`)
