# Session Log

**Current Layer:** Layer 5 — Expense Classifier
**Current Session:** 2026-07-03 — Session 104: T-71 rebuild-all sequencer + backup hardening (subagent) + LTG Phase 5 relate(a,b) design frozen + plan authored

---
## 2026-07-03 - Session 104: T-71 rebuild-all sequencer + backup hardening (subagent) + LTG Phase 5 relate(a,b) design frozen + plan authored

### Context

PR #66 (Phase 4) merged and master updated at session start; session split into T-71 execution (delegated to a Sonnet subagent) and the LTG Phase 5 design discussion in parallel.

### What Was Done

- Merged PR #66 landing acknowledged; T-71 executed: `retrieval/run-rebuild-all.sh` sequencer (store→anchors→graph→communities) + backup-chain hardening — one authoritative pre-rebuild `{index}.bak` taken by the wrapper (`store.py --backup-only`), stages run `--no-backup`, ad-hoc single-stage runs use stage-suffixed slots (`.bak-store`/`.bak-anchors`/`.bak-communities`); `anchors.py` gained `--no-backup`; implemented by a Sonnet subagent, main-session review added a no-index guard to `--backup-only`; 321 tests green (310 baseline)
- LTG Phase 5 `relate(a,b)` design discussed and frozen (P5-D1–D7); plan authored: `docs/plans/ltg-phase5-relate.md` (`ref:ltg-phase5-plan`) with output schema, TDD tasks T1–T6, manifest-pinned acceptance pairs
- Acceptance pairs verified against the frozen corpus manifest: 6/7 present; `memory-architecture-design.md` lives in the web-research repo, not this corpus → pair substituted with `(smart-rag-mempalace.md, docs/research/QUICK-MEMORY.md)` (cross-source-group, also exercises provenance); copy-from-web-research recorded as opt-in fallback only
- Read `retrieval/.memories/` QUICK+KNOWLEDGE before plan-writing; two findings folded in: fine Leiden resolution barely splits (207→214, tuning lever noted) and L2-vs-cosine foot-gun (nearest_miss computes cosine via matmul, never LanceDB ANN)
- T-73 (relate anchor_key input extension) + T-74 (T-65 weighting excluded from relate) recorded in tasks.md

### Decisions Made

- T-71 backup design = A+B combined: single-writer-per-slot invariant — plain `.bak` written only by run-rebuild-all pre-pipeline; every other backup path stage-suffixed (session-102 loss was a shared-mutable-slot bug)
- P5-D1–D7 frozen (see plan): file-path-only inputs; direct edges + community overlap, no multi-hop (written escalation trigger); `nearest_miss` = narrow, principled exception to P4-D6 (sub-τ evidence can't exist in the edges table); verdict bands derived from recorded thresholds; qwen3:14b `relate_summary` is the ONLY model call, prose narrates precomputed facts, never discovers; null community columns → abort with rebuild remedy
- Synthesis prompt lives in `retrieval/prompts/relate_summary.txt` (extract.txt pattern) — prompt iterations diffable without code churn
- Plan mode (/plan) deliberately skipped: design was settled interactively and the deliverable is itself the plan doc — the doc review is the approval gate

### Next

- Implement LTG Phase 5 per `ref:ltg-phase5-plan` — tasks T1–T6 (loaders/guards → aggregation → nearest_miss/banding → prose synthesis → CLI → live acceptance on the 4 pairs)

### Gotchas

- Acceptance criteria written at concept time drift with the corpus: the master plan's `(mempalace, memory-architecture-design)` pair referenced a doc that was never in this repo (lives in `web-research/docs/research/`). Pin acceptance pairs to manifest paths in plan docs
- anchors is the only derivation stage with a live model call (embedding anchor descriptions) — it's the stage where "hermetic" subagent tests quietly stop being hermetic (T-71 subagent's smoke test crashed on a 16-dim fixture vs 4096-dim live model)
