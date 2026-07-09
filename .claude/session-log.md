# Session Log

**Current Layer:** Layer 5 — Expense Classifier
**Current Session:** 2026-07-08 — Session 110: T-79 — overlay v10 propagated to all 4 consumer repos; dry-run WARN tripwire found non-discriminating

---
## 2026-07-08 - Session 110: T-79 — overlay v10 propagated to all 4 consumer repos; dry-run WARN tripwire found non-discriminating

### Context

Follow-on to session 109: PR #70 merged, master updated, and the remaining half of T-61 was deployment. Session goal was T-79 — install session-tracking v10 (the `customizable:` resume.sh keep-region) into expenses/code, web-research, career-search and latent-topic-graph, following `docs/plans/overlay-v10-propagation.md`.

### What Was Done

- T-79 DONE: v10 installed + verified in all four consumer repos; each committed on master. `--verify` exit 0 everywhere: expenses/web-research/latent-topic-graph `SAME`, career-search `CUSTOMIZED`. CLAUDE.md marker now v10 in all four. Second install → `SKIP` (idempotent).
- career-search's "What to read first" §2b variant preserved: hand-wrapped in `overlay-keep:reading-guide` markers BEFORE install, so decision-3 saw a region and kept it. Verified end-to-end — the committed blob and the live `resume.sh` output both still print the variant title.
- Full `.bak` diff audited per repo (not just §2b): expenses + web-research changed by marker/comment lines only, zero executable change; career-search's only out-of-region changes were two overlay-owned comment lines; latent-topic-graph gained 18 lines, no deletions.
- Ran `resume.sh` in all four repos (exit 0) — installer output alone does not prove the script works.
- Rewrote `docs/plans/overlay-v10-propagation.md` as an executed record carrying both plan corrections (`ref:overlay-v10-warn-tripwire`); filed T-80.
- Deleted the six `.bak` files the installs created; pre-existing backups (notably LTG's `index.bak`) left alone.

### Decisions Made

- The plan's `--dry-run` reset-`WARN` tripwire is NOT usable as a safety gate, and the plan was corrected to say so. No consumer repo had markers yet, so decision-3 fired on all four and emitted byte-identical output for the benign reset (expenses: interior already equals the overlay default) and the destructive one (career-search: interior is a deliberate variant). The rule "a WARN on a customized repo means you missed the pre-step" fires everywhere and discriminates nothing. **The step-1 §2b diff is the only real discriminator** — the WARN is a prompt to go look, never a verdict. Filed as T-80 to make the installer emit a distinct loud line only when the reset would actually change content.
- Three repo classes, not the plan's two: `latent-topic-graph` had **no §2b block at all** (its `resume.sh` predates the session-76 reading guide), so the block was seeded fresh rather than reset. Reset was desirable there, not a hazard.
- The CLAUDE.md `merge_sections` version marker is **authoritative** — `handle_merge_sections` does `found_version == overlay_version → SKIP`, else rewrites the marker and records `UPDATE vN → vM`. The consumers read v6/v6/v6/v8, so session 108's "cross-repo v9 synced + merged" note overclaimed: it synced the **user-level shared engine** at `~/.claude/tools/handoff/` (one copy serving all repos, which is why every `always_user_files` entry reported `SKIP — up to date` today), which is not a per-repo install. Trust the marker over the session note. Initially recorded the inverse ("marker lags reality") and corrected it after checking the code.
- Did not commit T-79's checkoff or T-80's line through the handoff pipeline — both were applied by hand and committed before invoking the skill, so this payload carries no `checkoffs` / `tasks-append`.

### Next

- **T-80** — make the `customizable:` reset warning discriminate (`WARN-CLOBBER` only when the installed region interior differs from the overlay default), and move the `# 2b.` section comment inside the keep-region. (b) changes the region interior → bump to v11 and re-propagate; sequence both into one release.
- LTG Phase 6 MCP server (L-01) continues in the sibling `latent-topic-graph` repo.
- Side options: T-56 (add-task CLI), classifier benchmark (M-P1b/P2), persona hygiene (T-27/T-49).

### Gotchas

- A `customizable:` install into a repo that has never seen the markers ALWAYS warns "reset to overlay default", whether or not the reset destroys anything. Never treat that line as a safety signal — diff the region against the overlay default yourself first.
- `rtk git log --oneline -3` omitted the HEAD merge commit that plain `git log` shows; RTK's git-log filter appears to drop merge commits. Do not use it to confirm a PR landed.
- The `# 2b.` section comment sits OUTSIDE the keep-region, so career-search now has an overlay-owned comment reading "Pre-session reading guide" directly above repo-owned code echoing "What to read first". Cosmetic; folded into T-80.
- `manual_if_exists` flags `registry.yaml` as a `[TODO]` manual merge even in latent-topic-graph, where the file is byte-identical to source. Unconditional flagging — that is the T-54 gap, not v10 fallout.
