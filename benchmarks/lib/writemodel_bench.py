#!/usr/bin/env python3
"""oficina write-model benchmark harness (T-104).

Per (task, arm, run): build the arm's prompt, call the model once, apply the output via the arm's
mechanism, run the tests split into target vs regression, record a row. Aggregated BY SIZE BUCKET
per the pre-registered decision rule (`ref:oficina-write-model-benchmark`).

Invoke via the wrapper: benchmarks/lib/run-write-model-bench.sh  (do not call directly).

Arms:
  A code-anchored  — model returns only the function; code locates the span and applies it.
  B whole-file     — model returns the complete file; overwrite.
  C model-anchored — model returns SEARCH/REPLACE blocks; apply by exact match (loud fail on miss).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "personas" / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ollama_client import ollama_chat  # noqa: E402

from writemodel_apply import (  # noqa: E402
    apply_code_anchored,
    apply_search_replace,
    apply_whole_file,
    locate_function,
    strip_code_fences,
)
from writemodel_corpus import Task, generate_corpus  # noqa: E402

ARMS = ("code_anchored", "whole_file", "model_anchored")

_SYSTEM = "You are a precise Python engineer. Output only what is asked — no explanation."


def _function_source(task: Task) -> str:
    """The current source text of the task's target function (for the code-anchored prompt)."""
    span = locate_function(task.source, task.target_fn)
    if span is None:
        return ""
    start, end = span
    return "".join(task.source.splitlines(keepends=True)[start - 1 : end])


def build_prompt(task: Task, arm: str) -> str:
    """The arm's prompt. Each arm gets the minimal ask its mechanism needs (deliberately not
    controlled — 'which ask yields better code' is part of the write-model question)."""
    if arm == "code_anchored":
        return (
            f"{task.behavior}\n\nHere is the current function:\n\n"
            f"```python\n{_function_source(task)}```\n\n"
            "Return ONLY the complete rewritten function definition. No other text, no fences."
        )
    if arm == "whole_file":
        return (
            f"{task.behavior}\n\nHere is the complete file:\n\n"
            f"```python\n{task.source}```\n\n"
            "Return the COMPLETE modified file, with every other function unchanged. "
            "No other text, no fences."
        )
    if arm == "model_anchored":
        return (
            f"{task.behavior}\n\nHere is the complete file:\n\n"
            f"```python\n{task.source}```\n\n"
            "Return one or more edit blocks in this EXACT format (verbatim search text):\n"
            "<<<<<<< SEARCH\n<lines to find>\n=======\n<replacement lines>\n>>>>>>> REPLACE"
        )
    raise ValueError(f"unknown arm: {arm}")


def call_model(prompt: str, model: str, timeout: int) -> tuple[str, int]:
    """One model call; single retry on a cold-start timeout. Returns (content, eval_count)."""
    for attempt in (1, 2):
        try:
            resp = ollama_chat(prompt, model=model, system=_SYSTEM, timeout=timeout, keep_alive="10m")
            return resp["content"], int(resp.get("eval_count") or 0)
        except TimeoutError:
            if attempt == 2:
                raise
            time.sleep(3)
    return "", 0


def apply_output(task: Task, arm: str, content: str) -> str | None:
    """Apply the (defenced) model output via the arm's mechanism. None = apply failed."""
    text = strip_code_fences(content)
    if arm == "code_anchored":
        return apply_code_anchored(task.source, task.target_fn, text)
    if arm == "whole_file":
        return apply_whole_file(text)
    if arm == "model_anchored":
        return apply_search_replace(task.source, text)
    raise ValueError(f"unknown arm: {arm}")


def _pytest(tmp: Path, *node_args: str) -> bool:
    """Run pytest in tmp; True iff exit 0."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", *node_args],
        cwd=str(tmp),
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def run_tests(new_source: str, task: Task) -> tuple[bool, bool]:
    """Write the edited module + tests to a temp dir; return (target_pass, no_regression)."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        (tmp / "module_under_test.py").write_text(new_source, encoding="utf-8")
        (tmp / "test_gen.py").write_text(task.tests, encoding="utf-8")
        target_pass = _pytest(tmp, f"test_gen.py::{task.target_test}")
        no_regression = _pytest(tmp, "test_gen.py", "--deselect", f"test_gen.py::{task.target_test}")
        return target_pass, no_regression


def run_cell(task: Task, arm: str, model: str, run_idx: int, timeout: int) -> dict:
    """One (task, arm, run) → a record row."""
    t0 = time.perf_counter()
    error = None
    applied = False
    target_pass = no_regression = False
    eval_count = 0
    try:
        content, eval_count = call_model(build_prompt(task, arm), model, timeout)
        new_source = apply_output(task, arm, content)
        applied = new_source is not None
        if applied:
            target_pass, no_regression = run_tests(new_source, task)
    except Exception as exc:  # noqa: BLE001 — a failed cell must not abort the run
        error = f"{type(exc).__name__}: {exc}"
    return {
        "task": task.name,
        "bucket": task.bucket,
        "arm": arm,
        "run": run_idx,
        "applied": applied,
        "target_pass": target_pass,
        "no_regression": no_regression,
        "combined": applied and target_pass and no_regression,
        "eval_count": eval_count,
        "ms": round((time.perf_counter() - t0) * 1000),
        "error": error,
    }


def run_all(tasks, arms, model, runs, timeout, out_path):
    """Serial sweep (VRAM ceiling). Append each record to JSONL as it lands (crash-survivable)."""
    records = []
    total = len(tasks) * len(arms) * runs
    n = 0
    with open(out_path, "w", encoding="utf-8") as fh:
        for task in tasks:
            for arm in arms:
                for run_idx in range(runs):
                    n += 1
                    rec = run_cell(task, arm, model, run_idx, timeout)
                    records.append(rec)
                    fh.write(json.dumps(rec) + "\n")
                    fh.flush()
                    flag = "OK " if rec["combined"] else ("app" if rec["applied"] else "FAIL")
                    print(f"[{n:>3}/{total}] {task.name:<18} {arm:<15} {flag} "
                          f"tgt={int(rec['target_pass'])} reg={int(rec['no_regression'])} "
                          f"{rec['ms']}ms", flush=True)
    return records


def _rate(rows, key):
    return round(100 * sum(r[key] for r in rows) / len(rows)) if rows else 0


def report(records):
    """Print rates BY SIZE BUCKET × arm (never aggregate — the pre-registered rule)."""
    print("\n" + "=" * 78)
    print("WRITE-MODEL BENCHMARK — rates by size bucket (higher = better)")
    print("=" * 78)
    for bucket in ("small", "medium", "large"):
        brows = [r for r in records if r["bucket"] == bucket]
        if not brows:
            continue
        print(f"\n{bucket.upper()}  (n={len(brows) // len(ARMS)} tasks × runs per arm)")
        print(f"  {'arm':<15} {'applied':>8} {'target':>8} {'no-reg':>8} {'COMBINED':>9} {'toks':>7}")
        for arm in ARMS:
            rows = [r for r in brows if r["arm"] == arm]
            if not rows:
                continue
            toks = round(sum(r["eval_count"] for r in rows) / len(rows))
            print(f"  {arm:<15} {_rate(rows,'applied'):>7}% {_rate(rows,'target_pass'):>7}% "
                  f"{_rate(rows,'no_regression'):>7}% {_rate(rows,'combined'):>8}% {toks:>7}")
    errs = [r for r in records if r["error"]]
    if errs:
        print(f"\n{len(errs)} cell error(s); first: {errs[0]['error']}")


def main():
    p = argparse.ArgumentParser(description="oficina write-model benchmark")
    p.add_argument("--model", default="my-python-q25c14")
    p.add_argument("--arms", default=",".join(ARMS), help="comma-separated subset of arms")
    p.add_argument("--per-bucket", type=int, default=4, help="tasks per size bucket")
    p.add_argument("--buckets", default="small,medium,large")
    p.add_argument("--runs", type=int, default=3, help="runs per (task, arm) cell")
    p.add_argument("--timeout", type=int, default=180)
    p.add_argument("--out", default=None, help="JSONL output path")
    p.add_argument("--limit", type=int, default=None, help="cap total tasks (smoke testing)")
    args = p.parse_args()

    arms = [a for a in args.arms.split(",") if a in ARMS]
    buckets = set(args.buckets.split(","))
    tasks = [t for t in generate_corpus(args.per_bucket) if t.bucket in buckets]
    if args.limit:
        tasks = tasks[: args.limit]
    out_path = args.out or str(REPO_ROOT / "benchmarks" / "results" / "write-model-bench.jsonl")

    print(f"model={args.model} arms={arms} tasks={len(tasks)} runs={args.runs} "
          f"→ {len(tasks) * len(arms) * args.runs} generations\nout={out_path}\n")
    records = run_all(tasks, arms, args.model, args.runs, args.timeout, out_path)
    report(records)


if __name__ == "__main__":
    main()
