---
id: go-07-middleware-chain
domain: go
difficulty: medium
timeout: 300
description: Composable HTTP middleware chain with context values
---

Design a composable HTTP middleware system in Go.

Requirements:

1. Type alias: `type Middleware func(http.Handler) http.Handler`
2. Function: `Chain(middlewares ...Middleware) Middleware` that composes middlewares left-to-right (first in list runs first)
3. Implement three middlewares:
   - `RequestID()` — generates a UUID-like request ID (use `fmt.Sprintf("%d", time.Now().UnixNano())` as a simple ID), stores it in context, and adds `X-Request-ID` to response headers
   - `RateLimit(rps int)` — allows `rps` requests per second per remote IP using a token bucket; returns HTTP 429 when exceeded (use `sync.Map` to track per-IP state)
   - `BasicAuth(username, password string)` — validates `Authorization: Basic ...` header; returns 401 with `WWW-Authenticate` header if missing or wrong
4. A context key type and `GetRequestID(ctx context.Context) string` helper

Requirements:
- Define a typed context key (not a raw string) to avoid collisions
- `Chain` must work with any number of middlewares including zero
- Include a `main()` demonstrating all three middlewares applied to a simple echo handler
