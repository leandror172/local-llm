# session-tracking overlay

Packages the session continuity system for any Claude Code project.

## What it installs

| Action | Target | Condition |
|--------|--------|-----------|
| COPY | `.claude/tools/resume.sh` | Thin shim over `st-resume` (v11) |
| COPY | `.claude/tools/rotate-session-log.sh` | Always (backup if differs) |
| COPY | `.claude/tools/handoff-harvest.sh` | Always (backup if differs) |
| COPY | `~/.claude/tools/handoff/run-handoff.sh` | Thin shim over `st-handoff`. User-level by default; `--install-level project` installs per-repo |
| MANUAL | `.claude/handoff/registry.yaml` | Copied if missing; **flagged for manual merge if present** (per-repo register — `manual_if_exists`) |
| MANUAL | `.claude/resume.yaml` | Copied if missing; flagged if present. The step list `st-resume` renders (v11) |
| COPY | `~/.claude/skills/session-handoff/SKILL.md` | User-level by default; `--install-level project` installs per-repo |
| CREATE | `.claude/session-log.md` | Only if missing |
| CREATE | `.claude/session-context.md` | Only if missing |
| CREATE | `.claude/tasks.md` | Only if missing |
| MERGE | `CLAUDE.md` | Injects session-tracking section with overlay markers |

## Prerequisites

- `ref-indexing` overlay recommended (provides `ref-lookup.sh` used by `resume.sh` **and** by the handoff skill to fetch replace-mode interiors)
- **The `session-tracking` package** — since v11 the overlay does NOT install Python code. Install it once per machine:

  ```
  uv tool install --editable <llm-repo>/overlays/session-tracking
  ```

  This puts `st-handoff` and `st-resume` on `PATH`. The bash shims exec them, so existing repo
  paths, hooks, and docs keep working. **Code ships as a package; config ships as an overlay.**
- **PyYAML** is a package dependency — only `register/registry_io.py` imports it; the safety core
  (`register/locator.py`, `handoff/applier.py`, `handoff/verifier.py`) is stdlib-only

## Deterministic handoff pipeline

The `session-handoff` skill no longer edits the tracking files directly. It authors one
F7 payload (`.claude/local/handoff-pending.md`) and drives a two-phase CLI,
`.claude/tools/handoff/run-handoff.sh`: `--payload <file>` **stages** (locates each region via
the **register** `.claude/handoff/registry.yaml`, applies+verifies in memory, emits a JSON
handle; nothing written to tracking files) and `--id <handle>` **promotes** (applies, runs log
rotation, commits — rolling back on any failure). A failed stage leaves the payload at its
original path. Follow-up verbs: `--payload <file> --amend` attaches an additive-only run
(tasks-append + checkoffs, no scalars/header bump) to the last committed session;
`--abort <handle>` discards a pending run. The register is the per-repo customization
seam **and** the handoff-owned-vs-content boundary — every ref key NOT listed in it is content
the pipeline must never touch.

### Failure diagnostics (every failure says where, whose fault, and what)

The stage CLI emits a JSON `status` that classifies the failure so the author never has to read
pipeline source to understand it:

| `status` | Meaning | What to do |
|----------|---------|------------|
| `stage_ok` / `committed` | Success | Promote (`--id`) / done |
| `validation_failed` | Payload schema error (missing scalar, unknown role) | Payload untouched — re-edit and re-stage |
| `payload_error` | Your content is wrong (ref block not found, checkoff a non-existent task id) | Read `reason` (it names the file + role + specific target), fix, re-stage |
| `internal_tool_bug` | A pipeline invariant broke (applier/verifier disagree) | NOT your fault — `reason` cites the run's `input.md`; file a report, don't re-author |

Messages name **where** (file + role, e.g. `tasks-checkoff(T-02)@.claude/tasks.md`), **whose fault**
(a `kind` attribute on each pipeline exception routes payload-fault vs internal-fault), and **what**
(a first-diff byte context for verifier mismatches). A `tasks-append` and a `checkoffs:` entry targeting
the same file in one run is fully supported.

## Usage

```bash
# 0. Once per machine — the engine is a package, not overlay-installed files
uv tool install --editable <llm-repo>/overlays/session-tracking

# Install config + docs, with shim + skill at user level (default)
./overlays/install-overlay.py session-tracking --target /path/to/repo

# Install shim + skill per-repo (self-contained repo)
./overlays/install-overlay.py session-tracking --target /path/to/repo --install-level project

# Dry run
./overlays/install-overlay.py session-tracking --target /path/to/repo --dry-run

# Check an installed repo: overlay-owned drift, version marker, and the locator contract
./overlays/install-overlay.py session-tracking --target /path/to/repo --verify

# AI-assisted CLAUDE.md merge — see the caveat below before using
./overlays/install-overlay.py session-tracking --target /path/to/repo --mode ai --yes
```

> **`--mode ai` caveat (T-81):** `--dry-run` does **not** call the model — it only reports that
> it would. There is currently no way to preview an AI merge before it rewrites `CLAUDE.md`,
> and on a large file it may not finish. Prefer a hand-merge per `APPLY.md`; you can check it
> afterwards, because a correct hand-merge makes `--dry-run` report
> `[SKIP] CLAUDE.md — already installed vN`.

## resume.sh is configuration, not code (v11, R-D5)

`resume.sh` used to hold six hardcoded bash sections, which is why it needed an
`overlay-keep:reading-guide` region a repo could tailor. It doesn't any more. It is a thin shim,
and **what it prints lives in `.claude/resume.yaml`** — a step list rendered by `st-resume`.

Customize by editing that file: reorder, retitle, filter, drop steps, or add your own. Step kinds
are a fixed vocabulary (`text`, `region`, `log_next`, `git_log`, `git_status`) plus a `run:` escape
hatch for anything the overlay does not model. A step earns a fixed kind when the overlay owns the
invariant it depends on — `log_next` parses `session-log.md`'s structure; `git_log` pins plain
`git` because `rtk git log` drops merge commits.

A `region:` step names a **role in the register**, so it resolves through the same `locate()` the
handoff writes with. Rename or move a `ref:KEY` and both read and write follow, from one edit.

The installer's `customizable:` category still exists — it is the general escape hatch for overlay
files that have no config layer — but nothing uses it. That is the healthy steady state for an
escape hatch. Design: `docs/plans/resume-config-steps.md`.

## resume.sh output sections

`resume.sh` prints an ~80-100 line summary at session start. Section order:

| # | Section | Source |
|---|---------|--------|
| 1 | Current status | `ref:current-status` in `session-context.md` (head -30) |
| 2 | Last session "Next" pointer | Parsed from top entry in `session-log.md` under `### Next` |
| 2b | Pre-session reading guide | `ref:session-reading-guide` in `session-context.md` |
| 3 | Key file locations | `ref:quick-pointers` in `session-context.md` (full) |
| 4 | Active decisions | `ref:active-decisions` in `session-context.md` (head -12) |
| 5 | Recent git commits + uncommitted changes | `git log` / `git status` (the dirt section vanishes when clean) |
| 6 | Footer: user prefs, open-task count, ref-key count | `ref:user-prefs` + two `run:` steps |

Section order and content are **not** fixed by this table — it describes the shipped default
`resume.yaml`. Your repo's copy is the source of truth.
| 6 | Footer: user preferences + ref key count | `ref:user-prefs` in `session-context.md` |

All ref blocks are optional — missing blocks print a `(no ref:X block found)` notice rather than failing.

The `### Next` section in `session-log.md` entries should end with a `---` separator for the parser to find it cleanly.

## After install

1. Edit `.claude/session-context.md` — populate the `ref:current-status`, `ref:quick-pointers`,
   `ref:session-reading-guide`, `ref:active-decisions`, and `ref:user-prefs` blocks
2. Edit `.claude/tasks.md` — replace the placeholder phases; keep the `ref:deferred-infra` block,
   which is where the handoff appends newly-discovered tasks
3. Edit `.claude/session-log.md` — add a `### Next` subsection to the first entry. Keep the
   `**Current Session:**` / `**Current Layer:**` header fields; the pipeline bumps them via
   `field` locators
4. Tailor `.claude/resume.yaml` — the step list `resume.sh` renders. If this repo keeps a
   `ref:` block somewhere unusual, repoint the role in `.claude/handoff/registry.yaml` rather
   than editing `resume.sh`
5. Run `.claude/tools/resume.sh` to check the output
6. Run `--verify` — it asserts every register role still resolves. `BROKEN` means the handoff
   will fail; `ABSENT` means a read-only block is missing and resume prints its fallback
