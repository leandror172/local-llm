---
id: python-04-async-scraper
domain: python
difficulty: medium
timeout: 300
description: Async web scraper with rate limiting and error handling
---

Write an async web scraper using `aiohttp` and `asyncio`.

1. `RateLimiter` using `asyncio.Semaphore` with token bucket (`asyncio.sleep` for refill)

2. `Scraper` class:
   - `__init__(self, rps: int = 5, timeout: int = 30, retries: int = 3)`
   - `async def fetch(self, url: str) -> ScrapedPage` — GET with retry + exponential backoff (`0.5 * 2**attempt` seconds)
   - `async def fetch_many(self, urls: list[str]) -> list[ScrapedPage]` — concurrent with rate limiting
   - Works as async context manager

3. `ScrapedPage` dataclass: `url`, `status_code`, `content`, `fetch_time_ms`, `error: str | None = None`

4. `extract_links(html: str, base_url: str) -> list[str]` using stdlib `html.parser`

Requirements: full type hints, `logging` module (not print), `asyncio.gather`
