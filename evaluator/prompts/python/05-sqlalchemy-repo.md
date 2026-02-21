---
id: python-05-sqlalchemy-repo
domain: python
difficulty: medium
timeout: 300
description: SQLAlchemy 2.0 async repository with type-safe queries
---

Write a SQLAlchemy 2.0 async repository for a user management system.

1. Models using `DeclarativeBase`:
   - `User`: `id` (UUID PK), `email` (unique, indexed), `username` (unique), `hashed_password`, `is_active` (default True), `created_at` (server_default=now)
   - `Role`: `id` (int), `name` (unique)
   - Many-to-many: `UserRole` association table

2. `UserRepository(__init__(self, session: AsyncSession))`:
   - `create`, `get_by_id`, `get_by_email`, `list_active(limit, offset)`, `assign_role`, `deactivate`, `search` (ilike on username/email)

3. `get_session()` async generator for FastAPI dependency injection

Requirements:
- SQLAlchemy 2.0 `select()` style (no legacy `Query`)
- `Mapped[str]`, `Mapped[Optional[str]]` column typing
- `uuid.uuid4` as Python-side default for UUID PK
