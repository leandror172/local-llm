---
id: python-01-fastapi-crud
domain: python
difficulty: easy
timeout: 300
description: FastAPI CRUD with Pydantic models and dependency injection
---

Write a FastAPI application for managing a `Note` resource.

Requirements:

1. Pydantic models:
   - `NoteCreate(title: str, content: str)` — title not empty, max 200 chars
   - `NoteUpdate(title: str | None, content: str | None)` — all optional
   - `NoteResponse(id: int, title: str, content: str, created_at: datetime, updated_at: datetime)`

2. `NoteRepository` with in-memory dict store: `create`, `get`, `list_all`, `update`, `delete`

3. Endpoints: `POST /notes` (201), `GET /notes`, `GET /notes/{id}`, `PATCH /notes/{id}`, `DELETE /notes/{id}`

4. Dependency injection: `get_repository()` → singleton `NoteRepository` via `Depends`

Requirements:
- All type hints, `from __future__ import annotations`, `HTTPException` for 404
- Use `lifespan` context manager (not deprecated `@app.on_event`)
