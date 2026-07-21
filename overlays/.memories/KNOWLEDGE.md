# overlays/ — Knowledge (Semantic Memory)

*Concept-organized current truth for the overlay SYSTEM — installer mechanics, manifest
schema, verify, test convention, product topology. Read on demand. Each section ends with
"Source / more detail" pointers to the records holding the full findings. Chronology lives
in `git log -- overlays/`.*

*The `session-tracking` overlay has its own per-folder memory —
`overlays/session-tracking/.memories/{QUICK,KNOWLEDGE}.md` — holding the handoff-pipeline
architecture, invariants, and history. Nothing about that pipeline belongs here.*

*What belongs here: whatever a model should know before working on the overlay system,
that it would otherwise have to read `install-overlay.py` / `lib/actions.py` to learn.
Test for inclusion: "would this save a read-the-source round-trip?"*

*Write protocol: UPDATE the relevant concept section in place; replace superseded values,
don't append a dated block. Add a new section only for a genuinely new concept. Status
trivia (test counts, open PRs, current versions) belongs in `QUICK.md`, not here.*

---

<!-- ref:overlay-system-rationale -->
## Why Overlays Exist

Several repos need the same operational patterns: ref-indexing for documentation lookups,
session tracking for continuity across Claude Code sessions, local model conventions
for verdict recording and retry policy. Copying files manually drifts. Overlays make
cross-repo consistency installable and version-tracked.

**Rationale:** The alternative was documenting conventions and hoping each repo
implements them correctly. Overlays encode conventions as installable packages.
**Implication:** New cross-cutting patterns should become overlays, not wiki pages.
<!-- /ref:overlay-system-rationale -->

---

<!-- ref:overlay-merge-markers -->
## Merge Markers for Versioning

Overlay content injected into shared files (like CLAUDE.md) is wrapped in markers:
`<!-- overlay:ref-indexing v1 -->`. On update, the installer detects the old version,
removes the old content, and inserts the new version.

**Rationale:** CLAUDE.md is a shared file — multiple overlays and manual content coexist.
Markers let the installer find and replace its own content without touching the rest.
**Implication:** Manual edits inside overlay markers will be overwritten on update.
Customizations go outside the markers — or into a `customizable:` keep-region.

**The version is the ONLY trigger — content changes alone do not propagate.** Because the
installer decides by comparing the installed marker version against the manifest, editing a
`sections/*.md` file without bumping `manifest.yaml: version:` produces a **half-propagated
overlay that reports success**: the `files:` entries (hash-based) update normally while the
merge section dry-runs as `[SKIP] CLAUDE.md — already installed vN`. `--verify` will not catch
it either — the installed marker still matches what was installed; it just no longer matches
what the source now says. **Rule: a section edit and a version bump belong in the same commit.**
Found 2026-07-21 propagating `ollama-scaffolding` v2→v3 (T-105); the dry run said SKIP for all
three consumer repos and the corrected verdict rule would have reached none of them.

**Corollary — dry-run against the real repo root.** `--target` must be the directory that *is*
the git repo: `expenses/code`, not `expenses/`. Targeting a parent reports
`[CREATE] CLAUDE.md — file missing` and would fabricate a `CLAUDE.md` + `.claude/` in a
non-repo directory. Read every dry-run line: `[SKIP] … already installed` looks like healthy
idempotence and is exactly what a missed version bump looks like.
<!-- /ref:overlay-merge-markers -->

---

<!-- ref:overlay-ai-merge-mode -->
## AI-Assisted Merge Mode

When `--mode ai` is used, an LLM plans where to insert overlay sections into existing
files. The planner outputs structured JSON (`insert_after_line`, `delete_ranges`), which
is then applied deterministically — **the AI plans, code executes.**

Backends (priority order): Ollama qwen3:14b with thinking, Ollama deepseek-r1:14b,
Claude CLI subprocess, Claude API direct.

**Rationale:** CLAUDE.md files have varying structure. Hard-coding insertion points
would break across repos. AI reads the target file and decides the right location.
**Implication:** AI merge is optional — manual mode always works. AI mode saves time
on initial install but manual review is still recommended.

**Stage → apply split (T-81 Part 1, 2026-07-12).** `--mode ai` on an unmarked target
is now two explicit verbs (mirrors the handoff pipeline's stage/promote):
- `--stage` (early-branch, requires `--mode ai`): calls the model, prints a unified
  diff, writes a durable plan-handle under `<target>/.claude/local/overlay-merge-plans/`
  (gitignored), and does **not** touch the target.
- `--apply-plan <handle>` (early-branch): re-reads the handle, applies deterministically,
  backs up, writes.
- `--dry-run` stays **pure**: records `"would AI-merge … run --stage"` — no model call,
  no write. (Chosen over overloading `--dry-run` to be the stage: that would fire a
  multi-minute GPU call + write a file as a side effect of an ordinary full-sequence
  preview — a special-case bolted onto a general mechanism.)

**Staleness invariant (the one new safety property).** A plan's `insert_after_line` /
`delete_ranges` are line numbers valid ONLY against the exact pre-image they were
computed from. The handle stores `target_pre_sha256 = sha256(LF-normalized pre-image)`
plus the overlay-range-CORRECTED plan. `apply_staged_plan` aborts — records `STALE`,
writes nothing, exits 1 — unless `sha256(current) == target_pre_sha256` (checked BEFORE
any write, `planner.py:330`). Hashing is LF-normalized both ends, so a pure CRLF↔LF
change is not STALE and `_write_text_eol` preserves the target's EOL.

Handle schema `overlay-merge-plan/v1`; seam in `lib/planner.py` (`stage_merge` /
`apply_staged_plan` / `_compute_merge_plan` / `stage_all_sections`). Tests:
`overlays/test_merge_stage_apply.py` (13). Completion/latency (num_ctx, arm) is T-81 Part 2.

Source / more detail: `overlays/test-merge-plan.py` (a manual model-comparison
diagnostic, deliberately excluded from `make test`);
`docs/plans/t81-part1-merge-preview-stage-apply.md`.
<!-- /ref:overlay-ai-merge-mode -->

---

<!-- ref:overlay-manifest-schema -->
## Manifest Schema — six install categories

Each overlay has a `manifest.yaml` declaring what to install. **Exactly one category owns
any given path.**

| category | ownership | on update |
|---|---|---|
| `files` | overlay | overwrite (with backup) |
| `customizable` | overlay, except `overlay-keep:<name>` regions | overwrite outside regions only |
| `templates` | user, after creation | create only if missing |
| `merge_sections` | overlay owns one marked section inside a user file | rewrite that section |
| `append_lines` | shared | idempotent append (`.gitignore`, `.githooks`) |
| `manual_if_exists` | user | flag for human judgment, never overwrite |

Plus the install-level variants `always_user_files:` and `user_files:` (see install levels
below).

**Rationale:** Declarative manifest over imperative script. The installer interprets
the manifest; the overlay author declares intent.
**Implication:** Adding a new overlay requires only a manifest and content files,
no changes to the installer itself.

Source / more detail: `overlays/install-overlay.py`, `overlays/lib/actions.py`.
<!-- /ref:overlay-manifest-schema -->

---

<!-- ref:overlay-install-levels -->
## User-Level vs Project-Level Install

`--install-level` (renamed from `--skill-level`) controls where per-repo seams land:
`user` (default) → `~/.claude/`; `project` → `.claude/` per-repo. Files declared under
`always_user_files:` go to `~/.claude/` **regardless of this flag**.

The canonical application is the handoff pipeline: its `.py` modules are
`always_user_files:` (one shared engine, no drift), while the shim + SKILL.md follow the
flag. The shim carries a registry guard so user-level hooks no-op in repos without the
overlay installed. Project-level copies SHADOW the global ones.

**Rationale:** Skills and shims are useful everywhere; user-level avoids duplicating
them. Engine modules must be shared (one copy, no drift). A self-contained repo install
is still possible with `--install-level project`.
**Implication:** Per-repo installs store only the shim + SKILL.md + registry + templates;
engine code is always a machine-level shared resource. **Corollary (the paid-for failure
mode): a partial propagation leaves a repo running a stale engine against a current
register.** Byte-verify propagation, or run `--verify`.
<!-- /ref:overlay-install-levels -->

---

<!-- ref:overlay-customizable-category -->
## Customizable Keep-Regions (`customizable:`)

The overlay owns a file EXCEPT named `overlay-keep:<name>` … `/overlay-keep:<name>`
regions, which are **repo-owned** — seeded on first install and never overwritten again
(the shipped default is a **seed only**). This lets a repo keep a local tweak inside an
overlay-managed script while still receiving every OTHER update to that file.

- **Ownership rule:** outside regions overlay-owned (always new source); inside a region
  repo-owned (installed content always preserved; reset to source default + `WARN` only if
  the repo dropped the marker — decision 3). **No per-region version** — the overlay never
  rewrites the region, so there is nothing to version; the overlay `version:` covers the file.
- **Marker = plain comment, NOT `ref:KEY`.** Anchoring on the LTG ref grammar was considered
  and rejected: both `ref-lookup.sh` and LTG's `anchors.py` restrict to `*.md`
  (`anchors.py:138` git-greps `-- "*.md"`), so a `ref:`-style marker in a `.sh` is invisible
  to both — it would look resolvable yet resolve nowhere — and the ref-marker grammar (an
  HTML-comment `ref:` key limited to `[a-z0-9-]`) cannot carry a version token. The markers
  therefore do NOT touch the anchor graph; the only LTG-visible effect is the code-arm topic
  extractor seeing ~2 extra comment lines (marginal, format-independent).
- **Inverse of `merge_sections`:** merge_sections = overlay owns one marked section inside a
  *user* file (rewritten every update); customizable = *repo* owns marked regions inside an
  *overlay* file (never rewritten). Same marker + splice machinery, mirrored ownership.
- **`--verify`:** per-region `SAME` / `CUSTOMIZED` (non-gating — the sanctioned use of the
  seam) / `DIFF` for out-of-region drift (gates).
- **Code:** `_extract_regions` / `_splice_regions` (comment-agnostic parse; a negative
  lookbehind stops the close token being read as an open, since `/overlay-keep:n` contains
  `overlay-keep:n`) + `handle_customizable` + a `verify_overlay` extension, all in
  `lib/actions.py`. Wired **before** `handle_files` — exactly one category owns a path.

**Rationale:** the reinstall-clobber failure needed a seam that neither freezes the file
(`templates:`) nor nags every run (`manual_if_exists:`) nor overwrites (`files:`).
**Implication:** any overlay-owned script with a per-repo-tunable region declares
`customizable:` and wraps that region; the region content becomes the repo's, permanently.

Source / more detail: `docs/plans/overlay-customizable-regions.md` (design + the
algorithmic acceptance spec, `ref:overlay-customizable-acceptance`);
`docs/plans/overlay-v10-propagation.md` (the decision-3 clobber hazard).
<!-- /ref:overlay-customizable-category -->

---

<!-- ref:overlay-verify-mode -->
## Installer `--verify` mode

`verify_overlay(manifest, overlay_dir, target_root, install_level) -> tuple[int,int,int]`
in `lib/actions.py`.

**Key design decisions:**
- **EOL-normalized SAME:** `_norm(p) = p.read_bytes().replace(b'\r\n', b'\n').rstrip(b'\n')`
  — CRLF↔LF and sole-trailing-newline differences are `SAME`. Intentionally decoupled from
  the installer's byte-exact `sha256` SKIP (T-29 remains open).
- **Everything gates exit:** `templates` and `manual_if_exists` `DIFF`/`MISSING` both
  increment the failing tally, same as overlay-owned categories. The `USER-MANAGED` label
  is for report readability only — **not** a signal that failures are ignored.
- **merge_sections uses the version-marker mechanism:** the `open_pattern` regex checks the
  installed version number (`SAME` = match; `DIFF` = mismatch; `MISSING` = no marker or dest
  absent). It does NOT compare section content byte-by-byte.
- **`$HOME` isolation is mandatory in tests:** `always_user_files` and user-level `user_files`
  resolve under `Path.home()`; tests monkeypatch `HOME` to a tmp dir.
- **`verify_overlay` returns the tally; `main()` derives exit from the tally** — never parses
  `report._actions`.
- **CLI branch:** `--verify` fires after the header print, before any `handle_*` call; runs
  `verify_overlay`, `print_report`, `sys.exit(1 if any(tally) else 0)` — it never enters the
  install path.

**Source-dir mapping (mirrors the `handle_*` resolution exactly):**
- `files:` → `overlay_dir/files/<src_name>`
- `always_user_files:` → same `files_dir`; dest always `~/.claude/<dest_rel>`
- `user_files:` → same `files_dir`; dest `~/.claude/` or `target/.claude/` per level
- `templates:` → `overlay_dir/templates/<tmpl_name>`
- `manual_if_exists:` → `overlay_dir/files/<basename(dest_rel)>` (NOT the templates dir)

Source / more detail: `overlays/test_verify.py`; T-58.
<!-- /ref:overlay-verify-mode -->

---

<!-- ref:overlay-topology-rule -->
## Product topology + the model-registry decision

Products depend on primitives, **never product ↔ product**. Overlays and the LTG engine are
products; shared needs (model registry, ref-key grammar, signature extractor T-77) become
layer-0 primitives that both consume. This resolves "registry as a public dep — and vice
versa?" with: **no vice versa, ever.**
**Implication:** never import LTG-engine code into overlay tooling or vice versa; extract a
primitive instead.

- **`ai-backends.yaml` is one of two parents of a future shared registry library (T-76).**
  The prior-art survey concluded: provider *transport* is commodity (LiteLLM / any-llm —
  delegate, never rebuild); the *registry/roles layer* is the unowned library-worthy part.
  `ai-backends` contributes multi-provider, priority fallback, `schema_mode` strategy, and the
  CLI-subprocess backend (nobody else has it); LTG's `config.yaml` contributes semantic roles
  + provider quirk encoding. Extraction is DEFERRED — triggers: the first non-Ollama provider
  in LTG, the first external adopter, or a third internal consumer of the shape.
  **Rationale:** both implementations are contained (backends resolution in `overlays/lib`,
  `load_config()` in one LTG module) so deferral stays cheap; real requirements arrive with the
  first cross-provider consumer.
  **Implication:** evolving `ai-backends.yaml` requires checking LTG's `config.yaml` vocabulary
  first (no gratuitous divergence); when T-76 fires, design multi-provider from day one.
- **A future LTG overlay would be scaffolding-only:** it would carry per-repo config
  (`corpus.yaml` template, MCP registration, `.memories` integration) — the engine is a package
  dependency, never overlay-distributed files. This is the B+C lesson (engine central, config
  per-repo; wholesale-overwrite + stale-engine propagation were the paid-for failure modes)
  applied to a second product.

Source / more detail: `docs/ideas/ltg-model-registry-design.md` Part 2
(`ref:model-registry-library-decision`); `docs/plans/ltg-repo-split-discovery.md`.
<!-- /ref:overlay-topology-rule -->

---

<!-- ref:overlay-test-convention -->
## Overlay Test Convention — hermetic + ships with the overlay

Three rules, each with a reason that generalizes to every future overlay suite.

- **Tests live with the overlay source, not the consumer tree.** An authored test goes in
  `files/tests/` (co-located with the code it exercises, mirroring `session-tracking`'s
  `files/handoff/test_*.py`); the manifest `files:` map installs it into consumer repos'
  `.claude/tools/tests/`. The source repo does NOT commit an installed copy — that's a
  generated artifact. *Caveat:* a pre-existing installed copy of a *script* (e.g.
  `.claude/tools/ref-lookup.sh`) is left alone — the source-only rule applies to *new*
  artifacts, not a retro-cleanup of every installed file.

- **Tests must be hermetic — zero repo coupling.** Each case builds its own fixture corpus in
  a `mktemp` dir and points the tool at it via `--root <fixture>`. The tool only ever sees
  content the test authored (the "clean container" model). *Rationale:* the original test
  diffed against `baseline-*.txt` snapshots captured from THIS repo's ref blocks, so any
  unrelated edit to the repo's documentation could flip the test result. **A repo change must
  never risk a test outcome.** The `--root` flag is the isolation boundary — design new overlay
  tools with such a flag so their tests can be hermetic.
  - *Sub-finding:* hermeticity also exposed that `--paths` "first occurrence" of a duplicated
    key follows `grep -r` filesystem-traversal (readdir) order, NOT sorted path. Asserting a
    *specific* winner would just relocate the non-determinism from repo-content to
    filesystem-order, so the test asserts the **dedup invariant** (collapses to one real
    occurrence), which IS the tool's contract.

- **A `make` runner is the aggregation seam.** `overlays/Makefile` wires every suite behind one
  `make test`; bare `make` prints help; paths resolve via the Makefile's own dir
  (`$(dir $(realpath ...))`) so it runs from any invocation point. Targets **delegate to
  `overlays/scripts/` runners** (`test-<suite>.sh` each resolve the right cwd + interpreter;
  `run-all-tests.sh` aggregates with a PASS/FAIL summary and nonzero-on-any-fail), so the exact
  invocation works from make, a bare shell, or CI. `ARGS='-k x'` forwards pytest filters to one
  suite. *Rationale:* the per-suite cwd/interpreter quirks (handoff tests need their own dir on
  the path; `test_verify.py` needs `overlays/` as cwd) belong in scripts, not Makefile recipes —
  the Makefile stays a thin index, the scripts are reusable outside make. `make test` works
  precisely *because* the suites are hermetic (a runner needs only exit 0, no opinion about repo
  state). *Excluded:* `overlays/test-merge-plan.py` is a manual Ollama model-comparison
  diagnostic (network, prints JSON), NOT an automated suite.
  **Implication:** a new overlay suite wires in as a `scripts/test-<name>.sh` runner + a
  `test-<name>` target + one line in `run-all-tests.sh`. *(A suite added without that last step
  runs green while testing nothing — the `test_customizable.py` near-miss.)*

Source / more detail: PR #63 review (T-42); `overlays/Makefile`, `overlays/scripts/`.
<!-- /ref:overlay-test-convention -->
