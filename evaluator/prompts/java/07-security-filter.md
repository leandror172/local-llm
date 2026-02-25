---
id: java-07-security-filter
domain: java
difficulty: medium
timeout: 420
description: Spring Security JWT authentication filter chain
---

Implement JWT-based authentication for a Spring Boot 3.x application.

Requirements:

1. `JwtProperties` (`@ConfigurationProperties(prefix = "jwt")`): `secret`, `expirationMs`

2. `JwtService`: `generateToken(String username, List<String> roles)`, `extractUsername(String token)`, `isValid(String token)` — implement using HMAC-SHA256 with `javax.crypto.Mac` (note: `javax.crypto` is JDK stdlib, NOT Jakarta EE)

3. `JwtAuthenticationFilter` extends `OncePerRequestFilter`: reads `Authorization: Bearer` header, validates, sets `SecurityContextHolder`

4. `SecurityConfig` (`@Configuration`, `@EnableWebSecurity`):
   - `SecurityFilterChain` bean
   - Permit `/auth/**`, require auth for everything else
   - `SessionCreationPolicy.STATELESS`
   - Add filter before `UsernamePasswordAuthenticationFilter`

5. `AuthController` with `POST /auth/login` returning a JWT

Requirements:
- `jakarta.servlet.*` for servlet types, constructor injection, `SecurityFilterChain` pattern
