# LTG Phase 2.5 — Full-Corpus Expansion + Threshold Recalibration

**Status:** Planned (not started). Drafted session 95 (2026-06-23).
**Branch:** `feature/ltg-phase2.5-corpus` (off master; Phase 3 / PR #55 merged).
**Closes:** T-34 (threshold recalibration), T-36 (corpus expansion). Tees up T-63 (Phase 3.5) and lands the cheap half of T-65 (source-group provenance).
**Reading:** `docs/plans/ltg-phase3-anchors-implementation.md` §9 (honest limitations), `retrieval/DECISIONS.md` (`ref:ltg-corpus`, `ref:ltg-phase3-decisions`), `ref:ltg-phase3-discussion` (deferred items).

---

## 1. Why this phase exists

Phase 2.5 is a **data-hygiene + calibration phase**, not a feature phase. It puts the index on full-corpus, freshly-extracted footing and replaces guessed thresholds with measured ones — so Phase 4 (graph + communities) builds on solid ground rather than an 8-file snapshot.

Three deferred concerns share the same "when the corpus expands" trigger:
1. **Corpus expansion (T-36)** — index holds 69 topics from 8 files; widen to the full curated MVP corpus.
2. **Threshold recalibration (T-34)** — `COSINE_THRESHOLD` ≈ 0.85 and `NEARMISS_LOW` = 0.80 came from a 3-anchor probe (statistically meaningless); recalibrate from the full distribution.
3. **Generic-anchor precision** — all Phase 3 merges were LTG-self-referential (easiest case); false-merge precision on generic anchors (`ref:git-safety`) is untested (§9).

It also resolves the session-94 staleness: even the existing 8 files drifted since extraction (mtime warnings firing; `plan-latent-topic-graph` non-merge at 0.7742). Re-extraction heals this.

## 2. Corpus scope (decided session 95)

Measured corpus (markdown), after exclusions: **66 files / ~618 KB / ~155 K tokens** — roughly 19× the current content. Expected topic yield ≈ **500–650**.

| Source root | In? | Group tag (T-65) | Notes |
|-------------|-----|------------------|-------|
| `docs/research/` | ✅ | `docs-research` | Prose-dominant; acceptance cluster lives here |
| `docs/ideas/` | ✅ | `docs-ideas` | LTG concept paper + smart-rag conversations; richest `relate()` tests |
| `.memories/` (all folders) | ✅ | `memories` | Structural/conventional content |
| `.claude/` (skills, tools, plan-v2, tasks, index, session-context) | ✅ | `claude-meta` | Conventional + procedural |
| `.claude/archive/` | ✅ | `archive` | **Ingested but tagged as its own group** (decision below) |
| `.claude/local/` | ❌ | — | Gitignored, sensitive, 679 KB of handoff-run logs = procedural noise |
| Code (`.py` etc.) | ❌ (defer) | (`code`, future) | 2-arm router supports it, but code = Phase 8 territory per `ref:ltg-corpus` |

**Decisions:**
- **S2 — `.claude/archive/` IS included**, tagged `archive`, not excluded. Rationale: "relate over past decisions" is a real query type; archive should be *available* but down-weighted by default and up-weighted for decision-history queries. See **source-group provenance** below.
- **Long-file branch point — RESOLVED, no chunking.** Largest legitimate file is `.claude/tasks.md` at ~35 KB (~8.7 K tokens), well under the 16 K extraction ceiling. The `ref:ltg-corpus` long-file branch point is decided by measurement: skip chunking for this MVP.
- **Code branch point — DEFER.** Keep MVP prose-only; revisit when a multi-file-type proof is actually needed.

## 3. Source-group provenance (T-65 — the cheap half lands here)

A file's **origin group** is a new axis, orthogonal to the existing binary `source_class` (`topic_extracted` / `anchor_ref`, which encodes provenance, not origin). The Phase-5 feature is *query-type-dependent* weighting per group (archive down-weighted normally, up-weighted for "past decisions" queries; or qualified in the answer). The schema comment already frames `source_class` as a "config-projection of (file_path, node_kind)" — the group is the intended richer projection.

**Do now (cheap):** record the group at ingest — in the corpus-manifest sidecar, and add a `source_group` field on rows (derived from file path). Provenance is cheap to capture now, expensive to backfill.
**Defer to Phase 5:** the actual weighting logic. Tracked as T-65.

## 4. Execution steps

**Step 0 — Corpus config + frozen manifest.** Don't hardcode exclusions in a script. Introduce a **corpus-selection config** (e.g. `retrieval/corpus.yaml`, or a `corpus:` block in the existing `config.yaml`) that declares: `include_roots`, `exclude_globs` (e.g. `.claude/local/**`, `**/*.bak`, `**/archive/**` if ever excluded), and `groups` (path-prefix → group tag, per §2). The extractor reads this to decide what to ingest and how to tag — so changing what's ignored is a one-line config edit, not a code change. Then *materialize* the resolved file list into a committed `retrieval/corpus-manifest.yaml` sidecar (each line tagged with its group) for reproducibility and a durable "what's indexed" answer. Config = intent; manifest = the frozen resolution of that intent for this run.

**Step 1 — Re-extract (full corpus).** `retrieval/run-extract-topics.sh` over the manifest. Warm `qwen3:14b` first; all `.md` route to the prose arm → model stays resident, no eviction thrash. One JSONL row per file. Re-extracts the existing 8 too → heals staleness.

**Step 2 — Embed.** `retrieval/run-embed.sh` → `qwen3-embedding:8b` (4096-dim). Sequential constraint: runs *after* extraction (no co-residence with the 14B during generation). Re-embed the 143 anchors.

**Step 3 — Rebuild index + anchors.** `run-store.sh` (auto-backs up current index) → `run-anchors.sh --index` to re-link anchors against the *fresh* topics. Carry `source_group` through. Expect `plan-latent-topic-graph` to resolve once its snapshot is no longer stale.

**Step 4 — Calibration pass (T-34).** Dump the full score distribution from the new index. Measure: real-match cosine band (known-good anchor→topic pairs) vs. noise band (unrelated query vs. corpus). Set `COSINE_THRESHOLD`, `NEARMISS_LOW`, `acceptance_mode` in `ltg_inspect.py` from the gap, not the 3-anchor guess.

**Step 5 — Generic-anchor precision check.** Verify non-self-referential anchors (`ref:git-safety`, `ref:indexing-convention`) don't false-merge against the larger corpus (§9 risk). Record results.

**Step 6 — Acceptance + commit.** Re-run `run-inspect.sh --acceptance`; confirm R1–R4 pass at new thresholds. Update `retrieval/.memories/`, `DECISIONS.md`, close T-34 + T-36, tee up T-63 / Phase 3.5.

## 5. Compute-time estimate (local GPU, wall-clock)

Assumptions: 66 prose files, single 14B resident (no swap), qwen3:14b ~32 tok/s gen, ~8–9 topics/file × ~100 output tokens ≈ 800–1000 output tokens/file; prompt-eval of ~2 K-token input is a few seconds on the RTX 3060.

| Step | Work | Estimate |
|------|------|----------|
| 1 — Extract | 66 × ~30–45 s/file | **35–55 min** |
| 2 — Embed | ~600 topics + 143 anchors, batched | **3–8 min** |
| 3 — Store + anchor-link | I/O + matrix ops | **2–5 min** |
| 4–5 — Calibration + precision | analysis (some manual judgment) | minimal GPU |
| **Total GPU occupancy** | | **~45–70 min** (worst realistic ~90 min) |

Dollar cost ≈ 0 (local inference). Cost is GPU wall-clock + review time on calibration. Dominant variable: Step 1 — scales with actual topic-yield per file.

## 6. Out of scope

- Phase 4 (edges/graph/communities) — `alias_of` is a proto-edge it will relocate.
- Phase 5 retrieval-weight tuning — the *logic* for query-type-dependent group weighting (T-65); only provenance capture lands here.
- Phase 3.5 escalation LLM pass (T-63) — paired with this phase but tracked separately.
- Code-file ingestion — Phase 8 territory.
