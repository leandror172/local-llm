## 2026-07-15 - Session 119: oficina P2 evaluated-loop plan FROZEN (T-92) — caching-first design, advisor-reviewed; T-93 filed

### Context

Session opened on "discuss next steps" after resume. Chose **oficina P2** (the evaluated deliverable loop) as the next work, then whiteboarded and froze its plan rather than starting to build.

### What Was Done

- **Froze the oficina P2 plan** `docs/plans/oficina-p2-evaluated-loop.md` (P2-D1–D13 + run spec + individually-anchored state/loop Mermaid diagrams + 6-event promotion + acceptance + T1–T8 build steps); filed **T-92**; committed `c24281c`.
- **T-93 filed** (Mermaid diagrams as local-model coding context) + committed the cross-session **draft-ready** note (`eee21ca`) — an LTG session had already authored the section (parked at `overlays/ollama-scaffolding/drafts/diagrams-as-behavior-specs.md`) with measured evidence.
- Ran a freeze-review pass (fixed 3 consistency defects) and a post-freeze **advisor pass** (fixed 1 blocking correctness hole + 2 first-slice gaps); verified ref-anchoring clean (6 balanced blocks, matches the P1 precedent).

### Decisions Made

- **Caching drove the whole design.** Ollama exposes *implicit prefix reuse only* (no cache API, `ref:ollama-explicit-cache-api`) → monotonic stable-prefix prompt layout (P2-D2) in one swappable `SEGMENTS` tuple + ordering-guard test (P2-D3); in-loop classifier stays **rule-based** because a per-iteration model swap would evict the coder KV (P2-D4, reinforces S10); per-run reused worktree serves toolchain caches **and** S16 delta-scope (P2-D5).
- **First slice = `function`-against-pre-authored-tests**, Python validator only, 3-iter, no escalation (P2-D1). Layer-4 `validate-code.py` IS the Phase-1 evaluator; rubric judge is P4.
- **Failure category = which eval stage failed** via one shared `parse_validator_output → ParsedFailure{stage, file, error_key, raw}` (P2-D8); repetition signature = sorted normalized `error_key` set over the delta-scoped failure (P2-D7); diversity-not-size escalation, swap-once-at-exhaustion (P2-D9); `input_required` declared-but-unreachable in P2 (P2-D11).
- **Diagrams get their own ref anchors** (`ref:delegate-p2-state-diagram`/`-loop-diagram`) so `context.refs` can inject one diagram → the mechanism behind T-93.
- **Documentation lifecycle:** post-impl the diagrams/events go FINAL in the vision folder; the plan then reports the implementation result and points to them.

### Next

- **Build oficina P2 (T-92)** starting at **T1** (`parse_validator_output` — three readers depend on it), then T2–T8. **T-91 is a prerequisite** (P2-D10 needs `num_predict` floored/capped on the loop generator).
- **G-D4** gate-vs-P2 priority still open (T-90 showed contention not thrash → mild lean to gate-after-P2).
- Side options unchanged: T-86 distribution runbook, T-83 freeze, T-56, classifier benchmark, persona hygiene.

### Gotchas

- **Advisor caught a silent correctness hole:** blanket delta-scope `current − baseline` would subtract the target-absent `error_key` (`C0` lacks the target symbol) — the exact signature a misnamed/absent target produces → loop declares success on broken code. Fixed to subtract **only out-of-scope** failures; `ParsedFailure` gained `.file` (P2-D12). Acceptance criterion 3 now tests the masking inverse.
- Python `py_compile` catches only *syntax*; undefined-name/import defects surface at the test stage → read pytest ERROR(→mechanical)/FAILED(→structural) inside the test stage (P2-D8).
- Worktree teardown must `git worktree prune` the target on BOTH normal teardown and TTL retention, else dangling `.git/worktrees/<id>` entries accumulate.
- The repo's ref-integrity checker reports vision/plan blocks as "orphaned" — that is the intended reference-on-demand state (looked up via `ref-lookup.sh`, not inline `[ref:KEY]`); the P1 blocks show identically.
