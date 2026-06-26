#!/usr/bin/env python3
"""LTG Phase 2.5 — corpus manifest builder (ref:ltg-corpus).

Resolves retrieval/corpus.yaml (INTENT) against the tracked git tree and
materializes a frozen retrieval/corpus-manifest.yaml (RESOLUTION): one entry
per file with its provenance group and sha256 content hash, plus the commit
SHA the resolution was taken against.

Freeze model: no repo copy. The (commit SHA + per-file sha256) pair lets any
later run verify drift (re-hash, compare) and reconstruct inputs (checkout SHA).

The file universe is `git ls-files` — tracked content only. Gitignored paths
(e.g. .claude/local/**) never enter the candidate set.

Run via run-build-corpus-manifest.sh (bash-wrapper convention).
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

import yaml

from corpus_groups import assign_group, glob_to_regex

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_CONFIG = Path(__file__).parent / "corpus.yaml"
DEFAULT_OUTPUT = Path(__file__).parent / "corpus-manifest.yaml"


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(glob_to_regex(p).match(path) for p in patterns)


# --------------------------------------------------------------------------- #
# Config + resolution                                                          #
# --------------------------------------------------------------------------- #
def load_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def git_tracked_files(repo_root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=repo_root, capture_output=True, text=True, check=True
    )
    return [line for line in out.stdout.splitlines() if line]


def included_by_roots(path: str, include_roots: list[str]) -> bool:
    """A root ending in '/' is a directory prefix; otherwise an exact file."""
    for root in include_roots:
        if root.endswith("/"):
            if path.startswith(root):
                return True
        elif path == root:
            return True
    return False


def select_files(tracked: list[str], cfg: dict) -> list[str]:
    exts = tuple(cfg.get("file_extensions", []))
    include_roots = cfg.get("include_roots", [])
    include_globs = cfg.get("include_globs", [])
    exclude_globs = cfg.get("exclude_globs", [])

    selected = []
    for path in tracked:
        if exts and not path.endswith(exts):
            continue
        if not (included_by_roots(path, include_roots) or matches_any(path, include_globs)):
            continue
        if matches_any(path, exclude_globs):
            continue
        selected.append(path)
    return sorted(selected)


# --------------------------------------------------------------------------- #
# Hashing + git provenance                                                     #
# --------------------------------------------------------------------------- #
def sha256_file(abs_path: Path) -> str:
    h = hashlib.sha256()
    h.update(abs_path.read_bytes())
    return h.hexdigest()


def git_commit(repo_root: Path) -> str:
    out = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def dirty_corpus_files(repo_root: Path, selected: list[str]) -> list[str]:
    """Selected files with uncommitted modifications (recorded SHA wouldn't
    fully describe their content)."""
    out = subprocess.run(
        ["git", "status", "--porcelain", "--"] + selected,
        cwd=repo_root, capture_output=True, text=True, check=True,
    )
    dirty = []
    for line in out.stdout.splitlines():
        # porcelain: 'XY <path>' — strip the 2-char status + space
        if len(line) > 3:
            dirty.append(line[3:].strip())
    return dirty


# --------------------------------------------------------------------------- #
# Manifest assembly                                                            #
# --------------------------------------------------------------------------- #
def build_manifest(repo_root: Path, config_path: Path) -> dict:
    cfg = load_config(config_path)
    tracked = git_tracked_files(repo_root)
    selected = select_files(tracked, cfg)
    groups = cfg.get("groups", [])

    entries = []
    group_counts: dict[str, int] = {}
    total_bytes = 0
    for path in selected:
        abs_path = repo_root / path
        data = abs_path.read_bytes()
        group = assign_group(path, groups)
        entries.append(
            {
                "path": path,
                "group": group,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
        )
        group_counts[group] = group_counts.get(group, 0) + 1
        total_bytes += len(data)

    dirty = dirty_corpus_files(repo_root, selected) if selected else []

    return {
        "meta": {
            "generated_from": str(config_path.relative_to(repo_root)),
            "commit": git_commit(repo_root),
            "file_count": len(entries),
            "total_bytes": total_bytes,
            "group_counts": dict(sorted(group_counts.items())),
            "dirty_corpus_files": sorted(dirty),
        },
        "files": entries,
    }


def write_manifest(manifest: dict, output_path: Path) -> None:
    header = (
        "# LTG corpus manifest — FROZEN RESOLUTION of corpus.yaml (ref:ltg-corpus).\n"
        "# Generated by build_corpus_manifest.py; do not hand-edit.\n"
        "# Freeze = meta.commit + per-file sha256. Re-hash to detect drift.\n\n"
    )
    with output_path.open("w", encoding="utf-8") as f:
        f.write(header)
        yaml.safe_dump(manifest, f, sort_keys=False, default_flow_style=False, width=120)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LTG Phase 2.5 — build frozen corpus manifest")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print summary; do not write the manifest file.")
    args = parser.parse_args(argv)

    manifest = build_manifest(args.repo_root, args.config)
    meta = manifest["meta"]

    print(f"commit         {meta['commit'][:12]}")
    print(f"files          {meta['file_count']}")
    print(f"total_bytes    {meta['total_bytes']:,}")
    print("group_counts:")
    for g, n in meta["group_counts"].items():
        print(f"  {g:<16} {n}")
    if meta["dirty_corpus_files"]:
        print(f"WARNING: {len(meta['dirty_corpus_files'])} corpus file(s) have uncommitted changes:")
        for p in meta["dirty_corpus_files"]:
            print(f"  ! {p}")

    if args.dry_run:
        print("(dry-run — manifest not written)")
        return 0

    write_manifest(manifest, args.output)
    print(f"wrote {args.output.relative_to(args.repo_root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
