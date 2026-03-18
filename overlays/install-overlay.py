#!/usr/bin/env python3
"""
install-overlay.py — Install or update a repo overlay.

Usage:
    ./overlays/install-overlay.py <overlay-name> --target <repo-path> [options]

Options:
    --target PATH              Target repo root (required)
    --mode manual|ai           Merge mode for shared files (default: manual)
    --yes                      Auto-accept AI decisions (unattended)
    --backend ID               Backend id from ai-backends.yaml, or 'auto' (default: auto)
    --model MODEL              Override model for the selected backend
    --backup / --no-backup     Backup files before overwriting (default: on)
    --report FILE              Write summary report to file (default: stdout)
    --report-format text|json  Report format (default: text)
    --dry-run                  Show what would be done without making changes
"""

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip3 install pyyaml", file=sys.stderr)
    sys.exit(1)

from lib.backends import load_backends, resolve_backend
from lib.actions import (
    handle_files, handle_user_files, handle_templates, handle_append_lines,
    handle_merge_sections, handle_manual_if_exists,
)
from lib.report import print_report


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
                        help="Override model for the selected backend (+think suffix supported)")
    parser.add_argument("--report", metavar="FILE",
                        help="Write summary report to file (default: stdout)")
    parser.add_argument("--report-format", choices=["text", "json"], default="text",
                        help="Report format (default: text)")
    parser.add_argument(
        "--backup", action=argparse.BooleanOptionalAction, default=True,
        help="Backup files before overwriting (default: on, use --no-backup to skip)",
    )
    parser.add_argument(
        "--skill-level", choices=["user", "project"], default="user",
        help="Install user_files to ~/.claude/ (user) or .claude/ (project) (default: user)",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done without making changes")
    parser.add_argument("--debug", action="store_true",
                        help="Print raw backend responses for troubleshooting")
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

    backends = load_backends(script_dir)
    prompts_dir = script_dir / "prompts"

    dry_label = " (DRY RUN)" if args.dry_run else ""
    print(f"\nOverlay : {manifest['name']} v{manifest['version']}{dry_label}")
    print(f"Target  : {target_root}")
    print(f"Mode    : {args.mode}")
    if backends:
        avail = [b.id for b in backends if b.is_available()]
        print(f"Backends: {', '.join(avail) or 'none available'}")
    print()

    handle_files(manifest, overlay_dir, target_root, args.dry_run, args.backup)
    handle_user_files(manifest, overlay_dir, args.skill_level, target_root, args.dry_run, args.backup)
    handle_templates(manifest, overlay_dir, target_root, args.dry_run)
    handle_append_lines(manifest, target_root, args.dry_run)
    handle_merge_sections(
        manifest, overlay_dir, target_root, prompts_dir,
        args.mode, args.yes, args.backend, args.model,
        backends, args.dry_run, args.backup, args.debug,
    )
    handle_manual_if_exists(manifest, overlay_dir, target_root, args.dry_run)

    print_report(args.report_format, args.report)


if __name__ == "__main__":
    main()
