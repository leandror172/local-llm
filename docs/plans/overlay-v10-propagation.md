# Overlay v10 propagation — session-tracking `customizable:` resume.sh (T-61)

**Status:** ✅ **DONE (session 110, 2026-07-08).** All four consumer repos installed + verified.
This doc is now an executed record; the "As planned vs as executed" section below is the part
worth reading, because the plan's central safety rule turned out to be wrong.

**Scope:** propagate session-tracking **v10** (the `customizable:` resume.sh region) to the four
consumer repos. **v10 changed only:** `manifest.yaml` (version bump + `customizable:` block + resume.sh
moved out of `files:`), `files/resume.sh` (added `overlay-keep:reading-guide` markers), and the
installer library (`lib/actions.py` `handle_customizable` + `verify_overlay` ext). **No handoff-engine
`.py` changed** — the shared `~/.claude/tools/handoff/` stays as-is; no engine re-push needed.
(Confirmed at execution: every `always_user_files` entry reported `SKIP — up to date`.)

Consumers: `expenses/code`, `web-research`, `career-search`, `latent-topic-graph`.
The installer runs from the **llm repo's** `overlays/` (consumers hold no copy of `install-overlay.py`),
so running it against each target automatically uses the v10 logic.

---

<!-- ref:overlay-v10-warn-tripwire -->
## ⚠️ Correction — the `--dry-run` WARN tripwire does NOT discriminate

The original plan said: *"A `WARN` on a customized repo = the pre-step was missed → STOP."*
**This rule is unusable as written.** At execution, **no consumer repo had markers yet** (none had ever
had a v10 install), so decision-3 fired in *all four*. The dry-run output for career-search — where the
reset **destroys** its deliberate variant — was **byte-identical** to the output for expenses — where the
reset is a **content-level no-op**:

```
[WARN]   .claude/tools/resume.sh — keep-region 'reading-guide' marker absent in installed — reset to overlay default
[UPDATE] .claude/tools/resume.sh — regions preserved: []
```

Following the rule literally means stopping on every repo; rationalizing past it means clobbering the one
repo that mattered. **The `WARN` says a reset will happen. It does not say whether the reset changes
anything.**

**The real discriminator is the step-1 §2b diff**, which must be run per repo *before* any install.
The `WARN` is a reminder to go look, never a verdict.

**Follow-up (T-80):** make `--dry-run` report whether a reset actually *changes* the region content —
i.e. compare the installed interior against the overlay default and emit a distinct, loud line
(`WARN-CLOBBER`) only when they differ. That would make the tripwire real.
<!-- /ref:overlay-v10-warn-tripwire -->

---

## Three repo classes, not two

The plan anticipated two cases (§2b matches default / §2b customized). Execution found **three**:

| Repo | §2b state at install | Handling | `--verify` after |
|------|----------------------|----------|------------------|
| `expenses/code` | matches overlay default | reset = no-op; markers added | `SAME` |
| `web-research` | matches overlay default | reset = no-op; markers added | `SAME` |
| `latent-topic-graph` | **no §2b block at all** | whole block seeded fresh (+18 lines, 0 deletions) | `SAME` |
| `career-search` | **customized** ("What to read first" + lighter filter) | pre-wrapped in markers, then installed | `CUSTOMIZED` |

`latent-topic-graph`'s `resume.sh` predates the session-76 reading guide, so it had no §2b at all — a
class the plan never considered. Reset there was *desirable*, not a hazard.

Only **career-search** required the pre-step.

---

## Per-repo procedure (as actually executed)

1. **Inspect §2b** in the installed `.claude/tools/resume.sh` against the overlay default. The two things
   that vary are the `echo "── …"` title line and the `GUIDE=` filter chain:
   `grep -n -A5 'reading guide\|What to read' <repo>/.claude/tools/resume.sh`
   - **identical** → no pre-step (install just adds markers).
   - **customized** → pre-wrap the installed variant in `overlay-keep:reading-guide` markers.
   - **absent** → no pre-step; the block is seeded from the overlay.
2. **Pre-wrap (customized repos only)** — hand-place markers around the existing variant so decision-3
   sees a region and preserves it:
   ```
   # 2b. …                              <- overlay-owned comment (outside region)
   # overlay-keep:reading-guide
   echo "── What to read first (ref:session-reading-guide) ──"
   GUIDE=$(… repo's own filter …)
   if [ -n "$GUIDE" ]; then … fi
   # /overlay-keep:reading-guide
   echo ""
   ```
3. **`--dry-run`** — a pre-wrapped repo must now report
   `regions preserved: ['reading-guide']` **and no `WARN`**. A still-`WARN`ing customized repo = pre-step
   missed → STOP. (For default/absent repos the `WARN` is expected and benign — see the correction above.)
4. **Install** with backup: `python3 overlays/install-overlay.py session-tracking --target <repo> --backup`
5. **Diff-review the FULL file**, not just §2b: `diff <repo>/.claude/tools/resume.sh.bak <repo>/.claude/tools/resume.sh`
   Out-of-region hunks are overwritten by design — confirm none of them were local tweaks worth keeping.
6. **Run it**: `<repo>/.claude/tools/resume.sh` must exit 0, and a customized repo must still print its own
   title. Installer output alone does not prove the script works.
7. **`--verify` (after)** — `CUSTOMIZED` (customized) or `SAME` (default); exit 0.
8. **Commit** in that repo.

---

## Things to watch out for

- **The `WARN` tripwire is not a verdict** — see the correction section above. This was the plan's one
  genuinely dangerous instruction.
- **Diff the whole file, not just the region.** career-search was the only repo where a keep-region was
  preserved, and therefore the only one where out-of-region loss was possible. (It turned out clean: the
  sole out-of-region changes were two *comment* lines.)
- **CLAUDE.md version bump:** the `merge_sections` marker is **authoritative and rewritten on every
  install** (`found_version == overlay_version → SKIP`, else rewrite + `UPDATE vN → vM`). At execution the
  consumers read **v6/v6/v6/v8**, not the v9 the session-108 notes implied. The marker was *correct*; the
  note overclaimed — session 108 synced the **user-level shared engine** (`~/.claude/tools/handoff/`, one
  copy for all repos), which is not a per-repo install. **Trust the marker over the session note.**
  The bump itself is marker-only: section body was byte-identical in every repo.
- **Region boundary is one line too low.** The `# 2b.` section comment sits *outside* the keep-region, so
  career-search now has an overlay-owned comment reading "Pre-session reading guide" directly above
  repo-owned code echoing "What to read first". Cosmetic, but the comment should move inside the region
  (folded into T-80).
- **`registry.yaml` `[TODO]` is not v10 fallout.** v10 never touched `registry.yaml` (verified against the
  PR). The `manual_if_exists` handler flags it unconditionally — even in `latent-topic-graph`, where the
  file is byte-identical to source. That's the T-54 gap, not a propagation problem.
- **`--verify` timing:** a repo that hasn't installed v10 shows the customizable entry as `MISSING`/`DIFF`
  (no markers). Run the gating `--verify` **after** install, not before, if wiring into CI.
- **Engine untouched:** do not re-push `~/.claude/tools/handoff/` for v10 — nothing there changed.
- **CRLF:** the handler preserves the installed file's line endings; not exercised (all repos LF).

---

## Acceptance — confirmed at execution

career-search (the customized case):
- ✅ ACCEPT-1: region == career-search variant (preserved) AND out-of-region == overlay v10 (updated).
- ✅ ACCEPT-7: `--verify` → `CUSTOMIZED`, exit 0.
- ✅ Idempotency: second install → `SKIP`, byte-stable.
- ✅ End-to-end: `resume.sh` exits 0 and still prints `── What to read first`.

Default-case repos (`expenses`, `web-research`): region == overlay default, `--verify` → `SAME`;
full `.bak` diff shows marker/comment lines only, **zero executable change**.

Absent-case repo (`latent-topic-graph`): §2b seeded, `--verify` → `SAME`, `resume.sh` exits 0.

All four: CLAUDE.md at `v10`.
