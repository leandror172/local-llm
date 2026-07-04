# Overlays — Quick Memory

## session-tracking overlay
- **Version:** v8 (2026-06-26)
- **Status:** T-59 harvest boundary tightened to `chore(session-handoff): session ` COMPLETE (2026-06-26)
- **Tests:** 174 green (173 existing + 1 new `test_prefix_reuse_commit_is_not_a_boundary`)
- **Installed in:** expenses/code, web-research, career-search (per-repo shim/SKILL still v6-era); llm runs the engine from source. Since B+C, the **shared user-level engine** `~/.claude/tools/handoff/` is the v7 code ALL repos execute — reinstalled this session. `session-log.md` latest-only in ALL 4 repos.
- **PR:** #53 (failure-clarity) stacked on #52 (`feature/handoff-redesign-stage-promote`)
- **Home-repo invocation drift:** the `run-handoff.sh` shim guards on `.claude/handoff/registry.yaml` + ignores `--registry`; in the llm repo call `python3 ~/.claude/tools/handoff/handoff.py --payload <p> --registry overlays/session-tracking/files/registry.yaml --repo-root .` directly (see KNOWLEDGE gotcha).
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

## overlay test runner (2026-06-30)
- `overlays/Makefile` + `overlays/scripts/` — `make -C overlays test` runs **all 196**: `test-ref-indexing` (bash, 9) + `test-session-tracking` (pytest, 174) + `test-installer` (pytest, 13, `test_verify.py`). Default `make` prints help; `ARGS='-k x'` passes pytest filters to one suite.
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
