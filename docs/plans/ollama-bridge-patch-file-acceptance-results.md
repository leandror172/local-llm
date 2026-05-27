# patch_file Acceptance Test Results

*Session 67 — 2026-05-26. Branch: `feature/ollama-bridge-patch-file-impl`.*
*Companion to: `docs/plans/ollama-bridge-patch-file.md` (`ref:mcp-patch-file-acceptance`).*

---

## Environment

- **Bridge git SHA at test time:** `238873a` (verified via `make bridges` + log banner)
- **Bridge log:** `/tmp/ollama-bridge.jsonl`, `OLLAMA_BRIDGE_LOG_LEVEL=DEBUG`
- **Test suite state:** 21/21 green before live testing (`test_patch_file.py` + `test_output_file.py`)
- **Model:** `qwen2.5-coder:14b` via persona `my-python-q25c14`
- **Scratch dir:** `~/workspaces/tmp/`

---

## Tilde expansion fix — live verification

*This was the bug surfaced in session 66: `_resolve_output_path` did not call
`.expanduser()`, silently writing files under `<repo>/~/...` instead of `~`.*

**Test:** `generate_code(output_file="~/workspaces/tmp/p.py")` then
`patch_file("~/workspaces/tmp/p.py", ...)`.

| Check | Result |
|---|---|
| File written to `/home/leandror/workspaces/tmp/p.py` | ✅ |
| Stale `<repo>/~/workspaces/tmp/p.py` not created | ✅ |
| `patch_file` with `~/...` path resolved and patched successfully | ✅ |
| Error message for missing file shows resolved absolute path (not `~/...`) | ✅ (verified in Scenario 6) |

---

## Original 6 acceptance scenarios

<!-- ref:mcp-patch-file-acceptance-results -->

### Scenario 1 — Basic replacement, verify content

`generate_code` → write `get_answer()` returning `1` → `patch_file("return 1" → "return 42")` → `rtk read` confirms `return 42` in file.

**Result: ✅ PASS**

### Scenario 2 — Not found → error string

`patch_file` with `old_string="return 999"` on a file that does not contain it.

**Result: ✅ PASS**
Response: `"Error: old_string not found in /home/leandror/workspaces/tmp/scenario1.py."`

### Scenario 3 — Non-unique → error with count

File contains two occurrences of `return "hello"` (in `foo()` and `bar()`).
`patch_file` without `replace_all`.

**Result: ✅ PASS**
Response: `"Error: old_string found 2 times in .... Use replace_all=True to replace all, or provide a more specific old_string."`

### Scenario 4 — `replace_all=True` replaces all occurrences

Same file as Scenario 3. `patch_file(replace_all=True)` targeting `return "hello"`.

**Result: ✅ PASS**
Response: `"Patched ... (2 replacements)"`. `grep` confirmed zero `"hello"` remaining, two `"world"` present.

### Scenario 5 — Relative path resolves from REPO_ROOT

`patch_file(path="tmp_scenario5.py", ...)` (no leading `/` or `~/`).

**Result: ✅ PASS**
Response resolved to `/mnt/i/workspaces/llm/tmp_scenario5.py` (REPO_ROOT = `/mnt/i/workspaces/llm`).

### Scenario 6 — File not found → error, not crash

`patch_file(path="~/workspaces/tmp/does_not_exist.py", ...)`.

**Result: ✅ PASS**
Response: `"Error: file not found: /home/leandror/workspaces/tmp/does_not_exist.py"`
Note: `~` was expanded before the existence check — the resolved absolute path
appears in the error, confirming fix ordering is correct.

<!-- /ref:mcp-patch-file-acceptance-results -->

---

## User-requested additional scenarios

### User Scenario 1 — Multi-line generation + correction loop

**Prompt:** Parse an ISO-8601 duration string (`P1Y2M3DT4H5M6S`, `PT90S`, `P1W`) into total seconds.
Handle weeks/days/hours/minutes/seconds. Raise `ValueError` for invalid input.
Assume 1 year = 365 days, 1 month = 30 days.

**Local model output:** Structurally correct regex-based parser with dataclass for
components, correct arithmetic. Two defects found:
1. Missing week support — `P1W` format not in regex, would raise `ValueError`
2. Unused imports (`timedelta`, `Path`)

**Verdict:** 1 — improved. ~700 est. Claude tokens saved.

**Correction via `patch_file`:**
- Added week-only fast-path (`re.match(r'^P([0-9]+)W$', s)`) before main regex
- Added `not any(match.groups())` guard (catches bare `P` — technically invalid)
- Stripped unused imports

**Smoke test results (after patch):**

| Input | Expected | Got | Status |
|---|---|---|---|
| `P1W` | 604800 | 604800 | ✅ |
| `PT90S` | 90 | 90 | ✅ |
| `P1Y2M3DT4H5M6S` | 36993906 | 36993906 | ✅ |
| `PT0S` | 0 | 0 | ✅ |
| `"invalid"` | `ValueError` | `ValueError` | ✅ |

**Result: ✅ PASS** (after one `patch_file` correction)

---

### User Scenario 2 — Add functionality to existing file via `context_files` + `output_file`

**Task:** Pass the patched `iso_duration.py` via `context_files` and ask the local
model to add `format_duration(seconds: int) -> str` — the inverse of `parse_iso_duration`.

**Local model output:** Correctly appended `format_duration` and reproduced all
prior patches verbatim (confirming `context_files` injection works). Core
decomposition logic correct (years/months/days/hours/minutes/seconds with `T`
separator). One defect found:

- `format_duration(0)` raised `ValueError` instead of returning `"PT0S"` — a
  variable name shadow (`seconds` parameter reused as `remaining_seconds % 60`)
  led to dead-code confusion in the zero-duration guard.

Also contained dead code: a week-format check that could never trigger (`parts[0]`
never starts with `"P"` in the accumulator).

**Verdict:** 1 — improved. ~1200 est. Claude tokens saved.

**Correction via `patch_file`:** Replaced the entire broken zero-duration guard +
dead week-check block with two lines: `if not parts: return "PT0S"` and
`return "P" + "".join(parts)`.

**Smoke test results (after patch):**

| Input | Expected | Got | Status |
|---|---|---|---|
| `90` | `PT1M30S` | `PT1M30S` | ✅ |
| `0` | `PT0S` | `PT0S` | ✅ |
| `604800` (7 days) | `P7D` | `P7D` | ✅ |
| `36993906` | `P1Y2M3DT4H5M6S` | `P1Y2M3DT4H5M6S` | ✅ |
| `3600` | `PT1H` | `PT1H` | ✅ |
| round-trip `PT90S` | `PT1M30S` (normalized) | `PT1M30S` | ✅ |
| round-trip `P1Y2M3DT4H5M6S` | unchanged | unchanged | ✅ |
| round-trip `PT0S` | `PT0S` | `PT0S` | ✅ |

**Result: ✅ PASS** (after one `patch_file` correction)

---

### User Scenario 3 — Generate complex code, surgical `patch_file` fix

**Task:** Generate an `LRUCache` class (Python) using `OrderedDict`, with `get(key) -> int`
and `put(key, value) -> None`. Evict LRU on overflow.

**Local model output:** Correct LRU semantics throughout (`move_to_end` on access
and on update, `popitem(last=False)` for eviction). Two type issues:
- Key type hardcoded to `str` — unnecessarily restrictive (should be `Hashable`)
- `Dict` and `Optional` imported but unused

**Verdict:** 1 — improved. ~650 est. Claude tokens saved.

**Correction via `patch_file`** (3 surgical patches, no re-generation):
1. Replace unused imports (`Dict`, `Optional` → `Hashable`)
2. Update `OrderedDict[str, Any]` → `OrderedDict[Hashable, Any]`
3. Update both method signatures: `key: str` → `key: Hashable`

**Behavioral test results (after patch):**

| Assertion | Status |
|---|---|
| `get` returns value for existing key | ✅ |
| `get` returns `-1` for missing key | ✅ |
| `put` evicts LRU (key 2) on overflow | ✅ |
| Evicted key returns `-1` | ✅ |
| New key after eviction is accessible | ✅ |
| Tuple key accepted (`Hashable` fix works) | ✅ |

**Result: ✅ PASS** (after three `patch_file` corrections)

---

## Summary

| Test | Outcome |
|---|---|
| Tilde expansion fix (`~/` paths in both tools) | ✅ |
| Scenario 1: basic replacement + content verification | ✅ |
| Scenario 2: not found → `"Error:"` string | ✅ |
| Scenario 3: non-unique → error with count | ✅ |
| Scenario 4: `replace_all=True` | ✅ |
| Scenario 5: relative path from REPO_ROOT | ✅ |
| Scenario 6: missing file → error, not crash | ✅ |
| User S1: multi-line generation + correction loop | ✅ |
| User S2: add functionality via `context_files` + `output_file` | ✅ |
| User S3: complex generation + surgical `patch_file` fix | ✅ |

**10/10 scenarios pass. Branch ready to merge.**

---

## Observed local model pattern

Across all 5 `generate_code` calls, `qwen2.5-coder:14b` produced the same two
unrequested patterns:

1. **`logging.basicConfig(level=logging.INFO, ...)` at module level** — a
   side effect that configures the root logger for the entire process. Incorrect
   in library code; should use `logging.getLogger(__name__)` only.
2. **Catch-log-reraise same exception type** — wrapping logic in `try/except`
   that only logs then re-raises identically, adding noise without changing
   behavior.

Both were corrected via `patch_file` without re-generation. Analysis and proposed
Modelfile directives: `docs/ideas/persona-error-handling-conventions.md`.
