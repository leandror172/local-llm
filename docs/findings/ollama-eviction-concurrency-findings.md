# Ollama Eviction & Concurrency: Test Findings

**Date:** 2026-03-15 (session 43)
**Branch tested on:** master (post PR #15 merge)
**Setup:** RTX 3060 12GB, WSL2, Ollama 0.17.5, two Claude Code sessions (LLM repo + expense repo)

---

## Motivation

`warm_model` (Option 1, in-process in-flight tracking) was built with the assumption that evicting
a model mid-generation from another process could corrupt or truncate output. Session 43 exposed
that this assumption was untested, and that Option 2 (file-based coordination) was on the deferred
list specifically for cross-session protection. Before building Option 2 we ran two experiments.

---

## Experiment 1: Cross-session in-flight visibility

### Setup
- Expense repo session called `generate_code` (Java, 14B model, long prompt)
- LLM repo session called `warm_model("my-go-q3")` while generation was in progress

### Result
`warm_model` evicted and loaded successfully — it did **not** detect the expense repo's
in-flight request.

### Why
Each Claude Code session spawns its own MCP server process. The `_inflight` dict in
`OllamaClient` is per-process. The expense repo session's request increments a counter
in *that* process; the LLM repo session's `warm_model` reads a different process's counter.
The single-session limitation is documented in `warm_model`'s docstring.

### Impact
Option 1 in-flight guard only works within one Claude Code session. Cross-session calls
are invisible to each other.

---

## Experiment 2: Ollama eviction-during-generation behavior

### Question
If `keep_alive: 0` is sent while a model is actively generating, does Ollama:
(a) Queue the unload until generation completes — safe
(b) Interrupt generation immediately — dangerous
(c) Ignore the unload — safe but surprising

### Test 1 — Qwen3-8B (my-classifier-q3)

```
[21:35:24] Generation started (num_predict:300, "list 50 programming languages")
[21:35:25] Fired keep_alive:0 evict (1.5s into generation)
[21:35:25] Evict returned: {"done_reason":"unload"} — instantly
[21:35:30] Generation finished: done_reason=length, eval_count=300, content=""
```

Content was empty — not an eviction effect. Caused by `think:false` being passed in
`options{}` instead of top-level (known Ollama bug: silently ignores unknown options keys).
300 tokens were Qwen3 hidden `<think>` tokens; no visible output reached before num_predict
limit. Not relevant to eviction safety question.

### Test 2 — Qwen2.5-Coder-14B (my-go-q25c14, no thinking tokens)

```
[21:40:44] Generation started (num_predict:300, "list 30 programming languages")
[21:40:46] Fired keep_alive:0 evict (2s into generation)
[21:40:46] Evict returned: {"done_reason":"unload"} — instantly
[21:41:13] Generation finished: done_reason=length, eval_count=300, content=1477 chars
```

Content preview:
> "1. **Go (Golang)** - A statically typed, compiled language known for its simplicity...
>  2. **Python** - An interpreted, high-level language known for its..."

Generation ran for **27 seconds after evict fired**, completed fully with all 300 tokens
and coherent content.

### Conclusion

**Ollama is behavior (a): it queues the unload until generation completes.**

The `keep_alive: 0` response returns non-blocking/immediately, but the model stays loaded
and continues generating until the current request finishes. This is the internal `refCount`
mechanism — the scheduler in `server/sched.go` uses reference counting and will not evict
a model with `refCount > 0`.

The threat model in `docs/ideas/ollama-coordination-layer.md` ("warm-up evicts a model
mid-generation from another session") is **not a correctness risk**. Ollama protects
its own generation. At worst, the evict is silently deferred — the caller gets an "unload"
response before eviction actually happens.

---

## Upstream: PR #9392

An open Ollama PR ([#9392](https://github.com/ollama/ollama/pull/9392)) adds an `ACTIVE`
field to `/api/ps` powered by the same internal `refCount`. If it ships:

```
NAME              SIZE      PROCESSOR    ACTIVE    UNTIL
my-go-q25c14      9.0 GB    100% GPU     Yes       4 minutes from now
```

This would allow `warm_model` to check `active: true` directly via `/api/ps` before
evicting — eliminating the need for the file-based coordination layer entirely for the
busy-check use case. The only remaining value of Option 2 would be for external callers
(bash scripts, Aider, cron) that want to register their own Ollama requests.

Related: [issue #3144](https://github.com/ollama/ollama/issues/3144) (116 upvotes) requests
a `/metrics` Prometheus endpoint including request counts.

---

## Revised Risk Assessment

| Scenario | Before tests | After tests |
|---|---|---|
| `warm_model` evicts model mid-generation from same session | Blocked by Option 1 ✓ | Same ✓ |
| `warm_model` evicts model mid-generation from another session | **Unprotected, assumed dangerous** | **Safe — Ollama queues unload** |
| Two sessions thrashing VRAM (load/evict cycles) | Performance risk | Performance risk (unchanged) |
| `SessionStart` hook warms wrong model, causes churn | Performance risk | Performance risk (unchanged) |

Correctness risks: **0** (Ollama handles them natively).
Remaining concern: VRAM thrash (performance only) in multi-session setups.

---

## Recommendation

- **Don't build Option 2 now.** The file-based layer solves a performance problem, not a
  correctness problem. Building it risks being made redundant by PR #9392.
- **Watch PR #9392.** If it lands: update `warm_model`'s `is_busy()` check to read
  `/api/ps active` field. Option 2 becomes unnecessary for the warm_model use case.
- **Trigger for Option 2:** VRAM thrash becomes an observed, measurable pain point, AND
  PR #9392 has not shipped. At that point the file-based design is ready to implement.
- **Implementation remains trivial:** swap 3 methods in `client.py` (`mark_inflight`,
  `mark_complete`, `is_busy`) from dict ops to file ops. Interface unchanged.
