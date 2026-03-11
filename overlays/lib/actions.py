"""Deterministic action handlers: files, templates, append_lines, merge_sections, manual_if_exists."""

import hashlib
import re
import shutil
from pathlib import Path

from .backends import Backend
from .planner import ai_merge, _backup
from .report import record


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def handle_files(manifest: dict, overlay_dir: Path, target_root: Path,
                 dry_run: bool, do_backup: bool):
    files_dir = overlay_dir / "files"
    for src_name, dest_rel in manifest.get("files", {}).items():
        src = files_dir / src_name
        dest = target_root / dest_rel

        if not src.exists():
            record("ERROR", dest_rel, f"source missing in overlay: {src_name}")
            continue

        if not dest.exists():
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                dest.chmod(dest.stat().st_mode | 0o755)
            record("COPY", dest_rel, "file missing")
        elif sha256(src) == sha256(dest):
            record("SKIP", dest_rel, "up to date")
        else:
            if not dry_run:
                if do_backup:
                    _backup(dest)
                shutil.copy2(src, dest)
                dest.chmod(dest.stat().st_mode | 0o755)
            bak_note = f"backup: {dest_rel}.bak" if do_backup else "no backup (use --backup to enable)"
            record("UPDATE", dest_rel, "differs from overlay source", bak_note)


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

        existing = dest.read_text()
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
                    dest.write_text(updated)
                bak_note = f"backup: {dest_rel}.bak" if do_backup else "no backup (use --backup to enable)"
                record("UPDATE", dest_rel, f"v{found_version} → v{overlay_version}", bak_note)
        else:
            if mode == "ai":
                ai_merge(
                    dest, existing, section_content, open_marker, close_marker,
                    merge_hint, backend_id, model_override, backends,
                    prompts_dir, yes, dry_run, do_backup,
                )
            else:
                record("TODO", dest_rel,
                       "overlay section not present — add manually",
                       f"wrap content with markers per {overlay_dir}/APPLY.md")


def handle_manual_if_exists(manifest: dict, overlay_dir: Path, target_root: Path, dry_run: bool):
    files_dir = overlay_dir / "files"
    for dest_rel in manifest.get("manual_if_exists", []):
        dest = target_root / dest_rel
        src_name = Path(dest_rel).name
        src = files_dir / src_name

        if dest.exists():
            record("TODO", dest_rel,
                   "manual merge required — file already exists",
                   f"overlay source: overlays/{manifest['name']}/files/{src_name}"
                   if src.exists() else "no overlay source available")
        else:
            if src.exists():
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
                    dest.chmod(dest.stat().st_mode | 0o755)
                record("COPY", dest_rel, "file missing — copied from overlay")
            else:
                record("TODO", dest_rel, "file missing and no overlay source — add manually")
