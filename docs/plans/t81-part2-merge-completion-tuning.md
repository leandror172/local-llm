# T-81 Part 2 — AI-merge completion: make the model finish

**Status:** PLAN (ready to build). Owner task: **T-81** (part 2 of 2).
**Implementer:** Sonnet subagent, high effort. This plan has a **live-measurement** step (runs the local model), unlike Part 1.
**Sibling plan:** `docs/plans/t81-part1-merge-preview-stage-apply.md` (independent). Part 2 makes real merges actually complete; Part 1 makes them previewable. They compose but neither blocks the other.
**No oficina.** Attack latency directly (context window, arm choice, timeout) rather than moving the call to an async substrate — install-overlay is a one-shot CLI, so detached execution buys it nothing (user decision, 2026-07-12).

---

## 1. Problem (T-81 defect **b**)

Two live attempts to AI-merge the overlay section into llm's own `CLAUDE.md` (12.4 KB) failed: a 9-minute stall, then ~20 minutes producing **zero collected bytes** before being killed. Per `ref:local-model-conventions` that is a **TIMEOUT, not a verdict 0** — the model never got to be wrong. This plan makes the merge complete.

## 2. Root causes (verified in `overlays/lib/backends.py`, re-derive before trusting)

**RC1 — context window too small for the input (primary suspect).** `OllamaApiBackend.call` (`backends.py:63-109`) sets:
```python
num_ctx = 4096 if fmt is not None else 8192
# comment: "Planner output is small JSON — 4096 ctx is sufficient. Full-file merges need 8192 minimum."
```
The primary merge backend `local-qwen3-14b` uses `schema_mode: format_param` → `fmt is not None` → **`num_ctx = 4096`**. But the *input* (full 12.4 KB file ≈ 3.5-4K tokens + the `merge-plan.txt` template + the section to insert) **overflows 4096**. The defending comment reasons about *output* size ("planner output is small JSON") while the failure is *input* truncation — a textbook **special-case defect marker** (`feedback_special_case_comments`): the comment was written at the moment of the accident and has survived every reading since. `test-merge-plan.py:42` hardcodes the same `"num_ctx": 4096` bug, so the diagnostic understates the real context need.

**RC2 — thinking-mode latency.** `local-qwen3-14b` sets `think: true`. On a mechanical placement task, qwen3:14b can emit very long reasoning traces; these stream in a `thinking` field the loop does **not** collect (`backends.py:102` appends only `message.content`), so `chunks` stays empty for the whole think phase → the reported "zero bytes for 20 min". A non-thinking arm, or `think:false`, likely removes most of the wall time.

**RC3 — tight socket read timeout.** `urllib.request.urlopen(req, timeout=30)` (`backends.py:97`) is a **per-read** socket timeout. During a long silent phase (cold model load; a think burst with no `content` chunks) 30 s of silence raises. Streaming normally sends data often enough, but cold-start + heavy-think is exactly the risky window.

## 3. Fixes

### 3.1 — Size `num_ctx` to the actual prompt (RC1; the likely real fix)

Replace the fixed constant in `OllamaApiBackend.call` with a computed fit. Add a pure helper (named, testable):
```python
_CTX_BUCKETS = (4096, 8192, 16384, 32768)   # 32768 = probed 14B ceiling w/ q8_0 KV (ref:model-selection)

def fit_num_ctx(prompt_chars: int, output_headroom_tokens: int = 1024) -> int:
    """Smallest ctx bucket that holds the prompt (~chars/4 tokens) plus output headroom, capped at the 14B ceiling."""
    need = (prompt_chars // 4) + output_headroom_tokens
    for b in _CTX_BUCKETS:
        if b >= need:
            return b
    return _CTX_BUCKETS[-1]
```
Call it as `num_ctx = fit_num_ctx(len(prompt))`. **Delete the misleading comment** and replace with one that names the real constraint (input size, not output). The chars/4 heuristic is this repo's own diagnostic (`memory/debugging.md`); 32768 is the probed 14B ceiling (`ref:model-selection`) — do not exceed it (VRAM).

**Headroom caveat (advisor):** `output_headroom_tokens=1024` assumes the *plan JSON* is the only output. If a **thinking** arm survives the 3.2 measurement, its reasoning tokens also consume the context window — 1024 is then far too small and the merge can still overflow. Two mitigations, in order: (a) the fast **non-thinking** arm from 3.2 makes this moot (another reason 3.2 should land there); (b) if a thinking arm must be kept, raise headroom to cover thinking (e.g. 4096-8192) and record the chosen value + why in the findings doc. Do not silently keep 1024 with a thinking arm.

Apply the **same fix to `test-merge-plan.py:42`** so the diagnostic reflects production behavior.

### 3.2 — Pick the merge arm empirically (RC2; the measurement step)

Do not guess the arm — measure. `overlays/test-merge-plan.py` already benchmarks arms across models (it's the sanctioned manual diagnostic; excluded from the automated suite per `ref:overlay-test-convention`). After 3.1:

1. Copy a real ~12 KB target (e.g. this repo's `CLAUDE.md`) to `~/workspaces/tmp/` (`feedback_use_workspaces_tmp`).
2. Run `overlays/test-merge-plan.py --target-file ~/workspaces/tmp/CLAUDE.md --overlay session-tracking` (its default model list already spans the candidates: `qwen2.5-coder:14b`, `qwen3:8b(+think)`, `qwen3:14b(+think)`, `deepseek-r1:14b`).
3. Record per arm: wall time, whether a **valid** plan returned (`insert_after_line` sane, JSON parses), and plan quality (placement + any deletes). Local-first / measure, don't assume (`feedback_ollama_workflow`). If an arm times out, that's a TIMEOUT not a verdict — retry once after a brief wait (prompt cache warms the retry; `feedback_ollama_timeout_cache_retry`).
4. Write findings to **`docs/findings/overlay-merge-latency-2026-07-12.md`**: the table, the chosen arm, and the num_ctx each arm actually needed.
5. Set the default: if `qwen2.5-coder:14b` (no-think, format_param-capable) produces valid plans materially faster than `qwen3:14b+think` — the likely outcome — make it the **priority-1 merge backend**, either by reordering `overlays/ai-backends.yaml` or by giving the merge path a think override. Prefer the smallest config change that expresses "merges use the fast arm"; if reordering `ai-backends.yaml` would affect *other* overlay AI operations, instead thread a merge-specific backend preference rather than changing the global default (state which you did and why in the findings doc).

### 3.3 — Robust timeout + honest failure (RC3)

- Raise the per-read socket timeout from `30` to a config-driven value (default ~120 s) so cold-start + think bursts don't false-trip.
- Add an **overall wall-clock deadline** for the merge call (default generous, e.g. 600 s, config/flag `--merge-timeout`): if exceeded, abort with an explicit `TIMEOUT` message and return `None` — never record it as a quality failure (a timeout has no DPO triple; `feedback_ollama_timeout_cache_retry`). The caller already treats `None` as "add manually" (`planner.py`), so this degrades safely.
- Keep collecting only `message.content`, but if you want progress visibility, count `thinking` chunks too and log a heartbeat under `--debug` (optional, low priority).

### 3.4 — Chunking (DEFERRED — document, do not build)

If, *after* 3.1-3.3, a real 12 KB merge still cannot complete on any arm in acceptable wall time, the next lever is to stop sending the whole file: have the model choose placement relative to a **landmark** (e.g. "insert after the heading matching X"), then resolve the landmark to a line number deterministically — so only headings/structure reach the model, not the full body. This is a **contract change** to the merge planner (today it emits file-global line numbers over the whole file) and is out of scope. **Record the trigger explicitly** (`feedback_special_case_comments` corollary — a guessed trigger fires on the wrong event, so state the real one): *"3.1-3.3 measured, and no arm returns a valid plan on the ~12 KB target under `--merge-timeout`."* Do not pre-build it; 3.1 alone may make the full-file merge fit.

## 4. TDD (hermetic unit tests + one live measurement)

Automated, hermetic, no network — add to the existing installer suite (extend `overlays/test_verify.py`'s sibling set or add `overlays/test_backends.py`; wire into `overlays/scripts/test-installer.sh` per `ref:overlay-test-convention`). The `fit_num_ctx` helper is a **pure function** — ideal unit target:

| Test | Proves |
|---|---|
| `test_fit_num_ctx_small_prompt_uses_smallest_bucket` | ~500-char prompt → 4096 |
| `test_fit_num_ctx_four_k_token_input_grows` | ~16 KB prompt (the CLAUDE.md class) → 16384 (not 4096) — the RC1 regression guard |
| `test_fit_num_ctx_caps_at_ceiling` | enormous prompt → 32768, never higher |
| `test_call_computes_ctx_from_prompt_not_constant` | with a `FakeOllama` (mock `urllib`/the POST) capture the payload and assert `options.num_ctx == fit_num_ctx(len(prompt))`, **independent of `fmt`** — kills the `4096 if fmt` branch |
| `test_call_returns_none_on_wall_clock_deadline` | inject a slow/stub responder past the deadline → returns `None`, no exception, no partial write |

Delegate test bodies to the local model per `feedback_delegate_test_writing` (scaffold named empty tests + contract docstring; `generate_code` with the scaffold + `backends.py` as `context_files`; local-first per `feedback_ollama_workflow`). Overlay tests are **plain sync pytest** — no asyncio config applies here (that note is mcp-server-only).

The arm-selection + real-latency proof is **not** a unit test (needs a live GPU) — it lives in the findings doc from 3.2 and the live acceptance below.

## 5. Acceptance (live — the honest "does it finish now" proof)

On a `~/workspaces/tmp/` copy of a real ~12 KB target (not the repo's live file):
1. With the num_ctx fix + chosen arm, an AI merge (via Part 1's `--mode ai --dry-run` stage, or `test-merge-plan.py`) **returns a valid plan** — measure and record the wall time (target: single-digit minutes, ideally < ~2 min on the fast arm).
2. The staged plan's `insert_after_line` is sane (inside the file, not mid-overlay-block) and any `delete_ranges` are justified.
3. `docs/findings/overlay-merge-latency-2026-07-12.md` records the before (4096, timed out) vs after (fitted ctx, arm, wall time) with the chars/token measurements.
4. If it still times out on every arm → **stop, do not build chunking silently**; report the measurement and surface the 3.4 trigger to the user.

## 6. Out of scope

- Preview / stage→apply split — that is **Part 1**.
- oficina / async transport (user decision).
- Chunking (3.4) — deferred with a recorded trigger.
- General EOL rework (T-29).

## 7. Definition of done (verify, don't claim — `feedback_verify_done_claims`)

**You OWN (edit directly):** `backends.py`, `test-merge-plan.py`, the new tests, and the **new findings doc** (`docs/findings/overlay-merge-latency-2026-07-12.md` — yours to create).

**You PROPOSE (in your final report — do NOT edit; the parent applies):** all edits to shared tracking / memory / README files. Matches the user's "output = suggestions for updating memories/README" instruction and avoids write-conflicts.

- [ ] `backends.py` num_ctx is computed via `fit_num_ctx`; the misleading comment is gone; `test-merge-plan.py:42` fixed too.
- [ ] `make -C overlays test` green including the new num_ctx/timeout tests (paste the count).
- [ ] `docs/findings/overlay-merge-latency-2026-07-12.md` created with the arm table + before/after wall times + chosen headroom.
- [ ] Live acceptance: a real ~12 KB merge returns a valid plan; paste the arm + wall time (or, if all arms fail, the measurement + the 3.4 trigger — do NOT build chunking).
- [ ] **Report proposes** (with exact text/anchor): `.claude/index.md` rows for the findings doc + this plan; `.claude/tasks.md` T-81 part-2 checkoff (+ close T-81 if both parts done); a candidate memory capturing the num_ctx defect-marker lesson (input vs output sizing).
- [ ] Report each item with its artifact. You MAY call `advisor` before declaring done.
