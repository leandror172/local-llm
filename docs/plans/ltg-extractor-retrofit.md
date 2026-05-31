# LTG Extractor Retrofit — Implementation Plan

**Branch:** `feature/ltg-extractor-retrofit`
**Session origin:** session.77-ltg-extractor-retrofit (2026-05-30)
**Status:** Design complete, implementation not started. Tests for Task 1 written (routing.py TDD).

---

## CRITICAL: Read Before Starting

### Mandatory reading (in order)

1. **`.claude/overlays/local-model-conventions.md`** — YOU MUST FOLLOW THIS throughout.
   Key rules:
   - **TDD**: write tests first, run to confirm red, THEN call local model
   - **Local model first**: use `mcp__ollama-bridge__generate_code` for every new file/function >5 lines
   - **Model**: always pass `model="my-python-q25c14"` explicitly — auto-routing picks the 8B model; this project uses 14B for coding
   - **Context files**: pass the test file + any existing related modules as `context_files`
   - **Refs**: pass `refs=["patterns-code-named-methods"]` for any new class or module
   - **Verdict required**: record 0/1/2 + est. Claude tokens saved after every local model call
   - **Timeout**: 600s for 14B inference (`timeout=600`)

2. **`retrieval/model_client.py`** — current ModelClient (embed_texts only). This is what gets extended.

3. **`retrieval/embed.py`** — downstream consumer of extract_topics.py JSONL. The `winning_extractor()` and `select_winning_row()` functions define the pipeline contract that routing.py must agree with.

4. **`retrieval/extract_topics.py`** — the file being split. Read fully to understand what moves to sweep_extractors.py vs the new production runner.

5. **`retrieval/config.yaml`** — current flat shape (one role: embedding). Gets upgraded to two-level.

6. **`retrieval/tests/test_routing.py`** — already written (TDD). 14 tests for routing.py. This is Task 1's red step — already confirmed failing (ModuleNotFoundError).

7. **`retrieval/tests/test_model_client.py`** — existing tests that will break on the config upgrade (Task 4). Read to understand the fixture shape.

8. **`docs/patterns/code-design-conventions.md`** — the named-methods pattern. Pass as `refs=["patterns-code-named-methods"]` to local model calls.

9. **`docs/ideas/ltg-model-registry-design.md`** — two-level config.yaml design with naming convention and `load_config()` resolver.

10. **`retrieval/prompts/extract.txt`** — the extraction prompt template. Needed for understanding what `extract_prose()`/`extract_code()` must pass to Ollama.

---

## Architecture Decisions (all settled — do not relitigate)

### File split

| File | Purpose | What it keeps/gains |
|---|---|---|
| `retrieval/extract_topics.py` | **Production 2-arm runner** — feeds embed.py | CORPUS, build_prompt, load_prompt_template, parse_topics, JSONL writer, route()-based dispatch, client.extract_prose/extract_code |
| `retrieval/sweep_extractors.py` | **Benchmark sweeper** — evaluate N models with rubric | All current sweep code + rubric/summary/manual-rubric; call_ollama → client.call() |

`extract_topics.py` keeps the canonical name (it feeds the pipeline). `sweep_extractors.py` is the new file.

### ModelClient public surface

```python
# Public — named by intent (production runner)
def extract_prose(self, prompt: str) -> ChatResult:
    # binds role="extraction_prose" + TOPIC_FORMAT_SCHEMA from schemas.py

def extract_code(self, prompt: str) -> ChatResult:
    # binds role="extraction_code" + TOPIC_FORMAT_SCHEMA from schemas.py

# Public — generic (benchmark / dynamic-roles exception per pattern doc)
def call(self, prompt: str, model_config: dict, schema=None, timeout: int | None = None) -> ChatResult:

# Public — unchanged (documented asymmetry; embed_texts has established test surface)
def embed_texts(self, texts: list[str], role: str = "embedding") -> list[list[float]]:

# Private — owns ALL Ollama protocol quirks; operates on a RESOLVED config dict
def _chat(self, prompt: str, model_config: dict, schema=None, timeout: int | None = None) -> ChatResult:
```

`_chat` takes a **resolved config dict** (not a role string). `extract_prose`/`extract_code` resolve `self.config["extraction_prose/code"]` → dict → `_chat`. `call` is the public passthrough for configs not in config.yaml (benchmark candidate models).

### ChatResult

```python
from typing import NamedTuple

class ChatResult(NamedTuple):
    content: str
    model: str           # needed by production runner to label JSONL row["model"]
    prompt_tokens: int
    eval_count: int
    # caller keeps wall-clock timing for tok/s — do NOT use eval_duration
```

### _chat payload construction

```python
def _chat(self, prompt, model_config, schema=None, timeout=None):
    cfg_timeout = model_config.get("timeout_s", 120)
    effective_timeout = timeout if timeout is not None else cfg_timeout

    payload = {
        "model": model_config["model"],
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": model_config.get("options", {}),
    }
    if schema is not None:
        payload["format"] = schema
    if "think" in model_config:          # only inject when present — qwen2.5-coder has none
        payload["think"] = model_config["think"]

    url = f'{model_config["address"]}/api/chat'
    # ... httpx.post, raise_for_status, return ChatResult
```

### config.yaml two-level shape (exact)

```yaml
models:
  ollama-qwen3-embedding-8b-dim-4096:
    provider: ollama
    model: qwen3-embedding:8b
    address: http://localhost:11434
    embed_dim: 4096

  ollama-qwen3-14b-no-think:
    provider: ollama
    model: qwen3:14b
    address: http://localhost:11434
    think: false                   # top-level payload key (NOT inside options{})
    timeout_s: 600
    options:
      num_ctx: 32768               # session-76 value — NOT 16384
      temperature: 0.1

  ollama-qwen25coder-14b:
    provider: ollama
    model: qwen2.5-coder:14b
    address: http://localhost:11434
    # NO think key — qwen2.5-coder has no thinking mode
    timeout_s: 600
    options:
      num_ctx: 32768
      temperature: 0.1

roles:
  embedding: ollama-qwen3-embedding-8b-dim-4096
  extraction_prose: ollama-qwen3-14b-no-think
  extraction_code: ollama-qwen25coder-14b
```

### load_config() resolver

```python
def load_config(path) -> dict:
    raw = yaml.safe_load(open(path))
    # Two-level shape required — no flat fallback (advisor: no backward-compat shims)
    resolved = {}
    for role, model_name in raw["roles"].items():
        if model_name not in raw["models"]:
            raise KeyError(f"Role '{role}' references undefined model '{model_name}'")
        resolved[role] = raw["models"][model_name]
    return resolved   # same shape as before — callers unchanged
```

### schemas.py

`retrieval/schemas.py` — leaf module, no deps. Holds `TOPIC_FORMAT_SCHEMA` (the JSON schema currently in `extract_topics.py`). Imported by `model_client.py` (for named methods) and `sweep_extractors.py` (for `client.call`).

### routing.py

`retrieval/routing.py` — leaf module, no deps. Exports:
- `CODE_EXTENSIONS: set[str]` — `{".py", ".go", ".ts", ".java"}` (lowercase)
- `route(path: str) -> str` — `"extraction_code"` or `"extraction_prose"`

**Pipeline contract (BLOCKING §1):** `embed.py`'s `select_winning_row()` matches `row["model"]` against `winning_extractor(filepath)`. After the retrofit, the production runner writes `model_config["model"]` into `row["model"]`. So three things must agree:
1. `route(path)` → role → `config[role]["model"]` → model name string
2. `embed.py`'s `winning_extractor()` must return the same model name for the same path
3. The production runner must write the model name (not role) into `row["model"]`

**Fix:** Update `embed.py` to import `route` from `routing` and derive the model name from config. Specifically, `winning_extractor(filepath)` stays returning a model name string, but uses `CODE_EXTENSIONS` imported from `routing` (removes duplication). Add a test asserting `config["extraction_code"]["model"] == embed.CODE_EXTRACTOR` equivalent. Minimal change — do NOT touch `embed_batch_with_retry` or the HTTP path.

### Timeout strategy

Config has `timeout_s` per model (600 for 14B extractors). `_chat(timeout=None)` uses config default when not passed. Benchmark passes `timeout=600` explicitly (or its `TIMEOUT_S` constant). `embed_texts` keeps its own 120s — do not let extraction inherit it.

### Error handling

`_chat`/`call` **raise** — same as `embed_texts`. Raises: `httpx.TimeoutException`, `HTTPStatusError`, `ConnectError`. The status taxonomy (`timeout`/`http_error`/`error`/`malformed_json`) stays in the caller's try/except. JSON parse failure (`parse_topics` → None) is classified by caller as `malformed_json`, not raised by `_chat`.

---

## Implementation Sequence (8 tasks)

### Task 1 — `retrieval/routing.py` + update `embed.py`

**Tests already written:** `retrieval/tests/test_routing.py` (14 tests, confirmed red).

```
# Local model call:
generate_code(
    prompt="Implement retrieval/routing.py per the tests...",
    model="my-python-q25c14",
    language="python",
    context_files=[{"path": ".../retrieval/tests/test_routing.py"}],
    refs=["patterns-code-named-methods"],
    output_file="retrieval/routing.py",
    timeout=600,
)
```

After green on routing tests, update `embed.py`:
- Import `CODE_EXTENSIONS` from `routing` — remove its own copy
- Keep `CODE_EXTRACTOR`/`PROSE_EXTRACTOR` constants unchanged for now (replaced in Task 4)
- No config dependency in this task — config is still flat Phase-2 shape

Run all retrieval tests after. Expect green on routing + embed, no regressions.

### Task 2 — `retrieval/schemas.py`

Write tests first in `retrieval/tests/test_schemas.py`:
- `TOPIC_FORMAT_SCHEMA` is a dict
- Has `"type": "object"` at top level
- Has `"properties"` → `"topics"` → `"type": "array"`
- `"minItems": 3`, `"maxItems": 10` on the topics array
- Each topic item has `"name"`, `"description"`, `"spans"` keys

Then delegate to local model:
```
generate_code(
    prompt="Create retrieval/schemas.py — a leaf module holding TOPIC_FORMAT_SCHEMA...",
    model="my-python-q25c14",
    context_files=[
        {"path": ".../retrieval/tests/test_schemas.py"},
        {"path": ".../retrieval/extract_topics.py"},  # current FORMAT_SCHEMA location
    ],
    output_file="retrieval/schemas.py",
    timeout=600,
)
```

### Task 3 — Extend `model_client.py`

**Most complex task.** Write tests first in `test_model_client.py` (new test functions added to existing file):

New tests to write:
- `ChatResult` is a NamedTuple with fields `content`, `model`, `prompt_tokens`, `eval_count`
- `_chat` / `call` builds payload with `stream: False`
- `format` injected when schema passed, absent when not
- `think` injected into payload when present in config (qwen3), absent when not (qwen2.5-coder)
- `options` block passed verbatim from config
- Timeout override beats config `timeout_s`
- `httpx.TimeoutException` propagates from `_chat`
- `httpx.ConnectError` propagates
- `ChatResult` fields populated from faked Ollama response
- `extract_prose()` calls `_chat` with role `"extraction_prose"` resolved config
- `extract_code()` calls `_chat` with role `"extraction_code"` resolved config
- `call()` passes model_config directly to `_chat`
- New `load_config` tests: role resolves to model config dict; undefined model raises KeyError

Then delegate implementation to local model:
```
generate_code(
    prompt="Extend ModelClient with ChatResult, _chat, call, extract_prose, extract_code...",
    model="my-python-q25c14",
    context_files=[
        {"path": ".../retrieval/tests/test_model_client.py"},  # updated with new tests
        {"path": ".../retrieval/model_client.py"},             # current file
        {"path": ".../retrieval/schemas.py"},                  # for TOPIC_FORMAT_SCHEMA import
        {"path": ".../retrieval/prompts/extract.txt"},         # what _chat must handle
    ],
    refs=["patterns-code-named-methods"],
    output_file="retrieval/model_client.py",
    timeout=600,
)
```

### Task 4 — Upgrade `config.yaml` + fix test fixtures + routing agreement (one atomic commit)

**WARNING:** Several interdependent changes must land together — splitting them leaves the test suite broken between commits.

1. Rewrite `retrieval/config.yaml` with the two-level shape from the spec above
2. Update `VALID_CONFIG_YAML` fixture in `test_model_client.py` to two-level shape
3. In `embed.py`: replace `CODE_EXTRACTOR`/`PROSE_EXTRACTOR` hardcoded constants with `config[route(path)]["model"]` — thread the already-loaded cfg into `winning_extractor(filepath, cfg)`. Config becomes the single source of truth; no duplicate model name strings.
4. Add `test_routing_agreement` in `test_embed.py`: assert that `winning_extractor` returns the config-derived model name for a code path and a prose path (not a hardcoded string).
5. Run all tests — expect green

This task has no local model delegation. Do it directly.

After updating fixtures: tests that were green for the two-level `load_config` from Task 3 will now use the correct fixture.

### Task 5 — `retrieval/sweep_extractors.py` (benchmark)

This is essentially `extract_topics.py` with one substitution: `call_ollama()` → `client.call(prompt, model_config, schema)`.

```bash
cp retrieval/extract_topics.py retrieval/sweep_extractors.py
```

Then minimal edits:
- Add `from model_client import ModelClient, load_config` + `from schemas import TOPIC_FORMAT_SCHEMA`
- Add `from routing import CODE_EXTENSIONS` (replace its own copy)
- Remove `call_ollama()` function
- In `run_single()`: replace `call_ollama(model, prompt)` with:
  ```python
  client = ModelClient(load_config(CONFIG_PATH))
  model_config = _build_benchmark_config(model)  # helper that builds config dict from DEFAULT_MODELS + MODEL_EXTRA_PARAMS + OLLAMA_OPTIONS
  result = client.call(prompt, model_config, schema=TOPIC_FORMAT_SCHEMA, timeout=TIMEOUT_S)
  ```
- Keep all rubric, summary, manual-rubric output unchanged

Delegate the `_build_benchmark_config` helper and the `run_single` rewrite to local model with the current `extract_topics.py` + `model_client.py` as context files.

Write tests: confirm `_build_benchmark_config("qwen3:14b")` produces a dict with `think: false`; `_build_benchmark_config("qwen2.5-coder:14b")` has no `think` key; `_build_benchmark_config("gemma3:12b")` has correct model name.

### Task 6 — Rewrite `extract_topics.py` as 2-arm production runner

**New file replacing the sweep logic.** Write tests first in a new `retrieval/tests/test_extract_topics.py`:

Tests to write:
- `route_file(path)` returns correct role for `.py`/`.go`/`.ts`/`.java` (code) and `.md`/`.txt` (prose)
- JSONL row has contract fields: `file`, `model`, `status`, `run_id`, `timestamp`, `file_role`, `parsed_topics`
- Row `model` field matches `config[route(path)]["model"]` (not the role name)
- `embed.select_winning_row(rows, filepath)` finds a non-None row when production runner succeeds (integration guard — this is the §1 parity gate)
- `parse_topics` returns None on malformed JSON, list on valid

Then delegate to local model:
```
generate_code(
    prompt="Rewrite extract_topics.py as a 2-arm production runner...",
    model="my-python-q25c14",
    context_files=[
        {"path": ".../retrieval/tests/test_extract_topics.py"},
        {"path": ".../retrieval/model_client.py"},
        {"path": ".../retrieval/routing.py"},
        {"path": ".../retrieval/schemas.py"},
        {"path": ".../retrieval/embed.py"},      # to understand JSONL contract
        {"path": ".../retrieval/prompts/extract.txt"},
    ],
    refs=["patterns-code-named-methods"],
    output_file="retrieval/extract_topics.py",
    timeout=600,
)
```

**What the production runner keeps from the old file:**
- `CORPUS` list (8 files with hardcoded roles)
- `build_prompt()`, `load_prompt_template()`, `parse_topics()`
- JSONL writer that emits `run_id`, `timestamp`, `model`, `file`, `file_role`, `status`, `parsed_topics`

**What it sheds:**
- `DEFAULT_MODELS`, `MODEL_EXTRA_PARAMS`, `OLLAMA_OPTIONS`
- `call_ollama()`
- `compute_rubric()`, `print_summary()`, manual-rubric template
- `--model`, `--runs` CLI flags

**What it gains:**
- Routing: `route(path)` → role → `client.extract_prose/extract_code(prompt)`
- 1 row per file (not 4)

### Task 7 — Bash wrappers

Create following the `run-embed.sh` pattern exactly:

```bash
# retrieval/run-extract-topics.sh
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/extract_topics.py" "$@"

# retrieval/run-sweep-extractors.sh
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/sweep_extractors.py" "$@"
```

Make executable: `chmod +x retrieval/run-extract-topics.sh retrieval/run-sweep-extractors.sh`

Register both in `.claude/index.md` under the bash-wrappers table.

### Task 8 — Parity check (pipeline verification)

Run production runner on one prose + one code file:
```bash
python3 retrieval/extract_topics.py --file docs/research/smart-rag-repowise.md --file personas/build-persona.py
```

Then run embed on that output:
```bash
python3 retrieval/embed.py --input retrieval/runs/<tag>.jsonl --output /tmp/parity-check.jsonl
```

**Success criteria:**
- embed.py finds a non-None winning row for both files (prose→qwen3:14b, code→qwen2.5-coder:14b)
- Topic output for each file matches a prior sweep run for the same winning model (compare topic names / count against a prior JSONL in `retrieval/runs/`)
- No `WARNING: no winning row` messages in stderr

If parity check fails: the most likely cause is a routing agreement mismatch (§1). Check `row["model"]` in the new JSONL vs what `embed.py`'s `winning_extractor()` returns.

---

## Out of Scope (explicitly)

- `embed.py`'s `embed_batch_with_retry` HTTP path — stays as-is
- Phase 2.5 full corpus expansion — runs on existing 8-file CORPUS only
- N-criteria threshold recalibration for 4096-dim — separate deferred task
- Simplifying `select_winning_row` now that production emits 1 row/file
- `embed_texts(role=)` → named wrapper cleanup — separate task, established test surface

---

## Commit Strategy

Suggested granularity:
1. `routing.py` + embed.py update (Task 1)
2. `schemas.py` (Task 2)
3. `model_client.py` extensions + new tests (Task 3)
4. `config.yaml` upgrade + fixture fix (Task 4) — same commit, always together
5. `sweep_extractors.py` (Task 5)
6. `extract_topics.py` rewrite + new tests (Task 6)
7. Bash wrappers + index update (Task 7)
8. No commit for Task 8 (verification only, unless probe results are worth committing)

---

## Advisor Review (appended post-plan — read before Task 1)

The design decisions (fork B, named methods, `ChatResult`, `schemas.py`, two-level config) are correct — do not relitigate them. Three fixes required before coding:

### BLOCKING — sequencing bug: routing-agreement test can't pass in Task 1

Task 1 mentions adding `test_routing_agreement` asserting `config["extraction_code"]["model"] == embed.CODE_EXTRACTOR`. But `config.yaml` is not upgraded to the two-level shape (the step that *adds* the `extraction_prose`/`extraction_code` roles) until **Task 4**. At Task 1 the config is still the flat Phase-2 shape with only the `embedding` role — `config["extraction_code"]` raises `KeyError` — TDD thrashes.

**Fix:** Move `test_routing_agreement` and any embed.py change that reaches into `config[...extraction...]` to **Task 4**, in the same commit as the config upgrade. Task 1 scope: write `routing.py` (already-red `test_routing.py`) + swap embed.py's local `CODE_EXTENSIONS` for an import from `routing` only (no config dependency). That's it.

### SHOULD-FIX — embed.py still has two sources of truth for model names

§1 was meant to eliminate `CODE_EXTRACTOR`/`PROSE_EXTRACTOR` hardcoded constants. The plan re-introduced the guard-test approach instead. **In Task 4:** replace those constants with `config[route(path)]["model"]` (thread the already-loaded `cfg` into `winning_extractor`). This makes `config.yaml` the single source of truth, deletes the guard-test entirely, and naturally lands in Task 4 where the config dependency is satisfied. Update `test_embed.py`'s routing parametrization to assert the config-derived model name, not a hardcoded string.

### SHOULD-FIX — drop the `load_config` backward-compat shim

The plan's `load_config` adds `if "models" not in raw: return raw["roles"]`. Project guidelines forbid backwards-compat shims "when you can just change the code." After Task 4 every config + fixture is two-level, so the flat branch is dead (and a footgun). **Implement `load_config` to require the two-level shape with no flat fallback.** The config upgrade + fixture fix + `load_config` rewrite are one atomic commit (Task 4).

### Implementation gotchas

1. **`_chat` must use module-level `httpx.post(url, json=payload, timeout=...)` — NOT `httpx.Client`.** Existing `test_model_client.py` mocks `patch("httpx.post", ...)`. Using `httpx.Client` silently breaks every `_chat` test mock.
2. **Spell out `ChatResult` field extraction** in `_chat`: `content = resp.json()["message"]["content"]`; `model = resp.json().get("model", model_config["model"])`; `prompt_tokens = resp.json().get("prompt_eval_count", 0)`; `eval_count = resp.json().get("eval_count", 0)`. Benchmark rubric depends on token counts being populated.
3. **`_build_benchmark_config` must set `think: false` for ALL qwen3 variants** — qwen3:14b *and* qwen3:8b (old `MODEL_EXTRA_PARAMS` covered both). gemma3:12b and qwen2.5-coder:14b get no `think` key.
4. **Before Task 2 (schema move) and Task 6 (rewrite): run `git grep -n "from extract_topics\|import extract_topics\|FORMAT_SCHEMA"`** to confirm nothing imports `FORMAT_SCHEMA`/`CORPUS` from `extract_topics.py`. Silent breakage otherwise.

### Solid as-is

Fork B + `sweep_extractors.py`; `extract_prose`/`extract_code` + private `_chat(model_config)`; `ChatResult` with `model` field; `schemas.py` leaf module; timeout = config `timeout_s` + caller override; raise-and-let-caller-classify; Task 6 integration test + Task 8 parity check as the §1 regression guard.

---

## What Is Already Done

- Branch `feature/ltg-extractor-retrofit` created and checked out
- `retrieval/tests/test_routing.py` written (14 tests, confirmed red) — committed
- `docs/patterns/code-design-conventions.md` written — committed
- `docs/patterns/technology-conventions.md` updated with pointer — committed
- `.claude/index.md` updated — committed
