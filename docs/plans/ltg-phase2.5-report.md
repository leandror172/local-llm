# LTG Phase 2.5 — Run Report

**Session:** 94 [pipeline] / 96 [actual] · **Date:** 2026-06-26
**Branch:** `feature/ltg-phase2.5-corpus` · **PR:** #56 (open, not merged)
**Plan:** `docs/plans/ltg-phase2.5-corpus.md` · **Calibration detail:** `retrieval/probes/phase2.5-calibration.md`
**Closes:** T-36 (corpus expansion). **Advances:** T-34 (measurement-complete), T-65 (cheap half), T-18 (retrieval slice).

---

## 1. Objective

Move the LTG index off its 8-file / 69-topic Phase-2 snapshot onto the full curated MVP
corpus, freshly extracted, and replace guessed similarity thresholds with measured ones —
so Phase 4 (graph + communities) builds on solid ground. This is a **data-hygiene +
calibration** phase, not a feature phase.

The session ran the first half interactively (design decisions) and the second half
**unattended** (execution through PR + handoff) at the user's instruction.

---

## 2. Design decisions taken this session

| # | Decision | Rationale |
|---|----------|-----------|
| D-A | Corpus config in a **new `retrieval/corpus.yaml`**, not a block in `config.yaml` | Separation of concerns: `config.yaml` is models/roles (inference setup); corpus selection has a different lifecycle and reviewer. Matches the repo's one-concept-per-file convention. |
| D-B | Add **`source_group` to the schema now**, derived at store-time | Re-extraction rebuilds the index from scratch — the one moment a new column is free. Manifest-only would force a second full rebuild when Phase 5 wants it on rows. |
| D-C | **No repo copy** for the freeze; record commit SHA + per-file sha256 in the manifest | Git already content-freezes losslessly. A copy is a second source of truth that drifts. Hashes detect drift; the SHA reconstructs inputs. `git worktree` was offered for hard isolation but not needed (run-in-place). |
| D-D | **Archive included now** (full ~113-file run) | Honors plan decision S2; gives one clean frozen manifest. Config makes archive a one-line toggle if a faster pass were ever wanted. |
| D-E | **Python 3.12 upgrade scoped to `retrieval/` only**, decoupled from the corpus freeze | The freeze script is version-independent (custom glob matcher) and correct on 3.10. The upgrade is a cross-cutting infra change with its own test gate; entangling it with the corpus work would muddy both. Done as an isolated, test-gated step before the long extraction so that run sits on a verified interpreter. |
| D-F | `file_role` (now unused as a hand-label) is set to the **provenance group** | `file_role` is pure pass-through metadata (nothing branches on it); the group is the most meaningful descriptor available for 113 files. No schema change. |
| D-G | T-34 noise threshold **documented, not wired** | Only one true-noise acceptance sample (n=1); hard-coding off it would repeat the exact overfit T-34 exists to fix. `acceptance_mode` is record-only, so nothing forces a constant. |

---

## 3. Work delivered (commits, in order)

| Commit | Summary |
|--------|---------|
| `6c8bf0b` | `corpus.yaml` (selection intent) + `build_corpus_manifest.py` + wrapper + index doc. Version-independent glob matcher. |
| `4035254` | uv-managed Python 3.12 env for `retrieval/` (`pyproject.toml` + `uv.lock`, wrappers `uv run`). Mirrors `mcp-server`. |
| `b186c6e` | `source_group` schema field; shared `corpus_groups.py` matcher; store-time derivation. |
| `9db2c0f` | Frozen `corpus-manifest.yaml` (113 files, clean tree). |
| `e19e55f` | `extract_topics.py` reads the manifest; hardcoded `CORPUS` retired. |
| `93058e1` | Full-corpus rebuild results + T-34 calibration findings + `.memories` updates. |
| `7d9a737` | Session handoff (tracking files). |

### Architectural notes
- **File universe = `git ls-files`.** "Freeze" means tracked content; gitignored
  `.claude/local/**` never enters the candidate set — `exclude_globs` is belt-and-suspenders.
- **Single chokepoint for provenance.** Both writers (`embed.py`→`store.py` and
  `anchors.py`) funnel through `store.rows_to_arrow_table`. Deriving `source_group` there
  covers every row, both paths, with one edit. It is **authoritative** (overrides any
  writer value) so it cannot drift from the corpus rules.
- **Glob `**/` zero-dir semantics.** `**/foo` must match `foo` at the repo root; the
  correct translation is `(?:.*/)?`, not `.*/`. A naive matcher silently drops root-level
  `.memories/*.md`.

### Bugs caught before they shipped
1. **`**/` matcher dropped root `.memories`** — the manifest dry-run reported 12 memories
   vs 14 on disk; fixed in `glob_to_regex`, unit-tested. The standalone dry-run step (a
   deliberate design choice) surfaced this before any data was written.
2. **`test_anchors_rows` schema-drift guard fired** on the new field — correctly, since
   `source_group` is store-derived and absent from writer rows. Encoded the new contract
   (`STORE_DERIVED_FIELDS`) rather than weakening the check.
3. **Session-number clash at handoff** — pipeline derived 94 while content used the actual
   96; relabeled the status bullet to the established `[pipeline]/[actual]` convention
   before promoting, avoiding a duplicate "Session 94" in the log.

### Delegation
The Python 3.12 migration was delegated to a **Sonnet subagent** (bounded, objectively
gated by "254 tests green"). The `source_group` change was done **inline** (schema-design
judgment at a shared chokepoint — poor delegation fit). The migration's gate was
**independently re-run** in the main session, not trusted on report.

---

## 4. Pipeline run results

| Stage | Result |
|-------|--------|
| Extract (`run-extract-topics.sh`) | **113/113 files `ok`, 875 topics, 0 failures** (no timeouts, no malformed JSON) |
| Embed (`run-embed.sh`) | 875 rows, 4096-dim (`qwen3-embedding:8b`), 0 failed, **54.7s** |
| Store (`run-store.sh`) | 875 topic rows; `source_group` populated, **0 nulls** |
| Anchors (`run-anchors.sh --index`) | 143 anchors linked; **21 alias merges**; combined table **1018 rows** |

**Topic yield 875 exceeded the plan's 500–650 estimate.** `source_group` distribution
(topics): archive 436, docs-research 165, memories 110, docs-ideas 105, claude-meta 59.
Anchor `source_group`: 98 `ungrouped` (anchors defined in files outside corpus roots —
correct, since provenance reflects corpus membership), rest grouped by defining file.

Environment at launch: Ollama up, `qwen3:14b` present, VRAM empty (clean load), 399 GB
free. Model warmed (`keep_alive: 40m`) before extraction so all 113 prose-arm files share
one resident load.

---

## 5. Findings — T-34 calibration

Full data in `retrieval/probes/phase2.5-calibration.md`. Summary:

### Anchor merge threshold — `COSINE_THRESHOLD = 0.85` validated-keep
**The validating evidence is the Step-5 precision result** (below): generic anchors do not
false-merge, and the sub-0.85 near-misses inspected are spurious adjacency. The best-match
distribution shape is supporting, not primary, evidence — it is continuous (min 0.516,
median 0.755, p90 0.863, max 0.954; ≥0.85 = 22, ≥0.80 = 48) partly *because* it conflates
should-merge anchors with genuine orphans, so shape alone is weak. What the two together
show: lowering the threshold would admit coincidental matches (e.g. `ref:memory-files`→a
session-log's `task_and_file_management` @ 0.819) as false merges, not recover real ones.
0.85 is now empirically validated rather than guessed from 3 anchors — the substantive
closure of the anchor half of T-34.

### Noise-query threshold — measured (n=9), defensible, wiring deferred
Acceptance queries land at L2 ≤ 0.58 / cosine ≥ 0.83 (real). The "Kubernetes" query
(L2 0.746) is *tech-adjacent*, not pure noise. To escape an n=1 conclusion, 8 pure
off-corpus probes (risotto, NBA, flat tire, vitamin D, hiking, tides, tax, song lyrics)
were run:

| Band | L2 | cosine |
|------|----|--------|
| Real queries | ≤ 0.58 | ≥ 0.83 |
| Tech-adjacent (Kubernetes) | 0.746 | 0.722 |
| **Pure off-corpus noise (n=8)** | **0.91–1.17** (mean 1.03) | 0.32–0.58 |

Real and pure-noise bands are separated by a **~0.33-wide empty gap** (0.58 → 0.91);
0/8 noise queries fell below 0.65. The old `>1.0` L2 threshold (bge-m3 era) is badly
stale. **Recommended separator: L2 ≈ 0.70 (cosine ≈ 0.76)** — mid-gap, wide margin both
sides; now defensible from n=9, not the original n=1. **Wiring deferred:** `acceptance_mode`
is record-only; closing the rest of T-34 means adding a `NOISE_L2_THRESHOLD` constant +
pass/fail assertions. The *value* is grounded; only the enforcement code remains — left
out of this post-handoff wrap-up session.

### Step 5 — generic-anchor precision: PASS
`ref:git-safety`, `ref:indexing-convention`, `ref:bash-wrappers` correctly **no-merge** —
the §9 false-merge risk did not materialize at 0.85. `ref:git-worktrees`→`utility_commands`
is a defensible true merge. Minor: 2–3 borderline M:N **secondary** links above 0.85
(`ref:smart-rag-research`→`user_preferences`, `ref:rag-dify`→`ollama_pipeline_configuration`)
— non-catastrophic, T-63 candidates.

### Staleness healed
`plan-latent-topic-graph` rose **0.7742 → 0.8379** after re-extraction (was the session-94
D3 operational-metadata near-miss on a drifted corpus). Still < 0.85 — a clean T-63
(Phase 3.5) escalation target, now with fresh data.

---

## 6. Tests & artifacts

- **269 tests green** under Python 3.12 (was 254; **+15**: 8 `corpus_groups` + 5
  `source_group` store + 2 manifest loader; `test_anchors_rows` was modified, not added).
  Independently re-run in the main session.
- Committed: extraction source (`runs/phase2.5-full.jsonl`, 219 KB), per-run logs, acceptance
  + calibration markdown, `.memories` updates, config + manifest.
- Gitignored (regenerable): 48 MB `*-embeddings.jsonl`, the LanceDB `index/`.

---

## 7. Honest limitations / open items

- **T-34 not fully closed — but no longer blocked on data.** The noise threshold is now
  empirically grounded (n=9, clean gap → L2 ≈ 0.70). Only the *wiring* remains: add a
  `NOISE_L2_THRESHOLD` constant + pass/fail assertions to the currently record-only
  `acceptance_mode`. Deferred to keep this post-handoff session in wrap-up scope.
- **Borderline M:N anchor merges** (2–3 above 0.85) suggest 0.85 is near the precision
  edge for secondary links — worth revisiting in T-63.
- **Home-repo handoff** still needs the direct `handoff.py --registry` invocation (T-62);
  the installed shim path differs.
- **Python 3.12 is retrieval-only.** Benchmarks/scripts/`.claude/tools` remain on 3.10
  (repo-wide T-18 open).

---

## 8. Next session

1. Review + merge PR #56.
2. **LTG Phase 4** — graph + communities. `alias_of` lists are the proto-edges;
   anchor↔anchor edges from `index.md` cross-refs land here. Build on the fresh 1018-row
   index. (`ref:ltg-plan-phase-4`, `ref:ltg-graph-lib`.)
3. **T-63 (Phase 3.5)** — near-miss escalation, now with fresh data (`plan-latent-topic-graph`
   @ 0.838; ~26 anchors in the 0.80–0.85 band).
