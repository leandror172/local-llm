## 2026-07-24 - Session 128: T-114 edit-iteration default + T-115 refactoring-conventions promotion (PR #84)

### Context

Continued from a compacted session; entry point was the choice "T-114 / T-115" after a next-steps discussion. Docs-first ordering, local-model delegation with convention refs, and VRAM checks were all user-directed.

### What Was Done

- T-115: promoted `refactoring-conventions` to a first-class pattern-doc family (graduate-in-place) — gateway row in the master `ref:patterns-index`, Status staging→stable, `.claude/index.md` row + a code-design cross-ref updated; zero new ref-integrity errors (36==36 stashed-vs-applied).
- T-114: oficina **edit runs now default to a single iteration** (greenfield keeps 3; an explicit `budgets.iterations` always wins) — mirrors the E-D9 `num_predict` resolve-by-mode contract; +3 tests, suite 329→332.
- Core T-114 resolver + constants delegated to the local 16K coder (`my-python-q25c14-16k`) with code-design convention refs injected server-side (verdict 2, accepted as-is).
- De-staled memory: the "~3 iterations" lines in oficina QUICK + the KNOWLEDGE E-D9 sibling.
- Opened PR #84 (3 commits); branch `feature/oficina-t114-t115`.

### Decisions Made

- T-115 promotion = **graduate-in-place**: content stays in its own file (the process/shape/test-body taxonomy is why it's separate). Promotion is *earning a master-index gateway row*, not relocating content — a staged doc's tell is the ABSENCE of that row (test-executable-spec still has none; T-100 open).
- T-114 keyed on **mode** (edit→1, greenfield→3), resolved post-assembly like `num_predict` — mode isn't known at intake (decided at assembly by target-at-HEAD), so it can't be a schema default. Greenfield left at 3 (the 5/5 evidence is edit-only). The resolver is the single future home for an H2-forces-3 rule.

### Next

- Merge PR #84.
- **Axis B kinds reconsideration** — E-D8 `kind` rename + dead `acceptance.validators` removal ride one taxonomy pass.
- Triage **T-112** (input-fit guard) + **T-113** (ctx-footprint re-probe) — they protect the 16K coder defaults now used on every run.

### Gotchas

- The 16K coder's VRAM footprint is fixed by `num_ctx` pre-reserving the KV cache at load (11.25 GiB VRAM + 0.64 GiB CPU, 95/5) — it does NOT grow with how much context you send; oversized input truncates silently at 16K rather than spilling VRAM (the T-112 risk).
- The executable-spec DSL hard-codes `iterations=len(writing)`, so exercising a mode-*default* budget needed a `with_iterations=None` knob to OMIT the budget. Supply EXACTLY as many failing evals as iterations expected — `FakeEvaluate` returns `[]` (a pass) once exhausted, which would end the loop early and mask the count.
