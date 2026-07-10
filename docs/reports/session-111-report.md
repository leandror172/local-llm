# Session 111 — resume.sh becomes configuration, session-tracking becomes a package

**Date:** 2026-07-09
**Branch:** `feature/resume-config-steps` (12 commits) + 6 commits across four consumer repos
**Plan:** `docs/plans/resume-config-steps.md` (R-D1…R-D10)
**Tests:** 287 in the overlay suite (9 bash + 278 pytest), all green. `--verify` exit 0 on all five repos.

---

## What was asked, and what it turned into

The session opened on **T-80**: make the `customizable:` installer's reset warning
discriminate, move a comment inside a keep-region, bump v11, re-propagate.

The user reframed it: *what `resume.sh` brings up could be configurable — a file that
lists the steps you want executed.* That question dissolved most of T-80 and exposed a
chain of defects underneath it. Everything below descends from that one reframe.

---

## The thread that ran through everything

**Five bugs, one shape: a signal that collapses two distinct states into one.**

| # | Where | Two states conflated | Result |
|---|---|---|---|
| 1 | `handle_manual_if_exists` | "identical to source" vs "differs" | `[TODO]` on every install, forever |
| 2 | `handle_customizable` (T-80a) | "reset is a no-op" vs "reset destroys" | Identical `WARN` for both |
| 3 | `verify_overlay` (T-82) | overlay-owned drift vs user-managed divergence | `--verify` exit 1 on every repo, since T-58 |
| 4 | `present()` in resume | "empty" vs "absent" | `fallback: ""` silently dropped |
| 5 | `run:` count step | `grep -c` prints `0` **and** exits 1 | Footer read `0` / `0 items pending` |

The first three are the same defect at three altitudes, and they compounded: `--verify`
(#3) was the tool built to catch drift, but it fired on every repo, so nobody read it —
which is how #1 and #2 hid for months, and how a register role pointing at a nonexistent
block survived every run.

`(USER-MANAGED)` was appended to a human-readable *message*. The control flow never saw
it. Contrast `CUSTOMIZED`, which got its own *status* and could therefore be made
non-gating. **Information present in the prose, absent from the decision.**

---

## What shipped

### 1. Discriminating signals (T-54 partial, T-80a)

`handle_manual_if_exists` records `SAME` when the installed file is EOL-normalized
identical. `handle_customizable` records `INFO … reset is a no-op` when the overlay
default is already present verbatim, `WARN-CLOBBER` otherwise.

**The T-80 spec was unimplementable as written.** It said "compare the installed region
interior against `src_regions[name]`". Decision-3 fires precisely when the installed file
has *no markers* — there is no installed interior to read. The answerable question is
whether the default is present as a contiguous run of whole lines. So the signal is
**asymmetric on purpose: silence only on proof of safety.** `WARN-CLOBBER` claims "cannot
prove safe", never "will destroy" — a file predating the region lands there too.
Over-warning on ambiguity is the correct failure direction.

### 2. The packaging flip (R-D7 + R-D9)

Ten loose `.py` files copied into `~/.claude/tools/handoff/` were a hand-rolled package
manager. They are now a package:

```
src/sessiontracking/
  register/   registry_io + locator          <- layer-0 primitive
  handoff/    the write product
  resume/     the read product
```

Products depend on the primitive, never on each other — the repo's own topology rule
(`ref:model-registry-library-decision`), satisfied structurally rather than by discipline.
Sharing `locate()` is the point: read and write cannot disagree about where a region
begins.

Extracting the primitive looked expensive only because the flat directory had no package
semantics; a sibling importing `locator` needed `sys.path` hacks. **Packaging is what makes
the extraction cheap.** R-D7 and R-D9 were one decision.

`docs/findings/overlay-distribution-options.md:135` had deferred option D as *"no immediate
benefit; adopt when H becomes concrete."* That rationale was false: the real trigger was **a
second consumer needing the primitive**, which nobody wrote down. Precedent was two sessions
old — `latent-topic-graph` ships 13 entry points and the llm instance consumes it via an
editable path-dependency.

**The line this draws: code ships as a package; config ships as an overlay.**
`always_user_files:` is gone. The overlay's remaining job is `registry.yaml`, `resume.yaml`,
the starter templates, `CLAUDE.md`, and `SKILL.md` — files no package manager should own.

Publish-escalation trigger adopted verbatim from the LTG split: flip to a published package
only when (a) working from a machine without the checkout, or (b) a first external adopter.

### 3. Three version facts (user correction)

I claimed the CLAUDE.md `<!-- overlay:session-tracking vN -->` marker "becomes a queryable
package version". Wrong — a package version is machine-global; the marker is per-repo. The
marker **disentangles**, it does not dissolve:

| Fact | Scope | Where |
|---|---|---|
| Installed engine code | machine-global | package `--version` |
| Config schema contract | per-file | `registry.yaml: version:` |
| Config generation | **per-repo** | the CLAUDE.md `vN` marker |

Today the marker straddles the first and third because one installer run writes both — the
exact conflation session 110 caught, when "v9 synced cross-repo" turned out to mean the
shared engine while consumer markers read v6/v6/v6/v8.

**Consequence:** `registry_io.load_register` now validates the `version:` key and refuses an
unsupported schema (exit 2). That key had been read and ignored — a live no-op in five repos.
An *absent* version means schema 1: absence cannot prove incompatibility.

### 4. `resume.yaml` — the read side joins the register (R-D1/2/3)

`resume.sh` was six hardcoded bash sections. That is why it needed an `overlay-keep` region
at all. The sections are now a step list rendered by `st-resume`.

Fixed vocabulary + escape hatch: `text` · `region` · `log_next` · `git_log` · `git_status` ·
`run`. **A step earns a fixed kind when the overlay owns the invariant it depends on** —
`log_next` parses `session-log.md`'s structure (overlay-owned, already changed once);
`git_log` pins plain `git` because `rtk git log` drops merge commits. `run:` is for what only
the repo knows, and is executable config at Makefile trust level: named, not stumbled into.

`region:` steps name a **register role**. `registry.yaml`'s closing comment had asked for
exactly this since session 83, and `.claude/tasks.md` line 40 recorded it as an open decision
(*"lean: later"*). Answered: yes, now, and wider than scoped.

**The R-D6 byte-identity gate held**: 120 lines each, one deliberate difference — T-43's
residue, a sentence that read `(items pending — see ref:deferred-infra)` with no number, in
five repos. It now reads `29 items pending`.

The gate earned its keep twice. `_extract_next_section` silently dropped the
`## <date> - Session N:` heading the original `awk` prints. And the `rstrip` added to stop a
whitespace-only producer defeating `omit_if_empty` **ate the banner's trailing blank line**.
Neither was visible in code review.

### 5. `--verify` asks the right question (T-82)

Three questions, one per kind of ownership:

| Ownership | Question | Gates? |
|---|---|---|
| Overlay-owned `files:` | Are the bytes what we shipped? | yes — drift |
| `merge_sections:` | Is the version marker current? | yes — behind |
| User-managed | **Do the register's locators resolve?** | write: yes · read-only: advisory |

The third is new (`verify_locators:`), and only possible because the packaging flip made
`locate()` a plain import. Gating follows `used_by`, because the consequence does: a write
role that cannot resolve means the handoff **will** fail; a read-only one means resume prints
its fallback.

**It found four real bugs on its first run:**

1. **The overlay's own starter templates never satisfied the register shipping beside them.**
   A freshly-installed repo's *first handoff* would have failed on four roles:
   `session-log.md.tmpl` had no `**Current Session:**` / `**Current Layer:**` header fields;
   `session-context.md.tmpl` had no `ref:session-reading-guide`; `tasks.md.tmpl` had no
   `ref:deferred-infra`.
2. The source register pointed `quick-pointers` at `.claude/index.md` while the template wrote
   the block into `session-context.md`. They had never agreed.
3. Three repos carried the **retired** `header-previous-logs` role, pointing at a
   `**Previous logs:**` field deleted when the log went latest-only.
4. `latent-topic-graph`'s `tasks-append` pointed at a `ref:deferred-infra` block that was never
   written — any handoff task append would have failed.

---

## Migration: five repos, three layouts

| | `ref:quick-pointers` | deferred key |
|---|---|---|
| llm | `.claude/index.md` → **moved to** `session-context.md` | `deferred-infra` |
| career-search, latent-topic-graph | `.claude/session-context.md` | `deferred` / `deferred-infra` |
| expenses, web-research | **absent** — step prints its fallback | `deferred` |

Exactly the per-repo variation the config layer exists to hold. Tasks filed in expenses
(T-33) and web-research (T-06) to author the block; latent-topic-graph got L-13/L-14.

**career-search's "What to read first" variant made the trip** from an `overlay-keep` code
region into two lines of its own `resume.yaml` — the entire argument for R-D5. Its 22
unrelated dirty files were never staged.

Also fixed en route: the old bash footer hardcoded `ref:deferred-infra` in *every* repo,
including the three whose block is `ref:deferred`. It had been pointing at a nonexistent key.

And the v11 install finally delivered the **T-59 harvest-boundary fix (overlay v8)** to three
consumers that had never received it — concrete residue of session 108's overclaimed "v9
synced cross-repo".

---

## Corrections I had to make, and who caught them

Recording these because the pattern matters more than the fixes.

| What I claimed | Reality | Caught by |
|---|---|---|
| "llm shouldn't take the CLAUDE.md merge — its Resuming section has repo-specific content" | Then that content is in the wrong place. Relocated `Sensitive data` to Environment Context; llm now carries the v11 markers | **user** |
| "llm is the home repo, it points at the source register" | A real install would create `.claude/handoff/registry.yaml`, and `run-handoff.sh`'s guard keys on that file existing — the handoff would silently switch while resume read source | **user** |
| "`ref:quick-pointers` lives in `.claude/index.md`" | index.md is *content* and an LTG anchor source; the register's own header says every other `ref:KEY` is must-not-touch. The block belonged in `session-context.md` | **user** |
| "fix T-80(a) now while the fixtures are cheap" | `test_customizable.py` is hermetic (54 `tmp_path` uses). Fixtures never expire. The real reason was that T-54 is live and T-80a rides along | me, on inspection |
| "T-54 is the unconditional-flagging bug" | **T-54 asks for a `--force-manual` override.** Still unbuilt. Three commit messages call this "T-54" and are wrong | me, during bookkeeping |
| "the version marker becomes a package `--version`" | Machine-global ≠ per-repo. Three version facts | **user** |

Three of llm's "home repo is special" behaviours fell, each load-bearing on the last. None
was defended on its merits; each was an accident with a comment attached.

> **A comment explaining why this case is special is usually the artifact of the accident,
> not the justification for it.** (`file: .claude/index.md  # NOT session-context.md`)

---

## Three tests that encoded the bug as the contract

- `test_customizable.py::test_11` asserted `'WARN' in statuses` — the non-discriminating warning.
- `test_verify.py::test_template_diff_gates_exit` asserted T-58's Decision (a) verbatim.
- `test_resume_steps.py`'s first `_extract_next_section` expectation omitted the heading the
  original `awk` prints, because I wrote the test from my implementation.

Each time the test encoded the same assumption as the code, so the suite went green while the
behaviour was wrong. The only things that caught these were **the byte-identity diff against
real output** and **the locator-contract check** — both compare against something the
implementation did not author.

This is `feedback_review_rederive_invariants` in the wild, three times in one session.

---

## Local model usage

| Call | Verdict | Note |
|---|---|---|
| `_reset_is_provable_noop` + `_same_content` | **1 (improved)**, ~700 est. tokens saved | Independently reached for `splitlines(keepends=True)` — the line-boundary insight, which a naive substring test would get wrong. Dropped the trailing-whitespace normalisation the prompt asked for |
| `present()` | **1 (improved)**, ~650 est. tokens saved | Filter→head→branch structure kept. Three mechanical slips: `\n` embedded in title strings, truthiness on `fallback` (so `fallback: ""` vanished), and a trailing-blank guard that dropped the explicitly-specified `raw="" → [""]` case |
| `--mode ai` merge plan | **TIMEOUT**, not a verdict | Two attempts on llm's 12.4 KB CLAUDE.md: 9-minute timeout, then ~20 minutes producing zero bytes |

Both code verdicts were `1` for the same reason: the model got the *hard* structural insight
and missed a *stated* requirement. Worth noting for prompt design — the constraints block was
followed for shape and ignored for detail.

---

## `--mode ai` (T-81)

**`--dry-run` never calls the model.** It prints `would call local-qwen3-14b (dry-run — no AI
call made)`. So the only way to learn what the AI merge does to a repo's most load-bearing
instruction file is to let it do it. There is no safe preview.

The hand-merge took minutes and is *verifiable*: after it, `install-overlay --dry-run` reports
`[SKIP] CLAUDE.md — already installed v11`, proving byte-exact agreement with what the overlay
would generate. T-81 asks for a plan-then-apply split mirroring the handoff's stage/promote
shape, which solved exactly this problem.

---

## State at close

- **Overlay v11** installed and committed in all five repos. `--verify` exit 0 everywhere.
- **287 tests** green. Package: 214. Installer: 64.
- `customizable:` has **zero call-sites** — the healthy steady state for an escape hatch. The
  category stays.
- llm is a normal consumer of its own overlay: CLAUDE.md markers, a real register copy
  byte-identical to source, `quick-pointers` in the right file.

### Open

| Task | Note |
|---|---|
| **T-54** | Still open — `--force-manual` override, never built. See correction above |
| **T-81** | `--mode ai`: no preview, does not finish |
| **#6** (no id) | Installer records nothing about what it installed. Without a baseline, `manual_if_exists` cannot tell "source changed since you reconciled" from "legitimately differs" |
| **#7** (no id) | Drop `--registry` from llm's home-repo SKILL invocation — now trivial |
| **T-53** | Preflight check. A working `--verify` is most of it |
| **T-60** | D adopted; G/H still to evaluate |

### Deliberately not done

- **T-80(b)** — cancelled. It repaired a workaround R-D5 deleted.
- The legacy `~/.claude/tools/handoff/` copy is a dormant shim fallback; deletable once
  confidence settles.
- `manual_if_exists` still cannot detect *stale* per-repo config. The locator contract covers
  the dangerous half (a register that lies), not the stale half.
