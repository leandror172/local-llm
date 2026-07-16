# Session Log

**Current Layer:** Layer 5 — Expense Classifier (side-track: oficina P2 evaluated-loop FIRST SLICE BUILT + ACCEPTED (T-92, T1–T8, branch `feature/oficina-p2-loop`, PR #76); T-91 resolved within; next = post-slice widening)
**Current Session:** 2026-07-15 — Session 120: oficina P2 evaluated-loop first slice BUILT + ACCEPTED (T1–T8, PR #76) — T-91 resolved

---
## 2026-07-15 - Session 120: oficina P2 evaluated-loop first slice BUILT + ACCEPTED (T1–T8, PR #76) — T-91 resolved

### Context

Unattended build session: execute the FROZEN P2 plan (T-92) end-to-end, commit per TDD step, run live acceptance, close out. Test bodies for pure/data steps delegated to `my-python-q25c14`; architectural steps (git worktree, the loop, worker wiring) hand-written per the local-model conventions.

### What Was Done

- **Built oficina P2 first slice T1–T8** on `feature/oficina-p2-loop` (one commit each); suite 150→223 (~64 new tests). Five new modules in `mcp-server/src/ollama_mcp/oficina/`: `parser.py` (T1), `prompt.py` (T2), `workspace.py` (T4), `evaluator.py` (T5), `loop.py` (T6); intake/ledger/worker/client extended (T3/T7).
- **T-91 RESOLVED** (was a P2 prereq): `client.chat` had no `num_predict` → inherited the model default and truncated mid-code. Added the param; the loop's `default_coder` floors/caps at 2048. Reproduced live 4× this session as sync-truncation during test-body delegation.
- **T8 live acceptance — all 6 criteria met** (real Ollama + real git repo): a seeded compile defect was caught (iter1 mechanical/verdict 0) and repaired by the model (iter2 verdict 2) → Delivered, zero Claude edits. Criteria 2/3/4/6 by the suite.
- **Cache measurement gap found + closed:** `prompt_eval_count` reports FULL tokens in this Ollama build, so criterion 5 is only observable on `prompt_eval_duration` — now logged in `ChatResponse`+`calls.jsonl`. Proof: 477 tok @ 156ms vs cold 409 tok @ 443ms. Finding `ref:oficina-p2-cache-measurement`.
- **Close-out:** 6 loop events promoted to frozen-P2 in `event-model.md`; plan gained an implementation-result report; README + index updated; postmortem `docs/reports/session-120-report.md`; new reference memory (prefix-cache measurement). PR #76 opened.

### Decisions Made

- **`EvaluateFn` seam gained `base_repo`** (T4→T5): evaluation needs the repo→worktree target mapping; refined mid-build.
- **The loop emits iteration events + `Exhausted` but NOT `Delivered`** — terminal `Delivered`/packaging stays the worker's job (T7), matching P1's freeze.
- **Anti-cheat is defensive in the first slice** (loop writes only the target) — branch covered by a contrived test; realistic firing needs multi-file deliverables.
- **`validate-code.py` resolved repo-relative** (`parents[4]`); the machine-global install will need `OFICINA_VALIDATE_CODE` (folded into T-86).

### Next

- **Post-slice widening (per P2-D1):** more kinds/validators, the escalation ladder (P2-D9), the tiny-model classifier (P2-D4 — must batch OUTSIDE the coder loop or it evicts the coder KV).
- **Merge PR #76**, then the distribution fix (T-86: `OFICINA_VALIDATE_CODE` + the 3-step runbook + T-89 hook re-wiring).
- **T-93** mermaid-as-context: the `context.refs` seam is LIVE (a run spec injects a diagram anchor) but no measured verdict — P2 code was hand-written, so no diagram-driven delegation fired. One real loop delegation injecting `ref:delegate-p2-loop-diagram` would produce the evidence.

### Gotchas

- **Measure prefix caches on `prompt_eval_duration`, NEVER `prompt_eval_count`** (reports full tokens). Cache reuse is also non-monotonic — it skipped the first repair then engaged on the next; caching is speed-only, never correctness (P2-D6).
- **`category_for` is fail-loud** and caught my own test fixture using an unrealistic `error_key` — a test-stage failure must carry a `pytest-error:`/`pytest-failed:` prefix (what the real parser guarantees).
- **Tests-as-context makes the coder converge on iter1** when the pre-authored tests fully specify behavior (observed live: a ValueError edge case the terse objective omitted was still satisfied because the test sat in the stable prefix) — good product behavior, but it means a natural 2-iteration cache run needs a task the tests underspecify.
- The `oficina-run-<id>` branch is left in the target repo after teardown (it IS the deliverable, S15); teardown removes only the worktree + prunes.
