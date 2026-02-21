---
id: java-04-spring-events
domain: java
difficulty: medium
timeout: 300
description: Event-driven Spring Boot service with ApplicationEventPublisher
---

Implement an event-driven order processing service using Spring's application event system.

Requirements:

1. Events (plain POJOs, Spring 4.2+ style):
   - `OrderPlacedEvent(String orderId, String customerId, double total)`
   - `OrderShippedEvent(String orderId, String trackingNumber)`
   - `OrderCancelledEvent(String orderId, String reason)`

2. `OrderService` that injects `ApplicationEventPublisher`:
   - `placeOrder(String customerId, double total)` — creates UUID order ID, publishes `OrderPlacedEvent`, returns ID
   - `shipOrder(String orderId, String trackingNumber)` — publishes `OrderShippedEvent`
   - `cancelOrder(String orderId, String reason)` — publishes `OrderCancelledEvent`

3. `NotificationListener` with `@EventListener` for each event, logging a message
4. `AuditListener` with `@EventListener` that logs all three events to an in-memory `List<String>` and exposes `getLog()`

Requirements:
- Constructor injection throughout
- `@Async` on `NotificationListener` (configure `@EnableAsync`)
- Use `jakarta.*` namespace throughout
