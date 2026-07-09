# Session Log

**Current Layer:** "Layer 5 — Expense Classifier"
**Current Session:** 2026-07-08 — Session 109: T-61 general customization seam built — customizable: keep-regions + PR #70; session-tracking memory split

---
## 2026-07-08 - Session 109: T-61 general customization seam built — customizable: keep-regions + PR #70; session-tracking memory split

### Context

Continued the overlay/handoff tooling thread. User picked Option B — build T-61's remaining general customization seam — after a long design discussion that reshaped the approach twice.

### What Was Done

- Froze the design in `docs/plans/overlay-customizable-regions.md` (ownership rule, decisions 1–4, splice algorithm, 21-case TDD matrix, `ref:overlay-customizable-acceptance` 8-case algorithmic acceptance spec).
- Built the `customizable:` installer category: `_extract_regions`/`_splice_regions` + `handle_customizable` + `verify_overlay` extension in `overlays/lib/actions.py`; wired into `install-overlay.py` before `handle_files`. 21 tests; installer suite 13→34; full overlay suite 221 green.
- Moved `resume.sh` `files:`→`customizable:` with an `overlay-keep:reading-guide` region; manifest v9→v10. Live acceptance PASS on a tmp career-search-like copy (region preserved + out-of-region updated + CUSTOMIZED non-gating verify + idempotent).
- Split the handoff-pipeline history into its own `overlays/session-tracking/.memories/`; slimmed `overlays/.memories/` to overlay-SYSTEM scope; documented the customizable category in KNOWLEDGE + README.
- Wrote `docs/plans/overlay-v10-propagation.md` (T-79 follow-up). Opened **PR #70**.

### Decisions Made

- Keep-region markers are **plain comments, NOT `ref:KEY`**: both `ref-lookup.sh` and LTG `anchors.py` are `*.md`-only (`anchors.py:138`), so a `.sh` marker is LTG-inert — a `ref:` marker there would look resolvable yet resolve nowhere; no per-region version (overlay never rewrites a region).
- Ownership rule: outside regions overlay-owned; inside repo-owned (shipped default = first-install seed only). Inverse of `merge_sections`.
- session-tracking earned its own `.memories/` (the handoff pipeline was bloating the shared overlay memory).
- Ollama stalled mid-session (loaded-but-unresponsive; 4 timeouts, zero quality rejections) → implementation written directly as an infra-blocked fallback, not a `0` verdict; user restarted ollama afterward.

### Next

- **T-79** — propagate session-tracking v10 to the 4 consumer repos. **career-search hazard:** its §2b variant lacks `overlay-keep` markers, so a naive install hits decision-3 reset and clobbers it — pre-wrap the variant first. Full procedure + watch-outs: `docs/plans/overlay-v10-propagation.md`.
- PR #70 review/merge. Then LTG Phase 6 MCP (L-01) continues in the sibling `latent-topic-graph` repo.

### Gotchas

- The `customizable:` decision-3 (marker absent → reset to default) silently clobbers a customized-but-unmarked file — the `--dry-run` reset-`WARN` line is the tripwire; never install a customized repo showing it.
- Ollama can report a model loaded (`/api/ps` shows VRAM) yet be unresponsive to even a trivial prompt — a wedged server, fixed only by restart (needs sudo/user).
