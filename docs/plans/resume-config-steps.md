# resume.sh → configurable step pipeline

**Created:** 2026-07-09 (session 111)
**Branch:** `feature/resume-config-steps`
**Status:** PLAN — decisions R-D1…R-D8 proposed, NOT frozen. Execution deferred pending review.
**Supersedes:** most of `docs/plans/resume-sh-ref-audit.md` (T-43) — see § "What T-43 turns out to be".
**Reframes:** T-80(b). Leaves T-80(a) independent and still worth doing.

---

## The problem, stated at the right altitude

`resume.sh` is 120 lines of bash with **six hardcoded sections**. What it prints, in what
order, filtered how, and under what title, is source code. A repo that wants a different
session-start summary must edit the script.

That is why the `customizable:` installer category (T-61, overlay v10) exists at all for
this file: it lets a repo patch *code* inside `overlay-keep:<name>` markers. It works —
career-search's variant survived the v10 propagation — but every customization is a merge
hazard, and the installer's own reset warning cannot tell a benign reset from a clobber
(T-80a).

The **write** side of session tracking solved this problem years-equivalent ago. Nobody
edits `orchestrator.py` to change what the handoff writes; they edit `registry.yaml`. The
handoff's behavior is *data*. The read side never got the same treatment.

### The evidence that this was always the design

`overlays/session-tracking/files/registry.yaml` header:

> Shared by two consumers: `resume.sh` READ side — reads some regions at session start.
> the handoff pipeline WRITE side — writes/updates regions at session end.

Its schema already carries a `used_by:` field taking `[read]` / `[write]` / `[read, write]`,
and four roles are tagged `[read, write]` today. Its closing comment is an explicit deferral:

> Deferred (resume.sh refactor): read-only regions resume.sh also consumes — e.g.
> `ref:quick-pointers` (lives in `.claude/index.md` in THIS repo, not session-context.md).
> Add them here when resume.sh is migrated onto this register, so a renamed/moved block
> updates both read and write in one place.

**None of this is wired.** `resume.sh` never opens `registry.yaml`. It calls
`ref-lookup.sh` with five hardcoded key strings. `used_by:` is documentation of intent.
`.claude/tasks.md` line 40 records the open decision — *"whether `resume.sh` is refactored
onto the shared register now or later (lean: later)"*. This plan is that refactor,
generalized: not just *which regions*, but *which steps*.

---

## Why T-80(b) dissolves

Diff of career-search's `overlay-keep:reading-guide` region against llm's, in full:

| | llm | career-search |
|---|---|---|
| Section title | `── Pre-session reading guide (…) ──` | `── What to read first (…) ──` |
| Output filters | 4 `grep -v` | 2 `grep -v` |

**That is the entire divergence.** It is purely presentational — a title string and a
filter chain. With a config file those are a two-line YAML diff, and the keep-region for
this file never needs to exist.

T-80 has two halves. They part ways here:

- **T-80(a)** — `handle_customizable` decision-3 emits the same `WARN … reset to overlay
  default` whether the reset is a no-op or a silent clobber. **Survives this reframe.**
  `customizable:` is general machinery; the non-discriminating warning bites *any* future
  customizable file regardless of what happens to `resume.sh`. Independent, cheap, real.
- **T-80(b)** — move the `# 2b.` comment inside the keep-region, bump v11, re-propagate to
  five repos. **Repairs a workaround this plan deletes.** Do not do it.

---

## What T-43 turns out to be

`docs/plans/resume-sh-ref-audit.md` (session 60) proposed adding `ref:quick-pointers` and
`ref:active-decisions` to resume.sh, plus three structural fixes. Checked against the
current script:

| T-43 item | Status today |
|---|---|
| Add `ref:quick-pointers` | **Done** — section 3 |
| Add `ref:active-decisions` | **Done** — section 4 |
| Fix `head -20` truncation on current-status | **Done** — now `head -30` |
| Fix user-prefs flattened to one line | **Done** — multiline |
| Fix unreadable key list | **Done** — replaced with a count |
| Add open-deferred **count** one-liner | **NOT done** |

The residue is one line. `resume.sh:118` prints:

```bash
echo "  (items pending — see ref:deferred-infra)"
```

The sentence has a hole where the number goes. It has been shipping that way to five
repos. T-43 should be closed as "absorbed": the count becomes a `run:` step in the default
config, not a bash edit.

---

## Design

### Two files, one referencing the other (R-D1)

**Do not fold presentation into the register.** `registry.yaml` is a *safety boundary* —
the handoff's verifier (F4) hashes every byte outside a listed region and rejects any edit
that changed them. Roles listed there define what the pipeline is *permitted to write*.
Adding `head: 30`, `title:`, and `filters:` to a role would put display concerns inside the
mechanism that decides write authority. Two concerns, two files:

| File | Owns | Consumers |
|---|---|---|
| `registry.yaml` | **Where** a region lives: file + locator (+ write mode) | handoff (write), resume (read) |
| `resume.yaml` | **What** to show, in what order, filtered how | resume only |

A `region:` step names a **register role**, not a raw ref key. Resume resolves the location
*through* the register. That is the prize the deferred comment describes: rename a ref key
or move a block between files, edit `registry.yaml` once, and both read and write follow.

Steps that reference no region (a banner, a git command) name nothing.

### Step vocabulary — fixed set plus a `run:` escape hatch (R-D2)

Derived from what the current script actually does, not invented. Every one of the six
sections plus the footer maps onto this set:

| Step kind | Purpose | Maps to today's |
|---|---|---|
| `text` | Literal line(s); supports `{date}` | banner, footer rules |
| `region` | Resolve a **register role** → print its interior | current-status, reading-guide, quick-pointers, active-decisions, user-prefs |
| `log_next` | The `### Next` block of the newest session-log entry | §2's `awk` |
| `git_log` | Recent commits | `git log --oneline -5` |
| `git_status` | Working-tree dirt | `git status -s` |
| `run` | **Escape hatch.** Arbitrary shell, output captured | deferred-count (T-43 residue), anything repo-specific |

Shared per-step options: `title:`, `head:`, `filters:` (list of `grep -v` patterns),
`fallback:` (text when output is empty), `omit_if_empty:` (skip the whole step, incl. its
title — this is how §6 "Uncommitted changes" already behaves).

**The rule that decides fixed-vs-`run`:** a step earns a fixed kind when *the overlay owns
the invariant it depends on.*

- `log_next` depends on `session-log.md`'s structure — which the overlay owns and has
  already changed once (latest-only + slugged archive, session 90). As a `run: awk …` step
  frozen into five repos, the next storage-topology change breaks all of them silently.
- `git_log` depends on git, which is universal — but the overlay wants one place to encode
  known hazards. Live example: `rtk git log` drops merge commits (session-110 gotcha), so
  the fixed step pins plain `git`.
- `run:` is for genuinely repo-specific things. The deferred-count is a good first citizen.

`run:` makes the config executable code, at the same trust level as a `Makefile` — checked
into the repo, reviewed like source. Naming this explicitly rather than sleepwalking into
it. It is not a new trust boundary; it is the CircleCI shape, adopted knowingly.

### Language: Python, for reuse (R-D3)

Not "bash is bad" — **the pieces already exist in Python and are already installed.**

- `registry_io.load_register(path) -> Dict[role, role_dict]` — loads and validates the register.
- `locator.locate(role, text) -> Region(start, end, interior)` — resolves all four locator
  kinds, including `ref_block`.

A `region:` step is `locate(register[role], read(file)).interior` — the resolver already
exists and is the *same code the handoff uses*, so read and write can never disagree about
where a region begins. Bash + `yq` would reimplement both and add a dependency the overlay
does not currently require. PyYAML is already declared.

Startup cost (~40 ms) is irrelevant for a once-per-session script.

**Fallback for non-register keys:** `ref-lookup.sh --paths` (T-42, shipped) emits
`KEY<TAB>relpath`, so a `region:` step naming a ref key *not* in the register can still
resolve. Prefer register roles; allow raw keys with a documented caveat that they lose the
rename-safety property.

### Installation shape (R-D4) — the unresolved one

`.claude/tools/resume.sh` stays as the invoked path (a thin bash shim, mirroring
`run-handoff.sh`), and the step interpreter installs to `~/.claude/tools/handoff/` (or a
sibling `resume/`) via `always_user_files:` — one shared engine, matching the handoff.

The open question is **how `resume.yaml` ships**, and every option has a real cost:

| Option | Behavior | Cost |
|---|---|---|
| `templates:` | Created once, never overwritten | Overlay improvements to default steps never reach existing repos |
| `manual_if_exists:` | Copy once, then flag for manual merge | Flags on **every** install unconditionally — the T-54 gap. `registry.yaml` already does this; a second file doubles the noise |
| `customizable:` | Overlay owns it except keep-regions | The exact mechanism this plan is trying to stop needing |

The register faces the identical problem today and chose `manual_if_exists`. Consistency
argues for matching it; the T-54 gap argues for fixing T-54 first. **Not resolved here.**

### Fate of the keep-region (R-D5)

Once `resume.yaml` exists, `resume.sh` becomes a shim with no customizable surface. The
`customizable:` entry for it is removed from `manifest.yaml`, and the
`overlay-keep:reading-guide` markers disappear from all five repos. career-search's variant
migrates to two lines of its `resume.yaml`.

`customizable:` the **category** stays — it is general machinery with other plausible
consumers, and T-80(a) is a genuine bug in it. This plan removes its only current *user*,
which is worth being honest about: after this, `customizable:` is machinery with zero
call-sites. That is an argument for landing T-80(a) on its own merits, or for questioning
whether the category should have been built. Recorded, not resolved.

### Migration across five repos (R-D6)

Behavior must be byte-identical before and after for llm's own output, or we cannot tell a
regression from a config error. Proposed gate: capture `resume.sh` output on master, run
the new pipeline with the default `resume.yaml`, `diff` must be empty (modulo the date
line and the T-43 count, which is a deliberate addition).

career-search is the only repo with a customization and therefore the only real migration
test. Its two-line config diff is the acceptance case.

---

## Decision register (PROPOSED — not frozen)

| id | Decision | Lean | Open? |
|---|---|---|---|
| **R-D1** | Presentation config separate from the region register | Two files; `region:` steps resolve through `registry.yaml` | lean, needs ratification |
| **R-D2** | Step vocabulary | Fixed set (`text`/`region`/`log_next`/`git_log`/`git_status`) + `run:` escape hatch | **decided by user** |
| **R-D3** | Language | Python, reusing `registry_io` + `locator`; bash shim at the invoked path | lean, strong |
| **R-D4** | How `resume.yaml` ships | `templates:` vs `manual_if_exists:` vs new | **OPEN — blocks execution** |
| **R-D5** | Fate of `customizable:` for resume.sh | Remove the entry + markers; keep the category | lean |
| **R-D6** | Migration gate | Byte-identical output diff on llm; career-search is the acceptance case | lean |
| **R-D7** | Does the interpreter live in `handoff/` or a sibling `resume/` package? | Sibling — different lifecycle, shared imports | **OPEN** |
| **R-D8** | T-43 disposition | Close as absorbed; the deferred-count becomes a `run:` step in the default config | lean |

---

## Relationship to open tasks

- **T-80(a)** — independent, unblocked, still valid. Do it or don't; this plan neither
  needs nor prevents it.
- **T-80(b)** — **do not execute.** Superseded.
- **T-43** — close as absorbed (R-D8).
- **T-54** — `manual_if_exists` unconditional flagging. Becomes load-bearing if R-D4 picks
  `manual_if_exists`.
- **T-61 / T-79** — the work that produced the `customizable:` category and propagated it.
  This plan removes its only consumer; see R-D5.
- **`tasks.md` line 40** — the "refactor resume.sh onto the shared register" open decision.
  This plan answers it: **yes, now**, and wider than originally scoped.

---

## What is NOT decided

R-D4 (shipping mechanism) and R-D7 (package placement) block execution. R-D1/R-D3/R-D5/R-D6
are leans awaiting ratification. No code has been written. The next session should freeze
the register, then build — the session-106/107 shape (freeze in one sitting, execute the
next).
