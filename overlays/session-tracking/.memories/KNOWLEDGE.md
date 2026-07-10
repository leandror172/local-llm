# session-tracking overlay — Knowledge (Semantic Memory)

*Concept-organized current truth for the session-handoff pipeline and the overlay that
ships it. Read on demand. Each section = one concept, consolidated across rounds; the
"Source / more detail" pointers at section end lead to the records holding the full
findings. Chronology lives in `.claude/archive/session-tracking-handoff-history.md`
(per-round narrative) and `git log -- overlays/session-tracking/`. Restructured
2026-07-08 (session 110), per web-research `docs/research/memory-architecture-design.md`
and mirroring latent-topic-graph's L-08 dream pass.*

*What belongs here: whatever a model should know about this overlay BEFORE working in
it, that it would otherwise have to read the source to learn — orientation (what lives
where, what the modules do) as much as hard-won invariants. Test for inclusion: "I'm
about to use or change something in this area — what do I remember about it?" If the
answer would save a read-the-source round-trip, it belongs.*

*Write protocol: when a session produces durable knowledge — a finding, OR new/changed
structure a future session would otherwise rediscover by reading code — UPDATE the
relevant concept section(s) in place; replace superseded values, don't append a dated
block (consolidation happens at write-time, not in a later pass). Add a new section only
for a genuinely new concept. Point "Source / more detail" at the PR/plan/report that
established the fact. Per-round narrative belongs in the archive file, not here. Status
trivia (open PRs, test counts, current version) belongs in `QUICK.md`, not here.*

---

<!-- ref:handoff-pipeline-map -->
## Pipeline orientation — what lives where (`src/sessiontracking/`, v11 package)

The handoff pipeline replaces the token-heavy "Claude reads every tracking file and
writes each section via many Edits" skill with a **register-driven deterministic
transaction**. Scope A uses NO local model — Claude decides *content*, the pipeline does
*read + write*.

Layout: `register/` (primitive) + `handoff/` and `resume/` (products). Products import the
primitive; never each other.

Safety core (pure functions over `(role/Region, text)`, stdlib-only):
- `register/locator.py` — finds the byte range a role owns. Four locator kinds: `ref_block` /
  `structural` / `field` / `checklist`. Returns `Region(start, end, interior)` — the
  single boundary source of truth.
- `handoff/applier.py` — mutates text. Write modes: `replace` / `prepend` / `append` /
  `checkoff` / `nomodel`.
- `handoff/verifier.py` — recompute-and-compare: re-derives the expected text byte-exact,
  independently of the applier, then diffs. Plus the ref-marker multiset invariant.

Around it:
- `handoff/mechanics.py` — header-field bumps, `next-session-N` (bootstraps to 1 on a fresh
  repo), date, rotation invoker, `LogEntry` + `render_log_entry()`.
- `handoff/orchestrator.py` (+ injected `handoff/gitio.py` adapter) — atomic stage → apply → verify →
  write → rotate → commit.
- `handoff/payload.py` — the payload schema + parser. `register/registry_io.py` — PyYAML
  register loader; validates `registry.yaml`'s `version:` against `SUPPORTED_REGISTER_SCHEMA`.
- `handoff/runlog.py` — per-run dir `.claude/local/handoff-runs/session-<N>-<ts>-<status>/`
  holding `input.md` (verbatim payload = recovery artifact) + `report.md` (audit).
- `handoff/cli.py` — the CLI, entry point `st-handoff`. `run-handoff.sh` — the thin shim.
- `resume/` — `config.py` (resume.yaml schema) + `steps.py` (step kinds) + `cli.py`
  (`st-resume`). `resume.sh` is its shim.

Config shipped by the overlay in `files/`: `rotate-session-log.sh`, `handoff-harvest.sh`,
`resume.sh`, `resume.yaml`, `registry.yaml`, `session-handoff/SKILL.md`.

**Layering rule:** PyYAML is allowed *only* in the entrypoint glue (`register/registry_io`,
`resume/config`); the locator/applier/verifier/mechanics/orchestrator core stays stdlib-only.

Source / more detail: module docstrings; `ref:handoff-pipeline-design`;
`overlays/session-tracking/README.md`.
<!-- /ref:handoff-pipeline-map -->

---

<!-- ref:handoff-register -->
## The register — safety boundary *and* customization seam

`registry.yaml` is the per-repo source of truth mapping each handoff-owned region to a
file + locator + write mode. It does double duty:

- **Customization seam:** it is the *only* thing a consuming repo edits to change what
  the handoff writes. Ships via `manual_if_exists` (copy-once, then flag-on-update) —
  load-bearing yet per-repo, so neither silent overwrite nor silent skip is right.
- **Safety boundary:** every ref key *not* named in the register is content or an LTG
  anchor that the pipeline **must not touch**.

The pipeline only ever walks **payload → register**, never register → payload. A role
left in a target's register with no payload slot is therefore *operationally* inert — but
it is dead config that claims the handoff owns a region which may not exist. `--verify`'s
locator contract now reports such a role as `BROKEN`, and the retired
`header-previous-logs` was removed from all repos (session 111). Delete stale roles; the
payload→register direction is why deleting them is safe.

`handoff.py` resolves `repo_root` via `git rev-parse`, so the default register path is
correct without flags in installed repos.

Load-bearing contracts (register, payload schema, orchestration) stay Claude-authored;
leaf modules (mechanics, logging) are local-model-delegable.

Source / more detail: `files/registry.yaml`; `ref:handoff-pipeline-design`.
<!-- /ref:handoff-register -->

---

<!-- ref:handoff-invariants -->
## Invariants (the load-bearing rules)

Break any of these and the failure is silent or near-silent. Each was paid for once.

- **The nomodel fence.** The *applier* REFUSES `nomodel`; the *verifier* ACCEPTS it as
  `replace`. Consequence: a payload can never write header fields — only the script can.
  This is what will let an untrusted model drive the payload path in the deferred
  local-model Placer enhancement.
- **Newline-termination contract.** Applier and verifier share an implicit "content is
  newline-terminated" contract and must stay byte-identical. Normalize **once, upstream,
  at the seam** (`_normalize_block` in `_collect_edits`) — never inside the safety core.
  F4's invariants (out-of-region bytes + ref-marker multiset) cannot see a missing
  newline before a present marker, so nothing downstream will catch it.
- **Append and prepend are ZERO-WIDTH insertions — in the verifier too.** The applier
  inserts at `region.end`. A verifier that reconstructs via
  `replace([start,end], region.interior + content)` uses a **stale interior snapshot**
  and silently loses any nested edit (e.g. a checkoff flip) applied earlier in the
  descending-sort loop. `_effective_range` collapses append→insertion-point and
  checkoff→3-byte range; reconstruction must agree with it.
- **Idempotency key is the commit-title suffix, never the session number.** After the
  first commit the header updates and `peek_session_number` returns N+1 — a false-miss
  on crash-recovery, which would double-apply.
- **Sort order is stable-descending for equal-start regions**, identically in applier and
  verifier reconstruction.
- **`log-entry` is excluded from `payload.blocks`** by `parse()`, or it double-applies.
- **The recovery path is strictly LESS powerful than the happy path.** `--amend` allows
  append + checkoff only; no prepend, no header write, no scalars required. The worst
  possible amend mistake is therefore a duplicate appended task.
- **Two safety layers on write:** in-memory verify-then-write, plus git-checkout
  rollback — both guarded by a clean-tree precondition on the tracking files.

Source / more detail: `.claude/archive/session-tracking-handoff-history.md`
(sessions 86, 89–90, 93); tests `test_verifier.py`, `test_orchestrator.py`,
`test_append_region_enclosing_checkoff_verifies`.
<!-- /ref:handoff-invariants -->

---

<!-- ref:handoff-payload-contract -->
## Payload contract — value-only

A payload is first-two-`---` frontmatter (`session_title` / `current_layer` /
`checkoffs`) plus `## role:` sections. **The author supplies values; the pipeline renders
all scaffold.**

`log-entry` is structured snake_case sub-slots, not a free block. The pipeline renders
the `## <date> - Session N: <title>` heading (from date + derived N + `session_title`)
and the `### Context / What Was Done / Decisions Made / Next / Gotchas` subheadings and
bullets. The orchestrator computes `header_values` once and renders the log entry with
the SAME `session_number`. The old free-block `log-entry` form is rejected with a
migration error (clean break at v6).

Field names are deliberately aligned with the deferred local-model Placer schema, which
will fill this same contract via structured output.

Wrapped bullets are continuation-joined by the parser (T-78) — a bullet may span lines.

The newline contract is double-guarded here: `render_log_entry` rstrips then re-adds one
`\n`, and `_normalize_block` still wraps.

Source / more detail: `payload.py`; `files/session-handoff/SKILL.md`;
`ref:handoff-placer-enhancement`.
<!-- /ref:handoff-payload-contract -->

---

<!-- ref:handoff-cli-surface -->
## CLI surface and failure taxonomy

Stage / promote, not dry-run / apply:

- **`--payload <file>` (stage):** validate → ingest (copy into the run dir) → locate +
  apply + verify in memory → emit a JSON handle. The run dir stays `-pending`. The
  original payload is unlinked **last**, on success only — a failed or crashed stage
  never consumes the author's file.
- **`--id <handle>` (promote):** find the `-pending` run → idempotency check → apply →
  commit → rename the dir `-success` / `-failed`. Everything is recomputed from current
  files; no cached edits.
- **`--amend`:** attaches to the last *committed* session N (derived, never typed).
  Commit suffix `— amend`. Mode persisted in a `<run_dir>/mode` sidecar.
- **`--abort <handle>`:** renames `-pending` → `-aborted`. **Never `rm` a run dir by
  hand** — that is exactly the ad-hoc gesture this verb exists to replace.

The run-dir status suffix (`-pending` / `-success` / `-failed` / `-aborted`) *is* the
state machine. There is no `--dry-run`.

**Every failure message must answer three questions:** WHERE (file + role, as
`role(target)@file:line`), WHOSE FAULT, and WHAT (a diff or specifics). Whose-fault is
mechanized as a `kind` attribute on exceptions, surfaced as the CLI's exit status:

| status | meaning | what the author does |
|---|---|---|
| `payload_error` | the payload is wrong | fix the payload, re-stage |
| `internal_tool_bug` | the pipeline is wrong | file a report with `input.md` — never re-author |

Validation errors state *why* ("required because this run bumps the Current Session
header"). The overlap error is prefixed "two payload edits target overlapping bytes:" so
the reader immediately knows it is author-fixable.

Source / more detail: `handoff.py`, `orchestrator.py`;
`overlays/session-tracking/README.md`.
<!-- /ref:handoff-cli-surface -->

---

<!-- ref:handoff-storage-topology -->
## Storage topology — latest-only log + slugged archive

`session-log.md` holds **exactly one entry**: the newest. `rotate-session-log.sh` runs
with `--keep 1` and archives each spilled entry into its own file:

```
session-log-<date>-s<N>-<slug>.md      slug = lowercased, alnum→hyphen, ≤40 chars
                                       fallback: sNN
```

**The archive directory and its self-identifying filenames ARE the index.** There is no
`Previous logs:` pointer line and no `header-previous-logs` role — a single growing file
plus a giant pointer line was the bloat being removed. The naming mirrors `/export`, so
archived entries pair with exported transcripts.

`handoff-harvest.sh` seeds `what_was_done` deterministically:
`git log <newest chore(session-handoff): session >..HEAD --format=%s` (fallback: last 20
+ a stderr note). Zero model, zero re-read. The commit-boundary grep is tightened to
`^chore(session-handoff): session ` — a looser pattern matches unrelated commits.

**Why this shape:** the handoff runs at the worst possible moment — context near-full,
end of session, possibly on a weaker model, possibly against a usage-limit cliff.
Value-only payloads + harvest move authoring cost off the main window; latest-only keeps
the resident file small.

Source / more detail: `rotate-session-log.sh`, `handoff-harvest.sh`;
`.claude/archive/session-tracking-handoff-history.md` (session 90).
<!-- /ref:handoff-storage-topology -->

---

<!-- ref:session-tracking-distribution -->
## Distribution — one shared engine, per-repo seams

**Since v11 (R-D9): code ships as a package, config ships as an overlay.**

The pipeline is the `session-tracking` Python package (`overlays/session-tracking/`,
`src/sessiontracking/`), installed with `uv tool install --editable
overlays/session-tracking`, exposing the console entry point `st-handoff`. The
`always_user_files:` manifest key — which copied ten `.py` modules into
`~/.claude/tools/handoff/`, a hand-rolled package manager — **is gone**.

Package layout: `register/` (primitive: `registry_io` + `locator`) with `handoff/` and
`resume/` as products above it. Products depend on the primitive, never on each other
(`ref:model-registry-library-decision`). Sharing `locate()` is the point: read and write
cannot disagree about where a region begins.

`registry_io.load_register` validates the register's `version:` key against
`SUPPORTED_REGISTER_SCHEMA` and refuses an unrecognised one (exit 2). An *absent* version
is treated as schema 1 — absence cannot prove incompatibility. Three version facts, do not
conflate: package `--version` (machine-global), `registry.yaml: version:` (per-file
schema contract), CLAUDE.md `<!-- overlay:session-tracking vN -->` (per-repo config
generation).

The overlay still installs at two levels:

- **Shim + SKILL.md → follow `--install-level`** (default `user` → `~/.claude/`;
  `project` → per-repo `.claude/`). Project-level copies SHADOW the global, so a repo
  wanting its own SKILL must force-copy it (`user_files` is skip-if-present).
- **Register → `manual_if_exists`** (see the register section).
- **`resume.sh` → `customizable:`** (v10, T-61): the overlay owns the file *except* named
  `overlay-keep:<name>` regions, which are repo-owned. Region content installed on disk
  is never overwritten; the shipped default is a **first-install seed only**. Currently
  one region: `reading-guide` (§2b).

`run-handoff.sh` is a thin shim and the stable per-repo seam — migrating the engine changes
only this file.

**Every repo invokes it identically**: no `--registry`, because the engine resolves
`<repo-root>/.claude/handoff/registry.yaml` itself. The home repo holds a register copy like
any consumer; the overlay source is the authoring/distribution copy, and `manual_if_exists` +
T-54's `SAME`/`TODO` signal keep the two honest. `--registry` survives for the genuine case of
a register living elsewhere, and still bypasses the shim's registry-file guard.

It resolves the engine in order:

1. `st-handoff` on `PATH` — the installed package. Preferred.
2. a sibling `src/sessiontracking` — the overlay source checkout, so the dev home repo
   tests against source without installing.
3. `~/.claude/tools/handoff/handoff.py` — **legacy** flat-module copy. Transitional, kept
   only until every consumer repo has the package. Delete after migration.

In an uninstalled repo the guard makes the shim `exit 0` — user-level hooks stay safe.

`SKILL.md` installs via `user_files` (skip-if-present), so a project-level copy SHADOWS the
global one and silently stops receiving updates. llm carried such a shadow, three overlay
versions stale: it documented a `stage_failed` status the CLI never emits and omitted the
`payload_error` / `internal_tool_bug` triage entirely. Removed (session 111). Do not create a
project-level SKILL copy unless the repo genuinely needs a different skill.

Option D (pip editable) is **adopted** as of v11; `docs/findings/overlay-distribution-options.md`
deferred it as "no immediate benefit, adopt when H becomes concrete" — the real trigger
turned out to be *a second consumer needing the primitive*. Publish-escalation trigger,
adopted verbatim from the LTG split: flip from editable path install to a published package
only when (a) working from a machine without this checkout, or (b) the first external
adopter appears. G/H remain long-term targets.

Source / more detail: `manifest.yaml`; `docs/plans/overlay-customizable-regions.md`;
`overlays/session-tracking/README.md`.
<!-- /ref:session-tracking-distribution -->

---

<!-- ref:session-tracking-hazards -->
## Operational hazards

- **Reinstall blast radius (shared engine, per-repo writes).** Running the installer with
  `--target <llm-repo> --install-level user` to "just refresh the engine" ALSO reconciles
  *project-level* files against overlay source. It has tried to overwrite llm's local
  `resume.sh` and to drop a stray `.claude/handoff/registry.yaml`. **Always `--dry-run`
  and diff-review the project-side writes before any engine refresh.**
- **Propagation must be byte-verified.** Targets ship no tests, so `cmp` against source
  per `files:` entry is the only safety net. A partial v4 propagation once left expenses
  running a stale `verifier.py` — they hit an already-fixed bug on the most common payload
  shape. Installer `--verify` mode (T-58) now automates this; run it.
- **The `customizable:` decision-3 clobber.** If a repo has customized a region but the
  installed file carries **no `overlay-keep` markers**, the installer resets that region to
  the overlay default. Since T-80a (session 111) the signal discriminates: `INFO … reset is
  a no-op` when the overlay default is already present verbatim (**proven safe**, silent),
  `WARN-CLOBBER` otherwise. Polarity is deliberate — silence only on proof of safety;
  `WARN-CLOBBER` means "cannot prove safe", not "will destroy". Pre-wrap a variant in
  markers before installing. career-search's "What to read first" §2b variant is the live
  instance. Do **not** trust the pre-T-80a blanket `WARN` described in older notes.
- **The installer records nothing about what it installed.** Both T-54 and T-80a are
  downstream of this: with no baseline, `manual_if_exists` cannot tell "source changed since
  you reconciled" from "this file legitimately differs" (expenses/career-search registers
  flag on *every* install, correctly but uselessly), and `customizable:` cannot locate a
  region in an unmarked file. A recorded source hash — or a package manager — closes both.
- **`--verify` asks a different question per kind of ownership (T-82, session 111).**
  Overlay-owned `files:` → byte-diff, `DIFF` gates (real drift). `merge_sections:` →
  version marker, `DIFF` gates (behind). User-managed `templates:` / `manual_if_exists:` →
  byte-diff is **meaningless** (a session log diverges from its template immediately; a
  per-repo register diverges by design), so they record non-gating `EXPECTED`. What
  protects them is the **locator contract**: `verify_locators:` loads the repo's register
  and asserts every role resolves. Gating follows `used_by` — a *write* role that cannot
  resolve is `BROKEN` (the handoff will fail); a *read-only* role is `ABSENT` (resume
  prints its fallback). Before T-82 the gate fired on every repo always, so nobody read
  it — which is how a `tasks-append` role pointing at a nonexistent block survived.
  Exits 0 on all five repos as of session 111.
- **Only the marked regions are repo-owned.** Divergence in a `customizable:` file
  *outside* a keep-region will be overwritten, by design. Decide per case whether it
  should have been a keep-region (widen the manifest) or is stale (let it go).

Source / more detail: `docs/plans/overlay-v10-propagation.md`;
`docs/plans/overlay-customizable-regions.md` (`ref:overlay-customizable-acceptance`).
<!-- /ref:session-tracking-hazards -->
