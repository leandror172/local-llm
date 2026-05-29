---
id: 01-go-lru-cache
category: backend
models: my-coder,my-coder-q3
timeout: 300
description: Concurrent-safe LRU cache with TTL expiration in Go
source: closing-the-gap benchmark
---

Write a concurrent-safe LRU cache in Go with the following requirements:
- Generic key-value types using Go generics
- TTL (time-to-live) expiration per entry
- Thread-safe Get, Put, and Delete operations using sync.RWMutex
- Automatic eviction of expired entries on access
- A background goroutine that periodically cleans expired entries (configurable interval); must accept a context.Context stop signal so the goroutine exits cleanly — no goroutine leaks
- Maximum capacity with LRU eviction when full
- Include a complete main() demonstrating usage with 3+ concurrent goroutines performing Get/Put operations; must be runnable with `go run -race` without data race warnings
