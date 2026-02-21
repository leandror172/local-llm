---
id: java-05-rate-limiter
domain: java
difficulty: medium
timeout: 300
description: Token bucket rate limiter with concurrent access
---

Implement a thread-safe token bucket rate limiter in Java.

Requirements:

1. Interface:
   ```java
   public interface RateLimiter {
       boolean tryAcquire();
       boolean tryAcquire(int permits);
       void acquire() throws InterruptedException;
       RateLimiterStats stats();
   }
   ```

2. `TokenBucketRateLimiter` implementing `RateLimiter`:
   - Constructor: `TokenBucketRateLimiter(int capacity, int refillRatePerSecond)`
   - Background thread refills tokens using `ScheduledExecutorService`
   - `acquire()` blocks until a token is available using `ReentrantLock` + `Condition`

3. `record RateLimiterStats(long totalRequests, long grantedRequests, long rejectedRequests, int currentTokens)`

4. `RateLimiterRegistry` Spring `@Component`:
   - `getOrCreate(String name, int capacity, int refillRate)` → `RateLimiter`
   - `@PreDestroy` to shut down executors

Requirements:
- `AtomicInteger` for token count
- Constructor injection in `RateLimiterRegistry`
