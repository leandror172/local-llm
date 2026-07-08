# Overlay installer — `customizable:` keep-regions (T-61, option b)

**Status:** FROZEN / not built. Reference spec for the implementing session.
**Subsystem:** overlay installer (`overlays/lib/actions.py`, `overlays/install-overlay.py`, `manifest.yaml`).
**Surfaced:** T-61 — overlay-source `resume.sh` wholesale-overwrites a repo's local customization
(career-search's §2b "What to read first" variant). Session 108 did option (a) — backport the
llm reading-guide so source ⊇ installed. This is option (b): the **general customization seam**.
**Implements:** T-61 remaining half; related T-28(4), T-54 (opposite direction — force-overwrite).

---

## Problem

The installer's five categories offer no way to let the **overlay own a file** while a **repo keeps
a local tweak inside it**:

| Category | Update behavior | Why it fails T-61 |
|----------|-----------------|-------------------|
| `files:` | backup + wholesale overwrite | clobbers the local tweak (the bug) |
| `templates:` | create-only, never touch again | freezes the file — repo stops getting *any* update |
| `manual_if_exists:` | flag every time | nags on every install even for repos that never customized |
| `merge_sections:` | overlay owns one marked section **inside a user file** | inverted ownership |

`resume.sh` legitimately keeps evolving (the reading-guide block is recent), so freezing it (option c)
is wrong; and only a *region* of it is customized, so whole-file opt-out is too coarse.

---

## Frozen design

### The `customizable:` manifest category

```yaml
customizable:
  .claude/tools/resume.sh:
    keep_regions:
      - reading-guide          # sanctioned, by name (the allow-list)
```

`resume.sh` **moves out of `files:` into `customizable:`** — the two are mutually exclusive per path
(the `customizable:` handler owns that dest; `handle_files` must not also process it).

### Marker format (explicit, purpose-built, comment-agnostic)

The overlay **source** file carries the region delimiters:

```sh
# overlay-keep:reading-guide
   ...default content the overlay ships (first-install seed)...
# /overlay-keep:reading-guide
```

- Detection is **comment-syntax-agnostic**: the installer matches the token `overlay-keep:<name>`
  (open) and `/overlay-keep:<name>` (close) anywhere on a line, so the same mechanism works in `.sh`,
  `.py`, `.md`, etc. — the leading comment chars are ignored.
- `<name>` grammar: `[a-z0-9-]+` (mirrors the ref-key grammar for consistency).
- The **marker lines themselves are overlay-owned** (they come from the source skeleton); only the
  content **between** them is repo-owned.

**Why NOT the literal `ref:KEY` format** (considered, rejected): both `ref-lookup.sh` and LTG's
`anchors.py` restrict ref ingestion to `*.md` (`anchors.py:138` git-greps `-- "*.md"`), so a `ref:`
marker in a `.sh` is invisible to both — it would *look* like a resolvable ref yet resolve nowhere,
with zero upside. See the LTG-corpus note below.

### Ownership rule (the core semantic)

> **Outside keep-regions → overlay-owned** (update always takes the new source).
> **Inside a keep-region → repo-owned** (always preserved; the shipped default is a *first-install
> seed only*, never re-applied on update).

Consequence, stated plainly: an overlay **cannot push improvements into a keep-region** after first
install. That is correct — a seam the author keeps editing is not a seam. Content the author needs to
keep updating does not belong in a keep-region.

**No per-region version.** `merge_sections` versions its marker because the overlay *rewrites* that
section on update and must know which version is installed. A keep-region is the opposite — never
rewritten after seeding — so there is nothing to version. Versioning stays at the **manifest/file
level** (the overlay `version:`). (Bonus: a version token would also break the `ref:`-style grammar,
but that is moot since we are not using ref markers.)

### Splice algorithm (`handle_customizable`)

```
for each (dest_rel, spec) in manifest["customizable"]:
    src      = overlay_dir/files/<basename(dest_rel)>
    dest     = target_root/dest_rel
    regions  = spec["keep_regions"]

    src_text, _        = read source (LF-normalized)
    # --- contract validation (decisions 1 & 2) ---
    src_markers  = scan overlay-keep:<name> in src_text
    for name in regions:
        if name not in src_markers:        HARD FAIL  (decision 2: author bug — kind=internal/author)
    for name in src_markers:
        if name not in regions:            ERROR      (decision 1: unsanctioned marker in source)

    if not dest.exists():                  # fresh install
        copy src verbatim (markers + seed content); apply exec mode
        record COPY "seeded"; continue

    inst_text, inst_crlf = read dest (LF-normalized, remember EOL)
    inst_markers = scan overlay-keep:<name> in inst_text
    for name in inst_markers:
        if name not in regions:            ERROR      (decision 1: unsanctioned marker in installed)

    merged = src_text                      # start from new source skeleton (overlay-owned outside)
    for name in regions:
        if name in inst_markers:
            inst_interior = interior(inst_text, name)
            merged = replace_interior(merged, name, inst_interior)   # preserve repo content
        else:
            record WARN "region '<name>' marker absent in installed — reset to overlay default"  # decision 3

    if merged == inst_text:                record SKIP "up to date"
    else:
        if do_backup: backup(dest)
        write merged to dest with inst_crlf EOL; apply exec mode
        record UPDATE "regions preserved: <names customized>"   (+ backup note)
```

- `interior(text, name)` = the lines strictly between the open and close markers for `name`.
- `replace_interior` keeps the source's marker lines, substitutes the interior.
- **EOL**: reuse `_read_text_eol` / `_write_text_eol` (preserve CRLF), same as `merge_sections`.
- **Exec mode**: reuse `_is_executable_payload` / `_apply_mode` (0o755 for scripts).
- **dry-run**: compute everything, write nothing; record intended UPDATE + which regions would be
  preserved vs reset.

### Edge semantics (confirmed 1–4 + verify gating)

1. **Marker present but not in manifest** (source *or* installed) → **ERROR**. Distinct messages by
   whose-fault (source = author bug; installed = repo added an unsanctioned region), following the
   handoff failure-clarity `kind` convention (where / whose-fault / what).
2. **Manifest lists a region, source lacks the marker** → **HARD FAIL** (overlay-author bug).
3. **Repo deleted the marker from its installed file** → **reset to source default + WARN** (the
   manifest is the source of truth for which regions exist).
4. **`--dry-run` / `--backup` / `--verify` all understand regions**; dry-run shows preserved-vs-reset;
   backup fires before any region-preserving write.

**`--verify` per-region reporting** (extends `verify_overlay`):

| Condition | Status | Gates exit? |
|-----------|--------|-------------|
| dest missing | `MISSING` | yes |
| source region marker absent | `SRC-MISSING` | yes |
| installed region marker absent (would reset) | `DIFF` | yes |
| **outside-region content drifted from source** | `DIFF` | **yes** |
| **region interior customized** (marker present, interior differs) | `CUSTOMIZED` | **no** |
| all equal | `SAME` | no |

Rationale for the one sub-decision: a customized region is the *sanctioned* use of the seam, so it must
NOT fail `--verify` (CI); drift **outside** the regions is real unmanaged divergence and gates.

### LTG-corpus note (why the markers are safe)

`.claude/tools/` is in the LTG corpus `include_roots`, so `resume.sh` is topic-extracted. But:

- The **anchor graph is untouched** — `anchors.py` and `ref-lookup.sh` are both `*.md`-only, so a
  marker in a `.sh` reaches neither. No anchor node, no dangling ref.
- The **only** LTG-touching path is the code-arm **topic extractor**, which reads the whole file
  regardless of markers. The cost is therefore ~2 comment lines of marginal, format-independent
  topic noise in one code file — not the prose-tracking-file pollution the handoff register was
  designed to avoid. Acceptable.

---

## Test plan

### A. TDD unit tests — `overlays/test_customizable.py`

Mirrors `test_verify.py` conventions (`_make_overlay` / `_make_target` factories, `report._actions`
recorder, `$HOME` isolation for user-level paths).

| # | Group | Test | Asserts |
|---|-------|------|---------|
| 1 | marker parse | single region | interior extracted |
| 2 | | multiple regions | all parsed, order-independent |
| 3 | | no markers | empty |
| 4 | | unbalanced (open, no close) | raises, clear `kind` message |
| 5 | | duplicate region name | raises (ambiguous) |
| 6 | splice | fresh install (dest missing) | COPY verbatim; seed intact; 0o755 |
| 7 | | dest byte-identical to source | SKIP "up to date" |
| 8 | | region customized, rest identical | interior == installed; outside == source; CUSTOMIZED |
| 9 | | overlay changed OUTSIDE + repo customized INSIDE | new outside **and** kept region — both-halves proof |
| 10 | | overlay changed region default, repo untouched | region stays installed(=old seed) — frozen by design |
| 11 | | marker deleted from installed (#3) | reset to source default + WARN |
| 12 | contract | region listed, marker absent in source (#2) | hard fail, author message |
| 13 | | marker in source not listed (#1) | ERROR (unsanctioned, source) |
| 14 | | marker in installed not listed (#1) | ERROR (unsanctioned, installed) |
| 15 | idempotency | run twice | second run byte-stable / SKIP |
| 16 | EOL | CRLF installed file | merged keeps CRLF |
| 17 | dry-run | `--dry-run` on customized file | no write; records intended UPDATE + preserved regions |
| 18 | backup | update with `do_backup` | `.bak` before write |
| 19 | verify | region default matches | SAME (tally 0) |
| 20 | | region CUSTOMIZED | non-gating CUSTOMIZED (tally 0) |
| 21 | | outside-region drift | DIFF (gates; n_diff=1) |

### B. Live / acceptance test

Run on a **copy in `~/workspaces/tmp`** (not the real career-search repo — that is a separate,
user-approved v10 propagation step):

1. Author the seam: wrap resume.sh §2b (`reading-guide`) with `overlay-keep` markers in the overlay
   source; add the `customizable:` manifest entry; move resume.sh out of `files:`; bump v9→v10.
2. Dry-run vs **llm repo** (its resume.sh IS the canonical default) → region=default/SAME, no clobber.
3. Dry-run vs a **tmp copy of career-search's resume.sh** (its §2b variant + a staged unrelated §5
   overlay change) → `reading-guide = CUSTOMIZED (preserved)` **and** `§5 = UPDATE`. Key acceptance.
4. Real install to the tmp copy → diff: §2b == career-search variant, §5 == new overlay content,
   `.bak` present.
5. `--verify` on the tmp copy → per-region report correct; exit honors gating (customized non-gating,
   outside-drift gating).
6. Idempotency → install twice, second run byte-stable.
7. Full suite → `make -C overlays test` green (196 existing + ~21 new).

<!-- ref:overlay-customizable-acceptance -->
### C. Algorithmic acceptance-test spec (derive an automated harness from this)

Language-agnostic pseudocode precise enough to generate a `test_customizable_acceptance.py` (or a
bash harness) later. Uses only tmp fixtures — hermetic, no repo coupling.

```
CONST OPEN(n)  = "# overlay-keep:" + n
CONST CLOSE(n) = "# /overlay-keep:" + n

# ---- fixture builders -------------------------------------------------------
def source_v2(region="reading-guide"):
    # overlay source AFTER an unrelated out-of-region change (the "§5 update")
    return lines(
        "#!/usr/bin/env bash",
        "echo SECTION_1_UPDATED",            # <- out-of-region overlay change vs v1
        OPEN(region),
        "echo DEFAULT_TITLE",                # <- region seed content
        "GUIDE=$(default_filter)",
        CLOSE(region),
        "echo SECTION_5_UNCHANGED",
    )

def installed_customized(region="reading-guide"):
    # a consumer that customized the region but is still on the OLD out-of-region content
    return lines(
        "#!/usr/bin/env bash",
        "echo SECTION_1_OLD",                # <- old out-of-region (should be UPDATED by overlay)
        OPEN(region),
        "echo CAREER_SEARCH_TITLE",          # <- repo customization (must be PRESERVED)
        "GUIDE=$(lighter_filter)",
        CLOSE(region),
        "echo SECTION_5_UNCHANGED",
    )

# ---- ACCEPT-1: preserve-region-while-updating-outside (the T-61 thesis) -----
setup:   src=source_v2();  dest=installed_customized()
action:  merged = handle_customizable(src, dest, keep_regions=[region])
assert:  interior(merged, region) == interior(dest, region)          # repo tweak kept
assert:  "SECTION_1_UPDATED" in merged                               # overlay update applied
assert:  "SECTION_1_OLD" not in merged
assert:  marker lines OPEN/CLOSE still present, exactly once each
assert:  file mode == 0o755

# ---- ACCEPT-2: fresh install seeds verbatim --------------------------------
setup:   src=source_v2();  dest=<absent>
action:  merged = handle_customizable(src, dest, keep_regions=[region])
assert:  merged == src                                               # seed, byte-for-byte
assert:  interior(merged, region) == interior(src, region)

# ---- ACCEPT-3: idempotency --------------------------------------------------
setup:   src=source_v2();  dest=installed_customized()
action:  m1 = install(); m2 = install()                             # twice
assert:  m1 == m2                                                    # byte-stable
assert:  second run records SKIP "up to date"

# ---- ACCEPT-4: reset-on-missing-marker (decision 3) ------------------------
setup:   src=source_v2();  dest=installed_customized() WITH region markers deleted
action:  merged = handle_customizable(...)
assert:  interior(merged, region) == interior(src, region)          # reset to seed
assert:  a WARN "reset to overlay default" was recorded

# ---- ACCEPT-5: unsanctioned marker gates (decision 1) ----------------------
setup:   dest has OPEN("rogue")/CLOSE("rogue") not in keep_regions
action:  run
assert:  ERROR raised/recorded naming "rogue" + the file (whose-fault=repo)

# ---- ACCEPT-6: author bug — listed region missing in source (decision 2) ----
setup:   keep_regions=["ghost"] but source has no OPEN("ghost")
action:  run
assert:  HARD FAIL naming "ghost" (whose-fault=author)

# ---- ACCEPT-7: --verify gating ---------------------------------------------
setup A: dest == expected merged (region customized, outside matches source)
assert:  region -> CUSTOMIZED, tally == (0,0,0), exit 0            # sanctioned, non-gating
setup B: dest has out-of-region drift ("SECTION_5_HACKED")
assert:  -> DIFF, n_diff >= 1, exit 1                              # unmanaged drift gates

# ---- ACCEPT-8: CRLF preserved ----------------------------------------------
setup:   dest written with CRLF endings, region customized
action:  install
assert:  merged bytes contain \r\n; region tweak preserved
```

**Invariants any derived harness must keep:** hermetic (build fixtures in a tmp dir; never read the
real repo); assert on `report._actions` statuses AND on merged bytes; cover both the pure splice and
the on-disk write (mode + EOL). The 8 ACCEPT cases map 1:1 onto acceptance-test functions.
<!-- /ref:overlay-customizable-acceptance -->

---

## Build sequence (implementing session)

1. `_extract_regions(text) -> {name: interior}` + marker scan + balance/duplicate checks (tests 1–5).
2. `handle_customizable(manifest, overlay_dir, target_root, dry_run, do_backup)` — splice algorithm,
   contract validation, EOL/mode/idempotency (tests 6–18).
3. Extend `verify_overlay` with the `customizable:` section (tests 19–21).
4. Wire into `install-overlay.py` main() sequence (before `handle_files`; ensure no path is in both
   categories) + `--verify` branch.
5. Author the resume.sh seam + manifest entry + v9→v10 bump; run acceptance A–B; `make -C overlays test`.
6. Propagate v10 to consumer repos (expenses / web-research / career-search / latent-topic-graph) on
   the user's cadence, `--verify` dry-run first — **out of the build session**.

## Deferred / noted

- **Shared region-locator primitive:** "locate a region in a file" is now wanted by two products
  (handoff register's structural locator + this seam). Per the topology rule (products depend on
  primitives, never product↔product), a future layer-0 `region-locator` primitive could back both.
  Noted, not built — extract only when a third consumer appears (same discipline as T-76).
