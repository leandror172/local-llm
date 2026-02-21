---
id: java-08-cqrs-handler
domain: java
difficulty: hard
timeout: 420
description: CQRS command/query bus with validation and auditing
---

Implement a lightweight CQRS command bus in Java using Spring.

Requirements:

1. Generic interfaces:
   ```java
   interface Command<R> {}
   interface CommandHandler<C extends Command<R>, R> { R handle(C command); }
   interface Query<R> {}
   interface QueryHandler<Q extends Query<R>, R> { R handle(Q query); }
   ```

2. `SimpleCommandBus`:
   - Auto-discovers all `CommandHandler` beans via `ApplicationContext.getBeansOfType`
   - Dispatches command to correct handler by matching generic type parameter
   - Pipeline: validate (jakarta.validation `@Valid`) → audit log → execute
   - Throws `HandlerNotFoundException` if no handler registered

3. Concrete example — Product inventory:
   - `CreateProductCommand(String name, int quantity)` → `String` (product ID)
   - `AdjustInventoryCommand(String productId, int delta)` → `void`
   - `GetProductQuery(String productId)` → `ProductDto record(String id, String name, int quantity)`
   - Handlers for all three using in-memory store

Requirements:
- Spring `@Component` for all handlers, constructor injection, `jakarta.*` for validation
