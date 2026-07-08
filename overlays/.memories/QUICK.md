# Overlays — Quick Memory

## session-tracking overlay → own memory
Handoff-pipeline current state + history moved to `overlays/session-tracking/.memories/{QUICK,KNOWLEDGE}.md` (session 109 split). Latest: **overlay v10** — `customizable:` resume.sh reading-guide region (T-61). This file now covers the overlay SYSTEM only.

## cross-product notes (session 106, 2026-07-04)
- **`ai-backends.yaml` is the product-mature half of a future shared model-registry library (T-76, DEFERRED w/ triggers):** its multi-provider + priority-fallback + `schema_mode` + CLI-subprocess shape merges with `retrieval/config.yaml`'s roles shape when T-76 fires. **Discipline until then: when evolving `ai-backends.yaml`, check `retrieval/config.yaml`'s vocabulary first — no gratuitous shape divergence.** Full record: `docs/ideas/ltg-model-registry-design.md` Part 2 (`ref:model-registry-library-decision`).
- **Topology rule:** overlays and the LTG engine are *products*; both may depend on layer-0 *primitives* (model registry, ref-key grammar, T-77 signature extractor) but NEVER on each other.
- **Future LTG overlay (idea, not scheduled):** would carry per-repo *scaffolding only* (corpus.yaml template, MCP registration, .memories integration); the engine always arrives as a package dependency — the B+C lesson (engine central, config per-repo) applied. See `docs/plans/ltg-repo-split-discovery.md`.

## installer capabilities
- `--verify` mode available (T-58, 2026-06-26): read-only drift check per installed file; exit 1 on any DIFF/MISSING/SRC-MISSING; all categories gate exit (files, always_user_files, user_files, templates, manual_if_exists, merge_sections); EOL-normalized comparison (CRLF=LF).
- **`customizable:` keep-regions — BUILT (overlay v10, T-61 option b):** plan `docs/plans/overlay-customizable-regions.md`. Overlay owns a file EXCEPT named `overlay-keep:<name>`…`/overlay-keep:<name>` regions (repo-owned; shipped default = first-install seed, never re-applied). Explicit comment-agnostic markers (NOT `ref:KEY` — both ref-lookup + `anchors.py` are `*.md`-only, so a `.sh` marker is LTG-inert; only the topic extractor sees ~2 lines of marginal, graph-free noise). No per-region version. `_extract_regions`/`_splice_regions` + `handle_customizable` + `verify_overlay` extension in `lib/actions.py`; wired before `handle_files`. resume.sh moved `files:`→`customizable:` (reading-guide region). 21 tests (installer suite 13→34); live acceptance PASS on a tmp career-search-like copy (region preserved + out-of-region updated + CUSTOMIZED non-gating verify + idempotent). **Algorithmic acceptance-test spec (8 ACCEPT cases, derive an automated harness): `ref:overlay-customizable-acceptance`.** NOT yet propagated to consumer repos — v10 sync (incl. career-search's real §2b variant into the region) is a separate step.

## overlay test runner (2026-06-30)
- `overlays/Makefile` + `overlays/scripts/` — `make -C overlays test` runs **all 221**: `test-ref-indexing` (bash, 9) + `test-session-tracking` (pytest, 178) + `test-installer` (pytest, 34: `test_verify.py` + `test_customizable.py`). Default `make` prints help; `ARGS='-k x'` passes pytest filters to one suite.
- Makefile targets delegate to `scripts/test-<suite>.sh` (each resolves cwd + interpreter) and `scripts/run-all-tests.sh` (aggregator: runs all even on failure, PASS/FAIL summary, nonzero exit on any fail). Suites runnable standalone from shell or CI.
- **NOT a test:** `overlays/test-merge-plan.py` is a manual Ollama model-comparison diagnostic (network, prints JSON) — deliberately excluded from `make test`.
- Add a suite: drop `scripts/test-<name>.sh`, add a `test-<name>` target, list it in `run-all-tests.sh`.

## ref-indexing overlay
- **Version:** v4 (2026-06-30) — bumped for the overlay-shipped test suite
- **Tests:** `files/tests/test-ref-lookup-paths.sh` — fully hermetic (9 tests), builds its own fixture corpus in a `mktemp` dir and runs `ref-lookup.sh --root <fixture>`; NO repo coupling (the old `baseline-*.txt` snapshots were deleted). Covers `--paths` mapping, `.claude/local/` safety filter, dedup invariant, `--paths`↔`--list` consistency, single-key + glob lookup, unknown-key exit.
- **Test home:** overlay source ONLY (`files/tests/`); manifest `files:` installs it to consumer `.claude/tools/tests/`. The source repo does NOT commit an installed copy (it's a generated artifact) — PR #63 review (T-42).
- **Runner:** `make -C overlays test-ref-indexing` (see `## overlay test runner`).
- **Finding:** `--paths` "first occurrence" of a duplicated key follows `grep -r` traversal (filesystem readdir) order, NOT sorted path — so which file wins is unspecified. Test asserts the dedup invariant, not a specific winner.
- **PR:** #63 (`feat/t42-ref-lookup-paths`, --paths flag + this test work); not yet merged into umbrella `batch/session-97-base` (#57).
