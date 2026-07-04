# LTG Repo Split (T-33) — Frozen Decisions + Execution Plan

**Status:** DECISIONS FROZEN (session 107, 2026-07-04) — ready to execute.
**Task:** T-33 (`.claude/tasks.md`). Discovery record: `docs/plans/ltg-repo-split-discovery.md`
(established facts + the S-D1–S-D7 register this doc freezes). Companion:
`docs/ideas/ltg-model-registry-design.md` Part 2 (`ref:model-registry-library-decision`).
**Estimate:** 1.5–2 sessions (Session A = mechanics, Session B = acceptance + close-out).
**One open input:** the new repo's **name** — placeholder `<ltg-repo>` throughout. Must be
decided before `git init` (Session A, step SP-2). Axis: name the construct (`ltg`,
`latent-topic-graph`) vs. the function (survives technique evolution; keeps "Latent Topic
Graph" as the *paper/concept* name). Cheap to rename in week one; do not over-deliberate.

---

<!-- ref:ltg-split-frozen-decisions -->
## Frozen decisions (S-D1–S-D7, session 107)

- **S-D1 — Consumption path: (a) uv path-dependency on a sibling checkout.** The llm
  instance declares the engine via `[tool.uv.sources]` path reference. Escalate to (b)
  installed/published package when either fires: work from a machine without the engine
  checkout, or first external adopter (tier 3). Declaration survives `uv sync`; flip is a
  one-line consumer change.
- **S-D2 — Instance residency: (c) new top-level `ltg/` dir in the llm repo.** Holds
  `corpus.yaml`, `corpus-manifest.yaml`, `config.yaml` (instance-owned — see Corpus
  Consequences), `index/` (+ `.bak` slots), `probes/`, instance rebuild `run-*.sh`
  wrappers, and the instance half of `.memories/`. Old `retrieval/` disappears entirely.
- **S-D3 — Moves/stays/copies: category-level table below.** History extraction via
  `git filter-repo` is non-destructive — "new repo gets history" and "llm loses the file"
  are independent per-file choices. Addition: an **archive-mining task** — query the llm
  LTG index (`archive` source group) for LTG-relevant session-log content and distill a
  `docs/prehistory.md` in the new repo (pre-split pseudo-log; also T-65 evidence).
- **S-D4 — Bootstrap:** session-tracking + ref-indexing overlays day one (5th tracked
  repo; handoff engine already user-level); own `.memories/` seeded from the engine half
  of `retrieval/.memories/`; minimal CLAUDE.md from `docs/scaffolding-template.md`; same
  `feature/*` PR conventions; **self-indexing corpus day one, build-once scope, as the
  split's decoupling acceptance test**. Name = the register's one open blank.
- **S-D5 — Phase 6 MCP placement: (a) new MCP server in the new repo** (e.g. `mcp/`
  subpackage + `run-server.sh`), registered machine-globally like ollama-bridge.
  ollama-bridge untouched — no product→product dependency (topology rule holds).
- **S-D6 — Packaging flip: during the split.** Packaged layout + `[project.scripts]`
  entry points; S-D1(a) requires an importable package anyway. llm-side *instance*
  wrappers stay bash per `[ref:bash-wrappers]`; engine repo keeps thin bash shims over
  its entry points (whitelist-safety rationale carries over).
- **S-D7 — Cadence:** sessions are single-repo by default; each repo's tracking files are
  written only by its own sessions. Cross-repo touches are bounded tail-steps owned by
  the driving repo (instance rebuild after engine changes = engine-session tail-step,
  logged there; overlay propagation = llm-driven, new repo is a 4th target). Anything
  bigger = two sessions, two handoffs. **Open engine-scoped tasks migrate** to the new
  repo's tasks.md; **done LTG tasks are copied** into the new repo's `docs/prehistory.md`
  for history (llm's record stays in `.claude/archive/`, not tasks.md). Engine↔instance
  sync is pull-based/lazy; pin via tags only if a breakage ever forces it (note, don't
  build). GPU sequential-constraint rules unchanged.
<!-- /ref:ltg-split-frozen-decisions -->

---

## What moves / stays / copies (S-D3 resolution)

| Category | New repo (w/ history) | llm repo | Notes |
|---|---|---|---|
| Engine code, tests, `pyproject.toml`/`uv.lock`, `prompts/` | ✅ move | ❌ delete | The split itself. Packaging flip lands after history extraction. |
| Phase plans (`docs/plans/ltg-*`, `2026-04-13-latent-topic-graph-implementation.md`) | ✅ move | ❌ delete + index.md pointers | Not llm corpus roots — no llm index impact. Their ref blocks become new-repo anchors. |
| `retrieval/DECISIONS.md`, `spike-*.md` | ✅ move | ❌ delete | Ref-coupling handled by SP-9 sweep. |
| `retrieval/probes/` | ✅ move | ❌ delete | Engine evidence. Future *instance* probes land in `ltg/probes/`. |
| `docs/diagrams/ltg-phase4-dataflow.md` | ✅ move | ❌ delete + pointer | Engine operational model. |
| `retrieval/.memories/` | ✅ move, split content | ⚠️ instance half → `ltg/.memories/` | One-time engine-vs-instance tease-apart at move time. |
| Concept + smart-rag research/ideas (`docs/research/latent-topic-graph.md`, `smart-rag-*`, `docs/ideas/smart-rag*`) | ✅ copy (history extract) | ✅ keep | Dual citizenship: LTG lineage AND llm corpus/chatbot content. Frozen historical docs — drift risk ≈ 0. |
| `docs/ideas/ltg-model-registry-design.md` | ✅ copy | ✅ keep | T-76 is a shared decision both repos cite. |
| `.claude/archive/` session logs | ❌ (mined, not moved) | ✅ keep | Distilled into `docs/prehistory.md` via SP-14. |
| `corpus.yaml`, `corpus-manifest.yaml`, `config.yaml`, `index/`, rebuild wrappers | ❌ | ✅ → `ltg/` | Instance data + instance tuning (see below). |

### Corpus + config consequences (verified session 107)

- **`docs/plans/` is NOT an llm corpus root** (`corpus.yaml` include_roots: docs/research,
  docs/ideas, .claude/archive, .claude/skills, .claude/tools + named files + `.memories`
  glob). Moving the phase plans does not shrink the llm topic index.
- **Anchor delta is real and expected:** ref blocks inside moved files (`DECISIONS.md`
  `ref:ltg-scope` etc., phase-plan refs like `ref:ltg-phase4-plan`, `ref:ltg-split-decisions`)
  are anchors in today's 147. Post-split llm rebuild shows a **lower anchor count by
  exactly the moved-key set** — acceptance verifies the delta is explainable, not that
  counts are identical. `retrieval/.memories/` → `ltg/.memories/` changes those rows'
  `file_path` (glob still matches).
- **`config.yaml` is instance-owned.** Its `graph:` thresholds (τ=0.70/K=10) were probed
  on the llm corpus; roles/temps are instance tuning. llm's copy lives in `ltg/`; the
  engine ships a commented template (`config.example.yaml`); the new repo's self-index
  gets its own copy. `prompts/` are engine-owned and move.

---

## Execution plan

### Session A — mechanics

- **SP-1 — Preflight.** Clean tree both ends; `pip install git-filter-repo` (or uv tool);
  decide `<ltg-repo>` name (blocking input); fresh clone of llm as filter-repo workspace
  (filter-repo rewrites history — never run it in the working checkout).
- **SP-2 — History extraction + new repo.** In the scratch clone, `git filter-repo` with
  the full move+copy path set (table above; use `--path` per entry, `--path-rename
  retrieval/:src-staging/` optional — final layout is SP-3's job). Push result to the new
  `<ltg-repo>` origin. Verify: `git log --follow` works on a sample moved file
  (`store.py`, master plan).
- **SP-3 — Packaging flip (new repo).** Restructure to packaged layout (package dir named
  at SP-1, e.g. `src/<pkg>/`), `[project.scripts]` entry points for the pipeline stages +
  inspect + relate, thin bash shims kept, `package = false` removed, tests green under
  `uv run pytest` (377 baseline). One commit on top of extracted history.
- **SP-4 — REPO_ROOT kill (new repo).** Remove `Path(__file__).parent.parent` from **all
  seven** modules (`store.py`, `embed.py`, `extract_topics.py`, `ltg_inspect.py`,
  `sweep_extractors.py`, `viz_sweep.py`, `build_corpus_manifest.py`). Invariant: corpus
  root + index path + config path are explicit inputs (CLI args / function params) with
  no engine-location-derived defaults. Anchors' zero-ref degradation stays graceful
  (no ref keys → empty anchor source, not an error).
- **SP-5 — Bootstrap (new repo).** Minimal CLAUDE.md; `.claude/` scaffolding; overlays
  (session-tracking + ref-indexing) installed; `.memories/` = engine half of the old
  `retrieval/.memories/`; tasks.md seeded with migrated open tasks (SP-8 list);
  `config.example.yaml`; own `corpus.yaml` over its own `docs/` (self-index prep);
  `index/` gitignored.
- **SP-6 — llm instance dir.** Create `ltg/` per S-D2; move instance files in; rewrite
  rebuild wrappers to invoke engine entry points via the uv path-dependency
  (`[tool.uv.sources]` → sibling checkout); delete `retrieval/`.
- **SP-7 — llm doc surgery.** Delete moved docs; add index.md pointers ("moved to
  `<ltg-repo>`"); update `.claude/index.md` tables, `session-context.md` reading guide,
  root + `overlays/.memories` mentions of `retrieval/`.
- **SP-8 — Task migration.** Move open engine tasks to new repo tasks.md: T-34, T-35,
  T-38–T-41, T-63, T-64, T-72(1)(3), T-73, T-74, T-75 (+ Phases 6–9 as roadmap entries).
  Stay in llm: T-76/T-77 (layer-0 primitive candidates — llm is the coordination repo
  until a primitives home exists), instance-scoped items. Copy done LTG tasks + phase
  completions into new repo `docs/prehistory.md` (skeleton; SP-14 fills the mined half).
- **SP-9 — Ref-key sweep.** `ref-lookup.sh --paths | grep ltg` before deletion:
  enumerate every `ref:ltg-*` key and its llm-side consumers (index.md, session-context,
  CLAUDE.md, memories). Instance-operational content (rebuild order, threshold provenance)
  gets a slim `ltg/OPERATIONS.md` with its own ref blocks; stale consumers updated;
  keys that moved get pointer lines, not duplicated blocks.

### Session B — acceptance + close-out

- **SP-10 — llm regression rebuild.** From `ltg/`, full `run-rebuild-all.sh` against the
  sibling engine. PASS = 875 topics unchanged; anchor/edge deltas exactly explained by
  moved ref keys + `.memories` path change; spot-check one known `relate()` pair.
- **SP-11 — Self-index build (decoupling acceptance).** In the new repo: freeze its
  manifest, extract → embed → store → anchors → graph → communities over its own docs
  (~25 files, ~10–15 min GPU). PASS = pipeline end-to-end with explicit corpus root ≠
  engine assumption anywhere; anchors found from moved ref blocks (small nonzero set);
  one verified `relate()` pair on two moved phase plans. **Build-once scope** — freshness
  is not maintained; that's a future instance concern.
- **SP-12 — Overlay + tracking verification.** Handoff stage+promote works in the new
  repo (5th repo); `install-overlay.py --verify` clean.
- **SP-13 — Close-out.** T-33 checked off; llm session-log + memories updated; new repo
  README stub (portfolio driver: README/quickstart/demo-transcript polish is the
  *cheap-and-early* tier-3 item — a transcript of the tool relating its own design docs
  is the natural demo).
- **SP-14 — Archive mining (post-split, may be its own short session).** Query the llm
  index (archive source group) for LTG-relevant session-log content; distill into new
  repo `docs/prehistory.md` with pointers back to llm archives. Doubles as T-65 evidence
  (archive up-weighting for decision-history queries) and first self-referential use.

### Ordering constraints

filter-repo extraction (SP-2) **before** any restructuring — history stays navigable with
the rename as one commit on top. SP-6 (llm side) only after SP-3/SP-4 prove the engine
imports and runs from the new home. SP-10 before SP-11 (regression first isolates
llm-side breakage from engine-side).

---

## Risks / gotchas

- **Seven REPO_ROOT sites, not one.** Discovery doc said `store.py:44`; session-107 check
  found the same pattern in six more modules (`ltg_inspect.py` also derives
  `DEFAULT_INDEX`/`DEFAULT_CONFIG` from it). SP-4 covers all seven; grep for
  `parent.parent` as the exit check.
- **filter-repo is destructive to its clone** — always run in a scratch clone (SP-1).
- **Anchor-count acceptance trap:** "identical counts" would fail legitimately; the delta
  is the assertion (see Corpus Consequences).
- **DECISIONS.md ref-coupling** is the silent breakage nobody rediscovers cheaply — SP-9
  runs *before* deletion so the consumer list is complete.
- **GPL (tier-3 only):** leidenalg GPL-3 / python-igraph GPL-2 travel with the engine.
  Internal use unaffected; product license decided when tier 3 is real (discovery doc
  licensing note; T-72(3) caveat).
- **Name is the only blocking human input** — everything else in Session A is mechanical.
