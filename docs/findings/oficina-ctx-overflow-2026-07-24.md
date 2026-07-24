# oficina — the 16K coder's context budget is already spent (T-112 evidence)

Session 129, 2026-07-24. Scoping T-112 (input-fit guard) against `calls.jsonl` and the oficina
run store. A session-127 production edit run **crossed its context window live**; a tempting
causal story built on top of that crossing is **refuted** by the same data and recorded here so
it is not re-derived.

<!-- ref:oficina-ctx-overflow -->
## The crossing

Run `bIbxrIOo69Ty1fafoxPiAw` — the s127 `_parse_go_build` dogfood: `kind: function` at a
committed target (an **edit** run) on `my-python-q25c14-16k`, `num_ctx = 16384`.

| iter | prompt tok | output tok | total | ms/tok |
|------|-----------:|-----------:|------:|-------:|
| 1 | 10,387 | 2,974 | 13,361 | 1.13 |
| 2 | **13,451** | **2,974** | **16,425** ⚠ | 1.21 |
| 3 | 10,387 | 2,996 | 13,383 | 1.14 |

**Iteration 2 totalled 16,425 tokens against a 16,384 ceiling — over by 41.**

### That crossing is verified, the eviction target is not

A 41-token margin is 0.25%, and `prompt_eval_count + eval_count` is only meaningful here if that
sum is the quantity `num_ctx` actually bounds. Two readings were possible: **(a)** the sum may
legitimately exceed `num_ctx` because a context shift discarded old tokens — a real crossing; or
**(b)** the sum is not what `num_ctx` bounds, and nothing crossed. A synthetic probe against the
same persona discriminates them, because under (b) an over-ceiling sum is unobservable:

```
prompt_eval_count 16,275   eval_count 850   SUM 17,125  >  16,384   done_reason: stop
```

**(a) holds.** Generation ran 741 tokens past the window and stopped *naturally* — not at a
length cap — which is only possible if KV entries were discarded to make room. The 16,425
observation is a genuine crossing.

Two refinements the probe also settles:

- **Input is not truncated.** All 16,275 prompt tokens were evaluated. The failure mode is
  eviction *during generation*, not a silently shortened prompt.
- **Which tokens are evicted is UNVERIFIED.** Sliding-window eviction drops the oldest entries,
  which would be the head — where `system` and `constraints` live (`prompt.py:42-43`) — but
  `num_keep` exists precisely to pin the head, and `/api/show` returns **no `num_keep`** for this
  persona, so it sits at Ollama's default. Whether that default protects the system prompt under
  a chat template is untested. Do not cite the head-eviction mechanism as established.

`ref:ollama-kv-prefix-cache` considered this case and dismissed it: *"Prompt + context files +
output rarely exceeds ~5K tokens — well under 32K. Sliding-window eviction does not occur."*
Every premise has since inverted — **32K → 16K** (the s127 persona default) and **~5K → 16.4K**.
The finding named its own re-evaluation trigger and the trigger fired unobserved.

## Why it is structural, not a fluke

E-D9 sizes edit-mode `num_predict` to the input file: `min(8192, max(2048, ceil(chars/4) × 2))`.
`current_file` is also a **stable prompt segment** (`prompt.py:48`). So a large file inflates the
prompt *and* the output reservation **from the same input** — the two budgets are positively
correlated by design and negatively correlated by resource.

For this run, `parser.py` derives `num_predict ≈ 7,000` (14,867 chars today → 7,434; it was
smaller before the run added the function). Against the 16,384 ceiling:

```
iteration 1:  prompt 10,387  +  num_predict ~7,000  =  ~17,400   >  16,384
```

**Iteration 1 was already over budget** by the reservation that matters — it simply happened to
generate less than it was allowed. The observed crossing at iteration 2 is the same defect with
the variable segments added, not a separate one.

## What it does NOT explain — refuted

The tempting story — *overflow evicts the constraints, so retries repeat themselves* — fits this
run (it hit `FreshStart(reason: repetition)` at iteration 2 and ended `Exhausted`) and is
**wrong**. Every multi-iteration run in the store exhausts identically regardless of size:

| run | persona | peak total | prefix cache | outcome |
|-----|---------|-----------:|--------------|---------|
| `bIbxrIOo` | 16K | 16,425 ⚠ | NO REUSE | Exhausted, 1 fresh start |
| `CSvOx59u` | 16K | 13,872 | REUSED | Exhausted, 1 fresh start |
| `h7TPc5Zq` | 16K | 11,887 | REUSED | Exhausted, 1 fresh start |
| `38FnT5m9` | 16K | 12,604 | NO REUSE | Exhausted, 1 fresh start |
| `IxE669Wx27` | **32K** | **~1,150** | REUSED | Exhausted, 1 fresh start |

`IxE669Wx27` settles it: ~600-token prompts on a 32K-context persona, three orders of magnitude
of headroom, and it still exhausts with a repetition-driven fresh start. **Context overflow is
not the mechanism behind the s127 "retries never see their own residual" observation** that
justified T-114 — that phenomenon is independent and still unexplained.

Two further correlations fail the same way and should not be leaned on:

- **Overflow ↔ no-reuse:** `38FnT5m9` lost prefix reuse without ever crossing the ceiling, so
  overflow is not *necessary* for a NO-REUSE verdict. Whether it is *sufficient* rests on n=1.
  GPU contention evicting the model between calls is an untested alternative (s127 had a
  concurrent session — T-102 territory).
- **Overflow ↔ the 4-for-4 docstring deletions (E-D6):** `h7TPc5Zq` and `CSvOx59u` both stayed
  under the ceiling. E-D6 is systematic for some other reason.

## Method note

`prompt_eval_count` is the right signal *here* even though `ref:oficina-p2-cache-measurement`
forbids it for cache claims. The two questions differ: cache reuse needs
`prompt_eval_duration` (count reports full tokens regardless of reuse) — but "did this call fit
in the window?" is exactly a **full-token** question, so the same field that lies about caching
tells the truth about occupancy.
<!-- /ref:oficina-ctx-overflow -->

<!-- ref:oficina-ctx-overflow-guard -->
## What this settles for T-112

**The guard's predicate is `prompt_tokens + num_predict ≤ num_ctx`, not prompt size alone.** The
crossing run's *prompt* fit comfortably (13,451 of 16,384); only the reservation pushed it over.
A prompt-only check would have passed every iteration of the only run known to have overflowed.

**D3 is settled: fail loud, do not downshift.** Downshifting `num_predict` to the remaining room
would have left iteration 2 with `16,384 − 13,451 = 2,933` tokens to re-emit a file whose prior
iterations needed ~2,980 — converting an overflow into precisely the mid-file output truncation
that E-D9 exists to prevent. Trading silent head eviction for silent output truncation is not a
fix.

**A second, separate lever: drop `previous_attempt` on edit runs.** What pushed iteration 2 from
10,387 to 13,451 is the variable segments, and on an edit run `previous_attempt` is whole-file
sized (`loop.py:249,278` — it is `gen.content`, the last generation). Suppressing it keeps this
run at ~10,400, under the ceiling.

**This is a behaviour change, not redundancy removal — do not conflate them.** `current_file` is
the *committed* content, fixed at assembly and stable across iterations (`prompt.py:48`);
`previous_attempt` is the *last failed generation*. Same size, different content — baseline vs
attempt. The case for dropping it is empirical, not structural: s127 recorded that retries never
saw their own residual defect (5/5), so `previous_attempt` demonstrably was not helping. Make
that argument explicitly on its own evidence; it is cheap mechanically (`build_prompt` already
skips blank parts, and the segment is `stable: False`, so the P2-D2 prefix is untouched), but it
is a repair-loop change and wants its own decision.

**Exposure was already reduced, incidentally.** T-114 (s128) defaults edit runs to **one**
iteration, and every observed crossing lives at iteration 2. The paths still exposed are
greenfield (3 iterations), an explicit `budgets.iterations`, and — per the arithmetic above — a
single large edit iteration 1, which fails the predicate on its own. T-114 was decided purely on
loop economics; that reasoning would not protect a future change that restores iteration 2 for
edit runs.

**D1 (where `num_ctx` comes from) — `/api/show` answers it without firing T-76.** Verified live:
`/api/show` on `my-python-q25c14-16k` returns both the persona's effective `num_ctx` (16384, from
the Modelfile PARAMETER) and the base model's architectural max (`qwen2.context_length: 32768`).
No repo path, so T-96's `LLM_REPO_ROOT` removal and T-86's machine-global stance both hold, and
oficina never becomes a consumer of the registry *shape* — leaving
`ref:model-registry-library-decision`'s trigger 3 unfired and its deferral cheap. The alternative
— reading `personas/registry.yaml` — records **intent**, where Ollama records **reality**;
**T-113 exists because exactly that gap opened elsewhere** (`models.yaml` says 9,498 MiB,
`/api/ps` measures 14.2 GiB). Open sub-question: what a guard does when the ceiling is
undeterminable, since fail-open on a guard forfeits its purpose.
<!-- /ref:oficina-ctx-overflow-guard -->

## Reproducing

```bash
python3 .claude/tools/ollama-cache-report.py          # per-run prefix-reuse verdicts
# occupancy: sum prompt_eval_count + eval_count per run_id in
# ~/.local/share/ollama-bridge/calls.jsonl, compare against the persona's num_ctx
rtk proxy curl -s http://localhost:11435/api/show -d '{"model":"my-python-q25c14-16k"}'
```

**The boundary probe** (does the sum exceed `num_ctx`?): one `/api/chat` call carrying ~69,000
chars of filler (→ 16,275 prompt tokens) plus a "reproduce this module verbatim" task sized to
~850 output tokens, `num_predict: 2048`. Two design notes, both learned by failing first — the
task must be one the model **cannot shortcut** (asked to print 1–2000 it emitted a `for` loop;
asked for a 1500-word essay it stopped at 118 tokens), and forcing thousands of output tokens
times out under CPU offload, so **make the prompt large and the required output small**. Check
`/api/ps` first: this run was at 23% offload (T-90/T-102 contention), which is what timed out the
earlier attempts.
