# Determinism Re-Run — Ground Truth & Decision Rule

**Target:** `qwen3:14b` × `docs/research/smart-rag-index.md`
**Reason:** session 57, finding #7 in `ref:ltg-phase1-insights` — `qwen3:14b` exhibited an off-by-one shift on 3/7 dense single-line bullets in the original sweep (`retrieval/runs/20260416-181839.jsonl`). This experiment tests whether the off-by-one reproduces under repeated sampling at the same parameters, gating the routing-hypothesis branch decision.

**Pre-committed before runs execute** — this file is written *before* Step 2 of the determinism task (the actual `extract_topics.py --runs 5` invocation). The threshold rule below is fixed; do not edit it after seeing results.

---

## Ground truth — the 7 cross-cutting pattern bullets

Section 8 of `smart-rag-index.md` ("Cross-cutting patterns appearing in 3+ sources") is a numbered list, one bullet per line, lines 22-28 inclusive:

| Bullet # | Line | Bullet name (canonical) | First-line text in source |
|---|---|---|---|
| 1 | 22 | hybrid_retrieval | `Hybrid = BM25 + vectors + graph` |
| 2 | 23 | precompile_query_many | `Pre-compile once, query many` |
| 3 | 24 | exploit_existing_graph | `Exploit existing graph structure` |
| 4 | 25 | hierarchical_scoping | `Hierarchical scoping beats flat search` |
| 5 | 26 | filter_before_fetch | `Filter-before-fetch via IDs/summaries` |
| 6 | 27 | supersession_contradiction | `Supersession / contradiction tracking` |
| 7 | 28 | behavioral_edges | `Behavioral edges (git co-change)` |

Topic names are guidance only — model-emitted names will vary. Match by **bullet content** (e.g. anything mentioning "graph structure" / "exploit existing" → bullet #3) when reading the run JSON, not by name string equality.

---

## Original sweep observation (what we are testing)

From `retrieval/runs/20260416-181839.jsonl`, `qwen3:14b` × `smart-rag-index.md`:

| Bullet | True line | Model claimed | Δ |
|---|---|---|---|
| #1 hybrid_retrieval        | 22 | 22 | 0 ✓ |
| #2 precompile_query_many   | 23 | 23 | 0 ✓ |
| #3 exploit_existing_graph  | 24 | 23 | **−1 ✗** |
| #4 hierarchical_scoping    | 25 | 24 | **−1 ✗** |
| #5 filter_before_fetch     | 26 | 26 | 0 ✓ |
| #6 supersession_contradict | 27 | 26 | **−1 ✗** |
| #7 behavioral_edges        | 28 | 28 | 0 ✓ |

**Observed accuracy: 4/7.** Drift pattern: three bullets shift by exactly −1, the other four are correct. Not a uniform shift across the whole list — the misses are interleaved with correct mappings, which is what makes "model property vs sampling luck" the live question.

For reference, on the same file `qwen3:8b` scored 7/7 and `qwen2.5-coder:14b` also got 7/7 line-mapping (but failed elsewhere on rule 3). The failure is specific to `qwen3:14b` on this file.

---

## Decision rule (pre-committed)

Run `qwen3:14b` 5× at `temperature=0.1, think=False, num_ctx=8192` (identical to the original sweep parameters). For each run, compute `accuracy = correct_bullet_lines / 7` against the ground truth above. Branch decision:

| Outcome across 5 runs | Interpretation | Branch | Action |
|---|---|---|---|
| **All 5 runs ≥ 6/7** | Original 4/7 was sampling-unlucky; the model is stable here. | **A** | Keep 2-arm routing hypothesis (qwen3:14b for prose, qwen2.5-coder:14b for code). Add note under "Revisit triggers" in `ref:ltg-phase1-routing-hypothesis` that determinism cleared smart-rag-index.md. |
| **All 5 runs ≤ 4/7** | Off-by-one reproduces; format-sensitivity is a model property on dense single-line lists. | **C** | Add containment/post-pass guard rather than splitting routing further. Update `ref:ltg-phase1-routing-hypothesis` per Branch C draft in `ref:ltg-phase1-pending-revisions`. |
| **Mixed (2-4 runs ≥ 6/7)** | Borderline — sometimes drifts, sometimes clean. | **B** | Three-arm routing: code → coder, dense-cross-ref-index → qwen3:8b (which scored 7/7 here), prose → qwen3:14b. Update per Branch B draft. |
| **All 5 runs at exactly 4/7 with same 3 misses** | Deterministic drift — same off-by-one every time. | **C (strong)** | Same as all-≤-4/7 but flag the determinism: a deterministic format failure is more actionable (single fix) than a noisy one. |

**Stability metric (secondary).** Compute pairwise Jaccard over the {topic_name, span_lines} sets across the 5 runs. Per the runner's dim 9 rubric: ≥ 0.85 = strong stability bonus (+0.5), ≥ 0.80 = mild (+0.25), below = no bonus. Record but do not let it override the accuracy-based branch choice — Jaccard could be high on a *consistently wrong* output.

---

## Analysis template (fill in after Step 2)

```
Run | Bullet 1 (22) | Bullet 2 (23) | Bullet 3 (24) | Bullet 4 (25) | Bullet 5 (26) | Bullet 6 (27) | Bullet 7 (28) | Accuracy
1   | 22 ✓          | 12 ✗          | 23 ✓          | 25 ✓          | — ✗           | 26 ✗          | 27 ✗          |   3/7
2   | 22 ✓          | 12 ✗          | 23 ✗          | 24 ✗          | 25 ✗          | 26 ✗          | 23 ✓          |   2/7
3   | 22 ✓          | 12 ✗          | 23 ✗          | 24 ✗          | — ✗           | 26 ✗          | 23 ✓          |   2/7
4   | 22 ✓          | 12 ✗          | 23 ✓          | 25 ✓          | — ✗           | 26 ✗          | 27 ✗          |   3/7
5   | 22 ✓          | 12 ✗          | 23 ✗          | 24 ✗          | — ✗           | 26 ✗          | 23 ✗          |   1/7

Pairwise Jaccard (5 runs → 10 pairs):  min=0.455  median=0.600  max=0.778
Branch chosen: C
Justification: All 5 runs ≤ 4/7 (range: 1–3/7). Jaccard median 0.600 — below 0.80 threshold, no stability bonus.
Three deterministic failure modes confirmed:
  - B2 (line 23): absorbed into wiki_precompilation (anchored at line 12) in all 5 runs — semantic conflation
  - B6 (line 27): deterministic −1 shift every run (claims 26) — format-sensitivity property
  - B5 (line 26): dropped in 4/5 runs, subsumed by adjacent topics
B3/B4/B7 failures are variable but consistent with the model lacking stable positional anchors
on dense single-line bullet lists.
Run JSONL: retrieval/runs/20260504-153903.jsonl (2026-05-04)
```

---

## What this resolves

This is a single 5-cell observation that breaks a 3-way fork in the routing hypothesis. Without it, Phase 2 would either lock in `qwen3:14b` as single-model default (risking format-sensitivity bugs at retrieval time) or split routing prematurely on n=1 evidence. The decision tree above ensures the result maps mechanically to a routing-hypothesis revision; no post-hoc judgment.
