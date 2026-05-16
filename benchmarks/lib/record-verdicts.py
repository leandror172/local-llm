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

  # Non-interactive mode (verdicts supplied via flags — works in Claude Code):
  benchmarks/lib/run-record-verdicts.sh --entry 0 --verdicts "2,1" --notes "|package main + error string"
  benchmarks/lib/run-record-verdicts.sh --entry 1 --verdicts "1,1" --notes "external dep + deadlock|evictOldest wrong end"

  --verdicts: comma-separated 0/1/2 in model order (e.g. "2,1,0")
  --notes:    pipe-separated notes for each model; empty string for verdict 2 (e.g. "|note2|note3")
              Only required for verdict 1 (improved) and 0 (rejected) entries.
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
    p.add_argument(
        "--verdicts",
        help="Non-interactive: comma-separated verdicts in model order (e.g. '2,1,0')",
    )
    p.add_argument(
        "--notes",
        default="",
        help="Non-interactive: pipe-separated notes per model (e.g. '|note for model2|note for model3')",
    )
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


def apply_verdicts_noninteractive(results: list[dict], verdicts_str: str, notes_str: str) -> list[dict]:
    """Apply verdicts from CLI flags without any input() calls."""
    verdict_map = {"0": 0, "1": 1, "2": 2}
    raw = [v.strip() for v in verdicts_str.split(",")]
    notes = [n.strip() for n in notes_str.split("|")] if notes_str else []

    if len(raw) != len(results):
        print(
            f"ERROR: --verdicts has {len(raw)} value(s) but entry has {len(results)} model(s).",
            file=sys.stderr,
        )
        sys.exit(1)

    for i, (result, choice) in enumerate(zip(results, raw)):
        if choice not in verdict_map:
            print(f"ERROR: invalid verdict '{choice}' for model {i+1} — must be 0, 1, or 2.", file=sys.stderr)
            sys.exit(1)
        result["verdict"] = verdict_map[choice]
        result["verdict_note"] = notes[i] if i < len(notes) else ""

    return results


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
    print("    [2] accepted  — used as-is")
    print("    [1] improved  — used with modifications")
    print("    [0] rejected  — not usable")
    print()

    while True:
        choice = input("  Your verdict (0/1/2): ").strip()
        if choice in ("0", "1", "2"):
            break
        print("  Please enter 0, 1, or 2.")

    verdict_map = {"0": 0, "1": 1, "2": 2}
    verdict = verdict_map[choice]

    note = ""
    if choice in ("0", "1"):
        note = input(f"  Notes (verdict {verdict} — what changed / why rejected): ").strip()

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

    # Non-interactive path: --verdicts supplied via flag
    if args.verdicts:
        apply_verdicts_noninteractive(results, args.verdicts, args.notes)
    else:
        already_rated = sum(1 for r in results if r.get("verdict"))
        if already_rated == len(results):
            print(f"\n  Note: all {len(results)} responses already have verdicts.")
            redo = input("  Re-record all verdicts? [y/N]: ").strip().lower()
            if redo != "y":
                print("  Aborted — no changes made.")
                return

        # Collect verdict for each result interactively
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
