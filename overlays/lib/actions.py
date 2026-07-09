"""Deterministic action handlers: files, templates, append_lines, merge_sections, manual_if_exists."""

import hashlib
import re
import shutil
from pathlib import Path

from .backends import Backend
from .planner import ai_merge, _backup
from .report import record

# Extensions that should land executable. The overlay repo may live on a WSL
# drvfs mount, where every file reports mode 777 — so the filesystem's executable
# bit is unreliable. Decide by extension instead (empty suffix = likely a script).
_SCRIPT_SUFFIXES = {".sh", ".bash", ".zsh", ".py", ".pl", ".rb"}


def _is_executable_payload(src: Path) -> bool:
    return src.suffix.lower() in _SCRIPT_SUFFIXES or src.suffix == ""


def _apply_mode(dest: Path, executable: bool):
    # copy2 carries the source mode over; on drvfs that is 777. Set an explicit,
    # predictable mode so docs are not left executable.
    dest.chmod(0o755 if executable else 0o644)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _read_text_eol(path: Path) -> tuple[str, bool]:
    # Returns (LF-normalized text, whether the file used CRLF). Lets callers
    # process in LF and write back with the file's original line endings —
    # a read_text/write_text round-trip would otherwise normalize CRLF away.
    raw = path.read_bytes()
    crlf = b"\r\n" in raw
    return raw.decode("utf-8").replace("\r\n", "\n"), crlf


def _write_text_eol(path: Path, content: str, crlf: bool):
    if crlf:
        content = content.replace("\r\n", "\n").replace("\n", "\r\n")
    path.write_text(content, newline="")


# ── customizable keep-regions (T-61) ─────────────────────────────────────────
# A keep-region is delimited by `overlay-keep:<name>` … `/overlay-keep:<name>`
# markers (comment-syntax-agnostic: the token is matched anywhere on a line).
# The close token contains the open token as a substring, so opens use a
# negative lookbehind for '/' and each line is tested for close FIRST.
_KEEP_OPEN = re.compile(r"(?<!/)overlay-keep:([a-z0-9-]+)")
_KEEP_CLOSE = re.compile(r"/overlay-keep:([a-z0-9-]+)")


def _extract_regions(text: str) -> dict[str, str]:
    """Map each `overlay-keep:<name>` region to its interior (text strictly
    between the open/close marker lines; the marker lines are excluded).

    Raises ValueError on an unbalanced marker (open without matching close, or a
    close that does not match the currently-open region) or a duplicate name.
    """
    regions: dict[str, str] = {}
    current: str | None = None
    interior: list[str] = []
    for line in text.splitlines(keepends=True):
        close = _KEEP_CLOSE.search(line)
        opn = _KEEP_OPEN.search(line)
        if close:
            name = close.group(1)
            if current is None or current != name:
                raise ValueError(
                    f"unbalanced overlay-keep: close for '{name}' "
                    f"but open region is {current!r}"
                )
            regions[current] = "".join(interior)
            current, interior = None, []
        elif opn:
            name = opn.group(1)
            if current is not None:
                raise ValueError(
                    f"nested overlay-keep: opened '{name}' inside '{current}'"
                )
            if name in regions:
                raise ValueError(f"duplicate overlay-keep region '{name}'")
            current = name
        elif current is not None:
            interior.append(line)
    if current is not None:
        raise ValueError(f"unclosed overlay-keep region '{current}'")
    return regions


def _splice_regions(source_text: str, replacements: dict[str, str]) -> str:
    """Rebuild `source_text`, substituting each named region's interior with
    `replacements[name]` while keeping the source's own marker lines. Regions
    not in `replacements` (and non-region text) pass through unchanged.
    """
    out: list[str] = []
    skipping = None
    for line in source_text.splitlines(keepends=True):
        close = _KEEP_CLOSE.search(line)
        opn = _KEEP_OPEN.search(line)
        if close:
            skipping = None
            out.append(line)
        elif opn:
            name = opn.group(1)
            out.append(line)
            if name in replacements:
                out.append(replacements[name])
                skipping = name
        elif skipping is None:
            out.append(line)
    return "".join(out)


def _copy_file(src: Path, dest: Path, display: str, executable: bool,
               do_backup: bool, dry_run: bool):
    if not src.exists():
        record("ERROR", display, f"source missing in overlay: {src.name}")
        return

    if not dest.exists():
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            _apply_mode(dest, executable)
        record("COPY", display, "file missing")
    elif sha256(src) == sha256(dest):
        record("SKIP", display, "up to date")
    else:
        if not dry_run:
            if do_backup:
                _backup(dest)
            shutil.copy2(src, dest)
            _apply_mode(dest, executable)
        bak_note = f"backup: {display}.bak" if do_backup else "no backup (use --backup to enable)"
        record("UPDATE", display, "differs from overlay source", bak_note)


def handle_files(manifest: dict, overlay_dir: Path, target_root: Path,
                 dry_run: bool, do_backup: bool):
    files_dir = overlay_dir / "files"
    for src_name, dest_rel in manifest.get("files", {}).items():
        src = files_dir / src_name
        dest = target_root / dest_rel
        _copy_file(src, dest, dest_rel, executable=_is_executable_payload(src),
                   do_backup=do_backup, dry_run=dry_run)


def handle_always_user_files(manifest: dict, overlay_dir: Path,
                             dry_run: bool, do_backup: bool):
    """Install always_user_files to ~/.claude/ unconditionally — no level flag.

    Use for shared runtime files (e.g. pipeline modules) that must live at user
    level regardless of --install-level.  dest_root is always ~/.claude/.
    """
    always_user = manifest.get("always_user_files", {})
    if not always_user:
        return

    files_dir = overlay_dir / "files"
    dest_root = Path.home() / ".claude"

    for src_name, dest_rel in always_user.items():
        src = files_dir / src_name
        dest = dest_root / dest_rel
        _copy_file(src, dest, f"~/.claude/{dest_rel}", executable=_is_executable_payload(src),
                   do_backup=do_backup, dry_run=dry_run)


def handle_user_files(manifest: dict, overlay_dir: Path, install_level: str,
                      target_root: Path, dry_run: bool, do_backup: bool):
    """Install user_files to ~/.claude/ (user level) or .claude/ (project level).

    user_files are things like skills and the run-handoff shim — generic enough
    to live at user level but installable per-repo with --install-level project.
    """
    user_files = manifest.get("user_files", {})
    if not user_files:
        return

    files_dir = overlay_dir / "files"

    if install_level == "user":
        dest_root = Path.home() / ".claude"
        level_label = "~/.claude"
    else:
        dest_root = target_root / ".claude"
        level_label = ".claude"

    for src_name, dest_rel in user_files.items():
        src = files_dir / src_name
        dest = dest_root / dest_rel
        display = f"{level_label}/{dest_rel}"
        _copy_file(src, dest, display, executable=_is_executable_payload(src),
                   do_backup=do_backup, dry_run=dry_run)


def handle_templates(manifest: dict, overlay_dir: Path, target_root: Path, dry_run: bool):
    tmpl_dir = overlay_dir / "templates"
    for tmpl_name, dest_rel in manifest.get("templates", {}).items():
        src = tmpl_dir / tmpl_name
        dest = target_root / dest_rel

        if not src.exists():
            record("ERROR", dest_rel, f"template missing in overlay: {tmpl_name}")
            continue

        if dest.exists():
            record("SKIP", dest_rel, "already exists (user-managed, not overwritten)")
        else:
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
            record("CREATE", dest_rel, "created from template")


def handle_append_lines(manifest: dict, target_root: Path, dry_run: bool):
    for dest_rel, lines in manifest.get("append_lines", {}).items():
        dest = target_root / dest_rel

        if not dest.exists():
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.touch()
            record("CREATE", dest_rel, "file missing — created empty")

        content = dest.read_text() if dest.exists() else ""
        existing_lines = content.splitlines()

        for line in lines:
            if line in existing_lines:
                record("SKIP", dest_rel, f"line already present: {line!r}")
            else:
                if not dry_run:
                    with dest.open("a") as f:
                        if content and not content.endswith("\n"):
                            f.write("\n")
                        f.write(line + "\n")
                    content = dest.read_text()
                record("APPEND", dest_rel, f"added line: {line!r}")


def handle_merge_sections(
    manifest: dict,
    overlay_dir: Path,
    target_root: Path,
    prompts_dir: Path,
    mode: str,
    yes: bool,
    backend_id: str,
    model_override: str | None,
    backends: list[Backend],
    dry_run: bool,
    do_backup: bool,
    debug: bool = False,
):
    overlay_name = manifest["name"]
    overlay_version = manifest["version"]

    for dest_rel, spec in manifest.get("merge_sections", {}).items():
        section_file = overlay_dir / spec["file"]
        dest = target_root / dest_rel
        merge_hint = spec.get("merge_hint", "")

        if not section_file.exists():
            record("ERROR", dest_rel, f"section file missing in overlay: {spec['file']}")
            continue

        section_content = section_file.read_text().rstrip()
        open_marker = f"<!-- overlay:{overlay_name} v{overlay_version} -->"
        close_marker = f"<!-- /overlay:{overlay_name} -->"
        open_pattern = re.compile(
            rf"<!-- overlay:{re.escape(overlay_name)} v(\d+) -->", re.MULTILINE
        )

        if not dest.exists():
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(f"{open_marker}\n{section_content}\n{close_marker}\n")
            record("CREATE", dest_rel, "file missing — created with overlay section only")
            continue

        existing, dest_crlf = _read_text_eol(dest)
        version_match = open_pattern.search(existing)

        if version_match:
            found_version = int(version_match.group(1))
            if found_version == overlay_version:
                record("SKIP", dest_rel, f"already installed v{overlay_version}")
            else:
                new_block = (
                    f"<!-- overlay:{overlay_name} v{overlay_version} -->\n"
                    f"{section_content}\n"
                    f"{close_marker}"
                )
                old_open = f"<!-- overlay:{overlay_name} v{found_version} -->"
                updated = re.sub(
                    rf"{re.escape(old_open)}.*?{re.escape(close_marker)}",
                    new_block, existing, flags=re.DOTALL,
                )
                if not dry_run:
                    if do_backup:
                        _backup(dest)
                    _write_text_eol(dest, updated, dest_crlf)
                bak_note = f"backup: {dest_rel}.bak" if do_backup else "no backup (use --backup to enable)"
                record("UPDATE", dest_rel, f"v{found_version} → v{overlay_version}", bak_note)
        else:
            if mode == "ai":
                ai_merge(
                    dest, existing, section_content, open_marker, close_marker,
                    merge_hint, backend_id, model_override, backends,
                    prompts_dir, yes, dry_run, do_backup, debug,
                )
            else:
                record("TODO", dest_rel,
                       "overlay section not present — add manually",
                       f"wrap content with markers per {overlay_dir}/APPLY.md")


def _same_content(a: Path, b: Path) -> bool:
    """True when both files exist and hold the same text, ignoring line endings."""
    if not a.exists() or not b.exists():
        return False
    return _read_text_eol(a)[0] == _read_text_eol(b)[0]


def _normalized_lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.strip("\n").split("\n")]


def _reset_is_provable_noop(installed_text: str, default_interior: str) -> bool:
    """True when `default_interior` already sits in `installed_text` as a contiguous
    run of whole lines (trailing whitespace ignored), so splicing the overlay default
    back in cannot change those bytes.

    Asymmetric on purpose. True is a PROOF of safety. False means "cannot prove safe"
    — never "proven unsafe": a file predating the region entirely also returns False.
    Decision-3 fires when the installed file has NO markers, so there is no installed
    interior to compare against; presence of the default is the only question we can
    answer. Spend silence only where safety is proven.
    """
    if not installed_text.strip():
        return False
    haystack = _normalized_lines(installed_text)
    needle = _normalized_lines(default_interior)
    if not needle:
        return False
    return any(
        haystack[i:i + len(needle)] == needle
        for i in range(len(haystack) - len(needle) + 1)
    )


def _record_manual_merge_state(dest_rel: str, src: Path, dest: Path,
                               overlay_name: str, src_name: str) -> None:
    """T-54: flagging an identical file trains the operator to ignore the flag."""
    if _same_content(src, dest):
        record("SAME", dest_rel, "identical to overlay source — no merge needed")
    elif src.exists():
        record("TODO", dest_rel, "manual merge required — differs from overlay source",
               f"overlay source: overlays/{overlay_name}/files/{src_name}")
    else:
        record("TODO", dest_rel, "manual merge required — file already exists",
               "no overlay source available")


def _record_reset_signal(dest_rel: str, name: str, inst_text: str,
                         default_interior: str) -> None:
    """T-80a: an unconditional WARN carries zero bits. Spend silence only on proof."""
    if _reset_is_provable_noop(inst_text, default_interior):
        record("INFO", dest_rel,
               f"keep-region '{name}' marker absent — overlay default already "
               f"present verbatim; reset is a no-op")
    else:
        record("WARN-CLOBBER", dest_rel,
               f"keep-region '{name}' marker absent AND the overlay default is "
               f"not present verbatim — installing REPLACES that area; a repo "
               f"customization there is LOST",
               "diff the region against the overlay default before proceeding")


def handle_manual_if_exists(manifest: dict, overlay_dir: Path, target_root: Path, dry_run: bool):
    files_dir = overlay_dir / "files"
    for dest_rel in manifest.get("manual_if_exists", []):
        dest = target_root / dest_rel
        src_name = Path(dest_rel).name
        src = files_dir / src_name

        if dest.exists():
            _record_manual_merge_state(dest_rel, src, dest, manifest["name"], src_name)
        else:
            if src.exists():
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
                    dest.chmod(dest.stat().st_mode | 0o755)
                record("COPY", dest_rel, "file missing — copied from overlay")
            else:
                record("TODO", dest_rel, "file missing and no overlay source — add manually")


def handle_customizable(manifest: dict, overlay_dir: Path, target_root: Path,
                        dry_run: bool, do_backup: bool):
    """Install `customizable:` files: overlay owns everything except named
    keep-regions, which are repo-owned (preserved on update; the shipped default
    is a first-install seed only). See docs/plans/overlay-customizable-regions.md.
    """
    files_dir = overlay_dir / "files"
    for dest_rel, spec in manifest.get("customizable", {}).items():
        sanctioned = set(spec.get("keep_regions", []))
        src = files_dir / Path(dest_rel).name
        dest = target_root / dest_rel

        if not src.exists():
            record("ERROR", dest_rel, f"source missing in overlay: {src.name}")
            continue

        src_text, src_crlf = _read_text_eol(src)
        try:
            src_regions = _extract_regions(src_text)
        except ValueError as e:
            record("ERROR", dest_rel, f"overlay source has malformed keep-region: {e}")
            continue

        # decision 2: a listed region must exist in the source (author bug).
        missing = sorted(sanctioned - set(src_regions))
        if missing:
            record("ERROR", dest_rel,
                   f"keep_regions {missing} not found in overlay source (author bug)")
            continue
        # decision 1: no unsanctioned marker in the source.
        rogue_src = sorted(set(src_regions) - sanctioned)
        if rogue_src:
            record("ERROR", dest_rel,
                   f"unsanctioned overlay-keep region(s) in source: {rogue_src}")
            continue

        exe = _is_executable_payload(src)

        if not dest.exists():
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                _write_text_eol(dest, src_text, src_crlf)
                _apply_mode(dest, exe)
            record("COPY", dest_rel, "file missing — seeded from overlay")
            continue

        inst_text, inst_crlf = _read_text_eol(dest)
        try:
            inst_regions = _extract_regions(inst_text)
        except ValueError as e:
            record("ERROR", dest_rel, f"installed file has malformed keep-region: {e}")
            continue
        # decision 1: no unsanctioned marker the repo invented.
        rogue_inst = sorted(set(inst_regions) - sanctioned)
        if rogue_inst:
            record("ERROR", dest_rel,
                   f"unsanctioned overlay-keep region(s) in installed file: {rogue_inst}")
            continue

        # Preserve installed interior where present; reset to source default
        # (decision 3) where the repo dropped the marker.
        replacements, reset = {}, []
        for name in sanctioned:
            if name in inst_regions:
                replacements[name] = inst_regions[name]
            else:
                replacements[name] = src_regions[name]
                reset.append(name)

        merged = _splice_regions(src_text, replacements)
        for name in sorted(reset):
            _record_reset_signal(dest_rel, name, inst_text, src_regions[name])

        if merged == inst_text:
            record("SKIP", dest_rel, "up to date")
            continue

        if not dry_run:
            if do_backup:
                _backup(dest)
            _write_text_eol(dest, merged, inst_crlf)
            _apply_mode(dest, exe)
        preserved = sorted(sanctioned - set(reset))
        bak_note = f"backup: {dest_rel}.bak" if do_backup else "no backup (use --backup to enable)"
        record("UPDATE", dest_rel, f"regions preserved: {preserved}", bak_note)


# ── verify mode (read-only) ───────────────────────────────────────────────────


def _norm(p: Path) -> bytes:
    """Read a file, normalize CRLF→LF and strip trailing newlines for comparison.

    SAME = content equal after EOL normalization (T-58 decision 2026-06-26).
    A file differing ONLY by CRLF↔LF, or by a sole trailing newline, is SAME.
    Note: this intentionally decouples verify-SAME from the installer's byte-exact
    sha256 SKIP — a file can be verify-SAME yet the installer would still re-copy it
    (open task T-29 for EOL handling).
    """
    return p.read_bytes().replace(b"\r\n", b"\n").rstrip(b"\n")


def verify_overlay(
    manifest: dict,
    overlay_dir: Path,
    target_root: Path,
    install_level: str,
) -> tuple[int, int, int]:
    """Read-only verification: compare each overlay-managed file against its installed dest.

    Mirrors the dest-resolution logic of handle_files / handle_always_user_files /
    handle_user_files / handle_templates / handle_manual_if_exists / handle_merge_sections
    without performing any writes, mkdir, backup, or chmod.

    Returns:
        (n_diff, n_missing, n_src_missing) — aggregate tally across ALL categories.
        Records SAME / DIFF / MISSING / SRC-MISSING per file via report.record().

    Exit logic (caller's responsibility):
        exit(1) if any(tally) else exit(0).
    """
    n_diff = 0
    n_missing = 0
    n_src_missing = 0

    def _check(src: Path, dest: Path, display: str) -> None:
        nonlocal n_diff, n_missing, n_src_missing
        if not src.exists():
            record("SRC-MISSING", display, "source missing in overlay")
            n_src_missing += 1
        elif not dest.exists():
            record("MISSING", display, "not installed")
            n_missing += 1
        elif _norm(src) == _norm(dest):
            record("SAME", display, "up to date")
        else:
            record("DIFF", display, "differs from overlay source")
            n_diff += 1

    files_dir = overlay_dir / "files"

    # ── files: → target_root/dest_rel ────────────────────────────────────────
    for src_name, dest_rel in manifest.get("files", {}).items():
        _check(files_dir / src_name, target_root / dest_rel, dest_rel)

    # ── always_user_files: → ~/.claude/dest_rel (never controlled by level) ──
    always_user = manifest.get("always_user_files", {})
    if always_user:
        user_dest_root = Path.home() / ".claude"
        for src_name, dest_rel in always_user.items():
            _check(
                files_dir / src_name,
                user_dest_root / dest_rel,
                f"~/.claude/{dest_rel}",
            )

    # ── user_files: → ~/.claude/ (user) or .claude/ (project) per level ──────
    user_files = manifest.get("user_files", {})
    if user_files:
        if install_level == "user":
            level_root = Path.home() / ".claude"
            level_label = "~/.claude"
        else:
            level_root = target_root / ".claude"
            level_label = ".claude"
        for src_name, dest_rel in user_files.items():
            _check(
                files_dir / src_name,
                level_root / dest_rel,
                f"{level_label}/{dest_rel}",
            )

    # ── templates: → target_root/dest_rel (user-managed after creation) ──────
    # Decision (a): DIFF and MISSING both gate exit, same as overlay-owned.
    # USER-MANAGED label kept in report for readability only.
    tmpl_dir = overlay_dir / "templates"
    for tmpl_name, dest_rel in manifest.get("templates", {}).items():
        src = tmpl_dir / tmpl_name
        dest = target_root / dest_rel
        if not src.exists():
            record("SRC-MISSING", dest_rel, "template source missing in overlay")
            n_src_missing += 1
        elif not dest.exists():
            record("MISSING", dest_rel, "not installed (USER-MANAGED)")
            n_missing += 1
        elif _norm(src) == _norm(dest):
            record("SAME", dest_rel, "up to date (USER-MANAGED)")
        else:
            record("DIFF", dest_rel, "differs from template source (USER-MANAGED)")
            n_diff += 1

    # ── manual_if_exists: → target_root/dest_rel, src = files/<basename> ─────
    # Decision (a): DIFF and MISSING both gate exit (same as overlay-owned).
    # USER-MANAGED label kept for readability only.
    for dest_rel in manifest.get("manual_if_exists", []):
        src = files_dir / Path(dest_rel).name
        dest = target_root / dest_rel
        if not src.exists():
            record("SRC-MISSING", dest_rel, "overlay source missing")
            n_src_missing += 1
        elif not dest.exists():
            record("MISSING", dest_rel, "not installed (USER-MANAGED)")
            n_missing += 1
        elif _norm(src) == _norm(dest):
            record("SAME", dest_rel, "up to date (USER-MANAGED)")
        else:
            record("DIFF", dest_rel, "differs from overlay source (USER-MANAGED)")
            n_diff += 1

    # ── merge_sections: version-marker based (separate mechanism) ────────────
    # SAME = installed version matches manifest version.
    # DIFF = installed version differs.
    # MISSING = dest exists but has no overlay marker, OR dest is absent.
    overlay_name = manifest.get("name", "")
    overlay_version = manifest.get("version", 0)
    open_pattern = re.compile(
        rf"<!-- overlay:{re.escape(overlay_name)} v(\d+) -->", re.MULTILINE
    )
    for dest_rel, spec in manifest.get("merge_sections", {}).items():
        section_file = overlay_dir / spec["file"]
        dest = target_root / dest_rel
        if not section_file.exists():
            record("SRC-MISSING", dest_rel, "section source missing in overlay")
            n_src_missing += 1
            continue
        if not dest.exists():
            record("MISSING", dest_rel, "dest file absent — section not installed")
            n_missing += 1
            continue
        existing = dest.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
        version_match = open_pattern.search(existing)
        if version_match:
            found_version = int(version_match.group(1))
            if found_version == overlay_version:
                record("SAME", dest_rel, f"v{overlay_version} marker present")
            else:
                record(
                    "DIFF", dest_rel,
                    f"v{found_version} installed, v{overlay_version} expected",
                )
                n_diff += 1
        else:
            record("MISSING", dest_rel, "overlay section marker not present")
            n_missing += 1

    # ── customizable: → per-region; CUSTOMIZED is non-gating, outside-drift gates ─
    for dest_rel, spec in manifest.get("customizable", {}).items():
        sanctioned = set(spec.get("keep_regions", []))
        src = files_dir / Path(dest_rel).name
        dest = target_root / dest_rel
        if not src.exists():
            record("SRC-MISSING", dest_rel, "overlay source missing")
            n_src_missing += 1
            continue
        if not dest.exists():
            record("MISSING", dest_rel, "not installed")
            n_missing += 1
            continue
        src_text = src.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
        inst_text = dest.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
        try:
            src_regions = _extract_regions(src_text)
            inst_regions = _extract_regions(inst_text)
        except ValueError:
            record("DIFF", dest_rel, "malformed keep-region markers")
            n_diff += 1
            continue
        # What the installer WOULD produce: source skeleton with installed regions
        # preserved (source default where a marker was dropped).
        expected = _splice_regions(
            src_text,
            {n: inst_regions.get(n, src_regions.get(n, "")) for n in sanctioned},
        )
        if expected != inst_text:
            record("DIFF", dest_rel, "differs from overlay source (outside keep-regions)")
            n_diff += 1
        elif any(n in inst_regions and inst_regions[n] != src_regions.get(n)
                 for n in sanctioned):
            record("CUSTOMIZED", dest_rel, "keep-region customized (sanctioned)")
        else:
            record("SAME", dest_rel, "up to date")

    return n_diff, n_missing, n_src_missing
