# Session 120 — oficina P2 first slice built end-to-end (T1–T8)

2026-07-15. Branch `feature/oficina-p2-loop`. An unattended session: build the FROZEN P2 plan
(T-92) start-to-finish, commit per step, run acceptance, close out.

## What shipped

The evaluated coder⇄evaluator loop — P1's single shot replaced (for `kind: function`) by
generate → evaluate → classify → repair/fresh-start → budget. Eight TDD steps, one commit each,
suite 150→223 (~64 new tests). Five new modules (`parser`, `prompt`, `workspace`, `evaluator`,
`loop`) + intake/ledger/worker/client extensions. All 6 acceptance criteria met — criterion 1
(live compile-defect repair → Delivered, zero Claude edits) and 5 (cache) verified against real
Ollama; 2/3/4/6 by the suite. Full module map + deltas: the plan's implementation-result report.

## The through-line: caching drove every layout choice, and the measurement caught us out

P2-D2's monotonic-prefix contract (stable-first, variable-last, so Ollama's implicit KV cache
reuses the prefix) shaped `SEGMENTS`, the fresh-start-keeps-prefix rule, and the rule-based
classifier (a model-swap mid-loop would evict the coder's KV). At T8 the acceptance criterion
asked to read the cache win from `prompt_eval_count` — and that number reports the **full** prompt
token count in this Ollama build, so it went *up* across iterations, not down. The cache is only
visible in `prompt_eval_duration`, which `calls.jsonl` wasn't logging. One additive field later
(Ollama already returns it), the proof was clean: **477 tokens served in 156 ms vs a cold 409
tokens in 443 ms** — a longer prompt, cheaper, because the prefix wasn't re-evaluated. Lesson
filed as a finding: measure prefix caches on duration, never token count.

## T-91 resolved as a side effect — after biting us four times

The plan flagged T-91 (sync `generate_code` truncating mid-code) a P2 prerequisite. It bit *this
session*: four of the local-model test-body delegations truncated mid-file. Root cause confirmed —
`client.chat` never set `num_predict`, so it inherited the model default. The fix (expose
`num_predict`; the loop floors/caps it) is what T6's `default_coder` needed anyway. The async
worker path never truncated — which is exactly why the plan routes the loop through the worker
seam, not the sync tool.

## Local-model delegation: honest verdicts

Test bodies for the pure/data steps (T1–T3, T5) were delegated to `my-python-q25c14`, verdicts
mostly 1 (one 2, one 0). Recurring defect: the model pushed test setup into function-signature
*default arguments* and dropped `pytest` fixture params — a structural slip fixed by hand (a 0).
The architectural steps (worktree git mechanics T4, the stateful loop T6, the worker wiring T7)
were hand-written per the local-model conventions ("not for multi-file reasoning") — which is why
the T-93 mermaid-as-context field test never fired: there was no diagram-driven *delegation*. The
`context.refs` seam is wired and live (a run spec can inject `ref:delegate-p2-loop-diagram`), so
the evidence is one real loop delegation away.

## What the fail-loud contracts bought

`category_for` raising on an uncategorizable failure caught my *own* test fixture using an
unrealistic `error_key` — the strict path surfaced a fixture that didn't match what the real
parser guarantees (`feedback_review_rederive_invariants` in action). The advisor's pre-freeze
delta-scope sharpening (subtract only *out-of-scope* baseline failures) held up: the masking-inverse
test (a misnamed target must NOT falsely Deliver) passes because target/test failures are never
subtracted.

## Open after this slice

Post-slice widening (more kinds/validators, escalation ladder P2-D9, tiny-model classifier P2-D4).
Distribution: the evaluator resolves `validate-code.py` repo-relative; the machine-global install
needs `OFICINA_VALIDATE_CODE` (T-86). Anti-cheat is defensive until multi-file deliverables exist.
T-93 awaits a diagram-driven delegation.
