# Session Log

**Current Layer:** Layer 5 — Expense Classifier (active thread: LTG retrieval substrate — Phase 2.5 done, Phase 4 next)
**Current Session:** 2026-06-26 — Session 94: LTG Phase 2.5 — full-corpus expansion + T-34 calibration + retrieval Python 3.12

---
## 2026-06-26 - Session 94: LTG Phase 2.5 — full-corpus expansion + T-34 calibration + retrieval Python 3.12

### Context

Unattended continuation of the LTG Phase 2.5 plan (`docs/plans/ltg-phase2.5-corpus.md`), starting at Step 0. User authorized autonomous execution through PR + handoff.

### What Was Done

- Built config-driven corpus selection: `corpus.yaml` (intent) + `build_corpus_manifest.py` → frozen `corpus-manifest.yaml` (113 files, commit SHA + per-file sha256; no repo copy). Shared glob matcher `corpus_groups.py` with correct `**/` zero-dir semantics (a dry-run caught the root-`.memories` drop bug).
- Migrated `retrieval/` to a uv-managed Python 3.12 env (`pyproject.toml` + `uv.lock`, mirrors mcp-server; wrappers use `uv run`). Done by a Sonnet subagent, gate re-verified in main session.
- Added `source_group` provenance field (T-65 cheap half), derived authoritatively at store-time from `file_path`; wired `extract_topics.py` to read the manifest (retired hardcoded `CORPUS`).
- Ran the full pipeline live: extract 113/113 ok / 875 topics / 0 fail; embed 875 rows 4096-dim / 54.7s; store + anchor re-link → 1018-row index (875 topics + 143 anchors), 21 alias merges, source_group 0 nulls.
- T-34 calibration measured + documented (`probes/phase2.5-calibration.md`); opened PR #56; 269 tests green under 3.12.

### Decisions Made

- `COSINE_THRESHOLD=0.85` validated-keep: full-corpus best-match distribution is continuous, and sub-0.85 near-misses are coincidental adjacency — lowering would add false merges, not recall.
- Noise-query threshold measured (real L2≤0.58, true-noise 0.75 → recommend L2≈0.65) but **documented, not wired**: `acceptance_mode` is record-only and there is only one true-noise sample (n=1) — wiring it would repeat the overfit T-34 set out to fix. T-34 therefore left OPEN (measurement complete, wiring deferred).
- 48M `*-embeddings.jsonl` gitignored (regenerable, like the LanceDB index); extraction source + per-run logs + findings committed.
- Python upgrade scoped to retrieval only; benchmarks/scripts/.claude tools stay on 3.10 (repo-wide T-18 still open).

### Next

- Review + merge PR #56 (`feature/ltg-phase2.5-corpus`).
- LTG Phase 4 — graph + communities (`alias_of` lists are proto-edges; anchor↔anchor edges from index.md cross-refs land here). Build on the fresh full-corpus index.
- T-63 (Phase 3.5): `plan-latent-topic-graph` healed 0.7742→0.8379 (still <0.85) + ~26 anchors in the 0.80–0.85 near-miss band — escalation / NEARMISS_LOW tuning.

### Gotchas

- 875 topics from 113 files (above the plan's 500–650 estimate); `.claude/archive` is ~51% of the corpus. Full extraction ran well under the ~2 hr worst-case.
- Home-repo handoff still needs the direct `handoff.py --registry` invocation (T-62); the installed shim path differs.
- Borderline M:N anchor links exist above 0.85 (`ref:smart-rag-research`→`user_preferences`, `ref:rag-dify`→`ollama_pipeline_configuration`) — non-catastrophic, T-63 candidates.
