---
id: go-04-concurrent-cache
domain: go
difficulty: medium
timeout: 300
description: Concurrent-safe LRU cache with TTL expiration
---

Implement a concurrent-safe LRU (Least Recently Used) cache in Go with TTL expiration.

Requirements:

1. Generic type: `Cache[K comparable, V any]`
2. Constructor: `NewCache[K, V](capacity int, ttl time.Duration) *Cache[K, V]`
3. Methods:
   - `Set(key K, value V)` — add or update an entry
   - `Get(key K) (V, bool)` — retrieve; returns false if missing or expired
   - `Delete(key K)` — remove an entry
   - `Len() int` — current number of valid (non-expired) entries
4. Eviction: when capacity is reached, evict the least recently used entry
5. TTL: entries expire after `ttl` duration; expired entries return false on `Get` even if still in the cache
6. Concurrent-safe: all methods must be safe to call from multiple goroutines simultaneously

Requirements:
- Use `sync.RWMutex` for concurrent access
- Use Go generics (Go 1.21+)
- Implement the LRU ordering with a doubly linked list + map (no external packages)
- Include a `main()` that demonstrates concurrent Set/Get operations using goroutines
