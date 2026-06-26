# LTG Phase 2.5 — Calibration & Acceptance Findings

**Date:** 2026-06-26 (session 96). **Branch:** `feature/ltg-phase2.5-corpus`.
**Closes:** T-34 (threshold recalibration — measurement), T-36 (corpus expansion). Lands T-65 cheap half. Feeds T-63 (Phase 3.5).
**Index built against:** corpus-manifest.yaml @ commit b186c6e (113 files, sha256-frozen).

## Pipeline result (full corpus)

| Stage | Result |
|-------|--------|
| Extract | 113/113 files `ok`, **875 topics**, 0 failures |
| Embed | 875 rows, 4096-dim (`qwen3-embedding:8b`), 0 failed, 54.7s |
| Store | 875 topic rows; `source_group` populated, **0 nulls** |
| Anchors | 143 anchors linked; **21 alias merges**; combined table **1018 rows** |

`source_group` distribution (topics): archive 436, docs-research 165, memories 110, docs-ideas 105, claude-meta 59.
Anchor `source_group`: 98 `ungrouped` (anchors defined in files outside corpus roots — correct), rest grouped by defining file.

## T-34 — Threshold recalibration

### Anchor merge threshold (`anchors.py COSINE_THRESHOLD`)
Best-match cosine across all 143 anchors is **continuous, not bimodal**:
min 0.516 · p10 0.628 · median 0.755 · p90 0.863 · max 0.954. Counts: ≥0.90 = 6, ≥0.85 = 22, ≥0.80 = 48.

Sub-0.85 near-misses are **coincidental topical adjacency**, not true aliases (e.g. `ref:memory-files`→a session-log's `task_and_file_management` @ 0.819). Lowering the threshold would add **false merges**, not recall.

**Decision: keep `COSINE_THRESHOLD = 0.85`** — now empirically validated on the full corpus rather than the original 3-anchor guess. `NEARMISS_LOW = 0.80` retained.

### Noise-query threshold (`ltg_inspect.py`)
Acceptance queries (L2 `_distance`, lower=closer):

| Query | Type | Top-1 L2 | ≈cosine |
|-------|------|----------|---------|
| repowise git co-change | real | 0.437 | 0.905 |
| memory across sessions | real | 0.583 | 0.830 |
| topic-extraction models | real | 0.356 | 0.937 |
| repowise analyze repos | real | 0.317 | 0.950 |
| expense classification | in-corpus (Layer-5 logs) | 0.374 | 0.930 |
| Kubernetes deployment YAML | **true noise** | 0.746 | 0.722 |

Real queries land at **L2 ≤ 0.58 / cosine ≥ 0.83**. The "Kubernetes" query (L2 0.746) is *tech-adjacent*, not pure noise — it brushes the repo's Ollama/Docker/infra content.

**Follow-up — 8 pure off-corpus noise probes** (risotto, NBA finals, flat tire, vitamin D, hiking trails, tides physics, tax deadline, song lyrics) to escape the n=1 trap:

| Band | L2 distance | cosine |
|------|-------------|--------|
| Real queries | ≤ 0.58 | ≥ 0.83 |
| Tech-adjacent (Kubernetes) | 0.746 | 0.722 |
| **Pure off-corpus noise (n=8)** | **0.91 – 1.17** (mean 1.03) | 0.32 – 0.58 |

The real and pure-noise bands are **cleanly separated by a ~0.33-wide empty gap** (0.58 → 0.91); 0/8 noise queries fell below 0.65, 0/8 below 0.58. The old `>1.0` L2 threshold (bge-m3 1024-dim era) is badly stale — it would classify *all* of this noise as real.

**Recommended noise separator: L2 ≈ 0.70 (cosine ≈ 0.76)** — mid-gap, wide margin to both the real band (0.58) and the pure-noise band (0.91). A stricter 0.65 also works; 0.80 would treat tech-adjacent queries as borderline-real. This is now defensible from **n=9** (1 tech-adjacent + 8 pure), not the original n=1.

**Status — documented, not yet wired.** `acceptance_mode` is currently record-only; wiring means adding a `NOISE_L2_THRESHOLD` constant + a pass/fail assertion (noise queries must exceed it; real queries must fall below). That is the *only* remaining T-34 work — the threshold value itself is now empirically grounded. Deferred to keep this (post-handoff) session in wrap-up scope, not because the number is untrustworthy.

## T-36 — Corpus expansion: DONE
Index now holds 875 topics from 113 files (was 69 from 8). Staleness healed: `plan-latent-topic-graph` rose **0.7742 → 0.8379** after re-extraction (still a near-miss under 0.85 — see T-63).

## Step 5 — Generic-anchor precision: PASS
Generic anchors did **not** false-merge: `ref:git-safety`, `ref:indexing-convention`, `ref:bash-wrappers` all correctly no-merge. `ref:git-worktrees`→`utility_commands` is a defensible true merge. §9 false-merge risk did not materialize at 0.85.

Minor: 2–3 borderline M:N *secondary* links above 0.85 (`ref:smart-rag-research`→`user_preferences`, `ref:rag-dify`→`ollama_pipeline_configuration`). Non-catastrophic; candidates for T-63 tuning.

## Follow-ups
- **T-63 (Phase 3.5):** `plan-latent-topic-graph` @ 0.8379 and ~26 anchors in the 0.80–0.85 near-miss band are the escalation/near-miss-tuning targets. Lowering `NEARMISS_LOW` or LLM one-liner escalation — deferred.
- **T-65 (Phase 5):** query-type-dependent group weighting — provenance now captured (`source_group`), weighting logic deferred.
- Noise-threshold wiring (above) — deferred pending enforced acceptance + more noise probes.
