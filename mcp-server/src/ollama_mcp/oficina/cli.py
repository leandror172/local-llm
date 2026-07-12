"""oficina CLI (P1-D11): submit | status | result | cancel | watch | runs | prune.

Thin verb parsing over the SAME service layer the MCP tools use — no logic
duplication. Verbs print JSON (machine-readable) or short text; typed service
errors become ``Error: ...`` on stderr with a non-zero exit. ``watch`` blocks,
polling the ledger and printing new events until a terminal state (P1-D10) — the
shell-invocable reattach path (also acceptance #2's replay command).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, List, Optional

import yaml

from . import service
from .config import default_root, load_retention_config
from .ledger import Ledger
from .retention import sweep
from .store import Store, UnknownRunError


def _load_spec(spec_path: str) -> Any:
    """Parse a spec file (YAML or JSON; '-' reads stdin)."""
    text = sys.stdin.read() if spec_path == "-" else Path(spec_path).read_text(encoding="utf-8")
    return yaml.safe_load(text)


def _emit(obj: Any) -> None:
    """Print a JSON line for a result object."""
    print(json.dumps(obj))


def cmd_submit(root: Path, spec_path: str) -> int:
    """submit: persist + queue a run and ensure a worker; print the handle."""
    try:
        _emit(service.submit(root, _load_spec(spec_path)))
        return 0
    except service.SpecShapeError as exc:
        print(f"Error: invalid spec — {exc}", file=sys.stderr)
        return 1


def cmd_status(root: Path, run_id: str, since_offset: int) -> int:
    """status: print the folded state/phase + events since an offset."""
    try:
        _emit(service.status(root, run_id, since_offset))
        return 0
    except UnknownRunError:
        print(f"Error: unknown run_id {run_id!r}", file=sys.stderr)
        return 1


def cmd_result(root: Path, run_id: str) -> int:
    """result: print a terminal run's report + deliverable (discriminates errors)."""
    try:
        _emit(service.result(root, run_id))
        return 0
    except UnknownRunError:
        print(f"Error: unknown run_id {run_id!r}", file=sys.stderr)
        return 1
    except service.RunNotTerminalError as exc:
        print(f"Error: run not terminal yet — {exc}", file=sys.stderr)
        return 1


def cmd_cancel(root: Path, run_id: str) -> int:
    """cancel: write the cancel flag; print the current state."""
    try:
        _emit(service.cancel(root, run_id))
        return 0
    except UnknownRunError:
        print(f"Error: unknown run_id {run_id!r}", file=sys.stderr)
        return 1


def cmd_watch(root: Path, run_id: str, interval: float = 1.0, _max_iters: Optional[int] = None) -> int:
    """watch: block, printing new events until the run reaches a terminal state."""
    offset = 0
    iters = 0
    while True:
        try:
            snap = service.status(root, run_id, offset)
        except UnknownRunError:
            print(f"Error: unknown run_id {run_id!r}", file=sys.stderr)
            return 1
        for event in snap["events"]:
            _emit(event)
        offset = snap["next_offset"]
        if snap["state"] in ("completed", "failed", "cancelled"):
            return 0
        iters += 1
        if _max_iters is not None and iters >= _max_iters:
            return 0
        time.sleep(interval)


def cmd_runs(root: Path) -> int:
    """runs: list every run with footprint + prune eligibility (P1-D2)."""
    _emit(service.list_runs(root))
    return 0


def cmd_prune(root: Path, dry_run: bool) -> int:
    """prune: run the retention sweep (or preview it with --dry-run)."""
    worker_ledger = Ledger(Path(root) / "worker-events.jsonl")
    records = sweep(Store(root), worker_ledger, load_retention_config(), dry_run=dry_run)
    _emit({"dry_run": dry_run, "pruned": [record.__dict__ for record in records]})
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the oficina argument parser (one subparser per verb)."""
    parser = argparse.ArgumentParser(prog="oficina", description="Async local-model deliverable runs.")
    sub = parser.add_subparsers(dest="verb", required=True)
    p_submit = sub.add_parser("submit", help="submit a run spec (YAML/JSON file, or - for stdin)")
    p_submit.add_argument("spec", help="path to the run spec, or '-' for stdin")
    for verb in ("status", "result", "cancel", "watch"):
        p = sub.add_parser(verb, help=f"{verb} a run by id")
        p.add_argument("run_id")
        if verb == "status":
            p.add_argument("--since", type=int, default=0, dest="since_offset")
        if verb == "watch":
            p.add_argument("--interval", type=float, default=1.0)
    sub.add_parser("runs", help="list runs with footprint + eligibility")
    p_prune = sub.add_parser("prune", help="run the retention sweep")
    p_prune.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Parse argv and dispatch to the matching verb handler."""
    args = build_parser().parse_args(argv)
    root = default_root()
    if args.verb == "submit":
        return cmd_submit(root, args.spec)
    if args.verb == "status":
        return cmd_status(root, args.run_id, args.since_offset)
    if args.verb == "result":
        return cmd_result(root, args.run_id)
    if args.verb == "cancel":
        return cmd_cancel(root, args.run_id)
    if args.verb == "watch":
        return cmd_watch(root, args.run_id, args.interval)
    if args.verb == "runs":
        return cmd_runs(root)
    if args.verb == "prune":
        return cmd_prune(root, args.dry_run)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
