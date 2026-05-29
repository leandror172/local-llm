# DeepCoder-14B Benchmark Report

<!-- ref:deepcoder-benchmark-meta -->
## Metadata

| Field | Value |
|---|---|
| Date | 2026-05-29 |
| Decision | M-P0a: swap `qwen2.5-coder:14b` → DeepCoder-14B? |
| Hardware | RTX 3060 12GB VRAM |
| Baseline model | `qwen2.5-coder:14b` (9.0 GB, ~6.8 tok/s) |
| Candidate model | `deepcoder:14b` (9.0 GB, DeepCoder-14B-Preview, fine-tuned from DeepSeek-R1-Distilled-Qwen-14B via distributed RL by Agentica + Together AI) |
| Timeout | 300s (baseline) / 500s (deepcoder) |
| Prompts | Go LRU cache · Python async pipeline · MCP file stats server |
| Personas tested | 3 baseline (constrained) · 3 deepcoder constrained · 3 deepcoder vanilla |
| Results dir | `benchmarks/results/deepcoder-benchmark-2026-05-28/` |
| Evaluators | Claude Sonnet 4.6 (primary) + Opus 4.8 subagent (independent) |

### Why DeepCoder was benchmarked

`qwen3.6-coder:14b` (M-P0a target from session 68 model survey) does not exist on Ollama — the tag was from unverified secondary sources. `qwen3.6` is a 27B/35B general model (too large). DeepCoder-14B emerged as the strongest verified 14B coder on Ollama: HumanEval+ 92.6%, LiveCodeBench 60.6%, same 9GB VRAM footprint.

### Thinking architecture note

DeepCoder is built on DeepSeek-R1-Distilled-Qwen-14B and generates `<think>...</think>` reasoning traces before code output. The HuggingFace model card recommends `max_tokens = 64000` (at least) to accommodate CoT traces. **No think-suppression mechanism is documented** — not on HuggingFace, Ollama, or the agentica/rllm GitHub. This is intrinsic to the model design, not a configuration parameter. Verified across three sources (2026-05-29).
<!-- /ref:deepcoder-benchmark-meta -->

---

<!-- ref:deepcoder-benchmark-run-summary -->
## Run Summary

| Run | Persona variant | Status | Elapsed | Tokens | tok/s |
|---|---|---|---|---|---|
| go-q25c14 | baseline (constrained) | ✅ completed | 212.9s | 1370 | 6.4 |
| python-q25c14 | baseline (constrained) | ✅ completed | 111.3s | 760 | 6.8 |
| mcp-q25c14 | baseline (constrained) | ✅ completed | 123.5s | 845 | 6.8 |
| go-deepcoder | constrained | ❌ TIMEOUT | 500s | 0 | — |
| python-deepcoder | constrained | ✅ completed | 194.8s | 1326 | 6.8 |
| mcp-deepcoder | constrained | ❌ TIMEOUT | 500s | 0 | — |
| go-deepcoder-vanilla | vanilla (no system prompt) | ❌ TIMEOUT | 500s | 0 | — |
| python-deepcoder-vanilla | vanilla (no system prompt) | ❌ TIMEOUT | 500s | 0 | — |
| mcp-deepcoder-vanilla | vanilla (no system prompt) | ❌ TIMEOUT | 500s | 0 | — |

**5 of 6 DeepCoder runs timed out.** The only completion was `python-deepcoder` at 194.8s — 75% slower than `python-q25c14` (111.3s). The Python pipeline is the simplest of the three prompts; the more complex Go and MCP tasks were unreachable within 500s (~8 minutes).

Notable: the constrained `python-deepcoder` completed while `python-deepcoder-vanilla` timed out. A system prompt that scopes the task appears to shorten the reasoning trace — but not reliably enough to generalize.
<!-- /ref:deepcoder-benchmark-run-summary -->

---

<!-- ref:deepcoder-benchmark-go -->
## Go — LRU Cache (Prompt 01)

**Prompt:** Concurrent-safe LRU cache with generics, TTL, `context.Context` stop signal, capacity eviction, runnable with `go run -race`.

### go-q25c14 (212.9s · 1370 tok · 6.4 tok/s)

| Checklist item | Result | Note |
|---|---|---|
| Uses generics correctly | PASS | `Cache[K comparable, V any]` correctly parameterized throughout |
| context.Context stop signal (no goroutine leak) | PARTIAL | Goroutine exits on `ctx.Done()` via `Close()`, but cache creates its own `context.Background()` internally rather than accepting a caller-supplied context |
| Get uses correct lock level — no data race | **FAIL** | `Get` holds only `RLock` but calls `moveToFront` (mutates list head/tail/prev/next) and `delete(c.cache, key)` (mutates map). Verified by Opus subagent: `go run -race` fires 10–13 data race reports per run |
| `go run -race` clean | **FAIL** | Explicit prompt requirement unmet — see above |
| LRU eviction correct | PARTIAL | `evictOldest` targets correct end (tail), but `pushToFront` never wires `e.next`, corrupting the doubly-linked list. Verified: 5 Puts yield only 4 tracked entries |
| TTL expiration on access | PARTIAL | On-access lazy expiry in `Get` works; periodic cleaner is effectively dead — walks from head (MRU/newest expiry) and breaks on first non-expired; combined with corrupt list, reaches at most one node. Verified: `cleanExpired` removed 0 of 4 expired entries |
| Compiles as emitted | **FAIL** | Two-file `go build` fails: unused `"fmt"` in lru_cache.go, unused `"context"` in main.go |

**Verdict: 1 (improved — usable with mechanical fixes).** Structure is idiomatic; all bugs are localized. Fixes: promote `Get` to `Lock`, fix `pushToFront` to wire `e.next`, fix cleaner traversal direction (tail→head), drop two unused imports.

### go-deepcoder: TIMEOUT (500s, 0 tokens) — Verdict: 0
### go-deepcoder-vanilla: TIMEOUT (500s, 0 tokens) — Verdict: 0
<!-- /ref:deepcoder-benchmark-go -->

---

<!-- ref:deepcoder-benchmark-python -->
## Python — Async Pipeline (Prompt 04)

**Prompt:** Pydantic FileRecord, @dataclass PipelineError/PipelineResult, non-blocking I/O via run_in_executor, broad exception catch per path, never raises.

### python-q25c14 (111.3s · 760 tok · 6.8 tok/s)

| Checklist item | Result | Note |
|---|---|---|
| FileRecord is Pydantic BaseModel | PASS | Correct |
| PipelineError / PipelineResult are @dataclass | **FAIL** | Both are plain classes with `__init__` — not @dataclass. Hard requirement missed |
| run_in_executor used (non-blocking) | PARTIAL | Read loop offloaded; but `path.stat()` and `path.open()` run on event loop (blocking syscalls) |
| run_pipeline catches ALL exceptions per path | PASS | Inner wrapper catches `Exception` broadly; never re-raises |
| path→error mapping correct | PASS | `PipelineError(path, str(e))` correctly bound |
| main() prints summary with path + reason | PASS | Logs totals and per-error detail |

Persona compliance notes: one f-string violation in main.py (`logger.error(f"Directory {directory}...")` — persona requires lazy `%` formatting); missing `import asyncio` in main.py (would fail at runtime).

**Verdict: 1 (improved).** Functionally sound pipeline semantics. Hard requirement failure (missing @dataclass) is a 2-line fix. Runtime import error requires one additional line.

---

### python-deepcoder (194.8s · 1326 tok · 6.8 tok/s) — think block present, stripped

| Checklist item | Result | Note |
|---|---|---|
| FileRecord is Pydantic BaseModel | PASS | Correct |
| PipelineError / PipelineResult are @dataclass | **PASS** | Both correctly `@dataclass` — **beats q25c14 on the exact item q25c14 failed** |
| run_in_executor used (non-blocking) | PASS | Both `stat()` and checksum fully offloaded via `run_in_executor` — more thorough than q25c14 |
| run_pipeline catches ALL exceptions per path | PASS | `except Exception` broadly; logs, collects, never raises |
| path→error mapping correct | PASS | `PipelineError(path=path, ...)` correctly bound per task |
| main() prints summary with path + reason | PASS | Prints totals and per-error path+reason |

Minor dings: `open(str(path))` instead of `Path.open()` (pathlib persona constraint); `print()` in main instead of `logger`; unused imports (`Optional`, `Tuple`); `asyncio.get_event_loop()` deprecated in 3.10+ (should use `get_running_loop()`).

**Verdict: 2 (accepted, near as-is).** Correct dataclasses, fuller non-blocking I/O. Only minor stylistic fixes needed. **Genuine quality win over q25c14 on this task.**

### python-deepcoder-vanilla: TIMEOUT (500s, 0 tokens) — Verdict: 0
<!-- /ref:deepcoder-benchmark-python -->

---

<!-- ref:deepcoder-benchmark-mcp -->
## MCP — File Stats Server (Prompt 05)

**Prompt:** FastMCP server, two tools, async handlers, ≥3 named helpers, structured error returns, no global state, scandir/iterdir only, extension filter with correct scoping.

### mcp-q25c14 (123.5s · 845 tok · 6.8 tok/s)

| Checklist item | Result | Note |
|---|---|---|
| Correct FastMCP API (FastMCP(), @mcp.tool() decorators) | **FAIL** | Uses `from fastmcp import MCP` + hand-rolled dispatcher. Real API is `FastMCP("name")` + `@mcp.tool()` decorators. No tools would register; does not run against real FastMCP |
| All handlers async | PASS | All functions correctly async |
| No exceptions reach client (grep raise clean) | **FAIL** | No `raise` keyword, but `os.stat()` succeeds on directories (not-a-file case not caught → `IsADirectoryError` from line_count `open()`); unreadable files produce uncaught `PermissionError` |
| ≥3 named helpers | PASS | `_read_file_metadata`, `_build_file_stats`, `_read_directory_entries`, `_build_directory_summary` |
| No module-level mutable state | PASS | None |
| Uses scandir/iterdir, not walk/rglob | PASS | `os.scandir`, non-recursive |
| extension filter scopes counts; extensions dict covers ALL | **FAIL** | Default `extension: str = ""` hits `ext == extension_filter` check; `""` is not `None`, so unfiltered calls count only extensionless files in `file_count`/`total_bytes`. Extensions dict is correct (covers all); scoping logic broken for default case |
| Description strings on tools and parameters | PARTIAL | Docstrings present; per-parameter descriptions crammed into docstring text, not declared per-parameter as FastMCP requires |

**Verdict: 0 (rejected).** Wrong framework API (won't run against real FastMCP), exceptions reach client, default-filter bug produces wrong counts on most common call.

### mcp-deepcoder: TIMEOUT (500s, 0 tokens) — Verdict: 0
### mcp-deepcoder-vanilla: TIMEOUT (500s, 0 tokens) — Verdict: 0
<!-- /ref:deepcoder-benchmark-mcp -->

---

<!-- ref:deepcoder-benchmark-my-eval -->
## My Evaluation — Verdict Summary

| Run | Verdict | Primary reason |
|---|---|---|
| go-q25c14 | 1 | Data race under RLock, corrupt list, dead cleaner, compile error |
| python-q25c14 | 1 | Missing @dataclass (hard req), f-string violation, missing import |
| mcp-q25c14 | 0 | Wrong FastMCP API, exception leaks, filter bug |
| go-deepcoder | 0 | TIMEOUT |
| python-deepcoder | 2 | Correct dataclasses, fuller async — best output of the set |
| mcp-deepcoder | 0 | TIMEOUT |
| go-deepcoder-vanilla | 0 | TIMEOUT |
| python-deepcoder-vanilla | 0 | TIMEOUT |
| mcp-deepcoder-vanilla | 0 | TIMEOUT |
<!-- /ref:deepcoder-benchmark-my-eval -->

---

<!-- ref:deepcoder-benchmark-opus-eval -->
## Opus 4.8 Independent Evaluation (verbatim)

> Scored independently before seeing my verdicts. Opus also empirically verified Go claims via scratch harness (`go build`, `go vet`, `go run -race`, behavioral cleaner test).

---

Conclusive. Two findings here:

1. **The map only ever holds 4 entries despite 5 `Put`s** — the linked list is corrupt. `pushToFront` sets `head.next = e` then `head = e` but never links `e.next` back, and `evictOldest`/capacity logic interacts badly. Capacity is 10 here so it's not eviction — it's that `cleanExpired` and the list traversal are broken.
2. **`cleanExpired` removed 0 entries** even though all 5 (well, 4 tracked) were expired. It starts at `head` (MRU, newest expiry), and because `pushToFront` builds a malformed list where `head.next` is stale, the loop terminates immediately. Expired entries at the tail are never reached. The periodic cleaner is effectively dead.

---

### RUN 1 — go-q25c14 (qwen2.5-coder:14b, constrained) ✅ 212.9s

| Checklist item | Result | Note |
|---|---|---|
| Uses generics correctly | PASS | `Cache[K comparable, V any]` and helpers all properly parameterized |
| context.Context stop signal (no leak) | PARTIAL | No leak (cleaner exits on `ctx.Done()` via `Close()`), but it **creates its own** `context.Background()` internally rather than *accepting* a caller `context.Context` as the prompt implies |
| Get uses correct lock level (no race) | **FAIL** | `Get` holds only `RLock` yet calls `moveToFront` (mutates list head/tail/prev/next) and `delete(c.cache, key)` (mutates map). **Verified: `go run -race` fires 10-13 DATA RACE reports/run under contention** |
| `go run -race` clean | **FAIL** | See above — explicit prompt requirement unmet |
| LRU eviction correct | PARTIAL | `evictOldest` targets `tail` (correct LRU end), but list is built malformed — `pushToFront` never wires `e.next`. **Verified: 5 `Put`s yield only 4 tracked entries** |
| TTL expiration on access | PARTIAL | On-access lazy expiry in `Get` works; periodic cleaner is dead — verified: `cleanExpired` removed 0 of 4 expired entries |
| Compiles as emitted | **FAIL** | Two-file `go build`: `"fmt" imported and not used`; `"context" imported and not used` |

**Verdict: 1.** Structure is sound and idiomatic; fixes are localized (promote `Get` to `Lock`, fix `pushToFront` linking, fix cleaner traversal direction, drop two imports). Borderline 0/1 — landed at 1 only because the defects are mechanical to repair.

### RUN 2 — python-q25c14 (qwen2.5-coder:14b, constrained) ✅ 111.3s

| Checklist item | Result | Note |
|---|---|---|
| FileRecord is Pydantic BaseModel | PASS | Correct |
| PipelineError / PipelineResult are @dataclass | **FAIL** | Both are plain classes with `__init__`, not `@dataclass`. Also violates persona's "use dataclasses for structured data" rule |
| run_in_executor used (non-blocking) | PARTIAL | `_compute_checksum` runs `f.read` in executor, but `path.stat()` and `path.open()` themselves run on the event loop (blocking syscalls) |
| run_pipeline catches ALL exceptions per path | PASS | Inner wrapper catches `Exception` broadly; never re-raises |
| path→error mapping correct | PASS | `PipelineError(path, str(e))` uses the loop-bound `path` correctly |
| main() prints summary w/ path + reason | PASS | Logs total processed, total errors, and per-error path+reason |

Persona compliance: type hints PASS; pathlib PASS; logging lazy-`%` mostly PASS but **one f-string violation** (`logger.error(f"Directory {directory} does not exist.")`); functions under ~15 lines PASS.

**Verdict: 1.** Functionally close and pipeline semantics are correct, but the explicit dataclass requirement is missed on both types — a hard requirement failure that's trivial to fix.

### RUN 3 — python-deepcoder (DeepCoder-14B, constrained) ✅ 194.8s (had `<think>` block)

| Checklist item | Result | Note |
|---|---|---|
| FileRecord is Pydantic BaseModel | PASS | Correct |
| PipelineError / PipelineResult are @dataclass | **PASS** | Both correctly `@dataclass`. **Beats q25c14 on the exact item q25c14 failed** |
| run_in_executor used (non-blocking) | PASS | Both `stat()` and checksum offloaded via `run_in_executor` — more thorough than q25c14 |
| run_pipeline catches ALL exceptions per path | PASS | Catches `Exception` broadly; logs and collects, never raises |
| path→error mapping correct | PASS | `PipelineError(path=path, ...)` bound correctly per task |
| main() prints summary w/ path + reason | PASS | Prints totals and per-error path+reason |

Persona compliance: type hints PASS; specific exceptions PASS; dataclasses PASS. Dings: uses `open(str(path))` instead of `Path.open` (persona wants pathlib); uses `print()` in main and a bare `import sys` mid-function rather than logging; unused imports (`Optional`, `Tuple`).

**Verdict: 2.** Slightly higher correctness than q25c14's Python — correct dataclasses, fuller non-blocking I/O. Minor pathlib/print stylistic dings. This is the **only completed DeepCoder run** and it is a genuine quality win on this task.

### RUN 4 — mcp-q25c14 (qwen2.5-coder:14b, constrained) ✅ 123.5s

| Checklist item | Result | Note |
|---|---|---|
| Correct FastMCP API (FastMCP(), @mcp.tool()) | **FAIL** | Uses `from fastmcp import MCP` + a hand-rolled `handle_request` dispatcher. Real FastMCP is `FastMCP("name")` with `@mcp.tool()` decorators. No tools would register; this does not run against real FastMCP |
| All handlers async | PASS | All functions correctly `async` |
| No exceptions reach client (grep raise clean) | **FAIL** | No `raise` keyword, but `os.stat()` succeeds on a directory, so "not a file" is never caught → `IsADirectoryError` from line_count `open()`. Unreadable file → uncaught `PermissionError` |
| ≥3 named helpers | PASS | Four helpers present |
| No module-level mutable state | PASS | None |
| Uses scandir/iterdir, not walk/rglob | PASS | `os.scandir`, non-recursive |
| extension filter scopes counts; extensions dict covers ALL | **FAIL** | Default `extension: str = ""` hits `ext == extension_filter`; `""` is not `None`, so unfiltered calls count only extensionless files |
| Description strings on tools + params | PARTIAL | Tools have docstrings; per-parameter descriptions crammed into docstring text, not declared per-parameter as FastMCP requires |

**Verdict: 0.** Wrong framework API (won't run), exceptions reach the client, and a default-argument filter bug that produces wrong results on the most common call.

### Timed-out runs

| Run | Verdict |
|---|---|
| go-deepcoder (constrained) | 0 — TIMEOUT (500s, 0 tokens) |
| mcp-deepcoder (constrained) | 0 — TIMEOUT (500s, 0 tokens) |
| go-deepcoder-vanilla | 0 — TIMEOUT (500s, 0 tokens) |
| python-deepcoder-vanilla | 0 — TIMEOUT (500s, 0 tokens) |
| mcp-deepcoder-vanilla | 0 — TIMEOUT (500s, 0 tokens) |

DeepCoder produced usable output in **1 of 6** runs.

### Opus Swap Recommendation: DO NOT SWAP

Overall: keep `qwen2.5-coder:14b` for all three personas. The decision is driven less by the average latency and more by DeepCoder being *structurally unfit* for this hardware and use case.

**Why this is structural, not run variance:** DeepCoder-14B is fine-tuned from DeepSeek-R1-Distilled-Qwen-14B — a reasoning model that emits `<think>` chains before answering (confirmed: the one completion carried a think block). That reasoning overhead is **intrinsic**, not a one-off slow run. 5/6 timeouts on a 500s (~8 min) budget is a systematic pattern. Latency is also unpredictable: the vanilla (unconstrained, less prompt) `python-deepcoder` **timed out**, while the constrained `python-deepcoder` **completed**. Completion time doesn't correlate with prompt simplicity.

**Per language:**
- **Go — keep q25c14.** No DeepCoder data (both timed out). q25c14 is flawed (verdict 1) but produces reviewable code in 213s. DeepCoder produces nothing within budget.
- **Python — keep q25c14, despite a real quality edge for DeepCoder.** The one DeepCoder win (correct dataclasses, fuller async, verdict 2 vs 1) does not justify ~2x latency and unpredictable completion. Cheaper to fix q25c14's dataclass miss than absorb DeepCoder's overhead.
- **MCP — keep q25c14 by default.** No DeepCoder data. Caveat: q25c14's MCP output is itself rejected (verdict 0) — wrong FastMCP API. Neither model is good here, but DeepCoder gave zero evidence it would do better.

**Bottom line:** DeepCoder-14B's R1-distill reasoning overhead makes it non-viable for interactive coding personas on a 12GB RTX 3060. Its single completed run shows promising raw quality (the Python dataclasses win is genuine), but 5/6 timeouts and unpredictable completion times disqualify it. Revisit only with (a) a non-reasoning DeepCoder variant or think-suppression that reliably works, or (b) faster hardware where 200s+ generations are acceptable.
<!-- /ref:deepcoder-benchmark-opus-eval -->

---

<!-- ref:deepcoder-benchmark-decision -->
## Final Decision

**VERDICT: DO NOT SWAP. Keep `qwen2.5-coder:14b` for all three personas.**

Both evaluators (Sonnet 4.6 + Opus 4.8) agree on all 9 verdicts and on the swap decision.

### Rationale

DeepCoder-14B is structurally unfit for interactive coding personas on RTX 3060 12GB:

1. **5/6 runs timed out at 500s.** The HuggingFace model card recommends `max_tokens = 64000` minimum — the reasoning traces alone can consume the entire generation budget before code begins. At 6.8 tok/s, 64K reasoning tokens = ~9,412s (~157 minutes). This is not a tuning problem.

2. **No think-suppression mechanism exists.** Verified against HuggingFace model card, agentica/rllm GitHub, and Ollama library page (2026-05-29). Unlike Qwen3 (`think: false`), DeepCoder has no documented way to skip CoT.

3. **Latency is unpredictable, not just slow.** `python-deepcoder-vanilla` (simpler: no system prompt) timed out while `python-deepcoder` (constrained: has system prompt) completed. Completion time does not correlate with prompt complexity. This makes it unsuitable for any interactive workflow.

4. **The one quality win is real but insufficient.** `python-deepcoder` (verdict 2) correctly used `@dataclass` and did fuller non-blocking I/O where `python-q25c14` (verdict 1) failed. This is a genuine improvement — but a 2-line fix to the baseline is a cheaper path than absorbing 2× latency and 83% timeout rate.

5. **MCP baseline itself needs fixing.** `mcp-q25c14` is rejected (verdict 0) — wrong FastMCP API. This is an independent issue that needs addressing regardless of the DeepCoder decision. DeepCoder provided no evidence of improvement here.

### Actions from this report

| Action | Status | Priority |
|---|---|---|
| Close M-P0a — no viable 14B coder upgrade exists at this time | Done (this report) | — |
| Update tasks.md: M-P0a closed as "no swap — model doesn't exist / DeepCoder unviable" | Pending | P0 |
| Fix `mcp-q25c14` persona — wrong FastMCP API is a production bug | Pending | P1 |
| Fix `go-q25c14` output issues — document for next Go benchmark run | Pending | P2 |
| Watch: DeepCoder update with think-suppression or non-reasoning variant | Deferred | watch |
| Watch: qwen3-coder 14B (if Qwen releases a 14B variant of qwen3-coder) | Deferred | watch |

### Conditions to revisit

- A future DeepCoder release adds verifiable think-suppression (like Qwen3's `think: false`)
- A 14B coder from the qwen3-coder family appears on Ollama
- Hardware upgrade that makes 200s+ per generation acceptable

### Persona status after this report

All six DeepCoder personas (`my-go-deepcoder`, `my-go-deepcoder-vanilla`, `my-python-deepcoder`, `my-python-deepcoder-vanilla`, `my-mcp-deepcoder`, `my-mcp-deepcoder-vanilla`) remain registered with `status: benchmark` in registry.yaml. They are not promoted to `active`. The `deepcoder:14b` model entry in `models.yaml` is retained for reference.
<!-- /ref:deepcoder-benchmark-decision -->
