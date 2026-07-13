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
    --dry-run                  Show what would be done without making changes.
                               PURE preview: for an unmarked --mode ai target it
                               records "would AI-merge … run --stage" — it makes NO
                               model call and writes nothing. Use --stage to preview.
    --stage                    (--mode ai) Call the model, print a unified diff, and
                               write a durable plan-handle under
                               <target>/.claude/local/overlay-merge-plans/ WITHOUT
                               touching the target. Preview before you apply.
    --apply-plan PATH          Apply a previously staged plan-handle. Verifies the
                               target is byte-for-byte the pre-image the plan was
                               computed from (STALE + abort otherwise), then merges
                               and backs up. Needs only the handle — no model call.
    --plan-file PATH           Override where --stage writes the handle (default: the
                               gitignored .claude/local path). Stage-only; --apply-plan
                               takes the handle path as its own argument.
    --verify                   Read-only check: compare installed files against overlay
                               source. Prints SAME/DIFF/MISSING/SRC-MISSING per file.
                               Exits 1 if any DIFF/MISSING/SRC-MISSING; 0 if all match.
                               All categories gate the exit: files, always_user_files,
                               user_files, templates, manual_if_exists, merge_sections.
                               NOTE: SAME uses EOL-normalized comparison (CRLF=LF),
                               which decouples verify from the installer's byte-exact
                               skip check (open task T-29).
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
    handle_files, handle_always_user_files, handle_user_files,
    handle_templates, handle_append_lines,
    handle_merge_sections, handle_manual_if_exists, handle_customizable,
    verify_overlay,
)
from lib.planner import stage_all_sections, apply_staged_plan
from lib.report import print_report, any_action


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
        "--install-level", choices=["user", "project"], default="user",
        help="Install shim/hooks/skill to ~/.claude/ (user) or .claude/ (project) (default: user)",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done without making changes (pure — no model call)")
    parser.add_argument("--stage", action="store_true",
                        help="(--mode ai) Preview: model-call + diff + write plan handle; no target write")
    parser.add_argument("--apply-plan", metavar="PATH", default=None,
                        help="Apply a staged plan handle (verifies pre-image, then merges + backs up)")
    parser.add_argument("--plan-file", metavar="PATH", default=None,
                        help="Override plan-handle location for --stage / --apply-plan")
    parser.add_argument("--verify", action="store_true",
                        help=(
                            "Read-only check: compare installed files against overlay source. "
                            "Exits 1 if any DIFF/MISSING/SRC-MISSING; 0 if all match. "
                            "Mutually exclusive with install — no writes are ever performed."
                        ))
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
    verify_label = " (VERIFY)" if args.verify else ""
    print(f"\nOverlay : {manifest['name']} v{manifest['version']}{dry_label}{verify_label}")
    print(f"Target  : {target_root}")
    if not args.verify:
        print(f"Mode    : {args.mode}")
    if backends and not args.verify:
        avail = [b.id for b in backends if b.is_available()]
        print(f"Backends: {', '.join(avail) or 'none available'}")
    print()

    if args.verify:
        n_diff, n_missing, n_src_missing = verify_overlay(
            manifest, overlay_dir, target_root, args.install_level
        )
        print_report(args.report_format, args.report)
        sys.exit(1 if (n_diff or n_missing or n_src_missing) else 0)

    # ── stage / apply early-branches (T-81), symmetric with --verify above ──────
    if args.stage:
        if args.mode != "ai":
            parser.error("--stage requires --mode ai")
        stage_all_sections(
            manifest, overlay_dir, target_root, prompts_dir,
            args.backend, args.model, backends, args.plan_file, args.debug,
        )
        print_report(args.report_format, args.report)
        sys.exit(1 if any_action("ERROR", "TODO") else 0)

    if args.apply_plan:
        apply_staged_plan(Path(args.apply_plan), args.backup)
        print_report(args.report_format, args.report)
        sys.exit(1 if any_action("ERROR", "STALE") else 0)

    # customizable: before files: — a path is owned by exactly one category.
    handle_customizable(manifest, overlay_dir, target_root, args.dry_run, args.backup)
    handle_files(manifest, overlay_dir, target_root, args.dry_run, args.backup)
    handle_always_user_files(manifest, overlay_dir, args.dry_run, args.backup)
    handle_user_files(manifest, overlay_dir, args.install_level, target_root, args.dry_run, args.backup)
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
