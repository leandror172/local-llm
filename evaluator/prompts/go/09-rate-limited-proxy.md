---
id: go-09-rate-limited-proxy
domain: go
difficulty: hard
timeout: 600
description: Rate-limited HTTP reverse proxy with per-host limits
---

Implement a rate-limited HTTP reverse proxy in Go using only the standard library.

Requirements:

1. `ProxyConfig` struct:
   - `Targets []string` — list of backend URLs to round-robin
   - `RateLimit int` — requests per second (global, across all targets)
   - `Timeout time.Duration` — per-request timeout
   - `StripPrefix string` — optional path prefix to strip before forwarding

2. `RateLimitedProxy` struct with:
   - Constructor: `NewProxy(cfg ProxyConfig) (*RateLimitedProxy, error)`
   - Implements `http.Handler`
   - Round-robins across targets using an atomic counter
   - Enforces global rate limit using a token bucket (`time.Ticker` refilling a buffered channel)
   - Returns HTTP 429 with `Retry-After` header when rate limited
   - Strips `StripPrefix` from request path before proxying
   - Adds `X-Forwarded-For` and `X-Forwarded-Host` headers

3. Health check endpoint at `/proxy-health` (handled directly, not proxied)

Requirements:
- Use `httputil.ReverseProxy` as the actual proxy mechanism
- Use `atomic.Int64` for round-robin counter
- Token bucket implemented with a buffered channel (capacity = rate limit, refilled by goroutine)
- Include a `main()` with two mock backend servers and the proxy
