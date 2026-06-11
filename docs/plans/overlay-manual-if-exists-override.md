# Overlay installer — opt-in override for `manual_if_exists` (T-54)

**Status:** deferred / not built. Reference spec for a future session.
**Subsystem:** overlay installer (`overlays/lib/actions.py`, `overlays/install-overlay.py`).
**Surfaced:** session 86, designing Option-C register delivery for the session-handoff overlay.

## Goal

Today `manual_if_exists` only ever **flags** an already-present file
(`[TODO] manual merge required`) and never overwrites — the safe default for a load-bearing,
per-repo artifact (e.g. `.claude/handoff/registry.yaml`). Add a first-class, opt-in way to push
the canonical version through **with a backup**, for when a repo genuinely wants to re-sync.

## Current behavior (the code to change)

`overlays/lib/actions.py` → `handle_manual_if_exists(manifest, overlay_dir, target_root, dry_run)`
(≈ line 233):
```python
files_dir = overlay_dir / "files"
for dest_rel in manifest.get("manual_if_exists", []):
    dest = target_root / dest_rel
    src  = files_dir / Path(dest_rel).name
    if dest.exists():
        record("TODO", dest_rel, "manual merge required — file already exists", ...)
    else:
        shutil.copy2(src, dest); dest.chmod(... | 0o755); record("COPY", ...)
```
Wired in `overlays/install-overlay.py` ≈ line 112:
```python
handle_manual_if_exists(manifest, overlay_dir, target_root, args.dry_run)
```

## Code changes

- **`handle_manual_if_exists(...)`** — add `force: bool = False`. In the `dest.exists()` branch:
  - if `force` and bytes differ → route through the **existing** `_copy_file(src, dest, dest_rel,
    executable=_is_executable_payload(src), do_backup=True, dry_run=dry_run)` (same backup-if-differs
    helper `handle_files` uses) and `record("OVERWRITE", dest_rel, "forced — backup made")`.
  - if `force` and bytes identical → `record("SKIP", dest_rel, "already up to date")` (idempotent).
  - if not `force` → today's `TODO` behavior, unchanged.

- **`install-overlay.py`** — add `--force-manual` (store_true; start global, per-path
  `--force-manual <path>` is a future refinement) and pass it:
  `handle_manual_if_exists(manifest, overlay_dir, target_root, args.dry_run, force=args.force_manual)`.

- **Docs** — note the flag in the overlay README(s) that use `manual_if_exists`
  (`overlays/session-tracking/README.md` register row).

## Why reuse `_copy_file`
It already implements backup-if-differs + dry-run + executable-bit handling. Forcing through it
keeps one backup code path and stays consistent with `files:` installs. Do **not** hand-roll a
second backup mechanism.

## Acceptance
- Fresh target: first install `COPY`s the file (unchanged behavior).
- Second install, no flag: `[TODO] manual merge required` (unchanged — the safe default).
- Second install, `--force-manual`, file differs: `[OVERWRITE]` + a `.bak` left beside it.
- Second install, `--force-manual`, file identical: `[SKIP]` (idempotent).
- `--dry-run --force-manual` reports the OVERWRITE without writing.
