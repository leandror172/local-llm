---
id: python-06-decorator-factory
domain: python
difficulty: medium
timeout: 300
description: Decorator factories for caching, retry, and rate limiting
---

Write a collection of decorator factories in Python.

1. `@cache(maxsize: int = 128, ttl: float | None = None)` — LRU cache with optional TTL:
   - Works on both sync and async functions
   - Exposes `fn.cache_clear()` and `fn.cache_info()` on the wrapped function

2. `@retry(max_attempts: int = 3, exceptions: tuple = (Exception,), backoff: float = 0.5)`:
   - Works on both sync and async functions, exponential backoff, logs each retry

3. `@rate_limit(calls: int, period: float)` — thread-safe using `threading.Lock`; raises `RateLimitExceeded`

4. `@validate_types` — validates type hints at call time using `__annotations__`; supports `Optional[X]` and `Union[X, Y]`

Requirements: `functools.wraps`, `TypeVar`, `Callable[..., T]`, doctest examples in docstrings
