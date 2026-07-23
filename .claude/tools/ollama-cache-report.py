#!/usr/bin/env python3
"""Prefix-cache reuse report over the ollama-bridge call log (T-110 acceptance criterion 5).

Ollama reuses the KV prefix implicitly; the ONLY honest reuse signal is
prompt_eval_duration collapsing per token on later calls of the same run —
prompt_eval_count always reports the FULL token count even when the prefix was
reused (`ref:oficina-p2-cache-measurement`). This tool derives, at read time, a
per-run reuse verdict from the raw log. Runs with a single call report "n/a":
tests-as-context usually converges iteration 1, so multi-call runs are the
interesting (and rare) case — a NO-REUSE verdict there means the stable prompt
prefix lost byte-stability and should be investigated.

Deferred alternative (option B, session 126): thread prompt-eval telemetry into
GenerationResult + the IterationEvaluated ledger payload so run forensics show
reuse inline without joining calls.jsonl. Trigger: needing cache visibility in
run_status / the runs-scan hook. Until then this read-side view is the tracker
(log raw, derive at read time — T-95(b)/T-99(b) keep per-call telemetry in
calls.jsonl only).
"""

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CallRecord:
    run_id: str
    prompt_eval_duration_ms: float
    prompt_eval_count: int
    ts: str
    model: str


def _parse_record(line: str) -> "CallRecord | None":
    """A qualifying call record, or None (verdict records and partial lines lack the fields)."""
    try:
        record = json.loads(line)
        return CallRecord(
            run_id=record["run_id"],
            prompt_eval_duration_ms=float(record["prompt_eval_duration_ms"]),
            prompt_eval_count=int(record["prompt_eval_count"]),
            ts=record["ts"],
            model=record.get("model", "unknown"),
        )
    except (KeyError, ValueError, json.JSONDecodeError):
        return None


def _ms_per_token(call: CallRecord) -> float:
    return call.prompt_eval_duration_ms / call.prompt_eval_count


def _run_verdict(run_calls: "list[CallRecord]") -> str:
    """REUSED / NO REUSE / n-a for one run's chronologically ordered calls."""
    if len(run_calls) < 2:
        return "n/a (single call — nothing to compare)"
    base = _ms_per_token(run_calls[0])
    ratios = [_ms_per_token(call) / base for call in run_calls[1:]]
    if any(ratio < 0.5 for ratio in ratios):
        return f"REUSED (prefix cache hit) — best {min(ratios):.2f}x of cold"
    return "NO REUSE — investigate stable-prefix byte-stability"


def _run_report_block(run_id: str, calls: "list[CallRecord]") -> str:
    lines = [f"{run_id}  ({calls[0].model})"]
    for idx, call in enumerate(calls, start=1):
        lines.append(
            f"  {idx}: {call.prompt_eval_count} tok, "
            f"{call.prompt_eval_duration_ms:.0f} ms, {_ms_per_token(call):.2f} ms/tok"
        )
    return "\n".join(lines)


def _read_qualifying_records(log_path: Path) -> "tuple[list[CallRecord], int]":
    records, skipped = [], 0
    with log_path.open("r", encoding="utf-8") as file:
        for line in file:
            record = _parse_record(line)
            if record and record.prompt_eval_count > 0:
                records.append(record)
            else:
                skipped += 1
    return records, skipped


def _group_by_run(records: "list[CallRecord]") -> "dict[str, list[CallRecord]]":
    runs = defaultdict(list)
    for record in records:
        runs[record.run_id].append(record)
    return {run_id: sorted(calls, key=lambda c: c.ts) for run_id, calls in runs.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--log",
        type=Path,
        default=Path("~/.local/share/ollama-bridge/calls.jsonl").expanduser(),
        help="override the log path",
    )
    parser.add_argument("--run", help="report only this run_id")
    args = parser.parse_args()

    if not args.log.exists():
        print(f"log not found: {args.log}", file=sys.stderr)
        return

    records, skipped = _read_qualifying_records(args.log)
    runs = _group_by_run(records)
    if args.run:
        runs = {run_id: calls for run_id, calls in runs.items() if run_id == args.run}

    counts = {"REUSED": 0, "NO REUSE": 0, "n/a": 0}
    for run_id, calls in sorted(runs.items(), key=lambda item: item[1][0].ts):
        verdict = _run_verdict(calls)
        print(_run_report_block(run_id, calls))
        print(f"  → {verdict}\n")
        counts[next(k for k in counts if verdict.startswith(k))] += 1

    print(
        f"{len(runs)} run(s): {counts['REUSED']} reused, {counts['NO REUSE']} no-reuse, "
        f"{counts['n/a']} n/a  ({skipped} non-qualifying lines skipped)"
    )


if __name__ == "__main__":
    main()
