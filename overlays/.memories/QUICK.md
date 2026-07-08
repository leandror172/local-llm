# Overlays — Quick Memory

## session-tracking overlay
- **Version:** v9 (2026-07-06)
- **Status:** v9 handoff-tooling bug sweep COMPLETE (2026-07-06) — T-78 wrapped-bullet parser continuation-join (`payload.py`), T-62 shim honors `--registry` + prefers co-located engine, T-61 resume.sh reading-guide backported (source ⊇ installed). llm commit on `fix/handoff-tooling-bugs`.
- **Tests:** 178 green (174 + 4 new wrapped-bullet tests in `test_payload.py`, T-78)
- **Installed in:** shared user-level engine `~/.claude/tools/handoff/` is **v9** (carries the T-78 `payload.py` fix) — ALL repos execute it. Per-repo files synced v9 (2026-07-06): expenses/code + web-research got `resume.sh` (T-61) + project shim (T-62); career-search got the shim ONLY — its local "What to read first" `resume.sh` variant preserved (T-61 option 2). llm runs the engine from source. `session-log.md` latest-only in ALL repos.
- **PR:** #53 (failure-clarity) stacked on #52 (`feature/handoff-redesign-stage-promote`)
- **Home-repo invocation (FIXED v9, T-62):** the `run-handoff.sh` shim now honors an explicit `--registry` (bypasses the registry-file guard) and prefers a co-located `handoff.py` over the user-level install — so `overlays/session-tracking/files/handoff/run-handoff.sh --registry overlays/session-tracking/files/registry.yaml` works from the llm home repo AND runs source. The old "call `handoff.py` directly" workaround is retired.
- **Key files:** `files/handoff/` (source), `manifest.yaml`, `files/rotate-session-log.sh`, `files/handoff-harvest.sh` (boundary: `^chore(session-handoff): session `), `files/session-handoff/SKILL.md`

### B+C distribution (2026-06-17)
- **Pipeline modules:** always user-level at `~/.claude/tools/handoff/` — new `always_user_files:` manifest key; never per-repo.
- **Shim + SKILL.md:** follow `--install-level` (renamed from `--skill-level`); default `user` → `~/.claude/`; `project` → per-repo `.claude/`.
- **run-handoff.sh:** rewritten as thin shim; calls `$HOME/.claude/tools/handoff/handoff.py`; registry guard (`exit 0` if no registry) makes user-level hooks safe in uninstalled repos.
- **Migration:** 3 target repos committed — old `.py` copies removed, new shim written; `~/.claude/tools/handoff/` populated via installer.
- **Future:** D (pip editable) deferred; G/H remain long-term targets; shim is the stable per-repo seam.

### Session-90 increments (see KNOWLEDGE.md for detail)
- Latest-only topology + value-only payload + git-log harvest + clean break v5→v6.

### Prior rounds (see KNOWLEDGE.md)
- **session-89 stage/promote + session-29 fixes:** `--payload` stage / `--id` promote / `--amend` / `--abort`; error messages name regions `role(target)@file:line`; copy-don't-move; idempotency by commit-title suffix.
- **Deferred:** Increment-4 separate-window synthesis (documented only); local-model Placer (E1–E2) fills the same value schema.

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
