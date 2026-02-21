---
id: java-02-jpa-entity
domain: java
difficulty: easy
timeout: 300
description: JPA entity with relationships and lifecycle hooks
---

Write a JPA entity model in Java (Spring Boot 3.x / Jakarta Persistence) for a blog system.

Requirements:

1. `Author` entity: `id` (Long, auto-generated), `name` (String, not null), `email` (String, unique), `createdAt` (Instant)
2. `Post` entity: `id`, `title`, `content` (Text), `publishedAt` (Instant, nullable), `author` (ManyToOne)
3. `Tag` entity: `id`, `name` (unique); Posts have a ManyToMany relationship with Tags
4. `@PrePersist` lifecycle hook on `Post` to set `createdAt` automatically
5. A Spring Data JPA repository for each entity with at least one custom query method each

Requirements:
- Use `jakarta.persistence.*` (NOT `javax.persistence.*`)
- All relationships use `FetchType.LAZY`
- `@Column` annotations with `nullable = false` where appropriate
- `@Table` with `name` specified for each entity
