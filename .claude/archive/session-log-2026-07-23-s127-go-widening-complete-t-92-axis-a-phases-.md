## 2026-07-23 - Session 127: "Go widening complete (T-92 Axis A, Phases 2–5) — LanguagePack + 16K coder defaults; PR #83"

### Context

Resumed post-merge of PR #82 (edit mode) with the register naming "Axis A Go read-side" as next. The Go-widening plan was amended to current state first (A1–A4: post-T-110 deltas, `-json` imposed, `_parse_gotest` dogfood as an edit run), then the user green-lit Phases 2+3 and later extended to "the next 3 phases" — the whole of Axis A landed in one session.

### What Was Done

- **T-92 Axis A COMPLETE, Phases 2–5, suite 298→329, PR #83 OPEN** (`feature/oficina-p2-go`, 30 commits)
- Phase 2: language-derived compile `error_key` prefix (`_ERROR_KEY_PREFIX`; R1 identifiers in, pinned `py-` spelling out) — built by the first-ever production edit run on `parser.py`
- Phase 3 (duplicated-on-purpose): `_parse_go_build` + `_parse_gotest` beside the Python parsers; flat Go categories; loop language axis; language-dispatched `evaluate()` — in-worktree `go build ./...` (R3), Go test stage IMPOSES `go test -json ./...` (A2), greenfield-C0 stderr fallback pinned empirically (go<1.24 emits build failures unwrapped)
- Phase 4: `LanguagePack` extracted from the two working implementations — 4 members vs 5–6 predicted, zero test edits; delta recorded as new `ref:patterns-refactoring-duplicate-first` (staging doc met its own promotion bar); `acceptance.validators` decided (language is the key; dead-field removal queued for Axis B)
- Phase 5: live acceptance PASSED (greenfield Go, 1 iteration, auto-routed, fallback fired in production) + stretch: first Go EDIT run — surgical 1-line diff, doc comment preserved
- `create-persona --num-ctx` override + `my-python-q25c14-16k`/`my-go-q25c14-16k`; loop coder defaults flipped to them (measured: 32K = 14.2 GiB live, cannot fit the card, 2.5 tok/s offloaded; 16K = 11.1 GiB VRAM-fit, 13–21 tok/s)
- GPU forensics mid-session: stale load-time VRAM split diagnosed (evict+rewarm rebalances), desktop cleared of suspects, live T-102 evidence (concurrent session), one run killed via ollama restart
- Verdict-capture failure diagnosed to mechanism (T-109(1)): mid-turn assistant text is NOT persisted to Fable transcripts — rule memorized + recorded; all 8 session verdicts captured and grep-verified thereafter
- T-111 registered (cooperative cancel cannot interrupt an in-flight generation); stubs-then-retry recovery validated after a run restructured `evaluate()`; session-127 wrap (QUICK memories ×2, KNOWLEDGE LanguagePack section, E-D6 addendum in the edit-mode plan, staleness sweep: persona counts 61/53, README `kind: function`+Go)

### Decisions Made

- Dogfood-first build shape: hand-written red pins gating oficina edit runs on the modules being widened (parser ×2, evaluator ×2); worked, with review-fix-inline closing each run's 5–10% residue
- A2 settled: the Go test stage owns its command — a caller `test_cmd` without `-json` is overridden, never honored (P2-D12 masking-hole class)
- Coder defaults = 16K-ctx personas (measured VRAM decision, reversible; no input-fit guard yet → T-112)
- Loop-economics finding (5/5 runs): iteration 1 lands 90–95% and retries never see the residual defect → `budgets.iterations: 1` for reviewed edit runs is now a data-backed candidate (T-114)
- Follow-ups registered as T-112–T-115 (input-fit guard, ctx re-probe, iterations default, refactoring-conventions promotion)

### Next

- Review + merge **PR #83** (Go widening, 30 commits)
- **Axis B kinds reconsideration** — fed by Axis A (E-D8 rename + dead `acceptance.validators` removal ride the same taxonomy pass)
- Triage T-112–T-115; standing: T-102 busy-check (G-D8), T-105 Phase 6, T-103, T-111

### Gotchas

- **Mid-turn assistant text is not persisted to Fable session transcripts** — a `[VERDICT]` block emitted between tool calls is invisible to the Stop-hook capture; blocks must ride the turn's FINAL message, then verify with a `calls.jsonl` grep (T-109(1) mechanism, diagnosed live)
- **go<1.24: build failures under `go test -json` arrive UNWRAPPED on stderr in go-build shape** with zero fail events — every greenfield Go C0 hits this; the stderr fallback is load-bearing
- **Ollama's VRAM/CPU split is decided at load time and never rebalanced** — after freeing VRAM, evict + rewarm to claim it; `/api/ps size_vram < size` is the offload tell
- **Cooperative cancel waits out the in-flight generation** — cancel latency equals the remaining per-call transport window (25+ min observed under contention; T-111)
- **Whole-file edit runs deleted a large module docstring 4-for-4**, twice against an explicit do-not-modify constraint — restore-in-review is the working mitigation (E-D6 addendum)
