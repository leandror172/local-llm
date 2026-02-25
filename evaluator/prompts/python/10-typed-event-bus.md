---
id: python-10-typed-event-bus
domain: python
difficulty: hard
timeout: 420
description: Type-safe event bus with Protocol, generics, and async handlers
---

Implement a type-safe event bus using `typing.Protocol` and generics.

1. `EventHandler(Protocol[E])`: `async def handle(self, event: E) -> None`

2. `EventBus`:
   - `subscribe(event_type: type[E], handler) -> Callable[[], None]` (returns unsubscribe)
   - `subscribe_fn(event_type, fn: Callable[[E], Awaitable[None]]) -> Callable[[], None]`
   - `async def publish(self, event: E) -> list[PublishResult]` — all handlers concurrently
   - `handler_count(event_type: type) -> int`

3. `PublishResult` dataclass: `handler_name`, `success`, `error: Exception | None`, `duration_ms`

4. Concrete example: `UserSignedUp`, `PasswordChanged` events; `WelcomeEmailHandler`, `AuditHandler`

5. `broadcast_many(bus, events)` → publish all events concurrently with `asyncio.gather`

Requirements: `from __future__ import annotations`, `asyncio.gather(return_exceptions=True)`, idempotent unsubscribe, async `main()` demo
