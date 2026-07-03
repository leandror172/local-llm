# Session Log

**Current Layer:** LTG retrieval substrate — Phase 4 COMPLETE (PR #66); next Phase 5 relate(a,b)
**Current Session:** 2026-07-03 — Session 103: PR #66 review round — 9-angle code review, 8 findings fixed via subagents, dataflow model started

---
## 2026-07-03 - Session 103: PR #66 review round — 9-angle code review, 8 findings fixed via subagents, dataflow model started

### Context

Session opened with resume.sh + `/code-review PR #66` (the Phase 4 graph+communities diff), with an added user-supplied review angle: the web-research repo's Function Decomposition Pattern (incl. the filter-vs-slice top-K trap).

### What Was Done

- fix(ltg): PR #66 review round — copy-based backup preserves edges table + 7 more findings (ref:ltg-phase4-plan)
- 9-angle review (3 correctness + 3 cleanup + altitude + conventions + decomposition-pattern) → 8 verified findings; fixed via Opus subagent (store/anchors/communities backup+write consolidation), Sonnet subagent (graph.py: --table plumbing, zero-norm NaN guard, empty-YAML KeyError, top-k probe↔build unification, import consolidation), + inline (`write_edges_table` → `store.open_or_create_table`); 310 tests green (was 304)
- `docs/ATTRIBUTIONS.md` created — leidenalg **GPL-3** / python-igraph GPL-2+ recorded per CLAUDE.md licensing rule (revisit before publishing retrieval/ code)
- `docs/diagrams/ltg-phase4-dataflow.md` — first system-operation model (`ref:ltg-phase4-dataflow`): mermaid pipeline dataflow + stage×state matrix (what each stage reads/writes/destroys) + edge-kinds table
- `.claude/index.md` (Phase 4 module names + 2 new doc rows) and retrieval QUICK/KNOWLEDGE updated (stale copytree gotcha rewritten; review-round item added); PR #66 body updated with review-round section

### Decisions Made

- Backup semantics: `store.backup_index` is now copy-based (copytree) and single-sourced — the move-then-recreate original destroyed the live `edges` table on every anchors rebuild; single-slot `.bak` hardening deliberately left to T-71
- Decomposition-pattern check on the top-K code came back clean: self masked to -inf before the argpartition slice, τ-after-K matches the degree probe exactly — no filter-vs-slice trap
- Three verified low-priority findings deferred to T-72 instead of fixing in this round
- Flow-model format: stage×state matrix over sequence diagram — composition bugs (like the backup one) live in state-lifecycle columns, not call order; matrix must be updated in the same PR that changes stage behavior

### Next

- LTG Phase 5 — `relate(a,b)` tool (`ref:ltg-plan-phase-5`); PR #66 now includes the review round and is ready for merge review

### Gotchas

- A mid-session Claude Code restart silently killed in-flight background finder agents — but some "lost" originals later completed and double-delivered alongside relaunched duplicates; stop duplicates via TaskStop instead of letting both run
- Partitioning parallel fix-subagents by file ownership left a seam neither owned (`write_edges_table` in graph.py needed a store.py import) — after a parallel fan-out, re-check the boundary lines between ownership zones
