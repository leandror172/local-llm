## 2026-07-03 - Session 105: LTG Phase 5 relate(a,b) implemented + accepted via Opus subagents (PR #67)

### Context

Session dedicated to executing the Phase 5 plan frozen in session 104. Two new single-shot Opus agent types created (`impl-opus` high / `impl-opus-med` medium, per-user directives: directed reading, advisor ≤3 first-after-contextualization, proposed-not-applied memory updates), then T1–T3 and T4–T5 run as background subagents with main-session verification, and T6 live acceptance run interactively in the main session.

### What Was Done

- chore(agents): impl-opus + impl-opus-med — single-shot Opus implementation subagents (high/medium effort)
- feat(ltg): Phase 5 relate(a,b) — pairwise relation tool (P5-D1-D7, T1-T5) — 56 new tests, 377 total green
- docs(ltg): Phase 5 acceptance ACCEPTED — 5 pairs, bands final; memories + plan checkoff
- PR #67 opened (`feature/ltg-phase5-relate`)
- T6 in main session: 4 planned pairs + 1 added cross-group probe run live; every prose claim checked against the structured dicts; one prompt iteration + two formatter fixes; acceptance report `retrieval/probes/phase5-relate-acceptance.md` (`ref:ltg-phase5-acceptance`)

### Decisions Made

- Verdict bands FINAL at provisional values (strong: same_as or sim≥0.85; moderate: any similarity edge; weak: nearest-miss≥0.55) — pair-2 "expected low, got moderate" accepted as correct-over-expectation (one genuine 0.79 topic link); the weak/moderate nearest-miss inversion kept deliberately as evidence-honest
- Master-plan pair-1 "divergence" criterion amended — divergence has no structured field and prose may only cite structured facts (P5-D5) → new deferred T-75 (divergences view)
- Prose defects fixed at the rendering layer, not by prompt-wrestling: `_fmt_community_overlap` now renders counts (raw id lists read as counts by the model), `_fmt_nearest_miss(None)` renders `n/a` (explanatory sentence was paraphrased as speculation); prompt rules 6–7 added (no absent-field narration, quote numbers as-is)
- Effort split validated: impl-opus (high) for the correctness-trap batch T1–T3, impl-opus-med for pattern-following T4–T5, T6 judgment in main session

### Next

- Merge PR #67; then LTG Phase 6 (MCP retrieve_context/relate_files) — but evaluate T-33 repo separation FIRST (`ref:ltg-plan-phase-6` pre-phase gate)
- T-63 Phase 3.5 anchor escalation remains unblocked side-option; T-75 divergence view when a consumer needs contrast

### Gotchas

- New `.claude/agents/*.md` were spawnable WITHOUT a session reload (harness picked both up immediately) — contradicts the T-66(c) session-97 finding; current Claude Code appears to hot-load agent files. Update T-66 evidence when next exercised
- LLM prose "hallucinations" traced to the facts formatter, not the model: `shared [4]` (community id list) became "four shared communities"; the null-formatter's explanatory sentence became speculation. The formatter is part of the prompt — check it before blaming the model
- Both Opus implementation subagents under-delegated to the local model (wrote code/tests directly, self-reported honestly) — Opus agents skew toward writing code themselves; convention-compliance needs stronger prompt emphasis or acceptance of the trade-off
