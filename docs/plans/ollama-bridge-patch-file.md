# Plan: `patch_file` Tool for Pinpoint Server-Side File Edits

*Written 2026-05-21. Complements `ollama-bridge-output-file.md` — implement that first so `_write_output_file`'s path-resolution pattern is already established.*

---

<!-- ref:mcp-patch-file-goal -->
## Goal

Add a `patch_file` MCP tool that edits a file server-side via exact string
replacement. Claude supplies `old_string` and `new_string`; the server reads
the file, replaces, and writes back. Claude never pays the token cost of
reading the file into context.

This closes the write loop opened by `output_file`:

```
generate_code(output_file="src/foo.py")        → file written, content returned to Claude
patch_file("src/foo.py", old, new)             → pinpoint edit, zero Claude read cost
generate_code(context_files=[{"path": "..."}]) → local model sees the edited file
```
<!-- /ref:mcp-patch-file-goal -->

---

<!-- ref:mcp-patch-file-semantics -->
## Semantics (mirrors the Edit tool)

| Behaviour | Value |
|-----------|-------|
| Match type | Exact string (no regex, no glob) |
| Default occurrence | First only (`replace_all=False`) |
| `old_string` not found | Error — do not write |
| `old_string` appears >1 time and `replace_all=False` | Error — require uniqueness or set `replace_all=True` |
| `replace_all=True` | Replace all occurrences (rename/refactor use case) |
| Encoding | UTF-8 (consistent with all other file I/O in server) |
| Path resolution | Same as `output_file`: absolute as-is; relative from `REPO_ROOT`; error if relative and `REPO_ROOT` unset |

The uniqueness constraint mirrors the Edit tool exactly. It catches the common
mistake of replacing the wrong occurrence when `old_string` is non-unique.
<!-- /ref:mcp-patch-file-semantics -->

---

<!-- ref:mcp-patch-file-reading -->
## Required Reading

### Files

| File | Lines | Why |
|------|-------|-----|
| `mcp-server/src/ollama_mcp/server.py` | 51–87 | `_build_context_block` — error-string convention; new tool follows same pattern |
| `mcp-server/src/ollama_mcp/server.py` | 480–556 | `generate_code` — tool structure to mirror for `patch_file` |
| `mcp-server/src/ollama_mcp/config.py` | all | `REPO_ROOT` — path resolution anchor |
| `docs/plans/ollama-bridge-output-file.md` | Step 1 | `_write_output_file` path-resolution logic — `patch_file` reuses the same pattern |
| `overlays/ollama-scaffolding/files/local-model-conventions.md` | 44–70 | Context files + output_file sections — `patch_file` usage goes adjacent |

### Refs

| Key | Why |
|-----|-----|
| `mcp-output-file-decisions` | Path-resolution decisions from Plan 2 — `patch_file` inherits them verbatim |
| `patterns-mcp-development` | MCP tool structure conventions (FastMCP decorator, error-string returns, no raises) |
| `local-model-conventions` | Full overlay file — understand structure before adding `patch_file` section |
<!-- /ref:mcp-patch-file-reading -->

---

<!-- ref:mcp-patch-file-decisions -->
## Decisions

| Decision | Value | Rationale |
|----------|-------|-----------|
| Tool name | `patch_file` | Clear, distinct from `write_output`; matches shell/git vocabulary |
| `replace_all` param | `bool = False` | Mirrors Edit tool; enables rename/refactor without a separate tool |
| Uniqueness check | Error if count > 1 and `replace_all=False` | Prevents silent wrong-site replacement; same rule makes Edit tool safe |
| Path resolution | Same helper logic as `_write_output_file` | Consistency; don't invent a second resolution strategy |
| Extract shared helper? | No — inline 4-line resolution in `patch_file` | 4 lines don't justify a shared helper; avoid premature abstraction |
| Return on success | `"Patched /abs/path (1 replacement)"` or `"Patched /abs/path (N replacements)"` | Gives Claude the resolved path + count for confirmation |
| New file creation | Error — do not create | `patch_file` edits existing files; use `output_file` to create |
<!-- /ref:mcp-patch-file-decisions -->

---

<!-- ref:mcp-patch-file-tests -->
## Tests

**TDD order:** write test file → run → confirm all red → implement → run → confirm all green.
Requires `conftest.py` and pyproject.toml additions from Plan 1.
No Ollama mock needed — `patch_file` is pure file I/O.

### `mcp-server/tests/test_patch_file.py`

**Context to send to `generate_code`:**
```
context_files:
  - path: docs/plans/ollama-bridge-patch-file.md
    start_line: 24          # Semantics table — the exact contract the tests verify
    end_line: 40
```
(No implementation exists yet — write tests from the spec, not from code.)

**Prompt:**
> Write pytest tests for a new async MCP tool `patch_file(path, old_string, new_string,
> replace_all=False)` in `ollama_mcp.server` (not yet implemented). Import it directly:
> `from ollama_mcp.server import patch_file`. Monkeypatch
> `ollama_mcp.server.REPO_ROOT` to str(tmp_path) in every test. Write exactly
> these test cases — no others:
>
> 1. `test_basic_replacement_changes_file_content`: write a file with unique content
>    "def foo():\n    return 1\n". Call patch_file with old_string="return 1",
>    new_string="return 42". Assert file content is now "def foo():\n    return 42\n".
>
> 2. `test_basic_replacement_return_includes_count`: same call; assert "1 replacement"
>    in result (case-insensitive OK).
>
> 3. `test_old_string_not_found_returns_error`: call with old_string that is absent.
>    Assert result starts with "Error:". Assert file content is UNCHANGED
>    (capture content before call, compare after).
>
> 4. `test_non_unique_old_string_returns_error_with_count`: write a file where
>    "return 1" appears exactly twice. Call patch_file with old_string="return 1"
>    and replace_all=False. Assert result starts with "Error:". Assert "2" appears
>    in result. Assert file content is UNCHANGED.
>
> 5. `test_replace_all_replaces_every_occurrence`: same file with "return 1" twice.
>    Call with replace_all=True. Assert "2 replacement" in result (or "2 replacements").
>    Assert "return 1" NOT in file content. Assert "return 99" appears exactly twice.
>
> 6. `test_multiline_old_string`: write a file with "    x = 1\n    return x\n".
>    Call with old_string="    x = 1\n    return x", new_string="    return 42".
>    Assert "x = 1" NOT in file content. Assert "return 42" in file content.
>    This test guards against a single-line-only implementation.
>
> 7. `test_file_not_found_returns_error_not_exception`: call with a path that does
>    not exist. Assert result starts with "Error:". Must not raise any exception.
>
> 8. `test_relative_path_resolved_from_repo_root`: write a file at tmp_path/"r.py"
>    with content "x = 1\n". Call with path="r.py" (relative). Assert "1 replacement"
>    in result. Assert file content is "x = 2\n" (new_string="x = 2").
<!-- /ref:mcp-patch-file-tests -->

---

<!-- ref:mcp-patch-file-impl -->
## Implementation

### Step 1 — Add `patch_file` tool (~50 lines)

**Location:** `mcp-server/src/ollama_mcp/server.py`, after `ref_lookup` tool
(end of file, around line 1118).

**What it does:**
1. Resolve path (same logic as `_write_output_file`): absolute as-is; relative prepend `REPO_ROOT`; error if can't resolve.
2. Check file exists — error if not (don't create).
3. Read content as UTF-8.
4. Count occurrences of `old_string`.
5. If count == 0: return `"Error: old_string not found in {path}"`.
6. If count > 1 and `replace_all=False`: return `"Error: old_string found {count} times in {path}. Use replace_all=True to replace all, or provide a more specific old_string."`.
7. Replace: `content.replace(old_string, new_string)` (all) or `content.replace(old_string, new_string, 1)` (first).
8. Write back UTF-8.
9. Return `"Patched {abs_path} ({n} replacement{'s' if n != 1 else ''})"`.
10. Wrap all I/O in try/except OSError → error string.

**Context to send to `generate_code`:**
```
context_files:
  - path: mcp-server/src/ollama_mcp/server.py
    start_line: 480
    end_line: 556            # generate_code tool — @mcp.tool() structure to mirror
  - path: mcp-server/src/ollama_mcp/server.py
    start_line: 51
    end_line: 87             # _build_context_block — error-string + pathlib pattern
  - path: mcp-server/src/ollama_mcp/config.py  # for REPO_ROOT
```

**Prompt:**
> Write a new `@mcp.tool()` async function `patch_file` for a Python FastMCP
> server. Parameters: `path: str`, `old_string: str`, `new_string: str`,
> `replace_all: bool = False`. Path resolution: if absolute use as-is; if
> relative prepend REPO_ROOT (from config); if REPO_ROOT is None and path is
> relative return an error string. Check file exists (error if not). Read as
> UTF-8. Count occurrences of old_string: if 0 return error; if >1 and
> replace_all=False return error listing count. Replace using str.replace with
> count=1 or no limit depending on replace_all. Write back UTF-8. Return
> "Patched {abs_path} (N replacement/s)" on success. Catch OSError → error
> string. Never raise. Follow the @mcp.tool() decorator pattern and
> error-string convention from the tools already in this file.

---

### Step 2 — Update `mcp-server/.memories/QUICK.md`

Add `patch_file` to the Tool Catalog line and Key Patterns:

```
Tool Catalog: ... patch_file

- **patch_file** — server-side exact string replace on a file; same semantics
  as Edit tool (uniqueness check, replace_all flag); zero Claude read cost
```

---

### Step 3 — Update overlay: `overlays/ollama-scaffolding/files/local-model-conventions.md`

Add a subsection after the `output_file` section (Plan 2 Step 5):

```markdown
### patch_file: pinpoint edits without reading

Use `patch_file(path, old_string, new_string)` to edit a file the local model
wrote — without reading it back into Claude's context. Same semantics as the
Edit tool: exact match, first occurrence only, error if not found or non-unique.

```python
# Generate a file
generate_code(prompt="...", output_file="src/foo.py")

# Fix one thing without re-reading the whole file
patch_file("src/foo.py", old_string="def foo():", new_string="def foo(x: int):")

# Use replace_all=True for renames across the file
patch_file("src/foo.py", old_string="old_name", new_string="new_name", replace_all=True)
```

**When to use vs. Edit tool:**
- `patch_file`: file was just generated; you already know what's in it; no prior Read in conversation
- Edit tool: file already existed in the codebase; you read it during orientation

Do not use `patch_file` as a way to avoid reading files you should understand
before editing. It's for the specific case of editing freshly generated output.
```
<!-- /ref:mcp-patch-file-impl -->

---

<!-- ref:mcp-patch-file-acceptance -->
## Acceptance Test

After implementation, verify manually:

```python
# 1. Basic replacement
generate_code(prompt="Write a function foo() that returns 1.", language="python", output_file="/tmp/p.py")
patch_file("/tmp/p.py", old_string="return 1", new_string="return 42")
# Expected: "Patched /tmp/p.py (1 replacement)" — verify file content changed

# 2. Not found → error
patch_file("/tmp/p.py", old_string="this_does_not_exist", new_string="x")
# Expected: "Error: old_string not found in /tmp/p.py"

# 3. Non-unique → error
# (First write a file with a repeated string, then try to patch it)
patch_file("/tmp/p.py", old_string="42", new_string="99")
# If "42" appears multiple times: "Error: old_string found N times..."

# 4. replace_all=True — renames all occurrences
patch_file("/tmp/p.py", old_string="42", new_string="99", replace_all=True)
# Expected: all occurrences replaced, count in return message

# 5. Relative path
generate_code(prompt="Write hello world.", language="python", output_file="retrieval/test_patch.py")
patch_file("retrieval/test_patch.py", old_string="print", new_string="sys.stdout.write")
# Expected: resolved to /mnt/i/workspaces/llm/retrieval/test_patch.py

# 6. File does not exist → error
patch_file("/tmp/nonexistent_xyz.py", old_string="x", new_string="y")
# Expected: "Error: ..." — not a crash
```
<!-- /ref:mcp-patch-file-acceptance -->

---

## No changes needed

- `config.py`: `REPO_ROOT` already exported.
- `run-server.sh`: no changes.
- Bash wrappers: not applicable.
- `overlays/ollama-scaffolding/manifest.yaml`: no changes; `files:` entry
  already propagates `local-model-conventions.md` on re-install.
