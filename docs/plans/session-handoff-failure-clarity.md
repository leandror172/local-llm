# Plan — Session-handoff: append↔checkoff fix + failure-clarity sweep

**Status:** Frozen, not built. Written 2026-06-17 (session 93).
**Trigger:** Bug report from the expenses repo — `expenses/code/.claude/local/session-tracking-bug-report.md`.
**Owner module tree:** `overlays/session-tracking/files/handoff/` (the engine source; this repo runs it from source, the 3 target repos run the **user-level** install at `~/.claude/tools/handoff/`).

This plan is written to be executable by a low-capability model. Follow the steps **in order**.
Every step says exactly which file, which function, what to change, and how to prove it worked.
Do **not** improvise beyond what is written. If a step's "BEFORE" text does not match the file,
**stop and report** — do not guess.

---

## 0. Background you must understand before touching anything

The handoff pipeline takes a *payload* (what Claude authored this session) and splices it into
tracking files (`.claude/tasks.md`, `.claude/session-log.md`, etc.) deterministically. The flow:

```
payload.py   parse + validate the payload
locator.py   find the byte-range (a "Region") each edit targets in a file
applier.py   produce the modified text for one Region
verifier.py  INDEPENDENTLY recompute the expected text and compare to the applied text
orchestrator.py  glue: locate all → apply all → verify all → write → commit
handoff.py   CLI: turns the above into JSON on stdout (status + reason)
```

`verifier.py` is a **second, independent implementation** of the splice. The whole point is that
if the applier and verifier disagree, something is wrong. They are *supposed* to always agree.

### The bug (two defects, fix both)

A single run carried a `tasks-append` (add a new task) **and** a `checkoffs:` entry (flip `T-02` to
done), both targeting `.claude/tasks.md`. It failed with the opaque message
`"Modified text does not match the expected text"`.

**Defect 1 — correctness (the two halves disagree).**
- `applier.py` treats `append` as a pure **insertion** at `region.end`: it never rewrites the
  interior bytes, so a sibling checkoff's `[ ]`→`[x]` flip *inside* the append region survives.
- `verifier.py:_segment` treats `append` as a **replace** of `[start,end]` with
  `region.interior + content`. `region.interior` is a stale snapshot (un-flipped `[ ]`). So the
  verifier's recomputed "expected" text **reverts the checkoff**, and `expected != modified`.
- The applier's insertion behavior is the **intended** one. `_segment` is the buggy half. Fix = make
  `_segment` for `append` an insertion too, so the two halves agree and the (legal, useful)
  append+checkoff-in-one-file combination verifies cleanly.

**Defect 2 — diagnostics (the failure was unreadable).**
The error named no file, no roles, gave no diff, and its wording ("**Modified** text") wrongly
implied the *payload* was bad — sending a reader to re-author content that was fine. Recovering the
real cause required reading 5 source files. **That must be structurally impossible.** Requirement:

> Every failure message must answer **where** (file + role[s]), **whose fault** (payload error the
> author can fix, vs internal tool bug to report), and **what** (a concrete diff/specifics) — so the
> reader never has to read pipeline source to understand the failure.

### Decisions already made (do not relitigate)
- **D-fix:** make `append` consistent as an insertion (NOT forbid the combo). [chosen by user]
- **D-class mechanism:** distinguish payload-fault vs tool-fault using a **`kind` attribute on the
  exception** (NOT separate exception subclasses). [chosen by user — "simpler for now"]
- **D-sweep depth:** **full** sweep — every failure exit in the pipeline gets the where/whose/what
  triad, plus a guard test. [chosen by user]
- **D-prepend:** Track 1 fixes BOTH `append` and `prepend` as insertions (prepend has the identical
  latent hazard). [confirmed by user]
- **D-contract:** the `stage_failed` → `payload_error`/`internal_tool_bug` JSON rename is a clean
  break — **no external consumers**, so no back-compat alias needed. [confirmed by user]
- **D-rollout:** installation is now B+C — the engine lives user-level at `~/.claude/tools/handoff/`,
  shared by all repos. **No per-repo byte-verify propagation needed.** Just update source + bump the
  manifest version + reinstall the user-level copy.

---

## 0.5 Execution split — two-agent dispatch (Sonnet spine + Haiku mechanical)

This plan is meant to run as **two subagents in sequence**, not one. The split follows the risk
surface: reasoning + all self-authored tests go to the stronger model; mechanical string-enrichment
goes to the cheaper model **only after** the spine is green and the test suite exists as a guardrail.

### Agent A — Sonnet (the spine). Run FIRST.
**Gate before starting:** run the baseline (Section 1). If it is not **166 green**, STOP and report —
do not start.

Scope, in order:
- **Track 1 entirely:** Steps 1.1, 1.2, 1.3, 1.4 (regression test → loop fix → guard-agreement check
  → green).
- **Step 2.0** (populate `Region.role/target/file` via `dataclasses.replace`).
- **Step 2.1** (add `kind` to the five exception classes) — cheap, but it's the contract the rest
  depends on, so do it here.
- **Step 2.2** (rewrite verifier mismatch + marker messages with `_first_diff`/`_edits_label`).
- **Step 2.4** (CLI status routing — the dual-path `kind` reasoning).
- **Step 2.6** (the `test_failure_clarity.py` contract tests — ALL test authoring stays with A).

**Exit criteria for Agent A (the handoff gate):** full suite green INCLUDING the new
`test_failure_clarity.py`; append+checkoff combo verifies; CLI returns `payload_error` vs
`internal_tool_bug` correctly. Agent A reports the test count and the list of files it touched.
**If Agent A's exit criteria are not met, do NOT dispatch Agent B** — fix the spine first.

Why these are A's: 1.1/2.6 are self-authored tests with no oracle above them (a vacuous green test on
a correctness fix is the worst outcome); 1.2 has the "fix `_segment` and it still fails" trap; 2.0 has
the frozen-dataclass hazard; 2.4 needs the stage-vs-promote dual-path reasoning. See Section 6.

### Agent B — Haiku or local `my-python-q25c14` (mechanical). Run SECOND, only after A's gate.
Per repo convention `my-python-q25c14` is the preferred Python codegen model and generating with it
produces DPO data — prefer it over Haiku if available; record a verdict (2/1/0) per
`[ref:local-model-conventions]`.

Scope (all are find-the-raise / enrich-the-string, with the full suite as a regression guard):
- **Step 2.3** (locator messages: name role + file + specific target; keep `kind="payload"`).
- **Step 2.5** (sweep table: confirm/enrich remaining raises + set correct `kind`).
- **Step 3** (SKILL.md path nit + document new statuses).
- **Step 4** items 1–2,4 (manifest bump, overlay-memory update, index.md row). Item 3 (reinstall) and
  item 5 (reply to bug report) are **operational — leave for the main session / user**, not Agent B.

**Constraints on Agent B:** do not modify `verifier.py` reconstruction logic, `orchestrator._collect_edits`,
or any test file. If a change makes a test fail, STOP and report — a red suite after B means B touched
behavior it shouldn't have. B only enriches strings and sets `kind=`.

**Exit criteria for Agent B:** full suite still green; every message in the Section-5 checklist names
file + role(s); SKILL.md updated. Report files touched.

### After both agents
Main session / user handles: the user-level reinstall (Step 4.3 — **ask which installer command**,
don't guess), the bug-report reply (Step 4.5), and the final Section-5 acceptance pass.

---

## 1. How to run the tests (you will do this after every code step)

The tests live alongside the source as `test_*.py` and import modules by bare name
(`from verifier import ...`), so they must run with the working directory set to the handoff dir.

```bash
cd /mnt/i/workspaces/llm/overlays/session-tracking/files/handoff
python -m pytest -q
```

Baseline before you start: **166 tests, all green.** If the baseline is not green, STOP and report —
do not start changing code on a red baseline. After each step, the suite must stay green (plus any
new tests you add). Per repo convention, prefer `rtk cargo test`-style wrappers where they exist; for
this Python suite there is no wrapper, so `python -m pytest` from the handoff dir is the accepted way.

---

## TRACK 1 — Correctness fix (append↔checkoff)

### Step 1.1 — Write the failing regression test FIRST (TDD)

File: `overlays/session-tracking/files/handoff/test_verifier.py` (append a new test function).

Goal: a single combined edit set on ONE text — an `append` region that **encloses** a `checkoff`
target line — must `verify()` without raising.

**CRITICAL — the bug only manifests when `append.start < checkoff.start`.** Both `_apply_all` and
`verify()` sort edits by `start` **descending** with a *stable* sort. If append and checkoff have the
**equal** start, append reconstructs first (replacing the span with the stale interior) and the
checkoff re-flips on top — net `expected == modified`, so `verify` does **NOT** raise and the test is
**vacuous** (it passes against the buggy code). A naive construction where the task line is the first
byte of the region makes the starts equal and silently defeats the test. You MUST place a line (a
marker or heading) before the first task so the append region starts strictly *before* the checkoff
line. The realistic `ref_block` shape already does this — copy it exactly:

```python
def test_append_region_enclosing_checkoff_verifies():
    # Realistic ref_block tasks.md fragment. The append region's interior begins at
    # "## Deferred" (right after the open marker); the T-02 line is a LATER line, so
    # append.start < checkoff.start — which is what makes the bug reproduce.
    original = (
        "<!-- ref:deferred-infra -->\n"
        "## Deferred\n"
        "- [ ] (T-02) wire up retry\n"
        "- [ ] (T-03) cache headers\n"
        "<!-- /ref:deferred-infra -->\n"
    )
    interior_start = original.index("## Deferred")        # after the open-marker line
    interior_end = original.index("<!-- /ref:deferred-infra -->")
    append_region = Region(
        kind="ref_block", mode="append",
        start=interior_start, end=interior_end,
        interior=original[interior_start:interior_end],
        role="tasks-append", target="deferred-infra", file=".claude/tasks.md",
    )
    co_start = original.index("- [ ] (T-02)")             # strictly > interior_start
    co_end = original.index("\n", co_start) + 1
    checkoff_region = Region(
        kind="checklist", mode="checkoff",
        start=co_start, end=co_end,
        interior=original[co_start:co_end],
        role="tasks-checkoff", target="T-02", file=".claude/tasks.md",
    )
    assert append_region.start < checkoff_region.start    # guard: bug only reproduces here

    append_content = "- [ ] (T-04) new task\n"
    # What applier+checkoff actually produce: checkoff flips T-02, append inserts at region.end.
    flipped = original.replace("- [ ] (T-02)", "- [x] (T-02)", 1)
    modified = flipped[:append_region.end] + append_content + flipped[append_region.end:]

    edits = [(append_region, append_content), (checkoff_region, "")]
    verify(original, modified, edits)   # must NOT raise (after Step 1.2)
```

**Pre-fix assertion (do this BEFORE Step 1.2):** run this test against the *unmodified* `verifier.py`
and confirm it **raises `VerifyError`** with a message containing `does not match`. That proves the
construction actually reproduces the bug. **If it does NOT raise, the construction is wrong (most
likely `append.start == checkoff.start`) — STOP and report; do not proceed to the fix**, because a
fix verified only by a test that never failed is worthless. Only after you've seen it raise do you
apply Step 1.2 and re-run to see it pass.

> Why the `assert append_region.start < checkoff_region.start` line: it's a tripwire so that if anyone
> later "simplifies" the fixture into equal starts, the test fails loudly instead of going vacuous.

### Step 1.2 — Fix `_segment` for append in `verifier.py`

File: `overlays/session-tracking/files/handoff/verifier.py`, function `_segment` (around line 28-39).

The verifier reconstructs the whole file by, for each region, doing
`expected = expected[:region.start] + _segment(region, content) + expected[region.end:]`
(see `verify()` around line 74-77). For `append` this currently **replaces** `[start,end]`, which
clobbers nested edits. We must make append contribute an **insertion at the end** that preserves
whatever bytes are currently in `[start,end]` (they may have been mutated by a nested edit applied
earlier in the descending-sort sequence).

BEFORE (the append branch):
```python
    elif region.mode == "append":
        return region.interior + content
```

The problem: this returns `interior` (stale snapshot) and the caller replaces `[start,end]`. The
fix is to NOT overwrite the interior. The cleanest way that fits the existing reconstruction loop:
append should re-emit the **current** interior of `expected` (not the stale snapshot) followed by
`content`. But `_segment` does not see `expected`. So the fix must be in the reconstruction loop, not
only in `_segment`. Implement it in `verify()`:

In `verify()` (around lines 74-77), the reconstruction loop is:
```python
    expected = original
    for region, content in sorted(edits, key=lambda e: e[0].start, reverse=True):
        segment = _segment(region, content)
        expected = expected[:region.start] + segment + expected[region.end:]
```

Change the `append` (and `checkoff`, which has the same nested-snapshot hazard) handling so that for
**insertion-style** modes the existing bytes in `expected[region.start:region.end]` are preserved
rather than replaced by a snapshot. Concretely, special-case append to be a true insertion at
`region.end`:

AFTER:
```python
    expected = original
    for region, content in sorted(edits, key=lambda e: e[0].start, reverse=True):
        if region.mode == "append":
            # Insertion at region.end — DO NOT overwrite the interior, which may
            # carry a nested edit (e.g. a checkoff flip) applied earlier in this loop.
            expected = expected[:region.end] + content + expected[region.end:]
        elif region.mode == "prepend":
            # Insertion at region.start — same reasoning.
            expected = expected[:region.start] + content + expected[region.start:]
        else:
            segment = _segment(region, content)
            expected = expected[:region.start] + segment + expected[region.end:]
```

Then delete the now-unused `append`/`prepend` branches from `_segment` ONLY IF nothing else calls
them. Search first: `grep -n "_segment" verifier.py test_verifier.py`. If `_segment` is called only
from this loop, simplify it; if it's referenced elsewhere/tested directly, leave the branches and
just rely on the loop's special-casing (the loop now never asks `_segment` for append/prepend, so the
dead branches are harmless). **When unsure, leave `_segment` alone** — the loop change is what fixes
the bug.

> Why prepend too: prepend is also an insertion (`applier._apply_prepend` inserts at `region.start`
> without touching interior). It has the identical latent hazard. Fixing both now closes the class.

### Step 1.3 — Make the overlap guard agree (verify it already does)

`verifier.py:_effective_range` already returns a **zero-width** range for append (`(region.end,
region.end)`) and prepend (`(region.start, region.start)`), and a 3-byte range for checkoff. After
Step 1.2 the reconstruction also treats append/prepend as zero-width insertions, so guard and
reconstruction now **agree**. No change expected here — but **read `_effective_range` (lines 42-57)
and confirm** append=point, prepend=point, checkoff=3-byte. If they already match, do nothing. If they
don't, STOP and report (the assumption behind this plan is wrong).

### Step 1.4 — Run tests

`python -m pytest -q` from the handoff dir. The Step 1.1 test must now **pass**; all prior tests stay
green. If any prior test breaks, the most likely cause is a test that asserted the OLD (buggy)
append-as-replace reconstruction — read it, and if it encodes the bug, update it to the insertion
semantics (and note why in the test). If a break is NOT obviously the old-behavior assertion, STOP
and report.

---

## TRACK 2 — Failure-clarity sweep

The triad every failure must satisfy: **where** (file + role[s]) · **whose fault** (payload vs tool) ·
**what** (specifics / diff). Mechanism for "whose fault" = a `kind` attribute on the exception.

### Step 2.0 — Precondition discovered during planning: Region metadata is NOT populated

`locator.Region` has `.role`, `.target`, `.file` fields (locator.py:14-17) intended for diagnostics,
but `_collect_edits` in `orchestrator.py` does **not** populate them — `locate()` returns a Region
with those fields empty, and the role name is kept only as a tuple element. So today
`verifier._region_label` would print `()@:` for these regions. **This must be fixed first**, or the
"name the file + roles" requirement cannot be met.

File: `orchestrator.py`, function `_collect_edits` (lines 126-175) and `_add_header_edits_from_values`
(178-184). `Region` is a **frozen** dataclass, so use `dataclasses.replace`.

Add at top of orchestrator.py: `from dataclasses import replace as _replace`.

Create a small helper near `_collect_edits`:
```python
def _enrich(region: Region, role: str, role_def: dict, target: str = "") -> Region:
    """Attach diagnostic metadata so downstream errors can name the source."""
    return _replace(region, role=role, file=role_def.get("file", ""), target=target)
```

Then wrap every `locate(...)` result before `add(...)`. For each call site:
- block roles loop (line 142): `target` = the locator key/label if present, else "".
  `region = _enrich(locate(role_def, text_of(rel)), role, role_def, _target_of(role_def))`
- checkoff loop (line 148): `target = task_id`.
- header edits (`_add_header_edits_from_values`, line 183): `target = role_def["locator"].get("label","")`.
- log-entry (line 173): `target` = "".

Add a tiny `_target_of(role_def)` helper that returns `role_def["locator"].get("key")` or
`.get("label")` or `""` depending on locator type (read it defensively with `.get`).

After this, `verify()` receives regions whose `.role`/`.file`/`.target` are populated, so
`_region_label` produces `tasks-checkoff(T-02)@.claude/tasks.md:2`.

Run tests — should stay green (additive metadata only). If a test asserted empty role/file on a
Region, update it.

### Step 2.1 — Add the `kind` attribute to pipeline exceptions

Goal: each raised exception declares whether it is a **payload** fault (author can fix) or an
**internal** fault (tool bug, report it). Default to a sensible value so nothing crashes if unset.

For EACH exception class below, add an optional `kind` argument with a class-appropriate default:

- `verifier.py` → `VerifyError`: default `kind="internal"` (verifier mismatches are invariant breaks).
- `locator.py` → `LocatorError`: default `kind="payload"` (target not found = author/content issue).
- `applier.py` → `ApplierError`: default `kind="internal"` (unknown/nomodel mode = wiring bug).
- `payload.py` → `PayloadError`: default `kind="payload"`.
- `registry_io.py` → `RegistryError`: default `kind="internal"` (registry is shipped config, not author payload).

Pattern (apply to each class — example for `VerifyError`):
```python
class VerifyError(Exception):
    def __init__(self, message, *, kind="internal"):
        super().__init__(message)
        self.kind = kind
```

Do NOT change call sites that raise these yet (next steps do that). Existing raises keep working
because `kind` defaults. Run tests — green.

### Step 2.2 — Rewrite the offending verifier messages (where + what + label)

File: `verifier.py`, function `verify()`.

Add a diff helper near the top of the module:
```python
def _first_diff(expected: str, actual: str, ctx: int = 40) -> str:
    """Return 'at byte N: expected <…> | actual <…>' for the first differing byte."""
    n = min(len(expected), len(actual))
    i = 0
    while i < n and expected[i] == actual[i]:
        i += 1
    e = expected[max(0, i - ctx): i + ctx].replace("\n", "\\n")
    a = actual[max(0, i - ctx): i + ctx].replace("\n", "\\n")
    return f"at byte {i}: expected «{e}» | actual «{a}»"
```

Add a roles+file summary helper:
```python
def _edits_label(original, edits) -> str:
    files = sorted({getattr(r, "file", "") for r, _ in edits if getattr(r, "file", "")})
    roles = [getattr(r, "role", "") for r, _ in edits if getattr(r, "role", "")]
    return f"file(s) {files} after applying roles {roles}"
```

BEFORE (line ~80):
```python
    if expected != modified:
        raise VerifyError("Modified text does not match the expected text")
```
AFTER:
```python
    if expected != modified:
        raise VerifyError(
            "internal verification mismatch — this is likely a TOOL BUG, not your payload. "
            "Please report it with the run's input.md. "
            f"verify failed on {_edits_label(original, edits)}; "
            f"diff {_first_diff(expected, modified)}",
            kind="internal",
        )
```

BEFORE (line ~91):
```python
    if sorted(original_markers) != sorted(modified_markers):
        raise VerifyError("Ref-marker multisets differ")
```
AFTER: compute which markers were lost/gained and include them, keep `kind="internal"`:
```python
    if sorted(original_markers) != sorted(modified_markers):
        lost = sorted(set(original_markers) - set(modified_markers))
        gained = sorted(set(modified_markers) - set(original_markers))
        raise VerifyError(
            "internal verification mismatch (ref-marker set changed) — likely a TOOL BUG; "
            f"report with input.md. on {_edits_label(original, edits)}; "
            f"lost={lost} gained={gained}",
            kind="internal",
        )
```

The `_segment`/`_effective_range` "Unsupported mode" raises (lines 39, 57) keep `kind="internal"` and
should name the mode and (if available) the role — change message to
`f"unsupported mode '{region.mode}' for role '{getattr(region,'role','?')}' — TOOL BUG"`.

Run tests. Existing verifier tests that assert the OLD literal strings will break — update those
assertions to match the new messages (search: `grep -n "does not match the expected" test_verifier.py`
and `grep -n "multisets differ" test_verifier.py`). Adjusting test assertions to new, richer messages
is expected and correct here.

### Step 2.3 — Make locator messages name role + file + the specific target

File: `locator.py`. Problem: messages like `"Missing marker(s)"`, `"Checklist item not found or
duplicated"` name nothing. The functions receive `role` (the register dict, has `file` + locator
details). Pass through enough to name things. The role *name* string is not in the dict, but the
file, locator key/label/pattern, and (for checklist) the `task_id` ARE available locally.

Rewrite each `raise LocatorError(...)` to include file + the specific identifier + found-vs-expected.
Keep `kind="payload"` (these are author-fixable). Examples:

- `_locate_ref_block` line 46:
  `raise LocatorError(f"ref block <!-- ref:{key} --> not found in {role['file']} "
                      f"(open found={start_index!=-1}, close found={end_index!=-1}). "
                      f"Check the marker exists and is spelled exactly.", kind="payload")`
- line 49 (duplicate): name `key`, `role['file']`, and the counts.
- `_locate_field` line 69: name `label`, `role['file']`, and `len(matches)` ("found 0" vs "found 2").
- `_locate_structural` line 90: name `pattern`, `occurrence+1`, `role['file']`, `len(matches)`.
- `_locate_checklist` line 129: name `task_id`, `role['file']`, `len(matches)` — e.g.
  `f"task id {task_id} matched {len(matches)} checklist items in {role['file']} (need exactly 1). "
   f"If 0: the task isn't an unchecked '- [ ]' line. If >1: the id is ambiguous."` with `kind="payload"`.

The `ValueError`s in locator (lines 35, 111, 115) are internal wiring (bad register) — leave as
`ValueError` but enrich the text (`f"unknown locator type '{locator_type}' in register"`); these
indicate a malformed register, not author payload.

Run tests; update any locator test asserting the old literals.

### Step 2.4 — Surface `kind` in the orchestrator + CLI (the "whose fault" routing)

The orchestrator catches `LocatorError`/`VerifyError` and funnels through `_fail`, then `handoff.py`
stamps a JSON `status`. Today everything from staging becomes `stage_failed`, hiding whose fault it is.

**orchestrator.py** — `run_handoff` `except` blocks (lines 65-68): preserve the exception's `kind`
into the reason or a new RunReport field. Simplest within "kind on exception, simpler for now": prefix
the reason with the kind so it survives to the CLI, e.g.:
```python
    except LocatorError as exc:
        return _fail(run_dir, session_number,
                     f"[{getattr(exc,'kind','payload')}] locate failed: {exc}",
                     verify_ok=False, edits=[])
    except VerifyError as exc:
        return _fail(run_dir, session_number,
                     f"[{getattr(exc,'kind','internal')}] verify failed: {exc}",
                     verify_ok=False, edits=[])
```

**handoff.py** — `_stage_path`, the stage `except Exception` block (lines 125-128). Right now:
```python
    except Exception as e:
        run_dir = mark_run_failed(run_dir)
        print(json.dumps({"status": "stage_failed", "reason": str(e)}))
        return 1
```
Replace the flat `stage_failed` with a status derived from `kind`:
```python
    except Exception as e:
        run_dir = mark_run_failed(run_dir)
        kind = getattr(e, "kind", "internal")
        status = "payload_error" if kind == "payload" else "internal_tool_bug"
        reason = str(e)
        if status == "internal_tool_bug" and "input.md" not in reason:
            reason += f"  (report this with {run_dir}/input.md)"
        print(json.dumps({"status": status, "reason": reason}))
        return 1
```
Note: `stage_and_apply` raises the bare `LocatorError`/`VerifyError` (it does NOT go through the
orchestrator's `[kind]` prefixing — that prefixing is only on the `run_handoff`/`--id` path). So the
stage path reads `e.kind` directly off the exception, which is why Step 2.1 put `kind` on the classes.
For the `--id`/promote path, the reason string already carries `[kind]` from the orchestrator; if you
want the same `payload_error`/`internal_tool_bug` status there too, parse the `[...]` prefix in
`_promote_path` similarly — do this for consistency.

Run tests; update `test_handoff_cli.py` assertions that expect `stage_failed` (search:
`grep -n "stage_failed" test_handoff_cli.py`). The new statuses are `payload_error` /
`internal_tool_bug`. **If any external doc or skill references the literal `stage_failed`, update it
too** (search the SKILL.md — Step 3).

### Step 2.5 — Sweep the remaining raises for the triad

Walk every failure exit found in the audit and confirm it names where + what and carries the right
`kind`. Most are already decent; enrich only where a token is missing.

| File:line | Action |
|---|---|
| `payload.py` 90/137/177/188/204/249 | Already specific + actionable. Just ensure `kind="payload"`. |
| `mechanics.py` 27/29 (LogEntry slots) | `ValueError` — message is clear; leave (it's caught and surfaced as PayloadError upstream at payload.py:249). |
| `registry_io.py` 38/45/49/52 | Already name the path. Ensure `kind="internal"` (shipped config, not author payload). |
| `runlog.py` 49/53/55/62/71/80 | Already name the handle / dir. These surface as `status:"error"` in handoff.py — leave. |
| `orchestrator.py` 50 (dirty tree) | Already clear and actionable ("commit or stash first" could be added). `kind` n/a (it's a RunReport reason, not an exception). Optionally append "— commit or stash the tracking files, then retry." |
| `orchestrator.py` 206 (rotation) | `RuntimeError` with stderr — internal/operational; leave, but ensure stderr is included (it is). |
| `applier.py` 30/32 | `ApplierError` `kind="internal"`; message already names the mode. |
| `verifier.py` 70 (overlap guard) | Already calls `_region_label` (so Step 2.0 fixes its naming). Set `kind="payload"` — two genuinely overlapping regions means the author specified conflicting edits. Prefix message with "two payload edits target overlapping bytes:" so the reader knows it's fixable by re-authoring, not a tool bug. |

### Step 2.6 — Add the contract guard test (prevents regression of "no investigation")

New test file: `overlays/session-tracking/files/handoff/test_failure_clarity.py`.

Purpose: assert the triad holds, so future raises can't silently regress to bare strings.

Write at least these tests:
1. **Append+checkoff now succeeds end-to-end** (integration via `stage_and_apply` or `_collect_edits`
   + `verify`) — the real-world reproduction of the bug report, green.
2. **The internal equality-mismatch raise (line 81).** IMPORTANT: you cannot reach line 81 through
   normal flow after the Step 1.2 fix — applier and verifier now agree, so a real run never diverges.
   And two overlapping `replace` regions trip the **overlap guard at line 70** (`...overlaps...`),
   NOT line 81 — do not use that, its message has no `TOOL BUG`/`byte` tokens and the test would fail.
   To exercise line 81 you must **inject a divergence**: build a valid `original` + `edits`, compute
   the correct `modified` the applier would produce, then hand `verify()` a *deliberately corrupted*
   `modified` (e.g. flip one byte) so reconstruction ≠ supplied. Assert the raised `VerifyError`
   contains `TOOL BUG`, a `.claude/` file token, the word `roles`, and `byte`; and `err.kind == "internal"`.
   (Add a sibling test that injects a ref-marker deletion into `modified` to hit the marker-mismatch
   raise at line 91; assert it contains `TOOL BUG` and `lost=`.)
3. **A locator miss** (checkoff a non-existent task id) → `LocatorError` whose message contains the
   task id and the file path, and `err.kind == "payload"`.
4. **CLI classification**: drive `handoff.main(["--payload", <bad-payload>])` (or the lower-level
   `_stage_path`) for (a) a payload error (e.g. checkoff a non-existent task id → `LocatorError`,
   `kind="payload"`) → JSON `status == "payload_error"`; and (b) the internal case → `status ==
   "internal_tool_bug"` and reason mentions `input.md`. For (b) you cannot trigger an internal
   mismatch through a normal payload (see test 2) — **monkeypatch** the applier (or
   `orchestrator._apply_all`) to return corrupted text so `verify()` raises `VerifyError(kind=
   "internal")` inside `stage_and_apply`, then assert the CLI maps it to `internal_tool_bug`. Use the
   existing CLI test harness/fixtures in `test_handoff_cli.py` as the template for how to invoke and
   how to monkeypatch.

Run the full suite. Everything green.

---

## 3. Skill doc fixes (the report's doc nit + new statuses)

File: the session-handoff skill — `overlays/session-tracking/files/session-handoff/SKILL.md` (source of
truth). Also the installed copies follow install-level now (user-level by default), so updating source
+ reinstall is enough.

1. **Path nit (report's final section):** the skill documents `run-handoff.sh` at
   `.claude/tools/run-handoff.sh`; the real path is `.claude/tools/handoff/run-handoff.sh`. Find and
   correct every occurrence (`grep -n "tools/run-handoff" SKILL.md`).
2. **New failure statuses:** wherever the skill explains stage output, document the new statuses:
   - `payload_error` — your payload/content is wrong; read `reason`, fix, re-stage.
   - `internal_tool_bug` — pipeline invariant broke; file a report with the run's `input.md`; do NOT
     keep re-authoring.
   (Keep `validation_failed`, `stage_ok`, `committed`, `error`, `aborted` as-is.)
3. **Append+checkoff is now supported:** if the skill anywhere warns against combining `tasks-append`
   with `checkoffs:` in one run (it may not — that workaround was the report author's, not necessarily
   in the skill), remove/needn't-add that warning. The combo works after Track 1.

---

## 4. Rollout

Because of B+C distribution, the engine is **user-level shared** (`~/.claude/tools/handoff/`), not
copied per repo. So:

1. Bump the overlay version in `overlays/session-tracking/manifest.yaml` (v6 → v7) with a one-line
   changelog: "append↔checkoff consistency fix + failure-clarity sweep (where/whose/what + kind)".
2. Update `overlays/.memories/QUICK.md` and `KNOWLEDGE.md` session-tracking sections: new version,
   new statuses, the `_segment` insertion fix, the `kind`-on-exception mechanism.
3. Reinstall the user-level copy from source via the overlay installer (the same mechanism that
   populated `~/.claude/tools/handoff/` during the B+C migration). **No byte-verify of the 3 target
   repos** — they share the user-level engine. Confirm with the user which installer command to run
   (it changed in the B+C migration); do not guess the command.
4. Update `.claude/index.md` if any script/behavior description changed (the `run-handoff.sh` row).
5. Reply to the expenses bug report (leave a note in
   `expenses/code/.claude/local/session-tracking-bug-report.md` or a follow-up file): root cause
   confirmed, both defects fixed, new statuses, combo now supported, path nit fixed.

---

## 5. Acceptance checklist (all must be true before declaring done)

- [ ] Baseline 166 tests were green before changes.
- [ ] Track-1 regression test (append enclosing checkoff) failed before the fix, passes after.
- [ ] `verifier.verify` treats append AND prepend as insertions; guard and reconstruction agree.
- [ ] Full suite green, plus the new `test_failure_clarity.py` tests.
- [ ] Region `.role/.file/.target` populated in `_collect_edits` (Step 2.0).
- [ ] Every Track-2 message names file + role(s); verifier mismatch says "TOOL BUG" + diff; locator
      miss names the id + file.
- [ ] CLI returns `payload_error` vs `internal_tool_bug` correctly; internal case mentions `input.md`.
- [ ] SKILL.md path nit fixed; new statuses documented.
- [ ] Manifest bumped to v7; overlay memories updated; user-level engine reinstalled.
- [ ] Bug report responded to.

---

## 6. Things that will trip up a careless implementer (read this)

- **Frozen dataclass:** `Region` is `@dataclass(frozen=True)`. You cannot do `region.role = ...`. Use
  `dataclasses.replace`.
- **Apply order is descending by `start`:** `orchestrator._apply_all` and `verifier.verify` both sort
  descending. Do not change this — the Track-1 fix relies on nested edits being applied before the
  enclosing insertion in the recompute loop.
- **Stage path vs promote path read `kind` differently:** stage (`--payload`) reads `e.kind` off the
  live exception; promote (`--id`) gets a reason string already prefixed `[kind]` by the orchestrator.
  Handle both.
- **Don't forbid the combo.** The decision is to SUPPORT append+checkoff. Do not add a containment
  rejection in `payload.validate` — that was an alternative the user rejected.
- **Update tests, don't delete them.** Several existing tests assert the OLD literal error strings or
  `stage_failed`. Update assertions to the new richer text/statuses; never delete a test to make the
  suite pass.
- **If a BEFORE snippet doesn't match the file, STOP and report.** Line numbers in this plan are from
  session 93 and may drift; match on the code text, not the line number.
