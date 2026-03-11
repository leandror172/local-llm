#!/usr/bin/env python3
"""
install-overlay.py — Install or update a repo overlay.

Usage:
    python3 overlays/install-overlay.py <overlay-name> --target <repo-path> [options]

Options:
    --target PATH              Target repo root (required)
    --mode manual|ai           Merge mode for shared files (default: manual)
    --yes                      Auto-accept AI decisions (unattended)
    --backend ollama|claude|auto   AI backend for --mode ai (default: auto)
    --ollama-model MODEL       Ollama model to use (default: qwen2.5-coder:14b)
    --report FILE              Write report to file (default: stdout)
    --report-format text|json  Report format (default: text)
    --dry-run                  Show what would be done without making changes
"""

import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip3 install pyyaml", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Report accumulation
# ---------------------------------------------------------------------------

_actions: list[dict] = []


def record(action: str, target: str, reason: str = "", details: str = ""):
    _actions.append({"action": action, "target": target, "reason": reason, "details": details})
    # Print immediately so the user sees progress
    tag = f"[{action}]"
    line = f"  {tag:<12} {target}"
    if reason:
        line += f"  — {reason}"
    print(line)
    if details:
        print(f"               {details}")


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def backup(path: Path) -> Path:
    bak = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, bak)
    return bak


# ---------------------------------------------------------------------------
# Action handlers
# ---------------------------------------------------------------------------

def handle_files(manifest: dict, overlay_dir: Path, target_root: Path, dry_run: bool):
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
                backup(dest)
                shutil.copy2(src, dest)
                dest.chmod(dest.stat().st_mode | 0o755)
            record("UPDATE", dest_rel, "differs from overlay source", f"backup: {dest_rel}.bak")


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

        # Read after potential creation (or empty string in dry_run)
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
                    content = dest.read_text()  # refresh for next line
                record("APPEND", dest_rel, f"added line: {line!r}")


def handle_merge_sections(
    manifest: dict,
    overlay_dir: Path,
    target_root: Path,
    mode: str,
    yes: bool,
    backend: str,
    ollama_model: str,
    dry_run: bool,
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
            # File doesn't exist at all — create it with just the section
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
                # Replace content between markers (version bump)
                new_block = (
                    f"<!-- overlay:{overlay_name} v{overlay_version} -->\n"
                    f"{section_content}\n"
                    f"{close_marker}"
                )
                old_open = f"<!-- overlay:{overlay_name} v{found_version} -->"
                updated = re.sub(
                    rf"{re.escape(old_open)}.*?{re.escape(close_marker)}",
                    new_block,
                    existing,
                    flags=re.DOTALL,
                )
                if not dry_run:
                    backup(dest)
                    dest.write_text(updated)
                record(
                    "UPDATE",
                    dest_rel,
                    f"v{found_version} → v{overlay_version}",
                    f"backup: {dest_rel}.bak",
                )
        else:
            # No marker — need to inject
            if mode == "ai":
                _ai_merge(
                    dest, existing, section_content,
                    open_marker, close_marker,
                    merge_hint, backend, ollama_model, yes, dry_run,
                )
            else:
                record(
                    "TODO",
                    dest_rel,
                    "overlay section not present — add manually",
                    f"wrap content with markers per {overlay_dir}/APPLY.md",
                )


def handle_manual_if_exists(manifest: dict, overlay_dir: Path, target_root: Path, dry_run: bool):
    files_dir = overlay_dir / "files"
    for dest_rel in manifest.get("manual_if_exists", []):
        dest = target_root / dest_rel
        src_name = Path(dest_rel).name
        src = files_dir / src_name

        if dest.exists():
            record(
                "TODO",
                dest_rel,
                "manual merge required — file already exists",
                f"overlay source: overlays/{manifest['name']}/files/{src_name}" if src.exists() else "no overlay source available",
            )
        else:
            if src.exists():
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
                    dest.chmod(dest.stat().st_mode | 0o755)
                record("COPY", dest_rel, "file missing — copied from overlay")
            else:
                record("TODO", dest_rel, "file missing and no overlay source — add manually")


# ---------------------------------------------------------------------------
# AI merge
# ---------------------------------------------------------------------------

def _ai_merge(
    dest: Path,
    existing_content: str,
    section_content: str,
    open_marker: str,
    close_marker: str,
    merge_hint: str,
    backend: str,
    ollama_model: str,
    yes: bool,
    dry_run: bool,
):
    dest_rel = dest.name

    resolved = _resolve_backend(backend, ollama_model)
    if resolved is None:
        record(
            "TODO",
            dest_rel,
            "AI merge skipped — no backend available (Ollama not running, claude not found)",
            "add section manually per APPLY.md",
        )
        return

    script_dir = Path(__file__).parent
    prompt_template_path = script_dir / "prompts" / "merge-section.txt"
    if not prompt_template_path.exists():
        record("TODO", dest_rel, f"AI merge skipped — prompt template missing: {prompt_template_path}")
        return
    prompt = (
        prompt_template_path.read_text()
        .replace("<<EXISTING_CONTENT>>", existing_content)
        .replace("<<OPEN_MARKER>>", open_marker)
        .replace("<<SECTION_CONTENT>>", section_content)
        .replace("<<CLOSE_MARKER>>", close_marker)
        .replace("<<MERGE_HINT>>", merge_hint)
    )

    print(f"\n  Calling AI backend ({resolved[0]}) for merge of {dest_rel}...")
    merged = _call_backend(resolved, prompt)

    if merged is None:
        record("TODO", dest_rel, "AI merge failed — add section manually per APPLY.md")
        return

    # Validate that the AI preserved the required overlay markers
    if open_marker not in merged or close_marker not in merged:
        record(
            "TODO", dest_rel,
            "AI merge rejected — output missing overlay markers (model dropped HTML comments)",
            "add section manually per APPLY.md, or retry with a different model",
        )
        return

    if dry_run:
        record("MERGE:AI", dest_rel, f"would merge via {resolved[0]} (dry-run)")
        return

    if yes:
        backup(dest)
        dest.write_text(merged)
        record("MERGE:AI", dest_rel, f"merged via {resolved[0]} (--yes, no confirmation)")
    else:
        diff = list(difflib.unified_diff(
            existing_content.splitlines(keepends=True),
            merged.splitlines(keepends=True),
            fromfile=f"{dest.name} (before)",
            tofile=f"{dest.name} (after)",
            n=3,
        ))
        print("\n--- AI proposed merge (diff) ---")
        preview = diff[:80]
        print("".join(preview), end="")
        if len(diff) > 80:
            print(f"\n  ... ({len(diff) - 80} more diff lines)")
        print("--- end diff ---\n")

        try:
            ans = input("Apply this merge? [y/N] ").strip().lower()
        except EOFError:
            record(
                "TODO", dest_rel,
                "AI merge ready but no interactive stdin — re-run with --yes to apply",
                f"or apply the diff above manually",
            )
            return
        if ans == "y":
            backup(dest)
            dest.write_text(merged)
            record("MERGE:AI", dest_rel, f"merged via {resolved[0]} (confirmed by user)")
        else:
            record("TODO", dest_rel, "AI merge rejected by user — add section manually")


def _resolve_backend(preference: str, ollama_model: str) -> tuple | None:
    """Return (backend_name, config) or None if unavailable."""
    if preference in ("auto", "ollama"):
        try:
            import urllib.request
            urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
            return ("ollama", ollama_model)
        except Exception:
            if preference == "ollama":
                return None

    if preference in ("auto", "claude"):
        if shutil.which("claude"):
            return ("claude", None)

    return None


def _call_backend(resolved: tuple, prompt: str) -> str | None:
    backend_name, config = resolved
    if backend_name == "ollama":
        return _call_ollama(prompt, model=config)
    elif backend_name == "claude":
        return _call_claude(prompt)
    return None


def _call_ollama(prompt: str, model: str) -> str | None:
    import urllib.request

    # stream:true keeps the socket active (tokens arrive incrementally),
    # avoiding socket-timeout on long generations with stream:false.
    # num_ctx must cover prompt + full merged output. Default Ollama context
    # (4096) is too small for file-merge tasks; 8192 is a safe minimum.
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "think": False,
        "options": {"num_ctx": 8192},
    }).encode()

    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        chunks = []
        with urllib.request.urlopen(req, timeout=30) as resp:
            for line in resp:
                if not line.strip():
                    continue
                chunk = json.loads(line)
                if chunk.get("message", {}).get("content"):
                    chunks.append(chunk["message"]["content"])
                if chunk.get("done"):
                    break
        return "".join(chunks)
    except Exception as e:
        print(f"  WARNING: Ollama call failed: {e}", file=sys.stderr)
        return None


def _call_claude(prompt: str) -> str | None:
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            return result.stdout
        print(f"  WARNING: claude -p failed: {result.stderr}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  WARNING: claude call failed: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def print_report(report_format: str, report_file: str | None):
    counts: dict[str, int] = {}
    for a in _actions:
        counts[a["action"]] = counts.get(a["action"], 0) + 1

    if report_format == "json":
        output = json.dumps(_actions, indent=2)
    else:
        lines = ["", "── Summary " + "─" * 50]
        col_w = max(len(k) for k in counts) if counts else 8
        for action_name, count in sorted(counts.items()):
            lines.append(f"  {action_name:<{col_w + 2}} {count}")
        lines.append("")
        output = "\n".join(lines)

    if report_file:
        Path(report_file).write_text(output)
        print(f"\nReport written to: {report_file}")
    else:
        print(output)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Install or update a repo overlay.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("overlay", help="Overlay name (subdirectory under overlays/)")
    parser.add_argument("--target", required=True, metavar="PATH", help="Target repo root")
    parser.add_argument("--mode", choices=["manual", "ai"], default="manual",
                        help="Merge mode for shared files (default: manual)")
    parser.add_argument("--yes", action="store_true",
                        help="Auto-accept AI decisions (unattended)")
    parser.add_argument("--backend", choices=["ollama", "claude", "auto"], default="auto",
                        help="AI backend for --mode ai (default: auto-detect)")
    parser.add_argument("--ollama-model", default="qwen2.5-coder:14b", metavar="MODEL",
                        help="Ollama model for AI merge (default: qwen2.5-coder:14b)")
    parser.add_argument("--report", metavar="FILE",
                        help="Write summary report to file (default: stdout)")
    parser.add_argument("--report-format", choices=["text", "json"], default="text",
                        help="Report format (default: text)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done without making changes")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    overlay_dir = script_dir / args.overlay
    if not overlay_dir.is_dir():
        print(f"ERROR: overlay not found: {overlay_dir}", file=sys.stderr)
        sys.exit(1)

    manifest_path = overlay_dir / "manifest.yaml"
    if not manifest_path.exists():
        print(f"ERROR: manifest.yaml missing in {overlay_dir}", file=sys.stderr)
        sys.exit(1)

    manifest = yaml.safe_load(manifest_path.read_text())
    target_root = Path(args.target).resolve()

    if not target_root.is_dir():
        print(f"ERROR: target repo not found: {target_root}", file=sys.stderr)
        sys.exit(1)

    dry_label = " (DRY RUN)" if args.dry_run else ""
    print(f"\nOverlay : {manifest['name']} v{manifest['version']}{dry_label}")
    print(f"Target  : {target_root}")
    print(f"Mode    : {args.mode}")
    print()

    handle_files(manifest, overlay_dir, target_root, args.dry_run)
    handle_templates(manifest, overlay_dir, target_root, args.dry_run)
    handle_append_lines(manifest, target_root, args.dry_run)
    handle_merge_sections(
        manifest, overlay_dir, target_root,
        args.mode, args.yes, args.backend, args.ollama_model, args.dry_run,
    )
    handle_manual_if_exists(manifest, overlay_dir, target_root, args.dry_run)

    print_report(args.report_format, args.report)


if __name__ == "__main__":
    main()
