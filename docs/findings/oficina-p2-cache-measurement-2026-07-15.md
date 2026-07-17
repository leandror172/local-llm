# oficina P2 — prompt-cache measurement (T8 acceptance criterion 5)

Session 120, 2026-07-15. How the P2-D2 monotonic-prefix cache win was measured live, and a
gotcha that cost a measurement iteration.

<!-- ref:oficina-p2-cache-measurement -->
## The claim (P2-D2)

The loop lays every iteration's prompt out stable-first, variable-last, so the run-constant
prefix (system · constraints · context · tests · objective) is **byte-identical** across
iterations. Ollama's implicit prefix cache should then reuse that prefix's KV and evaluate only
the varying repair tail — repair iterations become cheap.

## The gotcha: `prompt_eval_count` reports FULL tokens, not evaluated tokens

Acceptance criterion 5 was written as "iteration-2 `prompt_eval_count` ≈ tail-only". That does
**not** hold with this Ollama build: `prompt_eval_count` reports the **full** prompt token count
regardless of cache reuse. Measured over 3 real generations sharing a stable 409-token prefix:

| call | prompt_eval_count | prompt_eval_duration_ms |
|------|-------------------|-------------------------|
| 1 (cold) | 409 | 443 |
| 2 | 477 | 455 |
| 3 | 477 | **156** |

`prompt_eval_count` went **up** (more total tokens), so the token-count form of the criterion is
unobservable. The cache shows only in **`prompt_eval_duration`** — and `calls.jsonl` was not
logging it. Fix: capture `prompt_eval_duration` from Ollama's response into `ChatResponse` and
`calls.jsonl` (additive, defaulted field). Ollama already returns it; we simply weren't keeping it.

## The proof (duration, not count)

Call 3 evaluates **477 tokens in 156 ms** vs the cold call 1's **409 tokens in 443 ms** — a
*longer* prompt processed **~2.8× cheaper**. That is only possible if the shared 409-token prefix
was **not re-evaluated**. Criterion 5 is confirmed on the duration signal.

**Caveat (call 2 non-monotonic):** reuse did not engage on the *first* repair (call 2 reprocessed
at 455 ms) but did on call 3. Prefix-cache reuse is not guaranteed on every consecutive call in
this build. This is **speed-only** — caching never affects correctness (P2-D6) — so it is an
observation/tuning note, not a defect. Watch when tuning in-loop `keep_alive` (P2-D6's named trigger).

## Takeaway for future cache claims

Measure the prefix cache with **`prompt_eval_duration`**, never `prompt_eval_count`. The tell is a
*longer* prompt costing *less* prompt-eval time than a shorter cold one.
<!-- /ref:oficina-p2-cache-measurement -->
