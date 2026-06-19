# Bug Report: tasks-append + tasks-checkoff Fail with "Overlapping edit regions detected" When Checkoff Items Live Inside the Append Block

**Severity:** Medium — payload is valid and semantically consistent; pipeline rejects it incorrectly  
**Component:** `verifier.py` (overlap guard), `locator.py` (`_locate_ref_block`)  
**Affects:** Any payload that includes both `tasks-append` and `checkoffs` for task IDs that currently live inside the `ref:deferred` block

---

## Scenario

The standard end-of-session handoff payload includes two operations against `tasks.md`:

1. **`tasks-append`** — appends newly discovered tasks to the end of the `<!-- ref:deferred -->` block  
2. **`checkoffs: [T-03, T-04, T-05, T-06]`** — flips four existing tasks from `- [ ]` to `- [x]`

The triggering state in `tasks.md` (abbreviated):

```markdown
<!-- ref:deferred -->
## Deferred / Backlog

- [ ] (T-03) Send André reply (#064) — ...
- [ ] (T-04) Send Dexian reply (#065) — ...
- [ ] (T-05) Decide and reply Fishbowl #066 — ...
- [ ] (T-06) Jahnel Group open roles — ...
<!-- /ref:deferred -->
```

T-03 through T-06 are all inside the `ref:deferred` block. `tasks-append` targets that same block. When both roles appear in the same payload, the dry-run fails immediately:

```
dry-run FAILED (session 57): dry-run: verify failed: Overlapping edit regions detected
verify: FAILED
```

The pipeline reports no further detail — just the one-line `VerifyError` from `verifier.py:32`.

---

## Root Cause Analysis

### How regions are computed

`_collect_edits` in `orchestrator.py` calls `locate()` for every role in the payload (lines 152–161). For `tasks-append`, `locate()` dispatches to `_locate_ref_block` in `locator.py`:

```python
# locator.py:33–56
def _locate_ref_block(role, text) -> Region:
    open_marker  = f"<!-- ref:{key} -->"
    close_marker = f"<!-- /ref:{key} -->"
    interior_start = text.index("\n", text.find(open_marker)) + 1
    interior_end   = text.find(close_marker)
    return Region(
        kind="ref_block",
        mode=role["write_mode"],   # "append" for tasks-append
        start=interior_start,
        end=interior_end,
        interior=text[interior_start:interior_end]
    )
```

For the `ref:deferred` block, this produces a region that **spans the entire interior** — from the byte immediately after `<!-- ref:deferred -->\n` to the byte immediately before `<!-- /ref:deferred -->`. Call this `R_append = [A_start, A_end)`.

For each checkoff in `payload.checkoffs`, `_locate_checklist` in `locator.py` returns a region spanning the matching task line:

```python
# locator.py:109–134
def _locate_checklist(role, text, *, task_id) -> Region:
    matches = [
        m for m in re.finditer(r'^- \[ \].*$', text, re.MULTILINE)
        if id_boundary.search(m.group()[:40])
    ]
    start, end = matches[0].span()
    return Region(kind="checklist", mode="checkoff", start=start, end=end, ...)
```

Each checkoff region `R_T03`, `R_T04`, … spans a single line inside the deferred block. Since these lines are between `<!-- ref:deferred -->` and `<!-- /ref:deferred -->`, each `R_Txx.start` and `R_Txx.end` are both strictly between `R_append.start` and `R_append.end`. The checkoff regions are **fully nested** inside the append region.

### The overlap guard

`verify()` in `verifier.py` runs a simple pairwise adjacency check after sorting edits by `region.start`:

```python
# verifier.py:28–32
sorted_edits = sorted(edits, key=lambda e: e[0].start)
for i in range(1, len(sorted_edits)):
    if sorted_edits[i][0].start < sorted_edits[i - 1][0].end:
        raise VerifyError("Overlapping edit regions detected")
```

When `R_append` comes first (lowest `start`), every checkoff region's `start` is less than `R_append.end` — the containment condition `R_Txx.start < R_append.end` is always true. The guard fires on the first checkoff and aborts.

### Why the guard is overly conservative here

The overlap guard was designed to catch genuinely conflicting edits — two `replace` operations that both claim the same byte range would produce non-deterministic output depending on application order. That concern is valid.

But `append` mode does not modify the interior `[start, end)`. Inspect `applier.py`:

```python
# applier.py:45–47
def _apply_append(text, region, content) -> str:
    return text[:region.end] + content + text[region.end:]
```

`_apply_append` only reads `region.end`. It inserts at that single point and leaves everything before it untouched. The interior `[region.start, region.end)` is passed through unchanged — `region.start` is never used by the applier.

Similarly, `checkoff` only modifies a specific `- [ ]` → `- [x]` substitution within its narrow line region. It does not touch `region.end` of the append block.

**These two operations do not conflict.** Applied in either order they produce identical output: the `- [ ]` lines get flipped to `- [x]`, and the new tasks are inserted after the last line in the block. The overlap guard rejects them because it treats `append` as if it modified the full `[start, end)` range — which the applier never actually does.

### Concrete byte picture

Given `tasks.md` with `ref:deferred` at bytes `[1000, 1400)` (interior):

| Role | Region | Bytes actually written |
|---|---|---|
| `tasks-append` | `start=1000, end=1400` | inserts at byte 1400 only |
| `tasks-checkoff` T-03 | `start=1050, end=1110` | flips `[ ]`→`[x]` at bytes 1051–1053 |
| `tasks-checkoff` T-04 | `start=1110, end=1170` | flips `[ ]`→`[x]` at bytes 1111–1113 |

No byte is written by more than one operation. The guard incorrectly concludes that `1050 < 1400` means T-03 overlaps with `tasks-append`.

---

## Workaround Used

Strip `tasks-append` from the payload. Run the handoff with checkoffs only. Manually append new tasks to `tasks.md` in a separate commit after the handoff completes.

This loses the atomicity guarantee for the task-addition step. The new tasks (T-07, T-08) are committed outside the handoff transaction and are not covered by the verifier.

---

## Proposed Fixes

### Fix A — Mode-aware overlap check in `verifier.py` (recommended)

Teach the overlap guard about write modes. Only `replace` and `checkoff` use their full `[start, end)` range. `append` only touches `end`; `prepend` only touches `start`.

```python
def _effective_range(region) -> tuple[int, int]:
    """Return the byte range actually written by this operation."""
    if region.mode == "append":
        return (region.end, region.end)       # point insertion after interior
    if region.mode == "prepend":
        return (region.start, region.start)   # point insertion before interior
    return (region.start, region.end)         # replace / checkoff: full range

def verify(original, modified, edits):
    sorted_edits = sorted(edits, key=lambda e: e[0].start)
    for i in range(1, len(sorted_edits)):
        prev_start, prev_end = _effective_range(sorted_edits[i - 1][0])
        curr_start, _        = _effective_range(sorted_edits[i][0])
        if curr_start < prev_end:
            raise VerifyError("Overlapping edit regions detected")
    # ... rest unchanged
```

With this change, `tasks-append` contributes effective range `(1400, 1400)` — a zero-width point. No checkoff region starts at 1400 or later, so no overlap is detected.

**Trade-off:** The guard no longer catches a `replace` + `append` to the same block where the replacement content would move the close marker and make the append land in the wrong place. That scenario is already caught by the "Modified text does not match expected text" check that follows — so the safety net is preserved, just at the next step rather than the eager guard.

### Fix B — Mode-aware region shape from `_locate_ref_block`

Change `_locate_ref_block` to return a narrowed region based on `write_mode` before the region ever reaches the overlap guard:

```python
def _locate_ref_block(role, text) -> Region:
    # ... (find markers as before)
    interior_start = text.index("\n", start_index) + 1
    interior_end   = text.find(close_marker)
    mode = role["write_mode"]
    if mode == "append":
        return Region(kind="ref_block", mode=mode,
                      start=interior_end, end=interior_end,
                      interior=text[interior_start:interior_end])
    if mode == "prepend":
        return Region(kind="ref_block", mode=mode,
                      start=interior_start, end=interior_start,
                      interior=text[interior_start:interior_end])
    return Region(kind="ref_block", mode=mode,
                  start=interior_start, end=interior_end,
                  interior=text[interior_start:interior_end])
```

The region object now accurately describes the single insertion point rather than the full span. The overlap guard, applier, and verifier all see a zero-width region and treat it correctly with no further changes.

**Trade-off:** `region.interior` still holds the full block content (needed by `_segment` in `verifier.py` for the re-derivation step). The `start`/`end` fields diverge from the `interior` length, which may be surprising. Requires a comment explaining the intentional shape.

### Fix C — Structural locator for `tasks-append`

Change `registry.yaml` to use a `structural` locator targeting the line immediately before `<!-- /ref:deferred -->` with `position: before`, instead of a `ref_block` locator. Structural locators return zero-width regions (`start == end`), so they never span any interior content and cannot overlap with checklist regions.

```yaml
tasks-append:
  file: .claude/tasks.md
  locator:
    type: structural
    pattern: '^<!-- /ref:deferred -->$'
    occurrence: 1
    position: before
  write_mode: prepend    # insert before the close marker = append to the block
```

**Trade-off:** Loses the semantic clarity of "append to the deferred block." The close-marker pattern is a physical coupling that would need updating if the block is renamed or moved. Also inverts the write_mode semantics (must use `prepend` to achieve logical `append`).

---

## Recommendation

**Fix A** is the cleanest because it corrects the conceptual error at its source: the overlap guard makes a wrong assumption about what `append` writes. The fix is narrow (one helper function, no schema or locator changes), the existing "expected == modified" check backstops any case the simplified guard misses, and the intent is self-documenting.

Fix B is equally correct but puts mildly surprising data in the `Region` object (interior length doesn't match `end - start`). Fix C works but is fragile and semantically confusing.

---

## Reproduction Steps

1. In `tasks.md`, ensure at least one `- [ ] (T-NN)` task exists inside `<!-- ref:deferred -->`.
2. Author a payload with:
   - `checkoffs: [T-NN]` (any task ID inside `ref:deferred`)
   - `## role: tasks-append` block with at least one new task line
3. Run `run-handoff.sh --dry-run --payload <file>`
4. Observe: `dry-run FAILED: dry-run: verify failed: Overlapping edit regions detected`

The bug triggers whenever any task being checked off currently lives in the same `ref:deferred` block that `tasks-append` writes to — which is the normal state of the deferred backlog.

---

## Files Referenced

| File | Relevant lines |
|---|---|
| `verifier.py` | 28–32 (overlap guard), 11–22 (`_segment` — shows append never uses `start`) |
| `locator.py` | 33–56 (`_locate_ref_block`), 109–134 (`_locate_checklist`) |
| `applier.py` | 45–47 (`_apply_append` — only reads `region.end`) |
| `orchestrator.py` | 139–164 (`_collect_edits` — where both roles are gathered into the same file group) |
| `registry.yaml` | `tasks-append` entry (ref_block/deferred/append), `tasks-checkoff` entry (checklist/checkoff) |
