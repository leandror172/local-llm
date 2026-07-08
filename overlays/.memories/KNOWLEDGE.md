# overlays/ — Knowledge (Semantic Memory)

*Overlay system decisions. Read on demand.*

## Why Overlays Exist (2026-03)

Three repos need the same operational patterns: ref-indexing for documentation lookups,
session tracking for continuity across Claude Code sessions, local model conventions
for verdict recording and retry policy. Copying files manually drifts. Overlays make
cross-repo consistency installable and version-tracked.

**Rationale:** The alternative was documenting conventions and hoping each repo
implements them correctly. Overlays encode conventions as installable packages.
**Implication:** New cross-cutting patterns should become overlays, not wiki pages.

## Merge Markers for Versioning (2026-03)

Overlay content injected into shared files (like CLAUDE.md) is wrapped in markers:
`<!-- overlay:ref-indexing v1 -->`. On update, the installer detects the old version,
removes the old content, and inserts the new version.

**Rationale:** CLAUDE.md is a shared file — multiple overlays and manual content coexist.
Markers let the installer find and replace its own content without touching the rest.
**Implication:** Manual edits inside overlay markers will be overwritten on update.
Customizations should go outside the markers.

## AI-Assisted Merge Mode (2026-03)

When `--mode ai` is used, an LLM plans where to insert overlay sections into existing
files. The planner outputs structured JSON (insert_after_line, delete_ranges), which
is then applied deterministically — the AI plans, code executes.

Backends (priority order): Ollama qwen3:14b with thinking, Ollama deepseek-r1:14b,
Claude CLI subprocess, Claude API direct.

**Rationale:** CLAUDE.md files have varying structure. Hard-coding insertion points
would break across repos. AI reads the target file and decides the right location.
**Implication:** AI merge is optional — manual mode always works. AI mode saves time
on initial install but manual review is still recommended.

## Manifest Schema (2026-03)

Each overlay has a `manifest.yaml` defining what to install:
- `files` — copy to destination (tools, scripts)
- `templates` — create only if missing (user-managed after creation)
- `merge_sections` — inject into shared files with merge hints
- `append_lines` — idempotent append to .gitignore, .githooks, etc.
- `manual_if_exists` — flag files that need human judgment if already present
- `customizable` — overlay owns the file except named `overlay-keep:<name>` regions the
  repo owns (T-61; see "Customizable Keep-Regions" below)

**Rationale:** Declarative manifest over imperative script. The installer interprets
the manifest; the overlay author declares intent.
**Implication:** Adding a new overlay requires only a manifest and content files,
no changes to the installer itself.

## User-Level vs Project-Level Install (2026-03, updated 2026-06-17)

`--install-level` (renamed from `--skill-level`) controls where the run-handoff shim
and SKILL.md land: `user` (default) → `~/.claude/`; `project` → `.claude/` per-repo.
Pipeline `.py` modules always go to `~/.claude/tools/handoff/` regardless of this flag
(`always_user_files:` manifest key). The shim includes a registry guard so user-level
hooks no-op in repos without the overlay installed.

**Rationale:** Skills and shims are useful everywhere; user-level avoids duplicating
them. Pipeline modules must be shared (one copy, no drift). Self-contained repo install
still possible with `--install-level project`.
**Implication:** Per-repo installs only store the shim + SKILL.md + registry + templates;
Python files are always a machine-level shared resource.

## Session-Handoff Pipeline — memory moved to session-tracking/.memories (session 109)

The handoff-pipeline architecture + per-session redesign history (pipeline arch, stage/promote,
session-29 fixes, session-90 latest-only topology, session-93 append↔checkoff + failure-clarity,
the home-repo shim + reinstall gotcha) now lives in its own per-folder memory:
`overlays/session-tracking/.memories/{QUICK,KNOWLEDGE}.md`. This file keeps overlay-SYSTEM
knowledge only — installer mechanics, manifest schema, verify, customizable, test convention,
product topology.

## Customizable Keep-Regions (`customizable:` category, T-61, 2026-07-08, overlay v10)

A sixth install category: the overlay owns a file EXCEPT named `overlay-keep:<name>` …
`/overlay-keep:<name>` regions, which are **repo-owned** — seeded on first install and never
overwritten again (the shipped default is a seed only). Closes T-61's remaining half: a repo
(career-search) keeps a local tweak inside an overlay-managed script while still receiving every
OTHER update to that file.

- **Ownership rule:** outside regions overlay-owned (always new source); inside a region
  repo-owned (installed content always preserved; reset to source default + WARN only if the repo
  dropped the marker — decision 3). No per-region version — the overlay never rewrites the region,
  so nothing to version; the overlay `version:` covers the file.
- **Marker = plain comment, NOT `ref:KEY`.** Anchoring on the LTG ref grammar was considered and
  rejected: both `ref-lookup.sh` and LTG `anchors.py` restrict to `*.md` (`anchors.py:138`
  git-greps `-- "*.md"`), so a `ref:`-style marker in a `.sh` is invisible to both — it would look
  resolvable yet resolve nowhere, and the ref-marker grammar (an HTML-comment `ref:<key>` with keys
  limited to `[a-z0-9-]`) can't carry a version token.
  The markers therefore do NOT touch the anchor graph; the only LTG-visible effect is the code-arm
  topic extractor seeing ~2 extra comment lines (marginal, format-independent) — acceptable, unlike
  the prose-tracking-file pollution the handoff register was built to avoid.
- **Inverse of `merge_sections`:** merge_sections = overlay owns one marked section inside a *user*
  file (rewritten every update); customizable = *repo* owns marked regions inside an overlay file
  (never rewritten). Same marker+splice machinery, mirrored ownership.
- **`--verify`:** per-region SAME / CUSTOMIZED (non-gating — the sanctioned use of the seam) / DIFF
  for out-of-region drift (gates). `resume.sh` moved `files:`→`customizable:` (v10).
- **Code:** `_extract_regions`/`_splice_regions` (comment-agnostic parse; negative lookbehind so the
  close token isn't read as an open) + `handle_customizable` + `verify_overlay` ext in
  `lib/actions.py`; wired before `handle_files` (exactly one category owns a path). 21 tests,
  installer suite 13→34, live acceptance PASS. Plan + algorithmic acceptance spec
  (`ref:overlay-customizable-acceptance`): `docs/plans/overlay-customizable-regions.md`.

**Rationale:** the reinstall-clobber failure (see `session-tracking/.memories` — Reinstall gotcha)
needed a seam that neither freezes the file (`templates:`) nor nags every run (`manual_if_exists:`)
nor overwrites (`files:`). **Implication:** any overlay-owned script with a per-repo-tunable region
declares `customizable:` + wraps that region; the region content becomes the repo's, permanently.

## Installer --verify mode (T-58, 2026-06-26) — IMPLEMENTED

`verify_overlay(manifest, overlay_dir, target_root, install_level) -> tuple[int,int,int]` in
`lib/actions.py` — 13 tests in `overlays/test_verify.py` (all green).

**Key design decisions:**
- **EOL-normalized SAME:** `_norm(p) = p.read_bytes().replace(b'\r\n',b'\n').rstrip(b'\n')` —
  CRLF↔LF and sole trailing-newline differences are SAME. Intentionally decouples from installer's
  byte-exact `sha256` SKIP (T-29 remains open).
- **Decision (a) — everything gates exit:** `templates` and `manual_if_exists` DIFF/MISSING both
  increment the failing tally (n_diff/n_missing), same as overlay-owned categories. `USER-MANAGED`
  label appears in the report for readability only — NOT a signal that failures are ignored.
- **merge_sections uses version-marker mechanism:** `open_pattern` regex checks installed version
  number (SAME = match; DIFF = mismatch; MISSING = no marker or dest absent). Does NOT compare
  section content byte-by-byte.
- **$HOME isolation mandatory in tests:** `always_user_files` and user-level `user_files` resolve
  under `Path.home()`; tests monkeypatch `HOME` to a tmp dir.
- **`verify_overlay` returns tally; `main()` derives exit from tally** — never parses `report._actions`.
- **CLI branch:** `--verify` branch fires after header print, before any `handle_*` call; runs
  `verify_overlay`, `print_report`, `sys.exit(1 if any(tally) else 0)` — never enters install path.

**Source-dir mapping (mirrors the handle_* resolution exactly):**
- `files:` → `overlay_dir/files/<src_name>`
- `always_user_files:` → same `files_dir`; dest always `~/.claude/<dest_rel>`
- `user_files:` → same `files_dir`; dest `~/.claude/` or `target/.claude/` per level
- `templates:` → `overlay_dir/templates/<tmpl_name>`
- `manual_if_exists:` → `overlay_dir/files/<basename(dest_rel)>` (NOT templates dir)

## Model-registry library decision + product topology (2026-07-04, session 106)

Session-106 product-framing discussion (T-33 LTG repo split) produced decisions that bind
overlays. Authoritative record: `docs/ideas/ltg-model-registry-design.md` Part 2
(`ref:model-registry-library-decision`) + `docs/plans/ltg-repo-split-discovery.md`.

- **`ai-backends.yaml` is one of two parents of a future shared registry library (T-76).**
  Prior-art survey concluded: provider *transport* is commodity (LiteLLM/any-llm — delegate,
  never rebuild); the *registry/roles layer* is the unowned library-worthy part. ai-backends
  contributes multi-provider, priority fallback, `schema_mode` strategy, and the CLI-subprocess
  backend (nobody else has it); `retrieval/config.yaml` contributes semantic roles + provider
  quirk encoding. Extraction DEFERRED — triggers: first non-Ollama provider in LTG, first
  external adopter, or a third internal consumer of the shape.
  **Rationale:** both implementations are contained (backends resolution in `overlays/lib`,
  `load_config()` in one retrieval module) so deferral stays cheap; real requirements arrive
  with the first cross-provider consumer.
  **Implication:** evolving `ai-backends.yaml` requires checking `retrieval/config.yaml`'s
  vocabulary first (no gratuitous divergence); when T-76 fires, design multi-provider from day one.
- **Topology rule — products depend on primitives, never product↔product:** overlays and the
  LTG engine are products; shared needs (model registry, ref-key grammar, signature extractor
  T-77) become layer-0 primitives both consume. Resolves "registry as public dep — and vice
  versa?" with: no vice versa, ever.
  **Implication:** never import LTG-engine code into overlay tooling (or vice versa); extract
  a primitive instead.
- **Future LTG overlay = scaffolding-only:** if/when LTG ships an overlay, it carries per-repo
  config (corpus.yaml template, MCP registration, .memories integration) — the engine is a
  package dependency, never overlay-distributed files. This is the B+C lesson (engine central,
  config per-repo; wholesale-overwrite + stale-engine propagation were the paid-for failure
  modes) applied to a second product.

## Overlay Test Convention — hermetic + ships with the overlay (2026-06-30, ref-indexing v4)

PR #63 review (T-42) established how overlay code is tested. Three rules, each with a reason
that generalizes to every future overlay suite:

- **Tests live with the overlay source, not the consumer tree.** Authored test → `files/tests/`
  (co-located with the code it exercises, mirroring `session-tracking`'s `files/handoff/test_*.py`);
  the manifest `files:` map installs it into consumer repos' `.claude/tools/tests/`. The source repo
  does NOT commit an installed copy — that's a generated artifact. *Rationale:* the reviewer flagged
  a test sitting in `.claude/tools/tests/` (the install surface) as "the wrong place"; the overlay is
  the single source of truth, consumers receive a copy. *Caveat:* a pre-existing installed copy of a
  *script* (e.g. `.claude/tools/ref-lookup.sh`) is left alone — the "source-only" rule applies to
  *new* artifacts, not a retro-cleanup of every installed file (that's a separate broader task).

- **Tests must be hermetic — zero repo coupling.** Each case builds its own fixture corpus in a
  `mktemp` dir and points the tool at it via `--root <fixture>`. The tool only ever sees content the
  test authored (the "clean container" model). *Rationale:* the original test diffed against
  `baseline-*.txt` snapshots captured from THIS repo's ref blocks, so any unrelated edit to the repo's
  documentation could flip the test result — exactly the dependency a test must not have. A repo
  change must never risk a test outcome. The `--root` flag (already on `ref-lookup.sh`) is the
  isolation boundary that makes this possible; design new overlay tools with such a flag so their
  tests can be hermetic.
  - *Sub-finding:* hermeticity also exposed that `--paths` "first occurrence" of a duplicated key
    follows `grep -r` filesystem-traversal (readdir) order, NOT sorted path. Asserting a *specific*
    winner would just relocate the non-determinism from repo-content to filesystem-order, so the test
    asserts the **dedup invariant** (collapses to one real occurrence), which IS the tool's contract.

- **A `make` runner is the aggregation seam (extended 2026-06-30).** `overlays/Makefile` now wires **all
  three existing suites** — `test-ref-indexing` (bash, 9), `test-session-tracking` (pytest, 174),
  `test-installer` (pytest, 13) = **196 total** — behind one `make test`; bare `make` prints help; paths
  resolve via the Makefile's own dir (`$(dir $(realpath ...))`) so it runs from any invocation point.
  Targets **delegate to `overlays/scripts/` runners** (`test-<suite>.sh` each resolve the right cwd +
  interpreter; `run-all-tests.sh` aggregates with a PASS/FAIL summary and nonzero-on-any-fail), so the
  exact invocation works from make, a bare shell, or CI. `ARGS='-k x'` forwards pytest filters to one
  suite. *Rationale:* the per-suite cwd/interpreter quirks (handoff tests need their own dir on the path;
  `test_verify.py` needs `overlays/` as cwd) belong in scripts, not Makefile recipes — the Makefile stays
  a thin index, the scripts are reusable outside make. `make test` works precisely *because* suites are
  hermetic (a runner needs only exit 0, no opinion about repo state). *Excluded:* `overlays/test-merge-plan.py`
  is a manual Ollama model-comparison diagnostic (network, prints JSON), NOT an automated suite — kept out
  of `make test`. *Implication:* a new overlay suite wires in as a `scripts/test-<name>.sh` runner + a
  `test-<name>` target + one line in `run-all-tests.sh`.
