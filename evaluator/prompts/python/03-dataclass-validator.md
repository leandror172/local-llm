---
id: python-03-dataclass-validator
domain: python
difficulty: easy
timeout: 180
description: Dataclass with custom validation and serialization
---

Write Python dataclasses for a configuration system with validation.

1. `@dataclass(frozen=True, slots=True)` class `DatabaseConfig`:
   - `host: str` (non-empty), `port: int` (1-65535), `database: str` (alphanumeric+underscores)
   - `pool_size: int = 5` (1-100), `timeout_seconds: float = 30.0` (>0), `password: str = ""`
   - `__post_init__` validates all constraints, raises `ValueError` with descriptive messages
   - `__repr__` must not expose `password` (mask it)

2. `@dataclass` class `AppConfig`:
   - `db: DatabaseConfig`, `debug: bool = False`
   - `allowed_hosts: tuple[str, ...] = ()` (each valid hostname or `"*"`)
   - `log_level: str = "INFO"` (must be in DEBUG/INFO/WARNING/ERROR/CRITICAL)

3. Class methods: `DatabaseConfig.from_dict(d)`, `AppConfig.from_env()`, `AppConfig.to_dict()`

Requirements: full type hints, `from __future__ import annotations`, `re` for hostname validation
