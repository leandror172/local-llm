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

from enum import Enum


class BackendType(str, Enum):
    OLLAMA_API = "ollama_api"
    CLI = "cli"
    CLAUDE_API = "claude_api"
    OPENAI_COMPATIBLE = "openai_compatible_api"


class SchemaMode(str, Enum):
    FORMAT_PARAM = "format_param"
    PROMPT_INJECTION = "prompt_injection"
    TOOL_USE = "tool_use"


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

def handle_files(manifest: dict, overlay_dir: Path, target_root: Path, dry_run: bool, do_backup: bool):
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
                    backup(dest)
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
    backend_id: str,
    model_override: str | None,
    backends: list[dict],
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
                    if do_backup:
                        backup(dest)
                    dest.write_text(updated)
                bak_note = f"backup: {dest_rel}.bak" if do_backup else "no backup (use --backup to enable)"
                record("UPDATE", dest_rel, f"v{found_version} → v{overlay_version}", bak_note)
        else:
            # No marker — need to inject
            if mode == "ai":
                _ai_merge(
                    dest, existing, section_content,
                    open_marker, close_marker,
                    merge_hint, backend_id, model_override, backends, yes, dry_run, do_backup,
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

def _apply_plan(plan: dict, existing_content: str, open_marker: str, section_content: str, close_marker: str) -> str:
    """Apply a merge plan deterministically. Returns new file content."""
    lines = existing_content.splitlines(keepends=True)
    insert_after = plan["insert_after_line"]  # 1-indexed

    # Apply deletes in reverse order so earlier line numbers stay valid
    for r in sorted(plan.get("delete_ranges", []), key=lambda r: r["start"], reverse=True):
        start_idx = r["start"] - 1   # 1-indexed → 0-indexed
        end_idx = r["end"]            # end is inclusive, slice end is exclusive
        removed = "".join(lines[start_idx:end_idx]).rstrip()
        preview = removed.splitlines()[0][:60] if removed else ""
        record(
            "DELETE", dest_rel,
            f"lines {r['start']}–{r['end']}: {r.get('reason', 'no reason given')}",
            f"first line: {preview!r}" if preview else "",
        )
        del lines[start_idx:end_idx]
        # Adjust insert point for lines removed before it
        deleted_before = sum(
            1 for i in range(r["start"], r["end"] + 1) if i <= insert_after
        )
        insert_after -= deleted_before

    # Build section block — markers are always added by the script, never the AI
    section_block = f"{open_marker}\n{section_content}\n{close_marker}\n"

    # insert_after=0 → prepend; otherwise insert after 1-indexed line N = index N
    lines.insert(max(0, insert_after), section_block)
    return "".join(lines)


def _ai_merge(
    dest: Path,
    existing_content: str,
    section_content: str,
    open_marker: str,
    close_marker: str,
    merge_hint: str,
    backend_id: str,
    model_override: str | None,
    backends: list[dict],
    yes: bool,
    dry_run: bool,
    do_backup: bool,
):
    dest_rel = dest.name
    script_dir = Path(__file__).parent
    prompts_dir = script_dir / "prompts"

    resolved = _resolve_backend(backends, backend_id, model_override)
    if resolved is None:
        record("TODO", dest_rel,
               "AI merge skipped — no backend available",
               "add section manually per APPLY.md")
        return

    # Load prompt template
    prompt_path = prompts_dir / "merge-plan.txt"
    if not prompt_path.exists():
        record("TODO", dest_rel, f"AI merge skipped — prompt template missing: {prompt_path}")
        return
    prompt = (
        prompt_path.read_text()
        .replace("<<EXISTING_CONTENT>>", existing_content)
        .replace("<<SECTION_CONTENT>>", section_content)
        .replace("<<MERGE_HINT>>", merge_hint)
    )

    # Load JSON schema (used by Ollama format param; embedded in prompt for claude fallback)
    schema_path = prompts_dir / "merge-plan-schema.json"
    schema = json.loads(schema_path.read_text()) if schema_path.exists() else None
    if schema is None:
        record("TODO", dest_rel, f"AI merge skipped — schema missing: {schema_path}")
        return

    schema_mode = SchemaMode(resolved.get("schema_mode", SchemaMode.PROMPT_INJECTION))
    if schema_mode == SchemaMode.PROMPT_INJECTION:
        prompt += f"\n\nRespond with a JSON object matching this schema:\n{json.dumps(schema, indent=2)}"

    print(f"\n  Calling AI backend ({resolved['id']}) for merge plan of {dest_rel}...")
    fmt = schema if schema_mode == SchemaMode.FORMAT_PARAM else None
    plan_text = _call_backend(resolved, prompt, fmt=fmt)

    if plan_text is None:
        record("TODO", dest_rel, "AI merge failed — add section manually per APPLY.md")
        return

    try:
        plan = json.loads(plan_text)
    except json.JSONDecodeError as e:
        record("TODO", dest_rel, f"AI returned invalid JSON: {e}", "add section manually per APPLY.md")
        return

    delete_ranges = plan.get("delete_ranges", [])
    print(f"  Plan: insert after line {plan['insert_after_line']}, "
          f"delete {len(delete_ranges)} range(s) — {plan.get('reasoning', '')}")
    if not delete_ranges:
        record(
            "WARN", dest_rel,
            "AI inserted section but removed nothing — verify no superseded content remains",
            "check for older/simpler versions of this section and remove manually if found",
        )

    merged = _apply_plan(plan, existing_content, open_marker, section_content, close_marker)

    if dry_run:
        record("MERGE:AI", dest_rel, f"would apply plan via {resolved['id']} (dry-run)")
        return

    diff = list(difflib.unified_diff(
        existing_content.splitlines(keepends=True),
        merged.splitlines(keepends=True),
        fromfile=f"{dest.name} (before)",
        tofile=f"{dest.name} (after)",
        n=3,
    ))

    if yes:
        if do_backup:
            backup(dest)
        dest.write_text(merged)
        record("MERGE:AI", dest_rel, f"merged via {resolved['id']} (--yes, no confirmation)")
    else:
        print("\n--- AI merge plan diff ---")
        print("".join(diff[:80]), end="")
        if len(diff) > 80:
            print(f"\n  ... ({len(diff) - 80} more lines)")
        print("--- end diff ---\n")
        try:
            ans = input("Apply? [y/N] ").strip().lower()
        except EOFError:
            record("TODO", dest_rel,
                   "AI merge ready but no interactive stdin — re-run with --yes to apply")
            return
        if ans == "y":
            if do_backup:
                backup(dest)
            dest.write_text(merged)
            record("MERGE:AI", dest_rel, f"merged via {resolved['id']} (confirmed by user)")
        else:
            record("TODO", dest_rel, "AI merge rejected by user — add section manually")


def _load_backends(script_dir: Path) -> list[dict]:
    """Load ai-backends.yaml; return sorted list of backend dicts."""
    path = script_dir / "ai-backends.yaml"
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text()).get("backends", [])
    return sorted(raw, key=lambda b: b.get("priority", 99))


def _backend_available(backend: dict) -> bool:
    import urllib.request
    t = BackendType(backend["type"])
    if t == BackendType.OLLAMA_API:
        try:
            base = backend["address"].split("/api/")[0]
            urllib.request.urlopen(f"{base}/api/tags", timeout=2)
            return True
        except Exception:
            return False
    elif t == BackendType.CLI:
        return shutil.which(backend["command"]) is not None
    elif t in (BackendType.CLAUDE_API, BackendType.OPENAI_COMPATIBLE):
        key_spec = backend.get("api_key", "")
        if str(key_spec).startswith("env:"):
            return os.environ.get(key_spec[4:]) is not None
        return bool(key_spec)
    return False


def _resolve_backend(backends: list[dict], preference: str, model_override: str | None) -> dict | None:
    """Return first available backend. 'auto' tries in priority order; otherwise match by id."""
    if preference == "auto":
        for b in backends:
            if _backend_available(b):
                return b
        return None
    for b in backends:
        if b["id"] == preference:
            return b if _backend_available(b) else None
    return None


def _call_backend(backend: dict, prompt: str, fmt: dict | None = None, model_override: str | None = None) -> str | None:
    t = BackendType(backend["type"])
    if t == BackendType.OLLAMA_API:
        return _call_ollama_api(backend, prompt, fmt=fmt, model_override=model_override)
    elif t == BackendType.CLI:
        return _call_cli(backend, prompt)
    elif t == BackendType.CLAUDE_API:
        return _call_claude_api(backend, prompt, fmt=fmt, model_override=model_override)
    print(f"  WARNING: unsupported backend type: {backend['type']}", file=sys.stderr)
    return None


def _call_ollama_api(backend: dict, prompt: str, fmt: dict | None = None, model_override: str | None = None) -> str | None:
    import urllib.request

    # model_override may carry +think suffix (CLI convenience); parse it out
    raw_model = model_override or backend.get("model", "")
    think_override = raw_model.endswith("+think")
    model = raw_model.removesuffix("+think")

    # think: explicit in config, overridden if +think suffix used
    think = think_override if model_override else backend.get("think")

    # stream:true avoids socket-timeout on long generations (stream:false
    # sends nothing until generation is complete).
    # Planner output is small JSON — 4096 ctx is sufficient.
    # Full-file merges need 8192 minimum.
    num_ctx = 4096 if fmt is not None else 8192
    payload_dict: dict = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "options": {"num_ctx": num_ctx},
    }
    # think param is Qwen3-specific; null means "don't send"
    if think is not None:
        payload_dict["think"] = think
    if fmt is not None:
        payload_dict["format"] = fmt

    try:
        req = urllib.request.Request(
            backend["address"],
            data=json.dumps(payload_dict).encode(),
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
        print(f"  WARNING: Ollama API call failed: {e}", file=sys.stderr)
        return None


def _call_cli(backend: dict, prompt: str) -> str | None:
    command = [backend["command"]] + backend.get("args", []) + [prompt]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return result.stdout
        print(f"  WARNING: CLI call failed: {result.stderr}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  WARNING: CLI call failed: {e}", file=sys.stderr)
        return None


def _call_claude_api(backend: dict, prompt: str, fmt: dict | None = None, model_override: str | None = None) -> str | None:
    import urllib.request
    key_spec = backend.get("api_key", "")
    api_key = os.environ.get(key_spec[4:]) if str(key_spec).startswith("env:") else key_spec
    if not api_key:
        print("  WARNING: Claude API key not available", file=sys.stderr)
        return None
    model = model_override or backend.get("model", "claude-haiku-4-5")
    # Tool use for structured output; fall back to prompt injection if no schema
    if fmt is not None:
        tool = {
            "name": "merge_plan",
            "description": "Output the merge plan",
            "input_schema": fmt,
        }
        payload = {
            "model": model,
            "max_tokens": 512,
            "tools": [tool],
            "tool_choice": {"type": "tool", "name": "merge_plan"},
            "messages": [{"role": "user", "content": prompt}],
        }
    else:
        payload = {
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
    try:
        req = urllib.request.Request(
            backend["address"],
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        # Extract tool input or text content
        for block in data.get("content", []):
            if block.get("type") == "tool_use":
                return json.dumps(block["input"])
            if block.get("type") == "text":
                return block["text"]
    except Exception as e:
        print(f"  WARNING: Claude API call failed: {e}", file=sys.stderr)
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
    parser.add_argument("--backend", default="auto", metavar="ID",
                        help="Backend id from ai-backends.yaml, or 'auto' (default: auto)")
    parser.add_argument("--model", default=None, metavar="MODEL",
                        help="Override model for the selected backend (append +think for Qwen3 thinking mode)")
    parser.add_argument("--report", metavar="FILE",
                        help="Write summary report to file (default: stdout)")
    parser.add_argument("--report-format", choices=["text", "json"], default="text",
                        help="Report format (default: text)")
    parser.add_argument(
        "--backup", action=argparse.BooleanOptionalAction, default=True,
        help="Create .bak backup before overwriting files (default: on, use --no-backup to skip)",
    )
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

    backends = _load_backends(script_dir)

    dry_label = " (DRY RUN)" if args.dry_run else ""
    print(f"\nOverlay : {manifest['name']} v{manifest['version']}{dry_label}")
    print(f"Target  : {target_root}")
    print(f"Mode    : {args.mode}")
    if backends:
        avail = [b["id"] for b in backends if _backend_available(b)]
        print(f"Backends: {', '.join(avail) or 'none available'}")
    print()

    handle_files(manifest, overlay_dir, target_root, args.dry_run, args.backup)
    handle_templates(manifest, overlay_dir, target_root, args.dry_run)
    handle_append_lines(manifest, target_root, args.dry_run)
    handle_merge_sections(
        manifest, overlay_dir, target_root,
        args.mode, args.yes, args.backend, args.model,
        backends, args.dry_run, args.backup,
    )
    handle_manual_if_exists(manifest, overlay_dir, target_root, args.dry_run)

    print_report(args.report_format, args.report)


if __name__ == "__main__":
    main()
