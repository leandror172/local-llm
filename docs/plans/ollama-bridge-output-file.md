# Plan: `output_file` Parameter for `ask_ollama` and `generate_code`

*Written 2026-05-21. Depends on: `ollama-bridge-refs-param.md` (implement first; this plan uses `refs_root` as a resolved-root concept).*

---

<!-- ref:mcp-output-file-goal -->
## Goal

Add `output_file: str | None = None` and `output_only: bool = False` to
`ask_ollama` and `generate_code`. When `output_file` is set, the response is
written to disk in addition to (or instead of) being returned to the caller.

This enables a natural edit loop:
1. `generate_code(prompt="...", output_file="retrieval/embed.py")` → file written + content returned
2. Claude reviews, identifies changes needed
3. `generate_code(prompt="add error handling", context_files=[{"path": "/abs/path/retrieval/embed.py"}])` → local model edits its own output
<!-- /ref:mcp-output-file-goal -->

---

<!-- ref:mcp-output-file-analysis -->
## `output_only` Analysis

Should the feature support a mode where the response is NOT returned to Claude
(only written to file)?

**Case for `output_only=True`:**
- Saves Claude tokens when the generated file is large (e.g., 500-line script)
- Claude doesn't need the content in context if it trusts the local model and
  will validate later via the file (e.g., run tests)
- Natural for large generation tasks where Claude's next action is "run the tests",
  not "review line by line"

**Case against / risks:**
- The verdict protocol in `local-model-conventions.md` requires evaluating every
  local model response. `output_only=True` breaks inline verdicts.
- Claude loses the ability to spot hallucinations, wrong imports, or bad API calls
  before the code runs — these are common failure modes for local 8B models.
- Encourages skipping the evaluation step, which degrades DPO training data quality.

**Decision:** Support `output_only: bool = False`, but only when `output_file` is set.
When active, return a compact status instead of full content:
`"Written 1234 bytes to /abs/path/to/file.py"`.

The overlay update must note that `output_only=True` defers verdict to after
file inspection. Claude must still give a verdict (use `context_files` to read
the file in the next call if needed).
<!-- /ref:mcp-output-file-analysis -->

---

<!-- ref:mcp-output-file-reading -->
## Required Reading

### Files

| File | Lines | Why |
|------|-------|-----|
| `mcp-server/src/ollama_mcp/server.py` | 51–87 | `_build_context_block` — I/O pattern reference; `_write_output_file` follows same error-string convention |
| `mcp-server/src/ollama_mcp/server.py` | 209–297 | `ask_ollama` — where to add `output_file` and `output_only` params |
| `mcp-server/src/ollama_mcp/server.py` | 480–556 | `generate_code` — same |
| `mcp-server/src/ollama_mcp/config.py` | all | `REPO_ROOT` — default anchor for relative path resolution |
| `mcp-server/run-server.sh` | all | Shows that `LLM_REPO_ROOT` is set to the repo root; CWD at spawn time is NOT reliable — always resolve relative paths from `REPO_ROOT` |
| `overlays/ollama-scaffolding/files/local-model-conventions.md` | 44–57 | The `context_files` section — new `output_file` section should be added adjacent to it |

### Refs

| Key | Why |
|-----|-----|
| `indexing-convention` | Not directly needed here, but referenced by Plan 1 which must be implemented first |
| `local-model-conventions` | Full text of the conventions file that will be updated — understand its current structure before editing |
| `patterns-script-conventions` | Bash wrapper conventions — confirm no new wrappers are needed for this feature (they aren't; pure Python change) |
<!-- /ref:mcp-output-file-reading -->

---

<!-- ref:mcp-output-file-decisions -->
## Decisions

| Decision | Value | Rationale |
|----------|-------|-----------|
| Relative path anchor | `REPO_ROOT` if set; otherwise error | CWD at MCP server spawn time is unreliable (depends on shell context); `REPO_ROOT` is explicitly set by `run-server.sh` |
| If `REPO_ROOT` unset and path relative | Return error, don't write | Fail loudly; writing to wrong location is worse than failing |
| `output_only` default | `False` | Preserves existing behaviour; opt-in only |
| `output_only` without `output_file` | Silently ignored (or warn) | No file = can't redirect; return content as usual |
| Return value when `output_only=True` | `"Written N bytes to /abs/path"` | Compact; gives Claude the resolved absolute path for subsequent `context_files` use |
| Return value when `output_file` set + `output_only=False` | Full content returned AND file written | Both; caller decides whether to read the content |
| File write mode | Overwrite (`w`); create parent dirs if needed | Generation tasks always produce fresh content |
| Encoding | UTF-8 | Consistent with `_build_context_block` and all other file I/O in the server |
<!-- /ref:mcp-output-file-decisions -->

---

<!-- ref:mcp-output-file-tests -->
## Tests

**TDD order:** write test file → run → confirm all red → implement → run → confirm all green.
Requires `conftest.py` and pyproject.toml additions from Plan 1.

### `mcp-server/tests/test_output_file.py`

**Context to send to `generate_code`:**
```
context_files:
  - path: mcp-server/src/ollama_mcp/server.py
    start_line: 209
    end_line: 297           # ask_ollama — the function under test
  - path: mcp-server/src/ollama_mcp/server.py
    start_line: 480
    end_line: 556           # generate_code — also under test; same output_file logic
```

**Prompt:**
> Write pytest tests for `output_file` and `output_only` parameters added to
> `ask_ollama` in `ollama_mcp.server`. Use the `mock_ollama` fixture from conftest.py
> (mock client returns content="mocked-model-output"). Monkeypatch
> `ollama_mcp.server.REPO_ROOT` where needed. Write exactly these test cases:
>
> 1. `test_file_is_written_when_output_file_set`: call `ask_ollama` with an absolute
>    `output_file` path in tmp_path. Assert the file exists after the call.
>
> 2. `test_returned_content_equals_file_content`: same call; assert
>    `result == file.read_text(encoding="utf-8")` — both paths carry identical content.
>
> 3. `test_output_only_returns_status_not_content`: call with `output_only=True`.
>    Assert "Written" in result. Assert "mocked-model-output" NOT in result.
>    Assert file exists and file content IS "mocked-model-output".
>
> 4. `test_output_only_status_contains_byte_count_and_path`: call with `output_only=True`,
>    absolute output_file. Assert the return string contains the absolute path string
>    and a digit (byte count). Do not check exact format — just that both are present.
>
> 5. `test_output_only_without_output_file_returns_full_content`: call with
>    `output_only=True` but NO `output_file`. Assert result == "mocked-model-output"
>    (flag is silently ignored when there is no file to write to).
>
> 6. `test_relative_path_resolved_from_repo_root`: monkeypatch REPO_ROOT to str(tmp_path).
>    Call with `output_file="subdir/out.py"` (relative). Assert
>    `(tmp_path / "subdir" / "out.py").exists()`.
>
> 7. `test_parent_directories_created_automatically`: call with a deeply nested absolute
>    path that does not exist yet (e.g., tmp_path / "a" / "b" / "c" / "out.py").
>    Assert the file exists after the call.
>
> 8. `test_relative_path_without_repo_root_returns_error`: monkeypatch REPO_ROOT to None.
>    Call with `output_file="relative/path.py"`. Assert result starts with "Error:".
>    Do NOT assert the file does not exist — just that the return is an error string.
<!-- /ref:mcp-output-file-tests -->

---

<!-- ref:mcp-output-file-impl -->
## Implementation

### Step 1 — Add `_write_output_file` helper (~25 lines)

**Location:** `mcp-server/src/ollama_mcp/server.py`, after `_build_refs_block`
(or after `_build_context_block` if Plan 1 not yet implemented).

**What it does:**
1. If `output_file` is an absolute path: use as-is.
2. If relative: prepend `REPO_ROOT`. If `REPO_ROOT` is `None`: return error string.
3. Create parent directories if they don't exist (`pathlib.Path.mkdir(parents=True, exist_ok=True)`).
4. Write `content` (str) to file, UTF-8, overwriting.
5. On success: return `f"Written {len(content.encode())} bytes to {resolved_path}"`.
6. On `OSError`: return `f"Error writing to {resolved_path}: {e}"`.
7. Never raise — return error strings, same as all other helpers.

**Context to send to `generate_code`:**
```
context_files:
  - path: mcp-server/src/ollama_mcp/server.py
    start_line: 51
    end_line: 87            # _build_context_block — error-string convention to follow
  - path: mcp-server/src/ollama_mcp/config.py
                            # for REPO_ROOT import
```

**Prompt:**
> Write an async helper `_write_output_file(path: str, content: str) -> str`
> for a Python FastMCP server. It resolves the path: if absolute, use as-is;
> if relative, prepend REPO_ROOT (from config). If REPO_ROOT is None and path
> is relative, return an error string. Create parent directories with
> `pathlib.Path.mkdir(parents=True, exist_ok=True)`. Write content as UTF-8.
> On success return `"Written N bytes to /abs/path"` (N = byte length).
> On OSError return `"Error writing to /abs/path: <e>"`. Never raise.
> Follow the error-string convention of `_build_context_block` in this file.

---

### Step 2 — Modify `ask_ollama` signature and body

**Location:** `mcp-server/src/ollama_mcp/server.py`, lines 209–297.

Add to signature (after `context_files`, before `timeout`):
```python
output_file: str | None = None,
output_only: bool = False,
```

Add to docstring (after `context_files` arg description):
```
output_file: Path to write the response to (relative or absolute).
             Relative paths are resolved from REPO_ROOT. Parent directories
             are created automatically. Content is always returned to the
             caller as well, unless output_only=True.
output_only: If True and output_file is set, write to file and return only
             a compact status string ("Written N bytes to /path") instead
             of the full response. Defers verdict assessment to after file
             inspection — you must still give a verdict after reading the file.
             Ignored if output_file is not set.
```

Add body (after `return response.content`, insert before returning):
```python
    content = response.content
    if output_file:
        write_result = await _write_output_file(output_file, content)
        if write_result.startswith("Error:"):
            return write_result
        if output_only:
            return write_result  # compact status, not full content
    return content
```

**Context to send to `generate_code`:**
```
context_files:
  - path: mcp-server/src/ollama_mcp/server.py
    start_line: 209
    end_line: 297           # full ask_ollama tool
```

**Prompt:**
> Add `output_file: str | None = None` and `output_only: bool = False` parameters
> to the `ask_ollama` async tool function shown in context. After getting
> `response.content`, if `output_file` is set, call `await _write_output_file(output_file, content)`.
> If the result starts with "Error:", return it. If `output_only` is True, return
> the write status instead of content. Otherwise return content as usual.
> Add docstring entries for both params in the existing style.

---

### Step 3 — Modify `generate_code` signature and body

Same as Step 2 but for `generate_code` (lines 480–556).

**Context to send to `generate_code`:**
```
context_files:
  - path: mcp-server/src/ollama_mcp/server.py
    start_line: 480
    end_line: 556           # full generate_code tool
```

**Prompt:** Same pattern as Step 2, adapted for `generate_code`.

---

### Step 4 — Update `mcp-server/.memories/QUICK.md`

Add to the Key Patterns section:

```
- **Output to file** — `output_file: str | None` on ask_ollama and generate_code;
  writes response to disk (relative paths from REPO_ROOT); `output_only=True`
  returns compact status instead of content (defers verdict to file inspection)
```

---

### Step 5 — Update overlay: `overlays/ollama-scaffolding/files/local-model-conventions.md`

Add a new subsection after the `context_files` section (around line 57):

```markdown
### Output to file: generate directly into the codebase

Use `output_file="rel/path/to/file.py"` to write the model's response directly
to a file. Relative paths resolve from the project root (`REPO_ROOT`); absolute
paths are used as-is. The response is returned to you AND written to the file.

**Edit loop pattern:**
1. `generate_code(prompt="...", output_file="src/foo.py")` — generates + writes
2. Review the returned content, give a verdict
3. For edits: `generate_code(prompt="fix X", context_files=[{"path": "/abs/src/foo.py"}])` —
   local model edits its own prior output

**`output_only=True`:** Returns only a compact status (`"Written N bytes to /path"`)
instead of the full content. Use when the generated file is large and you plan to
validate via tests rather than inline review. You MUST still give a verdict —
read the file afterwards with `context_files` if needed to assess quality.

Do NOT use `output_only=True` as a way to skip verdicts. The verdict (0/1/2) is
required regardless of how you inspect the output.
```
<!-- /ref:mcp-output-file-impl -->

---

<!-- ref:mcp-output-file-acceptance -->
## Acceptance Test

After implementation, verify manually:

```python
# 1. Basic write — file should exist and content should be returned
generate_code(
    prompt="Write a Python function that returns 42.",
    language="python",
    output_file="/tmp/test_output.py",
)
# Expected: code returned AND /tmp/test_output.py exists with the code

# 2. Relative path — resolved from REPO_ROOT
generate_code(
    prompt="Write a hello world Python script.",
    language="python",
    output_file="retrieval/test_output.py",  # should appear in /mnt/i/workspaces/llm/retrieval/
)

# 3. output_only=True — compact status returned, file written
ask_ollama(
    prompt="Write a one-line comment explaining binary search.",
    output_file="/tmp/comment.txt",
    output_only=True,
)
# Expected: "Written N bytes to /tmp/comment.txt" returned; file contains the comment

# 4. Edit loop — pass the written file as context_files
generate_code(
    prompt="Add a type annotation to the function.",
    language="python",
    context_files=[{"path": "/tmp/test_output.py"}],  # the file from test 1
)

# 5. Bad path (no REPO_ROOT, relative path) — should return error, not crash
# (Only testable if LLM_REPO_ROOT is unset — skip in normal dev env)

# 6. Combined with refs (Plan 1 feature)
generate_code(
    prompt="Write a bge-m3 embedding call using the correct API.",
    language="python",
    refs=["ltg-embedding"],
    output_file="/tmp/embed_test.py",
)
```
<!-- /ref:mcp-output-file-acceptance -->

---

## No changes needed

- `run-server.sh`: no changes; `LLM_REPO_ROOT` already exported.
- `config.py`: `REPO_ROOT` already exported.
- Bash wrappers: not applicable (pure Python server change).
- `overlays/ollama-scaffolding/manifest.yaml`: no changes needed; `files:` entry
  already propagates `local-model-conventions.md` on re-install.
