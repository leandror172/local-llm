---
id: go-10-event-bus
domain: go
difficulty: hard
timeout: 600
description: Type-safe event bus with generics and async dispatch
---

Implement a type-safe event bus in Go using generics.

Requirements:

1. Generic event bus:
   ```go
   type Bus[E any] struct { ... }
   func NewBus[E any]() *Bus[E]
   ```

2. Methods:
   - `Subscribe(handler func(E)) (cancel func())` — register a handler; returns a cancel function that unsubscribes it
   - `Publish(event E)` — deliver the event to all current subscribers asynchronously (each handler runs in its own goroutine)
   - `PublishSync(event E)` — deliver synchronously, wait for all handlers to complete
   - `Len() int` — number of active subscribers

3. Typed event structs (define at least three):
   - `UserCreated{ID string, Email string, CreatedAt time.Time}`
   - `OrderPlaced{OrderID string, UserID string, Amount float64}`
   - `EmailSent{To string, Subject string, SentAt time.Time}`

4. `MultiListener` helper:
   ```go
   func Subscribe[E any](bus *Bus[E], handler func(E)) func()
   ```
   (Package-level generic function — not a method — to work around Go's lack of generic methods)

Requirements:
- Concurrent-safe (sync.RWMutex on subscriber map)
- Cancel function is idempotent (calling it multiple times is safe)
- Async `Publish` must not block the caller even if handlers are slow
- Include a `main()` demonstrating three event types, multiple subscribers, and cancellation
