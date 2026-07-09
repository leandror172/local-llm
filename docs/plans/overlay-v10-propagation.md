# Overlay v10 propagation — session-tracking `customizable:` resume.sh (T-61)

**Status:** follow-up, not started. Run in a dedicated session.
**Scope:** propagate session-tracking **v10** (the `customizable:` resume.sh region) to the four
consumer repos. **v10 changed only:** `manifest.yaml` (version bump + `customizable:` block + resume.sh
moved out of `files:`), `files/resume.sh` (added `overlay-keep:reading-guide` markers), and the
installer library (`lib/actions.py` `handle_customizable` + `verify_overlay` ext). **No handoff-engine
`.py` changed** — the shared `~/.claude/tools/handoff/` stays as-is; no engine re-push needed.

Consumers: `expenses/code`, `web-research`, `career-search`, `latent-topic-graph`.
The installer runs from the **llm repo's** `overlays/` (consumers hold no copy of `install-overlay.py`),
so running it against each target automatically uses the v10 logic.

---

## ⚠️ The one hazard that must be handled first — career-search

career-search's installed `resume.sh` carries a **deliberate §2b variant** ("What to read first" title +
a lighter output filter) — this is the exhibit that motivated T-61. But that variant **predates the
`overlay-keep:reading-guide` markers**, so the installed file has **no markers**.

A naive v10 install therefore hits **decision 3** (marker absent in installed → *reset region to overlay
default + WARN*) and **clobbers the career-search variant** — the exact failure T-61 exists to prevent.

**Required pre-step for career-search (and any repo whose §2b differs from the overlay default):**
before installing v10, hand-place the markers around the existing variant in the *installed* file:

```
# 2b. Pre-session reading guide ...
# overlay-keep:reading-guide
   <career-search's existing "What to read first" title + lighter filter, UNCHANGED>
# /overlay-keep:reading-guide
echo ""
```

Then the v10 install sees the markers → **preserves** the variant (region present) and updates the rest of
`resume.sh` from the overlay. Verify afterward that the region still holds the career-search title.

> Rule of thumb: for each repo, if its §2b already matches the overlay default, no pre-step is needed
> (the install just adds the markers). If its §2b is customized, pre-wrap it in markers first, or the
> install resets it to default.

---

## Per-repo procedure (repeat for each of the 4)

1. **Inspect** the installed `.claude/tools/resume.sh` §2b against the overlay default:
   `diff <(sed -n '/2b\./,/# 3\./p' <repo>/.claude/tools/resume.sh) <(sed -n '/2b\./,/# 3\./p' overlays/session-tracking/files/resume.sh)`
   - If **identical** → no pre-step.
   - If **customized** → pre-wrap the installed variant in `overlay-keep:reading-guide` markers (above).
2. **`--verify` (before)** — record current drift:
   `python3 overlays/install-overlay.py session-tracking --target <repo> --verify`
   Expect resume.sh to show `MISSING`/`DIFF` for the customizable entry (markers not installed yet); this
   is the pre-install baseline, not a failure.
3. **`--dry-run`** — preview:
   `python3 overlays/install-overlay.py session-tracking --target <repo> --dry-run`
   Confirm resume.sh reports `UPDATE` (or `COPY` if fresh) with `regions preserved: ['reading-guide']`, and
   that **no `WARN` (reset) appears** for a repo you pre-wrapped. A `WARN` on a customized repo = the
   pre-step was missed → STOP.
4. **Install** with backup:
   `python3 overlays/install-overlay.py session-tracking --target <repo> --backup`
5. **Diff-review** the resume.sh change: region content unchanged (the repo's), everything else now matches
   the overlay; `.bak` present.
6. **`--verify` (after)** — customizable entry should be `CUSTOMIZED` (customized repos) or `SAME`
   (default repos); exit 0. Any `DIFF` = unmanaged out-of-region drift to investigate.
7. **Commit** in that repo (its own branch/cadence).

---

## Things to watch out for

- **CLAUDE.md version bump (all repos):** v9→v10 flips the `<!-- overlay:session-tracking v9 -->` marker,
  so `merge_sections` will `UPDATE` the CLAUDE.md session-rules section in every repo even though its text
  is unchanged. Expected; just confirm the section content still reads correctly after the bump.
- **`--verify` timing:** a customized region is non-gating (`CUSTOMIZED`), but a repo that hasn't installed
  v10 yet shows the customizable entry as `MISSING`/`DIFF` (no markers). Run the gating `--verify` **after**
  install, not before, if wiring into CI.
- **Decision-3 silent clobber:** the single biggest risk (see career-search above). The `--dry-run` `WARN`
  line is the tripwire — never install a customized repo that shows a reset `WARN`.
- **Only §2b is the seam:** if a repo diverged from the overlay in `resume.sh` *outside* §2b, v10 will
  overwrite that too (by design — only keep-regions are repo-owned). Step-1 diff surfaces this; decide
  per case whether that out-of-region divergence should have been a keep-region (widen the manifest) or is
  stale (let it be overwritten).
- **Engine untouched:** do not re-push `~/.claude/tools/handoff/` for v10 — nothing there changed. The
  `always_user_files` entries will just `SKIP`.
- **CRLF:** the handler preserves the installed file's line endings; not expected on these Linux/WSL repos
  but noted.

---

## Acceptance to confirm in-repo (mirrors `ref:overlay-customizable-acceptance`)

For at least career-search (the customized case) after install:
- ACCEPT-1: region content == career-search variant (preserved) AND out-of-region == overlay v10 (updated).
- ACCEPT-7: `--verify` → `CUSTOMIZED`, exit 0.
- Idempotency: a second install → `SKIP`, byte-stable.

For a default-case repo (e.g. expenses): region == overlay default, `--verify` → `SAME`.
