#!/usr/bin/env python3
"""
record-verdicts.py — Manually record verdicts for a completed comparison run.

Use this when compare-models.py ran in a non-interactive environment (e.g., Claude Code)
and couldn't collect verdicts at runtime. Run in a real terminal after the fact.

Usage (via wrapper — do not call directly):
  benchmarks/lib/run-record-verdicts.sh                          # last entry in default file
  benchmarks/lib/run-record-verdicts.sh --file results/my.jsonl # specific file, last entry
  benchmarks/lib/run-record-verdicts.sh --entry 0               # first entry (0-indexed, default: -1)
  benchmarks/lib/run-record-verdicts.sh --list                   # list all entries with timestamps
"""

import argparse
import json
import sys
from pathlib import Path

DEFAULT_FILE = Path(__file__).resolve().parent.parent / "results" / "compare-runs.jsonl"
THICK_SEP = "═" * 72
SEPARATOR = "─" * 72


def parse_args():
    p = argparse.ArgumentParser(description="Record verdicts for a completed comparison run.")
    p.add_argument("--file", default=str(DEFAULT_FILE), help="JSONL results file")
    p.add_argument(
        "--entry",
        type=int,
        default=-1,
        help="Entry index (0-based; -1 = last, default)",
    )
    p.add_argument("--list", action="store_true", help="List all entries and exit")
    return p.parse_args()


def load_entries(path: Path) -> list[dict]:
    if not path.exists():
        print(f"ERROR: {path} not found.", file=sys.stderr)
        sys.exit(1)
    entries = []
    for line in path.read_text().strip().splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    if not entries:
        print(f"ERROR: {path} is empty.", file=sys.stderr)
        sys.exit(1)
    return entries


def save_entries(path: Path, entries: list[dict]):
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n")


def list_entries(entries: list[dict]):
    print(f"\n  {'#':<4} {'Timestamp':<22} {'Models'}")
    print(f"  {'─'*4} {'─'*22} {'─'*40}")
    for i, e in enumerate(entries):
        models = " | ".join(r["model"] for r in e.get("results", []))
        has_verdicts = any(r.get("verdict") for r in e.get("results", []))
        marker = " ✓" if has_verdicts else ""
        print(f"  {i:<4} {e.get('timestamp', '?'):<22} {models}{marker}")
    print()


def collect_verdict(model: str, content: str, index: int, existing: dict | None) -> dict:
    """Show response and collect verdict interactively."""
    print(f"\n{THICK_SEP}")
    print(f"  MODEL {index}: {model}")
    print(THICK_SEP)
    if not content:
        print("  [no output — error or timeout]")
    else:
        print()
        print(content)

    # Show existing verdict if any
    if existing and existing.get("verdict"):
        print(f"\n  (existing verdict: {existing['verdict']} — {existing.get('verdict_note', '')})")
        reuse = input("  Keep existing verdict? [Y/n]: ").strip().lower()
        if reuse != "n":
            return existing

    print(f"\n  Verdict for model {index} ({model}):")
    print("    [A] ACCEPTED  — used as-is")
    print("    [I] IMPROVED  — used with modifications")
    print("    [R] REJECTED  — not usable")
    print()

    while True:
        choice = input("  Your verdict (A/I/R): ").strip().upper()
        if choice in ("A", "I", "R"):
            break
        print("  Please enter A, I, or R.")

    verdict_map = {"A": "ACCEPTED", "I": "IMPROVED", "R": "REJECTED"}
    verdict = verdict_map[choice]

    note = ""
    if choice in ("I", "R"):
        note = input(f"  Notes ({verdict} — what changed / why rejected): ").strip()

    return {"verdict": verdict, "verdict_note": note}


def main():
    args = parse_args()
    path = Path(args.file)
    entries = load_entries(path)

    if args.list:
        list_entries(entries)
        return

    # Resolve entry index
    idx = args.entry
    if idx < 0:
        idx = len(entries) + idx
    if not (0 <= idx < len(entries)):
        print(f"ERROR: entry {args.entry} out of range (0–{len(entries)-1})", file=sys.stderr)
        sys.exit(1)

    entry = entries[idx]
    results = entry.get("results", [])

    print(f"\n{THICK_SEP}")
    print("  VERDICT COLLECTION")
    print(THICK_SEP)
    print(f"  File:      {path}")
    print(f"  Entry:     #{idx} of {len(entries)-1}  ({entry.get('timestamp', '?')})")
    print(f"  Models:    {' | '.join(r['model'] for r in results)}")
    print(f"  Think:     {entry.get('think', False)}")
    print(f"\n  PROMPT:\n")
    for line in entry.get("prompt", "").splitlines():
        print(f"    {line}")

    already_rated = sum(1 for r in results if r.get("verdict"))
    if already_rated == len(results):
        print(f"\n  Note: all {len(results)} responses already have verdicts.")
        redo = input("  Re-record all verdicts? [y/N]: ").strip().lower()
        if redo != "y":
            print("  Aborted — no changes made.")
            return

    # Collect verdict for each result
    for i, result in enumerate(results, start=1):
        existing = {"verdict": result.get("verdict"), "verdict_note": result.get("verdict_note")}
        v = collect_verdict(result["model"], result.get("content", ""), i, existing)
        result["verdict"] = v["verdict"]
        result["verdict_note"] = v.get("verdict_note", "")

    # Summary
    print(f"\n{SEPARATOR}")
    print("  SUMMARY")
    print(SEPARATOR)
    for r in results:
        v = r["verdict"] or "—"
        note = f" — {r['verdict_note']}" if r.get("verdict_note") else ""
        print(f"  {r['model']:<30} {v}{note}")

    # Save
    entries[idx] = entry
    save_entries(path, entries)
    print(f"\n  Saved to {path}")


if __name__ == "__main__":
    main()
