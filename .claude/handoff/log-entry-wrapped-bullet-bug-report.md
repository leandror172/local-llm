# Bug report — handoff pipeline: wrapped log-entry bullets shredded into one bullet per line

**Surfaced:** 2026-07-06, latent-topic-graph repo, session 2 — the repo's FIRST live
handoff run (stage `session-2-20260706-171717`, promoted as llm-overlay consumer).
**Severity:** content preserved, formatting corrupted — the committed session-log
entry is readable but every wrapped bullet is broken into fragment-bullets.
**Reporter:** LTG session 2 close-out (cross-repo; fix belongs here, the overlay home).

## Symptom

A payload slot bullet authored as a wrapped (multi-line) markdown bullet:

```
### what_was_done
- SP-14 / L-05 executed end-to-end (commit 094087a): Steps A–C mined the llm
  instance index (10 semantic queries + 145-seed structural pass → 49 merged
  candidates); ...
```

renders in the promoted `session-log.md` as one bullet **per physical line**:

```
- SP-14 / L-05 executed end-to-end (commit 094087a): Steps A–C mined the llm
- instance index (10 semantic queries + 145-seed structural pass → 49 merged
- candidates); ...
```

Live exhibit: latent-topic-graph `.claude/session-log.md`, session-2 entry
(commit `1628870` in that repo) — left unfixed as the bug's exhibit.

## Root cause

`payload.py::_parse_bullets` (line ~226) treats EVERY non-empty physical line as a
standalone item:

```python
for line in _strip_lines(list(lines_list)):
    stripped = line.strip()
    if stripped.startswith("- "):
        result.append(stripped[2:])
    elif stripped:
        result.append(stripped)      # <-- continuation lines land here
```

A wrapped bullet's continuation lines (indented, no `- ` prefix) fall into the
`elif` branch and become separate items. `mechanics.py::_bullet_section`
(line ~32) then correctly renders one `- ` per item — the renderer is innocent;
the item list it receives is already shredded.

Neither the payload validator nor the F4 verifier can catch this: the corruption
is semantic and entirely INSIDE the registered log-entry region, where the
verifier deliberately does not look.

## Recommended fix (Fix A — parser continuation-join)

In `_parse_bullets`, treat a non-`- ` line as a continuation of the previous
item when one exists (join with a single space); only start a new item from an
unprefixed line when `result` is empty:

```python
elif stripped:
    if result:
        result[-1] += " " + stripped
    else:
        result.append(stripped)
```

One function, no schema change. Preserves current behavior for single-line
bullets and for prefix-less single-line slots; changes multi-line prefix-less
input from N items to 1 item (arguably the correct reading). Add tests to
`test_payload.py` (wrapped bullet → single item; mixed wrapped + single-line;
prefix-less multi-line).

## Alternatives considered

- **Fix B (validate + reject wrapped input):** unreliable — a continuation line
  is syntactically indistinguishable from an intentional unprefixed bullet.
- **Fix C (skill-doc rule only, "author single-line bullets"):** already deployed
  as an authoring memory in the LTG repo, but leaves the trap armed for every
  other consumer repo; keep as interim guidance, not the fix.

## Propagation note

After fixing the overlay source (`overlays/session-tracking/files/handoff/payload.py`),
propagate to the installed engine (`~/.claude/tools/handoff/`) and re-verify with
the T-58 `--verify` mode — the T-57/T-58 history shows a fixed-in-source /
stale-installed drift is the likely failure mode here too.
