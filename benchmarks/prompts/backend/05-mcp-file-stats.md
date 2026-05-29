---
id: 05-mcp-file-stats
category: backend
models: my-mcp-q25c14,my-mcp-deepcoder,my-mcp-deepcoder-vanilla
timeout: 300
description: FastMCP tool server with file stats, async I/O, helper decomposition, and structured error returns
source: closing-the-gap benchmark
---

Write a FastMCP server in Python that exposes two tools:

**Tool 1: `file_stats`**
- Parameters: `path` (str) — absolute or relative path to a file
- Returns a JSON object with: `path`, `size_bytes`, `line_count`, `extension` (with leading dot, e.g. `".py"`; empty string `""` if no extension), `last_modified` (ISO 8601)
- If the path does not exist or is not a file, return `{"error": "<reason>"}` — do not raise

**Tool 2: `directory_summary`**
- Parameters: `path` (str) — path to a directory; `extension` (str, optional) — if provided (e.g. `".py"`), count only files with that extension
- Returns: `{"file_count": N, "total_bytes": N, "extensions": {"ext": count, ...}}` where:
  - `file_count` and `total_bytes` reflect only the filtered files when `extension` is provided
  - `extensions` always lists all extensions present in the directory (regardless of filter), with keys using leading dots and `""` for no-extension files
  - Must use `os.scandir` or `Path.iterdir` — never `os.walk` or `rglob`; non-recursive
- If the path does not exist or is not a directory, return `{"error": "<reason>"}` — do not raise

**Requirements:**
- Use FastMCP with stdio transport
- All tool handlers must be async
- Extract named helpers for: reading file metadata, building each result dict, and formatting error responses — no inline logic mixed with I/O in the same function
- No global mutable state
- Every tool and every parameter must have a description string
- Entry point: `if __name__ == "__main__": mcp.run()`

---

**Grading checklist:**
- [ ] Runs as a FastMCP stdio server (smoke-testable)
- [ ] `grep -n raise` finds no exceptions reaching the client
- [ ] ≥3 named helpers: read-metadata, build-result, format-error (or equivalent split)
- [ ] No module-level mutable state
- [ ] `directory_summary` uses `scandir`/`iterdir`, not `walk`/`rglob`
- [ ] `extension` filter correctly scopes `file_count`/`total_bytes` while `extensions` dict covers all files
