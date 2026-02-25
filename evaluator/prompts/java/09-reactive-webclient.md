---
id: java-09-reactive-webclient
domain: java
difficulty: hard
timeout: 420
description: Reactive WebClient with retry, circuit breaker, and caching
---

Implement a resilient reactive HTTP client in Spring WebFlux.

Requirements:

1. `WeatherClient` using Spring's `WebClient`:
   - `getTemperature(String city)` → `Mono<Double>`
   - `getForecast(String city, int days)` → `Flux<DailyForecast>`
   - `getBulkTemperatures(List<String> cities)` → `Flux<CityTemperature>` (parallel)

2. Resilience:
   - Retry with exponential backoff: 3 retries, `Retry.backoff(3, Duration.ofSeconds(1))`
   - `.timeout(Duration.ofSeconds(5))` per request
   - Resilience4j `ReactorCircuitBreaker`

3. `CachingWeatherClient` decorator wrapping `WeatherClient` with 5-minute TTL `ConcurrentHashMap` cache

4. `WeatherProperties` (`@ConfigurationProperties(prefix = "weather")`): `baseUrl`, `apiKey`, `timeoutSeconds`

Requirements:
- `jakarta.*` namespace, constructor injection
- `record DailyForecast(LocalDate date, double high, double low, String condition)`
- `record CityTemperature(String city, double celsius, Instant fetchedAt)`
