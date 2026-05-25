# Plan: `refs` Parameter for `ask_ollama` and `generate_code`

*Written 2026-05-21. Ready to execute.*

---

<!-- ref:mcp-refs-param-goal -->
## Goal

Add `refs: list[str] | None = None` and `refs_root: str | None = None` to
`ask_ollama` and `generate_code`. When provided, the server resolves each ref
key by running `ref-lookup.sh` and prepends the resolved content as a
`<refs>…</refs>` block to the Ollama prompt — at zero Claude token cost.

Any folder that contains markdown files with `<!-- ref:KEY -->` markers can be
used as a `refs_root`. This is not limited to the LLM repo.
<!-- /ref:mcp-refs-param-goal -->

---

<!-- ref:mcp-refs-param-reading -->
## Required Reading

Read in order. Each answers a specific question during implementation.

### Files

| File | Lines | Why |
|------|-------|-----|
| `mcp-server/src/ollama_mcp/server.py` | 51–87 | `_build_context_block` — the exact pattern to follow for the new `_build_refs_block` helper |
| `mcp-server/src/ollama_mcp/server.py` | 1060–1117 | `ref_lookup` tool — contains the subprocess logic to extract into `_resolve_ref_key` |
| `mcp-server/src/ollama_mcp/server.py` | 209–297 | `ask_ollama` — where to add the two new parameters |
| `mcp-server/src/ollama_mcp/server.py` | 480–556 | `generate_code` — where to add the two new parameters |
| `.claude/tools/ref-lookup.sh` | all | CLI interface: `ref-lookup.sh KEY [--root DIR]`, exit codes, output format |
| `mcp-server/src/ollama_mcp/config.py` | all | `REPO_ROOT` — the default `refs_root` fallback |
| `overlays/ollama-scaffolding/files/local-model-conventions.md` | all | The overlay file that documents context conventions — needs a new section |

### Refs

| Key | Why |
|-----|-----|
| `indexing-convention` | Explains the `<!-- ref:KEY -->` two-tier marker system this feature is built on; essential for understanding what `refs_root` means and what makes a valid folder |
| `patterns-mcp-development` | MCP server architecture conventions (transport, tool structure) — context for where the new helpers fit in the server |
<!-- /ref:mcp-refs-param-reading -->

---

<!-- ref:mcp-refs-param-decisions -->
## Decisions

| Decision | Value | Rationale |
|----------|-------|-----------|
| Resolution location | Server-side (subprocess) | Same as `context_files`; ref content never passes through Claude's context |
| Missing key behaviour | Fail-fast: return error string | Same as `context_files` path errors; typos must surface immediately |
| Prompt ordering | `<refs>` → `<context>` → `[Language: hint]` → prompt | Docs/rules first, code files second, task last |
| Parallelism | `asyncio.gather` for multiple keys | Independent subprocesses; gain is real for 3+ refs, harmless for 1 |
| `refs_root` default | `REPO_ROOT` from `config.py` | Sensible default for LLM repo sessions; any folder accepted |
| `refs_root` = `None` + `REPO_ROOT` = `None` | Return error | Can't resolve without a search root; mirror `ref_lookup` tool behaviour |
<!-- /ref:mcp-refs-param-decisions -->

---

<!-- ref:mcp-refs-param-setup -->
## Setup (first plan only — shared across all three)

### pyproject.toml additions

Add dev dependency group and pytest async config:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"    # all async def test_* run automatically; no @pytest.mark.asyncio needed
testpaths = ["tests"]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
]
```

**Context to send to `generate_code`:** none needed — this is a mechanical addition.
Add manually to `mcp-server/pyproject.toml` before writing any tests.

---

### `mcp-server/tests/conftest.py` — shared fixtures

**Write before any test file. Context to send to `generate_code`:**
```
context_files:
  - path: mcp-server/src/ollama_mcp/server.py
    start_line: 109
    end_line: 122           # _client global + _get_client() — what to monkeypatch
  - path: mcp-server/src/ollama_mcp/client.py
                            # OllamaClient — what the mock replaces
```

**Prompt:**
> Write a pytest conftest.py for testing a FastMCP server (ollama_mcp).
> Three fixtures:
> (1) `repo_root() -> pathlib.Path` — returns the LLM repo root by resolving
>     `pathlib.Path(__file__).parent.parent.parent` (tests/ → mcp-server/ → llm/).
> (2) `ref_dir(tmp_path) -> pathlib.Path` — writes a single markdown file into
>     tmp_path containing two ref blocks: `<!-- ref:test-key -->ref content
>     here<!-- /ref:test-key -->` and `<!-- ref:other-key -->other
>     content<!-- /ref:other-key -->`. Returns tmp_path.
> (3) `mock_ollama(monkeypatch)` — creates an AsyncMock for OllamaClient with
>     `client.chat` returning a MagicMock whose `.content` is
>     `"mocked-model-output"`. Monkeypatches `ollama_mcp.server._client` with
>     this mock. Returns the mock client so tests can assert on call_args.
> Use `from unittest.mock import AsyncMock, MagicMock` and `import pathlib`.
<!-- /ref:mcp-refs-param-setup -->

---

<!-- ref:mcp-refs-param-tests -->
## Tests

**TDD order:** write `conftest.py` → write test file → run (`uv run --project mcp-server pytest`) → confirm all red → implement → run again → confirm all green.

### `mcp-server/tests/test_refs.py`

**Context to send to `generate_code`:**
```
context_files:
  - path: mcp-server/src/ollama_mcp/server.py
    start_line: 51
    end_line: 87            # _build_context_block — the pattern _build_refs_block will mirror
  - path: mcp-server/src/ollama_mcp/server.py
    start_line: 1060
    end_line: 1117          # ref_lookup tool — the subprocess logic _resolve_ref_key will extract
```

**Prompt:**
> Write pytest tests for two new private async functions `_resolve_ref_key(key, root)`
> and `_build_refs_block(refs, root)` in `ollama_mcp.server`, plus integration tests
> for the `refs` and `refs_root` parameters added to `ask_ollama`.
> Import the functions directly from `ollama_mcp.server` (private functions are
> importable for unit tests). Use the `repo_root`, `ref_dir`, and `mock_ollama`
> fixtures from conftest.py. Monkeypatch `ollama_mcp.server.REPO_ROOT` to
> `str(repo_root)` in every test (the server uses this to find ref-lookup.sh).
> Write exactly these test cases — no others:
>
> 1. `test_resolve_ref_key_returns_block_content`: call with "test-key" and ref_dir
>    as root; assert "ref content here" is in result and result does not start with "Error:".
>
> 2. `test_resolve_ref_key_missing_key_returns_error`: call with "nonexistent-key-xyz";
>    assert result starts with "Error:" or "not found" is in result (case-insensitive).
>    Must not raise.
>
> 3. `test_resolve_ref_key_root_is_respected`: call with key "test-key" but pass an
>    EMPTY tmp_path as root (not ref_dir). Assert result starts with "Error:" — proves
>    the root param is actually forwarded to ref-lookup.sh and not ignored.
>
> 4. `test_build_refs_block_wraps_in_refs_tags`: call with ["test-key"] and ref_dir;
>    assert result starts with "<refs>" and ends with "</refs>" (strip whitespace).
>
> 5. `test_build_refs_block_labels_each_key`: call with ["test-key"]; assert
>    "### ref:test-key" appears in result.
>
> 6. `test_build_refs_block_all_keys_present`: call with ["test-key", "other-key"];
>    assert both "ref content here" and "other content" are in result.
>
> 7. `test_build_refs_block_fails_fast_on_missing_key`: call with ["test-key",
>    "missing-xyz"]; assert result starts with "Error:" AND "ref content here"
>    is NOT in result (partial block must not be returned).
>
> 8. `test_refs_appear_before_user_prompt_in_ollama_call`: call `ask_ollama` with
>    prompt="MY_SENTINEL_PROMPT", refs=["test-key"], refs_root=str(ref_dir).
>    Get `prompt_sent` from `mock_ollama.chat.call_args.kwargs["prompt"]`.
>    Assert `prompt_sent.index("<refs>") < prompt_sent.index("MY_SENTINEL_PROMPT")`.
>
> 9. `test_refs_appear_before_context_when_both_provided`: call `ask_ollama` with
>    prompt="sentinel", refs=["test-key"], refs_root=str(ref_dir), and a
>    context_files=[ContextFile(path=str(some_existing_file))]. Assert
>    `prompt_sent.index("<refs>") < prompt_sent.index("<context>")`.
<!-- /ref:mcp-refs-param-tests -->

---

<!-- ref:mcp-refs-param-impl -->
## Implementation

### Step 1 — Add `_resolve_ref_key` helper (new function, ~20 lines)

**Location:** `mcp-server/src/ollama_mcp/server.py`, after `_build_context_block`
(around line 89, before the language-routing block).

**What it does:** Run `ref-lookup.sh KEY [--root DIR]` as a subprocess.
Return the stdout content on exit code 0, or an `Error: …` string on failure.
Timeout: 10 seconds (same as `ref_lookup` tool).

**Context to send to `generate_code`:**
```
context_files:
  - path: mcp-server/src/ollama_mcp/server.py
    start_line: 1060
    end_line: 1117          # ref_lookup tool — extract this subprocess pattern
  - path: mcp-server/src/ollama_mcp/config.py   # for REPO_ROOT
```

**Prompt:**
> Write an async helper `_resolve_ref_key(key: str, root: str | None) -> str`
> for a Python FastMCP server. It runs the shell script at
> `{REPO_ROOT}/.claude/tools/ref-lookup.sh` as a subprocess using
> `asyncio.create_subprocess_exec`. Arguments: `[script, key]` plus
> `["--root", root]` if root is not None. 10-second timeout. On success
> return stdout decoded. On non-zero exit or timeout return an `Error: …`
> string (never raise). Follow the same pattern as the `ref_lookup` tool
> already in this file.
> REPO_ROOT comes from `from ollama_mcp.config import REPO_ROOT`.

---

### Step 2 — Add `_build_refs_block` helper (new function, ~20 lines)

**Location:** Immediately after `_resolve_ref_key`.

**What it does:** Accept `refs: list[str]` and `root: str | None`. Resolve
`root` fallback: if `None`, use `REPO_ROOT`. If still `None`, return an error
string. Use `asyncio.gather` to resolve all keys in parallel. If any key
returns an `Error:` string, return that error immediately (fail-fast). Format
resolved content as:

```
<refs>
### ref:KEY1
{content1}

### ref:KEY2
{content2}
</refs>
```

**Context to send to `generate_code`:**
```
context_files:
  - path: mcp-server/src/ollama_mcp/server.py
    start_line: 51
    end_line: 87            # _build_context_block — exact formatting pattern to mirror
```

**Prompt:**
> Write an async helper `_build_refs_block(refs: list[str], root: str | None) -> str`
> that resolves each key by calling `_resolve_ref_key(key, root)` (already defined
> above it in this file). Use `asyncio.gather` for parallel resolution. If any
> result starts with "Error:", return that error string immediately. Format each
> resolved block with a `### ref:KEY` label, then join all blocks inside
> `<refs>…</refs>` tags. Follow the exact formatting style of `_build_context_block`
> above it.

---

### Step 3 — Modify `ask_ollama` signature and body

**Location:** `mcp-server/src/ollama_mcp/server.py`, lines 209–297.

Add to signature (after `context_files`, before `timeout`):
```python
refs: list[str] | None = None,
refs_root: str | None = None,
```

Add to docstring (after the `context_files` arg description):
```
refs: Reference keys to resolve and inject as documentation context.
      Each key must match a <!-- ref:KEY --> marker in a *.md file under
      refs_root. Resolved content is prepended as a <refs> block before
      the prompt — no Claude token cost. Use ref_lookup(key="list") to
      see available keys in a folder.
refs_root: Folder to search for ref markers (any folder with *.md files
           using <!-- ref:KEY --> convention). Defaults to REPO_ROOT.
           Pass the root of any project folder to look up its own refs.
```

Add body (after persona validation, before `full_prompt = prompt`):
```python
full_prompt = prompt
if refs:
    refs_block = await _build_refs_block(refs, refs_root)
    if refs_block.startswith("Error:"):
        return refs_block
    full_prompt = f"{refs_block}\n\n{full_prompt}"
if context_files:
    ...  # existing context_files block, unchanged
```

**Context to send to `generate_code`:**
```
context_files:
  - path: mcp-server/src/ollama_mcp/server.py
    start_line: 209
    end_line: 297           # full ask_ollama tool
```

**Prompt:**
> Add `refs: list[str] | None = None` and `refs_root: str | None = None`
> parameters to the `ask_ollama` async tool function shown in context.
> After the persona validation block and before building `full_prompt`,
> call `await _build_refs_block(refs, refs_root)` if refs is not None.
> If the result starts with "Error:", return it. Otherwise prepend it to
> `full_prompt` before the `context_files` block. Add docstring entries
> for both params following the existing style.

---

### Step 4 — Modify `generate_code` signature and body

Same as Step 3 but for `generate_code` (lines 480–556).

Ordering in `generate_code` after language hint prepend:
```
refs block → context_files block → [Language: hint] → prompt
```

(Language hint is prepended first, then context wraps around it, then refs.)

**Context to send to `generate_code`:**
```
context_files:
  - path: mcp-server/src/ollama_mcp/server.py
    start_line: 480
    end_line: 556           # full generate_code tool
```

**Prompt:** Same pattern as Step 3, adapted for `generate_code`.

---

### Step 5 — Update `mcp-server/.memories/QUICK.md`

Add `refs` and `refs_root` to the Key Patterns section:

```
- **Ref context injection** — `refs: list[str]` + `refs_root: str | None` on
  ask_ollama and generate_code; server resolves ref keys via ref-lookup.sh,
  prepends as <refs> block (zero Claude token cost; any folder accepted)
```

---

### Step 6 — Update overlay: `overlays/ollama-scaffolding/files/local-model-conventions.md`

Add a new subsection under "Context files: pass what defines the behavior"
(around line 46 in the current file):

```markdown
### Refs context: inject project documentation

Use `refs: ["key1", "key2"]` on `generate_code` or `ask_ollama` to inject
documentation, rules, or decisions from any folder that uses the
`<!-- ref:KEY -->` marker convention. The server resolves the keys and
prepends them as a `<refs>` block — no Claude token cost.

- Use for decisions, architecture rules, schema definitions, or prompting
  guidelines that live in markdown but aren't code files.
- Pass `refs_root` when working in a folder other than the default LLM repo.
  Any folder with `*.md` files using `<!-- ref:KEY -->` markers works.
- Combine with `context_files` freely: refs get prepended first (docs before code).
- Find available keys with `ref_lookup(key="list", path="/abs/path/to/folder")`.
```
<!-- /ref:mcp-refs-param-impl -->

---

<!-- ref:mcp-refs-param-acceptance -->
## Acceptance Test

After implementation, verify manually:

```python
# 1. Known key — should return response with the ref content injected
ask_ollama(
    prompt="Summarize the embedding decisions in one sentence.",
    refs=["ltg-embedding"],
)

# 2. Cross-folder key — should work from any folder with ref markers
ask_ollama(
    prompt="What model should I use for code files?",
    refs=["ltg-extractor"],
    refs_root="/mnt/i/workspaces/llm",
)

# 3. Missing key — should return error immediately
ask_ollama(
    prompt="test",
    refs=["nonexistent-key-xyz"],
)
# Expected: "Error: ref:'nonexistent-key-xyz' not found..."

# 4. Combined with context_files — both should appear in the prompt
generate_code(
    prompt="Add a docstring to this function.",
    language="python",
    refs=["local-model-conventions"],
    context_files=[{"path": "/abs/path/to/some.py"}],
)
```
<!-- /ref:mcp-refs-param-acceptance -->

---

## No changes needed

- `ref_lookup` tool: already has `path` parameter, no modification needed.
- `config.py`: `REPO_ROOT` already exported, no modification needed.
- `run-server.sh`: no changes needed.
- `overlays/ollama-scaffolding/manifest.yaml`: no changes needed (the overlay's
  `files:` entry already propagates `local-model-conventions.md` on re-install).
