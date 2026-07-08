## 2026-07-06 - Session 108: Handoff-tooling bug sweep — T-78/T-62/T-61 fixed (overlay v9), cross-repo synced + merged

### Context

Continued from the T-33 split close-out: confirmed PR #69 (LTG repo split) merged, then took on the three open handoff-tooling bugs (T-78/T-62/T-61) the split's first live handoff surfaced, delegating T-78 to a subagent.

### What Was Done

- Confirmed PR #69 (T-33 LTG repo split) merged; local master already carried the merged split commits.
- T-78 (subagent): `payload.py::_parse_bullets` continuation-join so a wrapped log-entry bullet stays one item instead of shredding per physical line; +4 tests in `test_payload.py`.
- T-62: `run-handoff.sh` shim now honors an explicit `--registry` (bypasses the registry-file guard) and prefers a co-located `handoff.py` over the user-level install — home repo runs source, target repos keep the shared engine.
- T-61: backported `resume.sh` §2b (pre-session reading guide) into the overlay source so source ⊇ installed; a reinstall no longer clobbers it.
- Propagated engine + shim to `~/.claude/tools/handoff/`; installer `--verify` reports all 15 code files SAME; overlay bumped v8→v9; 178 session-tracking tests green.
- Cross-repo v9 sync: expenses/code + web-research got `resume.sh` + shim; career-search got the shim only (its "What to read first" `resume.sh` variant preserved, T-61 option 2).
- Merged all four branches (fast-forward): llm `fix/handoff-tooling-bugs` → master; expenses sync → `docs/t23-calibration-probe`; web-research + career-search sync → master.
- Updated overlay memories: retired the now-false "shim ignores --registry" gotcha; recorded v9 + the career-search divergence.

### Decisions Made

- T-61 resolved via option (a) backport only; the general per-repo customization seam (b/c) stays open — career-search's deliberate "What to read first" §2b variant is the exhibit, tracked under existing T-28(4) (marked-file install mode) and T-54 (manual_if_exists override).
- Shim design "prefer co-located engine else user-level": home repo tests freshly-edited source automatically; target repos (shim-only, no co-located engine) keep using the shared user-level engine — no flag, purely by what's on disk.
- expenses sync merged into its feature branch t-23 (user call), not isolated onto master; per-repo commits isolated on `chore/session-tracking-overlay-v9` then `--ff-only` merged (provably non-destructive).

### Next

- LTG engine work continues in the sibling `latent-topic-graph` repo — SP-14 already run there; next is Phase 6 MCP server (its L-01).
- llm-side handoff tooling largely closed; remaining is the T-61 general customization-seam (T-28(4)/T-54). Side options: T-56 (add-task CLI), classifier benchmark (M-P1b/P2), persona hygiene (T-27/T-49).
- Nothing pushed — llm master + 3 target-repo branches are local; push on your cadence. Redundant `chore/*` + `fix/*` branches are fully merged (safe to delete).

### Gotchas

- The cross-repo `cp` was auto-denied by the mode classifier (out-of-project destructive write) even with in-conversation approval — the designed path is explicit per-target go-ahead; surfacing the exact write plan first is what enabled the T-61-respecting career-search choice.
- This handoff run is itself the end-to-end verification T-62 asked for — the stage→promote goes through the fixed shim's `--registry` path.
