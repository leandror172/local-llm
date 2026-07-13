# Overlay AI-merge latency — measurement & arm selection (T-81 Part 2)

**Date:** 2026-07-12
**Task:** T-81 Part 2 (`docs/plans/t81-part2-merge-completion-tuning.md`)
**Probe target:** `~/workspaces/tmp/CLAUDE.md` — a copy of this repo's real `CLAUDE.md`
(12,979 bytes / 261 lines). NEVER benchmarked against the live repo file.
**Overlay:** `session-tracking`

## TL;DR

- **Root cause was `num_ctx=4096` truncating the input**, not the model being slow.
  The merge prompt is **15,238 chars (~3,809 tokens)**; the old fixed `4096`
  context could not hold it, which is why two prior live attempts stalled 9 min
  then produced zero bytes for ~20 min (a **TIMEOUT**, not a verdict-0).
- After sizing `num_ctx` to the input (`fit_num_ctx` → **8192** for this prompt),
  **every arm completed** in single-digit-to-two-digit seconds. No timeouts.
- **Chosen default: `qwen3:14b` with `think: false`** on the priority-1
  `local-qwen3-14b` backend. It was the **fastest (17.0s)** and produced a valid,
  sane plan. Flipping `think` off is a **one-line change to `ai-backends.yaml`**,
  same model / same backend.

## Fix applied

| Where | Before | After |
|---|---|---|
| `overlays/lib/backends.py` (`OllamaApiBackend.call`) | `num_ctx = 4096 if fmt is not None else 8192` (output-sized, misleading comment) | `num_ctx = fit_num_ctx(len(prompt))` (input-sized) |
| `overlays/lib/backends.py` (socket timeout) | `urlopen(req, timeout=30)` | config-driven `read_timeout_s` (default **120s**) |
| `overlays/lib/backends.py` (overall bound) | none | wall-clock deadline `merge_timeout_s` (default **600s**) → returns `None` on exceed |
| `overlays/test-merge-plan.py:42` | `"num_ctx": 4096` (hardcoded) | `fit_num_ctx(len(prompt))` (matches production) |
| `overlays/ai-backends.yaml` (`local-qwen3-14b`) | `think: true` | `think: false` |

### `fit_num_ctx` chosen headroom

`fit_num_ctx(prompt_chars, output_headroom_tokens=1024)` returns the smallest of
`(4096, 8192, 16384, 32768)` that holds `prompt_chars//4 + headroom`, capped at
the probed 14B ceiling (32768, `ref:model-selection`).

- **Chosen headroom = 1024 tokens.** Valid because the winning arm is
  **non-thinking** — the only output is the small plan JSON. The headroom caveat
  (thinking arms also consume context, so 1024 is too small for them) is **moot**
  here because we selected the non-thinking arm. For this probe:
  `15238//4 + 1024 = 4833` → **8192** bucket. (Old `4096` overflowed by ~700 tokens
  before counting any output — the direct cause of the stall.)

## Measurement — arm table (probe: 15,238-char prompt, num_ctx=8192 for all)

| Arm | think | wall time | valid plan? | placement quality |
|---|---|---|---|---|
| **qwen3:14b** | **off** | **17.0s** | **yes** | insert_after_line=11 (auto-corrected out of the overlay block by `_correct_insert_line`); no deletes — **sane** |
| qwen2.5-coder:14b | off (n/a) | 68.3s | yes | insert_after_line=0 (very top); no deletes — valid but **weak** placement |
| qwen3:8b | off | 77.5s | yes | insert_after_line=13, delete 1–13 (correctly detected the duplicated "Resuming" section) — **best delete quality**, but slow |
| qwen3:14b | **on** | 86.9s | marginal | insert_after_line=**-1** (**invalid** line), delete 6–12 |
| deepseek-r1:14b | always | 119.6s | marginal | insert_after_line=4; no deletes; reasoning waffled ("already present…") |

`qwen3:30b-a3b+think` was intentionally skipped: serial VRAM ceiling (12 GB) makes
it many minutes for zero decision value once a 17s winner exists.

### Before vs after (the honest "does it finish now" proof)

| | num_ctx | outcome | wall time |
|---|---|---|---|
| **Before** (2 prior live attempts, plan §1) | 4096 | **stalled / 0 bytes** | 9 min, then ~20 min killed |
| **After** (this run, chosen arm) | 8192 | **valid plan returned** | **17.0s** |

## Decision & rationale

1. **`num_ctx` sizing is the real fix.** Every arm — even the thinking ones —
   completed once the input fit the context window. The prior "20-min zero bytes"
   was `4096` truncation, not model slowness.
2. **Arm = `qwen3:14b` no-think (RC2).** Head-to-head on the *same model*: thinking
   cost **5.1×** wall time (86.9s vs 17.0s) **and** produced a worse plan
   (`insert_after_line: -1`, invalid). Placement here is mechanical; reasoning
   traces add latency with no quality gain.
3. **Smallest config change: flip `think` on the existing priority-1 backend.**
   `local-qwen3-14b` is already priority-1 (the default merge backend). Flipping
   its `think: true → false` needs no reorder and no model swap. Every backend in
   `ai-backends.yaml` serves overlay merge ops only (per the file header), so the
   flip cannot affect other overlay AI operations — no merge-specific preference
   thread was needed. `qwen2.5-coder:14b` was **not** adopted: it is not a
   configured backend, is 4× slower than the winner, and placed worse (line 0).

## Production-chain acceptance (the edited code, not the diagnostic)

`test-merge-plan.py` has its *own* `call_ollama` — it does **not** run
`OllamaApiBackend.call`, read `ai-backends.yaml`, or apply
`_correct_insert_line`/`apply_plan`. So the arm table above proves the *models*
behave, but not the *shipped chain*. This run closes that gap.

**Vehicle:** Part 1's `--stage` on a markerless 11.8 KB target (the real
`CLAUDE.md` with its existing `session-tracking` block stripped, forcing a fresh
merge):

```
install-overlay.py session-tracking --target ~/workspaces/tmp/t81-accept \
    --install-level project --mode ai --stage --backend auto --yes
```

This exercises the **actual production path**: `OllamaApiBackend.call`
(→ `fit_num_ctx`) + `ai-backends.yaml` `think:false` (auto-selected the
priority-1 `local-qwen3-14b`) + `_correct_insert_line` + `apply_plan` + diff +
staged plan handle.

**Result:** valid plan, **completed in 4.16s total wall-clock** (process start +
warm model call), no timeout.
- `insert_after_line` landed on a real section boundary (line 10–15 across runs;
  non-deterministic but always a clean heading boundary, never mid-block).
- The staged diff inserts the section wrapped in correct
  `<!-- overlay:session-tracking v11 -->` / `<!-- /overlay:session-tracking -->`
  markers — clean, no duplication.
- Expected `WARN` ("removed nothing") because the prior block was stripped, so
  there is genuinely no superseded content to delete.

### Known limitation of the fast (no-think) arm — duplicate detection

On an **already-installed** target (marker present) the installer SKIPs, so this
never arises in practice. But when merging into a file that contains an *unmarked*
older copy of the section, the fast arm (`qwen3:14b` no-think) proposed **zero
deletes**, whereas `qwen3:8b` and `qwen3:14b+think` both detected and deleted the
duplicate (see arm table). The planner already emits a `WARN` on no-delete plans
("verify no superseded content remains"), and Part 1's `--stage` shows the diff
before any write — so the safety net is the human reviewing the staged diff, not
the model. This does **not** overturn the `think:false` decision (5.1× speed +
smallest-change still win); it is recorded as a known trade-off.

## Chunking (§3.4) — NOT triggered, NOT built

The §3.4 chunking trigger is: *"3.1–3.3 measured, and no arm returns a valid plan
on the ~12 KB target under `--merge-timeout`."* **Not met** — the chosen arm
returns a valid plan in **17.0s**, three arms returned valid plans, and none timed
out. Chunking remains correctly deferred; do not build it.

## Open risk

- The 12 KB / ~3.8K-token probe lands in the **8192** bucket. A materially larger
  target (>~28 KB prompt) would size to 16384/32768 — still within the 32768 14B
  ceiling, but wall time on those buckets is unmeasured. The `merge_timeout_s`
  (600s) deadline degrades such a case safely to "add manually" (returns `None`).
