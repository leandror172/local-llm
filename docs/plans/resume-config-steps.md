# resume.sh → configurable step pipeline (and the packaging flip it forces)

**Created:** 2026-07-09 (session 111)
**Branch:** `feature/resume-config-steps`
**Status:** PLAN — decisions R-D1…R-D9. R-D2/R-D7 decided; R-D4 conditionally decided; rest are leans. **No code written.**
**Supersedes:** most of `docs/plans/resume-sh-ref-audit.md` (T-43) — see § "What T-43 turns out to be".
**Reframes:** T-80(b) (do not execute). Leaves T-80(a) independent — see § "The discriminating-signals release".
**Answers:** `docs/findings/overlay-distribution-options.md` § "D deferred"; `.claude/tasks.md` line 40.

---

## The problem, stated at the right altitude

`resume.sh` is 120 lines of bash with **six hardcoded sections**. What it prints, in what
order, filtered how, and under what title, is source code. A repo that wants a different
session-start summary must edit the script.

That is why the `customizable:` installer category (T-61, overlay v10) exists for this
file: it lets a repo patch *code* inside `overlay-keep:<name>` markers. It works —
career-search's variant survived the v10 propagation — but every customization is a merge
hazard, and the installer's own reset warning cannot tell a benign reset from a clobber
(T-80a).

The **write** side of session tracking solved this long ago. Nobody edits
`orchestrator.py` to change what the handoff writes; they edit `registry.yaml`. The
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

## The escape hatch belongs at step granularity, not file granularity

Diff of career-search's `overlay-keep:reading-guide` region against llm's, in full:

| | llm | career-search |
|---|---|---|
| Section title | `── Pre-session reading guide (…) ──` | `── What to read first (…) ──` |
| Output filters | 4 `grep -v` | 2 `grep -v` |

**That is the entire divergence** — a title string and a filter chain. Purely
presentational. With a config file it is a two-line YAML diff, and the keep-region for this
file never needs to exist.

`customizable:` is to *files* what `run:` (below) is to *steps*: an escape hatch for "the
repo knows something the overlay can't." Same idea, different granularity. The migration
therefore does not remove the escape hatch — it **descends** it:

| | file-granularity (`overlay-keep`) | step-granularity (`run:`) |
|---|---|---|
| Unit of divergence | a span of shell code | one config entry |
| Merge behavior | hazard; hand-wrapping before install (T-79) | clean; YAML doesn't conflict like patched scripts |
| Blast radius of an overlay update | whole file | one step |

career-search keeps every freedom it has today and loses the propagation hazard.

### The uncomfortable part, recorded honestly

Every customization anyone has actually wanted from this overlay is **data**:

| File | What a repo would want to change | Data? |
|---|---|---|
| `resume.sh` | Section titles, filters, order | yes |
| `rotate-session-log.sh` | How many entries to keep | yes (`--keep N`) |
| `handoff-harvest.sh` | The commit-boundary grep pattern | yes |
| `registry.yaml` | Everything | already config |

T-61 asked *"how do we let repos customize an overlay-owned file?"* — well-posed,
competently answered, 21 tests, shipped to five repos. The question one level up — *"why
does this file have repo-specific behavior at all?"* — was never asked.

**Disposition:** keep the `customizable:` category (an unused escape hatch is the healthy
steady state), delete its only consumer. Its durable outputs were never the category
itself: they were `--verify`'s `CUSTOMIZED`-vs-`DIFF` gating semantics, the propagation
runbook, and the discovery that the reset warning lies. All survive.

Generalized rule → memory `feedback-config-over-keep-regions`.

---

## What T-43 turns out to be

`docs/plans/resume-sh-ref-audit.md` (session 60) proposed adding two ref tags plus three
structural fixes. Checked against the current script:

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

The sentence has a hole where the number goes, and has been shipping that way to five
repos. Close T-43 as **absorbed**: the count becomes a `run:` step in the default config.

---

## Design

### R-D1 — Two files, one referencing the other

**Do not fold presentation into the register.** `registry.yaml` is a *safety boundary* —
the handoff's verifier (F4) hashes every byte outside a listed region and rejects any edit
that changed them. Roles there define what the pipeline is *permitted to write*. Adding
`head: 30`, `title:`, `filters:` would put display concerns inside the mechanism that
decides write authority.

| File | Owns | Consumers |
|---|---|---|
| `registry.yaml` | **Where** a region lives: file + locator (+ write mode) | handoff (write), resume (read) |
| `resume.yaml` | **What** to show, in what order, filtered how | resume only |

A `region:` step names a **register role**, not a raw ref key, and resume resolves the
location *through* the register. That is the prize the deferred comment describes: rename a
ref key or move a block between files, edit `registry.yaml` once, both sides follow.

### R-D2 — Step vocabulary: fixed set + `run:` escape hatch  *(decided)*

Derived from what the script does today, not invented. All six sections plus the footer map
onto this set:

| Step kind | Purpose | Maps to today's |
|---|---|---|
| `text` | Literal line(s); supports `{date}` | banner, footer rules |
| `region` | Resolve a **register role** → print its interior | current-status, reading-guide, quick-pointers, active-decisions, user-prefs |
| `log_next` | The `### Next` block of the newest session-log entry | §2's `awk` |
| `git_log` | Recent commits | `git log --oneline -5` |
| `git_status` | Working-tree dirt | `git status -s` |
| `run` | **Escape hatch.** Arbitrary shell, output captured | deferred-count (T-43 residue), anything repo-specific |

Shared per-step options: `title:`, `head:`, `filters:` (list of `grep -v` patterns),
`fallback:` (text when empty), `omit_if_empty:` (skip the step *and its title* — how §6
already behaves).

**The rule that decides fixed-kind vs `run:`** — *a step earns a fixed kind when the
overlay owns the invariant it depends on:*

- `log_next` parses `session-log.md`'s structure, which the overlay owns and **has already
  changed once** (latest-only + slugged archive, session 90). Frozen into five repos as
  `run: awk …`, the next storage-topology change breaks all of them silently.
- `git_log` depends on git (universal), but the overlay wants one place to pin known
  hazards — e.g. `rtk git log` drops merge commits (session-110 gotcha).
- `run:` is for what only the repo knows.

`run:` makes the config executable code at the same trust level as a `Makefile` — checked
in, reviewed like source. This is the CircleCI shape, adopted knowingly rather than by
accident.

### R-D3 — Language: Python, for reuse

Not "bash is bad" — **the pieces already exist in Python.**

- `registry_io.load_register(path) -> Dict[role, role_dict]`
- `locator.locate(role, text) -> Region(start, end, interior)` — all four locator kinds

A `region:` step is `locate(register[role], read(file)).interior`, using **the same
resolver the handoff uses**, so read and write can never disagree about where a region
begins. Bash + `yq` would reimplement both and add a dependency the overlay doesn't
require. PyYAML is already declared. Startup (~40 ms) is irrelevant once per session.

**Non-register keys:** `ref-lookup.sh --paths` (T-42, shipped) emits `KEY<TAB>relpath`, so
a `region:` step naming a key *not* in the register still resolves — with the documented
caveat that it loses rename-safety. `ref-lookup.sh` belongs to a *different* overlay
(`ref-indexing`) and stays bash; do not drag it into this package.

### R-D7 — A real package  *(decided)* — and it is *cheaper*, not dearer

Earlier framing in this plan called the shared-primitive extraction expensive. **That was
an artifact of the current layout, not of the extraction.** `~/.claude/tools/handoff/` is
ten loose `.py` files copied into a directory — no `__init__.py`, no distribution, no
import root. A sibling `resume/` importing `locator` from it needs `sys.path` hacks or
duplication.

Inside a real package, `from sessiontracking.register import locate` is just an import.
**Packaging is the mechanism that makes R-D7 cheap.** R-D7 and R-D9 are one decision.

```
sessiontracking/
  register/     ← primitive: registry_io.py + locator.py  (the register + region resolution)
    ↑      ↑
  handoff/   resume/     ← products, mutually independent
```

Two products, one shared primitive, **no product↔product edge** — satisfying the repo's own
topology rule (`ref:model-registry-library-decision`, *"products depend on primitives,
never product↔product"*) structurally rather than by discipline. This is the second
sighting of that shape in three sessions; T-77's signature extractor would be the third.

Layering rule preserved: PyYAML stays confined to `registry_io`; `locator` and the handoff
safety core remain stdlib-only.

### R-D9 — Distribution flip: code ships as a package, config ships as an overlay  *(new)*

`docs/findings/overlay-distribution-options.md:47` already specifies this as **Option D —
pip editable install**, and line 135 defers it:

> D would clean up the shim further and pre-stage H, but **adds pip/venv complexity with no
> immediate benefit.** Adopt when H becomes concrete.

**That rationale is now false.** The immediate benefit is R-D7: a second product needs to
share a primitive with the first, and only a package makes that a plain import. The
recorded trigger was "when H becomes concrete"; the *real* trigger turned out to be "when a
second consumer appears," which nobody wrote down.

**Precedent, two sessions old and in this repo's family:**
`/mnt/i/workspaces/latent-topic-graph/pyproject.toml:21` declares thirteen
`[project.scripts]` entry points (`ltg-extract`, `ltg-embed`, `ltg-relate`, …); the llm
instance consumes them via an editable path-dependency (`ltg/pyproject.toml`); the bash
wrappers survived as three-line shims. Exactly this shape, already load-bearing.

Note on terminology: "binary" here means a **console-script entry point** — `pyproject.toml`
declares `st-resume = "sessiontracking.resume:main"` and installing puts `st-resume` on
`PATH`. It behaves like a binary; it is a launcher. A true single-file executable
(PyInstaller / `shiv` / `zipapp`) is possible and **not worth it**: Python is already
required (PyYAML, MCP server, `uv`), and real binaries mean per-platform builds for no gain.

**The line this draws:**

| Ships as | What | Mechanism |
|---|---|---|
| **Package** | `register/`, `handoff/`, `resume/`, entry points | `uv tool install` / editable path-dep |
| **Overlay** | `registry.yaml`, `resume.yaml`, templates, `CLAUDE.md`, `SKILL.md` | `install-overlay.py` |

Today the installer does both and conflates them. `always_user_files:` copies ten `.py`
files — a hand-rolled package manager. The other categories place per-repo config and docs,
which is what an overlay is uniquely for.

**What this dissolves** (named plainly, since the same thing just happened to `customizable:`):

- **`always_user_files:`** — exists only to copy the ten pipeline modules. Gone.
- **`--verify`'s code-drift check (T-58)** — built because a partial v4 propagation left
  expenses on a stale `verifier.py`. With one installed package there are no copies to
  drift. `--verify` survives, shrunk to config and doc files.

Both compensate for a missing package manager. Stop copying code and they fade.

#### The version marker does NOT dissolve — it disentangles (corrected)

An earlier draft claimed the `<!-- overlay:session-tracking vN -->` CLAUDE.md marker
"becomes a queryable package version." **Wrong.** A package version is *machine-global* —
one shared install. The marker is *per-repo*. They answer different questions, and after
R-D9 there are **three version facts**, not one:

| Fact | Scope | Where it lives | Question it answers |
|---|---|---|---|
| Installed engine **code** | machine-global | package `--version` | what code will run? |
| Config **schema** contract | per-file | `registry.yaml: version: 1` (already exists) | can this code read this config? |
| Overlay **config generation** | **per-repo** | `<!-- overlay:session-tracking vN -->` | has this repo taken the latest config? |

Today the marker straddles the first and third because one installer run writes both code
and config — which is precisely the conflation session 110 caught: session 108's "v9 synced
cross-repo" claim referred to the *shared user-level engine*, while consumer markers still
read v6/v6/v6/v8. The marker had to be *declared* authoritative because nothing else was.

After R-D9 the marker tracks exactly one thing and stops being a workaround. "Is repo X up
to date?" splits into two cleanly answerable questions: *does the installed package support
this repo's config schema?* — a check the package can run itself and fail loudly on, using
the `version:` key `registry.yaml` already carries — and *has this repo taken the latest
config generation?* — the marker. Neither was cleanly available before.

**Consequence for R-D9:** the package must validate `registry.yaml: version:` (and
`resume.yaml`'s, once it exists) on startup and refuse to run on an unsupported schema. That
is a new requirement this plan owes, not a freebie.

**The cost that does not dissolve:** editable installs are machine-local (the doc's own
recorded con). LTG hit this and answered by writing the escalation trigger down rather than
solving it early (`ltg/pyproject.toml:9`): *flip the path source to a published package
when (a) working from a machine without the sibling checkout, or (b) the first external
adopter appears.* **Adopt that trigger verbatim.** Do not publish to PyPI now.

Bash shims stay at `.claude/tools/resume.sh` and `run-handoff.sh` (`exec st-resume "$@"`) so
existing paths, hooks, and docs keep working. The shim was always the designed seam.

### R-D4 — How `resume.yaml` ships: `manual_if_exists`, conditional on fixing T-54

Under R-D9 `resume.yaml` is **pure per-repo config with no code beside it** — which makes
`manual_if_exists` the honest category, matching `registry.yaml`. The alternatives:

| Option | Behavior | Cost |
|---|---|---|
| `templates:` | Created once, never overwritten | Overlay improvements to default steps never reach existing repos |
| **`manual_if_exists:`** | Copy once, then flag for manual merge | Flags on **every** install unconditionally — the T-54 gap |
| `customizable:` | Overlay owns it except keep-regions | The mechanism this plan exists to stop needing |

**Condition:** with two `manual_if_exists` files, every install prints two `[TODO]`s that
usually mean nothing — alarm fatigue on the exact channel meant to protect the register.
T-54 must be fixed before or with this. See below.

### R-D5 — Fate of the keep-region

Remove the `customizable:` entry for `resume.sh` from `manifest.yaml`; the
`overlay-keep:reading-guide` markers disappear from all five repos; career-search's variant
migrates to two lines of its `resume.yaml`. Keep the category.

### R-D10 — `quick-pointers` belongs in `session-context.md` (session 111)

Discovered while migrating: llm kept its `ref:quick-pointers` block in `.claude/index.md`,
and its register carried a comment defending that — `# NOT session-context.md`. Every other
register-read role (`user-prefs`, `current-status`, `active-decisions`,
`session-reading-guide`) lives in `session-context.md`, and so does the starter template's
copy.

Consistency is the weak argument. The strong one is `registry.yaml`'s own header: *"this
register enumerates the handoff-owned regions. Every OTHER `ref:KEY` in the repo is content
/ an LTG anchor the pipeline MUST NOT touch."* `.claude/index.md` is content — it is the
knowledge map and an LTG anchor source. A register role pointing into it puts handoff-owned
regions and must-not-touch content in one file, blurring the boundary the register exists to
draw. `session-context.md` is the tracking file the register owns.

Moved. `index.md` keeps a navigation pointer. llm's register is now byte-identical to the
overlay source (`--verify`: `SAME`, `10/10 register locators resolve`), and `resume.sh`
output is unchanged. This removes the last of llm's "home repo is special" residue, after
the CLAUDE.md markers and the register copy.

### R-D6 — Migration gate

Behavior must be byte-identical before and after for llm's own output, or a regression is
indistinguishable from a config error. Gate: capture `resume.sh` output on master, run the
new pipeline with the default `resume.yaml`, `diff` must be empty — modulo the date line
and the T-43 count, which is a deliberate addition. career-search is the only repo with a
customization and therefore the only real migration test; its two-line config diff is the
acceptance case.

---

## The discriminating-signals release (T-54 + T-80a)

**Packaging does not touch this.** `handle_customizable` lives in `overlays/lib/actions.py`
— part of `install-overlay.py`, a dev tool run from the llm repo. That is not what gets
packaged. T-80(a) is fully independent of R-D9.

What retires T-80(a)'s *call-site* is this plan (R-D5), not packaging. `customizable:` is
used by exactly one manifest, for exactly one file.

**T-54 and T-80(a) are the same bug.** Both are installer signals that fire identically in
the dangerous case and the benign one, and therefore carry zero bits and train the operator
to ignore them:

- `handle_manual_if_exists` (`actions.py:325`) flags `[TODO] manual merge` on every install
  — *even when the file is byte-identical to source* (live in latent-topic-graph today).
- `handle_customizable` (`actions.py:348`) warns `reset to overlay default` on every
  unmarked region — *even when the reset changes nothing* (all four repos in T-79 produced
  byte-identical output for the benign reset and the destructive one).

They are **adjacent functions, 23 lines apart**, needing the identical fix: *compare the
installed content against the source before warning.* Write the comparison helper once,
call it twice.

**Priority, corrected.** An earlier draft argued "fix T-80(a) now while the fixtures are
cheap, before career-search's pre-v10 state becomes archaeology." **That was wrong** —
`test_customizable.py` is hermetic (54 `tmp_path` uses); the fixtures are synthetic and
never expire. The real ordering:

- **T-54 is live and worsening.** It guards `registry.yaml` today and `resume.yaml` under
  R-D4. Do it because of that.
- **T-80(a) rides along**, ~20 lines away, in the same file, same predicate. Doing one and
  not the other leaves the bug class half-fixed.
- **T-80(b) stays dead** — it repairs a workaround R-D5 deletes.

Suite: `make -C overlays test-installer`.

---

## Decision register

| id | Decision | State |
|---|---|---|
| **R-D1** | Presentation config separate from the region register; `region:` steps resolve through `registry.yaml` | lean, needs ratification |
| **R-D2** | Fixed step vocabulary + `run:` escape hatch | **DECIDED** |
| **R-D3** | Python, reusing `registry_io` + `locator`; bash shim at the invoked path | lean, strong |
| **R-D4** | `resume.yaml` ships via `manual_if_exists` | **DECIDED, conditional on T-54** |
| **R-D5** | Remove `customizable:` entry + markers; keep the category | lean |
| **R-D6** | Byte-identical output diff on llm; career-search is the acceptance case | lean |
| **R-D7** | New `sessiontracking` package; extract a `register/` primitive; no product↔product edge | **DECIDED** |
| **R-D8** | Close T-43 as absorbed; deferred-count becomes a `run:` step | lean |
| **R-D9** | Distribution flip to Option D: code as package + console entry points; overlay keeps config/docs. Adopt LTG's publish trigger verbatim | **DECIDED** (pending go) |

---

## Relationship to open tasks

- **T-54** — live, worsening under R-D4. Fix first. Same bug as T-80(a).
- **T-80(a)** — independent of packaging; rides along with T-54.
- **T-80(b)** — **do not execute.** Superseded by R-D5.
- **T-43** — close as absorbed (R-D8).
- **T-58 (`--verify`)** — code-drift half dissolves under R-D9; config/doc half survives.
- **T-60 (distribution G/H)** — this plan resolves **D**. D was already recorded as the
  stepping stone to H; adopting it pre-stages the plugin evaluation.
- **T-61 / T-79** — produced the `customizable:` category and propagated it. R-D5 removes
  its only consumer; the durable outputs survive.
- **T-77 (signature extractor)** — would be the third consumer of the primitives topology.
  R-D7 makes the shape explicit before it arrives.
- **`.claude/tasks.md` line 40** — "refactor resume.sh onto the shared register, lean:
  later." Answered: **yes, now**, and wider than scoped.

---

## Execution order (proposed, pending go)

1. **Discriminating-signals release** — T-54 + T-80(a), one comparison helper, two
   call-sites, hermetic tests. Independent; unblocks R-D4.
2. **Packaging flip (R-D9 + R-D7)** — `sessiontracking` package, `register/` primitive
   extracted, entry points, shims rewritten. Guarded by the 178 existing handoff tests.
3. **`resume.yaml` + step interpreter (R-D1/2/3)** — default config reproducing today's
   output byte-for-byte (R-D6), plus the T-43 count.
4. **Migration** — five repos; remove `customizable:` entry and markers (R-D5);
   career-search's two-line config diff is the acceptance case.

Steps 1 and 2 are independent of each other. Step 3 depends on 2. Step 4 depends on 3.

## What is NOT decided

R-D1, R-D3, R-D5, R-D6, R-D8 are leans awaiting ratification. R-D4 is contingent on step 1
landing. No code has been written; nothing starts without an explicit go.
